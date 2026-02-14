"""Supervisor Agent using LangGraph for orchestrating multi-agent system."""

import logging
import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.rag_agent import RAGAgent, get_rag_agent
from src.agents.sql_agent import SQLAgent, get_sql_agent
from src.core.llm import get_llm_service
from src.routers.semantic_router import SemanticRouter, get_semantic_router

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents available."""

    SQL = "sql"
    RAG = "rag"
    GENERAL = "general"


class ConversationState(TypedDict):
    """State maintained throughout the conversation."""

    # Input
    messages: Annotated[list[dict], operator.add]
    current_query: str

    # Routing
    intent: Optional[str]
    agent_type: Optional[AgentType]

    # Execution
    sql_result: Optional[dict]
    rag_result: Optional[dict]

    # Output
    response: Optional[str]
    sources: list[dict]

    # Control
    needs_clarification: bool
    error: Optional[str]
    iteration: int


# Prompts
PLANNING_PROMPT = """Bạn là Supervisor Agent điều phối hệ thống tư vấn tuyển sinh quân sự Việt Nam.

Phân tích câu hỏi của người dùng và quyết định cách xử lý:

1. **SQL Agent**: Cho câu hỏi về điểm chuẩn, chỉ tiêu, so sánh điểm
   - "Điểm chuẩn Học viện Kỹ thuật Quân sự?"
   - "Với 25 điểm, tôi vào được trường nào?"
   - "So sánh điểm năm 2023 và 2024"

2. **RAG Agent**: Cho câu hỏi về quy định, tiêu chuẩn, thủ tục
   - "Tiêu chuẩn sức khỏe để thi vào quân đội?"
   - "Quy trình đăng ký xét tuyển?"
   - "Đối tượng được ưu tiên?"

3. **General**: Cho câu hỏi chung, chào hỏi, hỏi về hệ thống
   - "Xin chào"
   - "Bạn có thể giúp gì?"
   - "Cảm ơn"

4. **Clarification**: Khi câu hỏi không rõ ràng

Câu hỏi: {query}
Lịch sử hội thoại: {history}

Trả về JSON:
{{
    "agent": "sql/rag/general/clarification",
    "confidence": 0.0-1.0,
    "reason": "lý do ngắn gọn",
    "clarification_question": "câu hỏi làm rõ nếu cần"
}}"""


COMBINE_PROMPT = """Tổng hợp kết quả từ các nguồn sau để trả lời câu hỏi người dùng.

Câu hỏi: {query}

Kết quả SQL (điểm chuẩn):
{sql_result}

Kết quả RAG (quy định):
{rag_result}

Hãy tổng hợp thành câu trả lời hoàn chỉnh, rõ ràng, dễ hiểu bằng tiếng Việt.
Nếu có cả số liệu và quy định, kết hợp chúng một cách logic."""


GENERAL_PROMPT = """Bạn là trợ lý tư vấn tuyển sinh quân sự Việt Nam.

Trả lời câu hỏi sau một cách thân thiện và hữu ích:

Câu hỏi: {query}

Nếu là chào hỏi, hãy chào lại và giới thiệu bạn có thể giúp:
- Tra cứu điểm chuẩn các trường quân đội
- Giải đáp về tiêu chuẩn, quy định tuyển sinh
- Tư vấn chọn trường phù hợp

Trả lời ngắn gọn, thân thiện."""


class SupervisorAgent:
    """Supervisor Agent for orchestrating the multi-agent system."""

    def __init__(
        self,
        sql_agent: Optional[SQLAgent] = None,
        rag_agent: Optional[RAGAgent] = None,
        router: Optional[SemanticRouter] = None,
        enable_memory: bool = True,
    ):
        """Initialize Supervisor Agent.

        Args:
            sql_agent: SQL Agent instance.
            rag_agent: RAG Agent instance.
            router: Semantic Router instance.
            enable_memory: Enable conversation memory.
        """
        self.sql_agent = sql_agent or get_sql_agent()
        self.rag_agent = rag_agent or get_rag_agent()
        self.router = router or get_semantic_router()
        self.llm_service = get_llm_service()

        # Build the workflow graph
        self.memory = MemorySaver() if enable_memory else None
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Returns:
            Compiled state graph.
        """
        # Create workflow
        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("route", self._route_node)
        workflow.add_node("sql_agent", self._sql_node)
        workflow.add_node("rag_agent", self._rag_node)
        workflow.add_node("general", self._general_node)
        workflow.add_node("combine", self._combine_node)
        workflow.add_node("clarify", self._clarify_node)

        # Set entry point
        workflow.set_entry_point("route")

        # Add conditional edges from router
        workflow.add_conditional_edges(
            "route",
            self._decide_next,
            {
                "sql": "sql_agent",
                "rag": "rag_agent",
                "general": "general",
                "clarify": "clarify",
                "both": "sql_agent",  # Start with SQL when both needed
            },
        )

        # SQL agent can lead to RAG or end
        workflow.add_conditional_edges(
            "sql_agent",
            self._after_sql,
            {
                "rag": "rag_agent",
                "combine": "combine",
                "end": END,
            },
        )

        # RAG agent leads to combine or end
        workflow.add_edge("rag_agent", "combine")

        # Other nodes lead to end
        workflow.add_edge("general", END)
        workflow.add_edge("combine", END)
        workflow.add_edge("clarify", END)

        # Compile with memory
        return workflow.compile(checkpointer=self.memory)

    async def _route_node(self, state: ConversationState) -> dict:
        """Route the query to appropriate agent.

        Args:
            state: Current conversation state.

        Returns:
            Updated state with routing decision.
        """
        import traceback

        print(f"[DEBUG] _route_node called")

        query = state["current_query"]
        messages = state.get("messages", [])
        print(f"[DEBUG] Processing query: {query[:50]}...")

        # Try semantic router first for fast routing
        try:
            print("[DEBUG] Calling semantic router...")
            route_result = await self.router.route(query)
            print(f"[DEBUG] Semantic router returned: {type(route_result)}, value={route_result}")

            if route_result is None:
                print("[DEBUG] Semantic router returned None")
                raise ValueError("Router returned None")

            print(f"[DEBUG] Route result keys: {list(route_result.keys()) if isinstance(route_result, dict) else 'not a dict'}")
            intent = route_result.get("intent", "unknown")
            confidence = route_result.get("confidence", 0.0)

            print(f"[DEBUG] Semantic router result: intent={intent}, confidence={confidence:.3f}")

            if confidence > 0.85:
                # Complete mapping for all intents from intents.json
                agent_mapping = {
                    # SQL Agent - tra cứu điểm, chỉ tiêu
                    "score_lookup": AgentType.SQL,
                    "score_check": AgentType.SQL,
                    "quota_lookup": AgentType.SQL,

                    # RAG Agent - quy định, tiêu chuẩn, thủ tục
                    "regulation_health": AgentType.RAG,
                    "regulation_politics": AgentType.RAG,
                    "regulation_academic": AgentType.RAG,
                    "regulation_age": AgentType.RAG,
                    "procedure_registration": AgentType.RAG,
                    "procedure_documents": AgentType.RAG,
                    "procedure_exam": AgentType.RAG,
                    "faq_benefits": AgentType.RAG,
                    "faq_life": AgentType.RAG,
                    "faq_career": AgentType.RAG,
                    "faq_female": AgentType.RAG,
                    "priority": AgentType.RAG,
                    "school_info": AgentType.RAG,

                    # General Agent - chào hỏi, về bot
                    "greeting": AgentType.GENERAL,
                    "about_bot": AgentType.GENERAL,
                    "unclear": AgentType.GENERAL,

                    # Comparison - bắt đầu với SQL
                    "comparison": AgentType.SQL,
                }

                # Get agent type, with smart fallback for unknown intents
                agent_type = agent_mapping.get(intent)

                if agent_type is None:
                    # Fallback based on intent name pattern
                    if intent.startswith("regulation_") or intent.startswith("procedure_") or intent.startswith("faq_"):
                        agent_type = AgentType.RAG
                    elif intent.startswith("score_") or intent.startswith("quota_"):
                        agent_type = AgentType.SQL
                    else:
                        agent_type = AgentType.GENERAL
                    logger.warning(f"Unknown intent '{intent}', falling back to {agent_type}")

                logger.info(f"Routing to {agent_type} for intent '{intent}'")

                return {
                    "intent": intent,
                    "agent_type": agent_type,
                }
        except Exception as e:
            print(f"[DEBUG] Semantic router failed: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")

        # Fall back to LLM-based planning
        print("[DEBUG] Falling back to LLM-based planning")
        history_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in messages[-5:]  # Last 5 messages
        ]) if messages else "Không có lịch sử"

        prompt = PLANNING_PROMPT.format(query=query, history=history_text)

        try:
            print("[DEBUG] Calling LLM generate_with_json...")
            response = await self.llm_service.generate_with_json(
                prompt=prompt,
                use_grader=False,
            )
            print(f"[DEBUG] LLM response: {type(response)}, value={response}")

            if response is None:
                print("[DEBUG] LLM returned None response, defaulting to GENERAL")
                return {
                    "intent": "general",
                    "agent_type": AgentType.GENERAL,
                }

            agent_str = response.get("agent", "general") if isinstance(response, dict) else "general"
            agent_type = {
                "sql": AgentType.SQL,
                "rag": AgentType.RAG,
                "general": AgentType.GENERAL,
                "clarification": None,  # Special case
            }.get(agent_str, AgentType.GENERAL)

            print(f"[DEBUG] LLM planning result: agent={agent_str}, agent_type={agent_type}")

            return {
                "intent": agent_str,
                "agent_type": agent_type,
                "needs_clarification": agent_str == "clarification",
            }

        except Exception as e:
            print(f"[DEBUG] Planning failed: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return {
                "intent": "general",
                "agent_type": AgentType.GENERAL,
                "error": str(e),
            }

    def _decide_next(self, state: ConversationState) -> str:
        """Decide next node based on routing.

        Args:
            state: Current state.

        Returns:
            Next node name.
        """
        if state.get("needs_clarification"):
            logger.info("Decision: clarify (needs_clarification=True)")
            return "clarify"

        agent_type = state.get("agent_type")
        intent = state.get("intent")

        if agent_type == AgentType.SQL:
            logger.info(f"Decision: sql (intent={intent}, agent_type={agent_type})")
            return "sql"
        elif agent_type == AgentType.RAG:
            logger.info(f"Decision: rag (intent={intent}, agent_type={agent_type})")
            return "rag"
        else:
            logger.info(f"Decision: general (intent={intent}, agent_type={agent_type})")
            return "general"

    async def _sql_node(self, state: ConversationState) -> dict:
        """Execute SQL Agent.

        Args:
            state: Current state.

        Returns:
            Updated state with SQL results.
        """
        query = state["current_query"]

        try:
            result = await self.sql_agent.process_query(query)
            return {
                "sql_result": result,
                "response": result.get("answer"),
            }
        except Exception as e:
            logger.error(f"SQL Agent error: {e}")
            return {
                "sql_result": {"error": str(e)},
                "error": str(e),
            }

    def _after_sql(self, state: ConversationState) -> str:
        """Decide what to do after SQL agent.

        Args:
            state: Current state.

        Returns:
            Next node name.
        """
        sql_result = state.get("sql_result") or {}

        # If SQL has results, we're done
        if sql_result.get("results"):
            return "end"

        # SQL returned no results - only fallback to RAG if the intent
        # was originally ambiguous (routed as "both"). Otherwise, the user
        # asked a data question and RAG will give irrelevant legal text.
        intent = state.get("intent", "")
        if intent in ("both", "rag"):
            return "rag"

        # For pure SQL queries with no results, end with SQL's own message
        # (e.g. "Không tìm thấy dữ liệu phù hợp")
        return "end"

    async def _rag_node(self, state: ConversationState) -> dict:
        """Execute RAG Agent.

        Args:
            state: Current state.

        Returns:
            Updated state with RAG results.
        """
        query = state["current_query"]

        try:
            result = await self.rag_agent.process_query(query)
            return {
                "rag_result": result,
                "response": result.get("answer"),
                "sources": result.get("sources", []),
            }
        except Exception as e:
            logger.error(f"RAG Agent error: {e}")
            return {
                "rag_result": {"error": str(e)},
                "error": str(e),
            }

    async def _general_node(self, state: ConversationState) -> dict:
        """Handle general queries.

        Args:
            state: Current state.

        Returns:
            Updated state with general response.
        """
        query = state["current_query"]

        prompt = GENERAL_PROMPT.format(query=query)
        response = await self.llm_service.generate(prompt=prompt)

        return {
            "response": response,
        }

    async def _combine_node(self, state: ConversationState) -> dict:
        """Combine results from multiple agents.

        Args:
            state: Current state.

        Returns:
            Updated state with combined response.
        """
        query = state["current_query"]
        # Use 'or {}' to handle None values (state.get returns None if key exists with None value)
        sql_result = state.get("sql_result") or {}
        rag_result = state.get("rag_result") or {}

        print(f"[DEBUG] _combine_node: sql_result={type(sql_result)}, rag_result={type(rag_result)}")

        # If only RAG has results, use that
        if not sql_result.get("results") and rag_result.get("answer"):
            return {"response": rag_result["answer"]}

        # If only SQL has results, use that
        if sql_result.get("answer") and not rag_result.get("answer"):
            return {"response": sql_result["answer"]}

        # If neither has results
        if not sql_result.get("answer") and not rag_result.get("answer"):
            return {"response": "Xin lỗi, tôi không tìm thấy thông tin liên quan. Vui lòng thử hỏi cách khác."}

        # Combine both results
        prompt = COMBINE_PROMPT.format(
            query=query,
            sql_result=sql_result.get("answer", "Không có kết quả"),
            rag_result=rag_result.get("answer", "Không có kết quả"),
        )

        response = await self.llm_service.generate(prompt=prompt)

        # Combine sources
        sources = state.get("sources") or []
        if sql_result.get("sql"):
            sources.append({"type": "sql", "query": sql_result["sql"]})

        return {
            "response": response,
            "sources": sources,
        }

    async def _clarify_node(self, state: ConversationState) -> dict:
        """Ask for clarification.

        Args:
            state: Current state.

        Returns:
            Updated state with clarification question.
        """
        query = state["current_query"]

        response = (
            f"Tôi cần thêm thông tin để trả lời câu hỏi của bạn.\n\n"
            f"Bạn muốn hỏi về:\n"
            f"1. Điểm chuẩn/chỉ tiêu tuyển sinh?\n"
            f"2. Tiêu chuẩn/điều kiện xét tuyển?\n"
            f"3. Quy trình/thủ tục đăng ký?\n\n"
            f"Vui lòng nói rõ hơn để tôi có thể giúp bạn tốt hơn."
        )

        return {
            "response": response,
            "needs_clarification": True,
        }

    async def process(
        self,
        query: str,
        session_id: str = "default",
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Process a user query through the supervisor.

        Args:
            query: User's question.
            session_id: Session ID for memory.
            context: Optional additional context.

        Returns:
            Response dictionary.
        """
        import traceback
        print(f"[DEBUG] SupervisorAgent.process called with query: {query[:50]}...")

        # Initialize state
        initial_state: ConversationState = {
            "messages": [{"role": "user", "content": query}],
            "current_query": query,
            "intent": None,
            "agent_type": None,
            "sql_result": None,
            "rag_result": None,
            "response": None,
            "sources": [],
            "needs_clarification": False,
            "error": None,
            "iteration": 0,
        }

        # Run the graph
        config = {"configurable": {"thread_id": session_id}}

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            return {
                "query": query,
                "response": final_state.get("response", "Xin lỗi, tôi không thể xử lý yêu cầu này."),
                "intent": final_state.get("intent"),
                "sources": final_state.get("sources", []),
                "error": final_state.get("error"),
            }

        except Exception as e:
            import traceback
            print(f"[DEBUG] Supervisor error: {e}")
            print(f"[DEBUG] Full traceback:\n{traceback.format_exc()}")
            return {
                "query": query,
                "response": "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
                "error": str(e),
            }

    async def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session.

        Args:
            session_id: Session ID.

        Returns:
            List of messages.
        """
        if not self.memory:
            return []

        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await self.graph.aget_state(config)
            return state.values.get("messages", [])
        except Exception:
            return []


# Factory function
_supervisor_instance: Optional[SupervisorAgent] = None


def get_supervisor_agent() -> SupervisorAgent:
    """Get global Supervisor Agent instance."""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = SupervisorAgent()
    return _supervisor_instance
