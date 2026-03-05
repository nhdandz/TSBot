"""Supervisor Agent using LangGraph for orchestrating multi-agent system."""

import json
import logging
import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, AsyncGenerator, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.rag_agent import RAGAgent, get_rag_agent
from src.agents.sql_agent import SQLAgent, get_sql_agent
from src.core.llm import get_llm_service
from src.database.postgres import get_postgres_db
from src.routers.semantic_router import SemanticRouter, get_semantic_router
from src.utils.vietnamese import VietnameseTextProcessor

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents available."""

    SQL = "sql"
    RAG = "rag"
    GENERAL = "general"
    SCHOOL_INFO = "school_info"


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
    chart_data: Optional[dict]

    # Control
    needs_clarification: bool
    error: Optional[str]
    iteration: int


# Prompts
PLANNING_PROMPT = """Bạn là Supervisor Agent điều phối hệ thống tư vấn tuyển sinh quân sự Việt Nam.

Phân tích câu hỏi của người dùng và quyết định cách xử lý:

1. **sql**: CHỈ cho câu hỏi cần TRA CỨU SỐ LIỆU cụ thể từ database
   - Điểm chuẩn cụ thể: "Điểm chuẩn Học viện KTQS năm 2024?"
   - So sánh điểm số: "So sánh điểm năm 2023 và 2024"
   - Kiểm tra điểm: "Với 25 điểm, tôi vào được trường nào?"
   - Chỉ tiêu tuyển sinh: "Chỉ tiêu năm nay bao nhiêu?"

2. **rag**: Cho câu hỏi về QUY ĐỊNH, TIÊU CHUẨN, THỦ TỤC, ĐIỀU KIỆN (tra cứu văn bản pháp lý)
   - Tiêu chuẩn sức khỏe, chính trị, học lực
   - Quy trình đăng ký, sơ tuyển, thi tuyển
   - Hồ sơ, thủ tục, điều kiện xét tuyển
   - Đối tượng ưu tiên, khu vực tuyển sinh
   - Tổ hợp môn thi, khối thi
   - Quy định về độ tuổi, giới tính
   - Bất kỳ câu hỏi nào liên quan đến luật, quy chế, thông tư

3. **school_info**: Cho câu hỏi giới thiệu, thông tin tổng quan về một trường cụ thể
   - "Giới thiệu về Học viện Kỹ thuật Quân sự"
   - "Học viện Hải quân có những ngành gì?"

4. **general**: CHỈ cho chào hỏi, cảm ơn, hỏi về bot
   - "Xin chào", "Cảm ơn", "Bạn là ai?"

5. **clarification**: Khi câu hỏi không rõ ràng

LƯU Ý QUAN TRỌNG:
- Nếu câu hỏi KHÔNG yêu cầu tra cứu số liệu cụ thể → KHÔNG dùng sql
- Câu hỏi về "tổ hợp xét tuyển", "điều kiện", "quy trình", "tiêu chuẩn" → dùng rag
- Khi không chắc chắn giữa sql và rag → ưu tiên rag

Câu hỏi: {query}
Lịch sử hội thoại: {history}

Trả về JSON:
{{
    "agent": "sql/rag/school_info/general/clarification",
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


EXTRACT_SCHOOL_NAME_PROMPT = """Trích xuất tên trường từ câu hỏi sau. Chỉ trả về tên trường, không giải thích.
Nếu không tìm thấy tên trường, trả về "NONE".

Câu hỏi: {query}
Tên trường:"""

SCHOOL_INFO_PROMPT = """Dựa trên thông tin sau, hãy giới thiệu về trường một cách tự nhiên, thân thiện:

Tên trường: {ten_truong}
Mô tả: {mo_ta}
Địa chỉ: {dia_chi}
Website: {website}
Các ngành đào tạo: {danh_sach_nganh}

Câu hỏi gốc: {query}

Trả lời bằng tiếng Việt, tự nhiên, đầy đủ thông tin. Nếu mô tả trống thì chỉ nêu thông tin cơ bản có sẵn."""

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
        enable_memory: bool = False,
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

        # Build the workflow graph (stateless — memory handled via DB history)
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
        workflow.add_node("school_info", self._school_info_node)
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
                "school_info": "school_info",
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

        # School info can end or fallback to RAG
        workflow.add_conditional_edges(
            "school_info",
            self._after_school_info,
            {"end": END, "rag": "rag_agent"},
        )

        # RAG agent leads to combine or end
        workflow.add_edge("rag_agent", "combine")

        # Other nodes lead to end
        workflow.add_edge("general", END)
        workflow.add_edge("combine", END)
        workflow.add_edge("clarify", END)

        # Stateless compile — history managed via PostgreSQL
        return workflow.compile()

    async def _route_node(self, state: ConversationState) -> dict:
        """Route the query to appropriate agent.

        Args:
            state: Current conversation state.

        Returns:
            Updated state with routing decision.
        """
        query = state["current_query"]
        messages = state.get("messages", [])
        logger.debug(f"_route_node called, query: {query[:50]}...")

        # Pre-check: chart/trend queries always go to SQL agent
        _chart_kw = [
            "biểu đồ", "bieu do", "xu hướng", "xu huong",
            "diễn biến", "dien bien", "theo năm", "theo nam",
            "so sánh qua các năm", "qua cac nam", "chart", "trend",
        ]
        _score_kw = ["điểm chuẩn", "diem chuan", "điểm", "diem", "chỉ tiêu"]
        _q_lower = query.lower()
        if (
            any(kw in _q_lower for kw in _chart_kw)
            and any(kw in _q_lower for kw in _score_kw)
        ):
            logger.debug("Pre-check: chart+score query → forcing SQL agent")
            return {"intent": "score_lookup", "agent_type": AgentType.SQL}

        # Try semantic router first for fast routing
        try:
            route_result = await self.router.route(query)
            logger.debug(f"Semantic router returned: intent={route_result.get('intent') if route_result else None}")

            if route_result is None:
                raise ValueError("Router returned None")

            intent = route_result.get("intent", "unknown")
            confidence = route_result.get("confidence", 0.0)

            logger.debug(f"Semantic router result: intent={intent}, confidence={confidence:.3f}")

            # Use best intent from all_scores if confidence is close but below threshold
            if intent == "unknown" and confidence > 0.75:
                all_scores = route_result.get("all_scores", {})
                if all_scores:
                    best_intent = max(all_scores, key=all_scores.get)
                    intent = best_intent
                    confidence = all_scores[best_intent]
                    logger.debug(f"Using best intent from all_scores: {intent}={confidence:.3f}")

            if confidence > 0.75:
                # Complete mapping for all intents from intents.json
                agent_mapping = {
                    # SQL Agent - tra cứu điểm, chỉ tiêu
                    "score_lookup": AgentType.SQL,
                    "score_check": AgentType.SQL,
                    "quota_lookup": AgentType.SQL,

                    # RAG Agent - quy định, tiêu chuẩn, thủ tục
                    "regulation": AgentType.RAG,
                    "regulation_health": AgentType.RAG,
                    "regulation_politics": AgentType.RAG,
                    "regulation_academic": AgentType.RAG,
                    "regulation_age": AgentType.RAG,
                    "procedure": AgentType.RAG,
                    "procedure_registration": AgentType.RAG,
                    "procedure_documents": AgentType.RAG,
                    "procedure_exam": AgentType.RAG,
                    "faq": AgentType.RAG,
                    "faq_benefits": AgentType.RAG,
                    "faq_life": AgentType.RAG,
                    "faq_career": AgentType.RAG,
                    "faq_female": AgentType.RAG,
                    "priority": AgentType.RAG,
                    "school_info": AgentType.SCHOOL_INFO,

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
                    if intent.startswith("regulation") or intent.startswith("procedure") or intent.startswith("faq"):
                        agent_type = AgentType.RAG
                    elif intent.startswith("score") or intent.startswith("quota"):
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
            logger.warning(f"Semantic router failed: {e}", exc_info=True)

        # Fall back to LLM-based planning
        logger.debug("Falling back to LLM-based planning")
        history_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in messages[-5:]  # Last 5 messages
        ]) if messages else "Không có lịch sử"

        prompt = PLANNING_PROMPT.format(query=query, history=history_text)

        try:
            response = await self.llm_service.generate_with_json(
                prompt=prompt,
                use_grader=False,
            )
            logger.debug(f"LLM planning response: {response}")

            if response is None:
                logger.warning("LLM returned None response, defaulting to GENERAL")
                return {
                    "intent": "general",
                    "agent_type": AgentType.GENERAL,
                }

            agent_str = response.get("agent", "general") if isinstance(response, dict) else "general"
            agent_type = {
                "sql": AgentType.SQL,
                "rag": AgentType.RAG,
                "school_info": AgentType.SCHOOL_INFO,
                "general": AgentType.GENERAL,
                "clarification": None,  # Special case
            }.get(agent_str, AgentType.GENERAL)

            logger.debug(f"LLM planning result: agent={agent_str}, agent_type={agent_type}")

            return {
                "intent": agent_str,
                "agent_type": agent_type,
                "needs_clarification": agent_str == "clarification",
            }

        except Exception as e:
            logger.error(f"LLM planning failed: {e}", exc_info=True)
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
        elif agent_type == AgentType.SCHOOL_INFO:
            logger.info(f"Decision: school_info (intent={intent}, agent_type={agent_type})")
            return "school_info"
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
                "chart_data": result.get("chart_data"),
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

    async def _school_info_node(self, state: ConversationState) -> dict:
        """Handle school info/introduction queries by fetching from DB.

        Args:
            state: Current state.

        Returns:
            Updated state with school info response.
        """
        query = state["current_query"]

        try:
            # Collapse uppercase sequences (e.g. "HV  KTQS" → "HVKTQS") before expanding
            import re
            query_collapsed = query
            while re.search(r'([A-Z]+)\s+([A-Z]+)', query_collapsed):
                query_collapsed = re.sub(r'([A-Z]+)\s+([A-Z]+)', r'\1\2', query_collapsed)
            # Expand abbreviations (e.g. HVKTQS → học viện kỹ thuật quân sự) then normalize
            query_expanded = VietnameseTextProcessor.expand_abbreviations(query_collapsed)
            query_normalized = VietnameseTextProcessor.normalize_text(query_expanded)
            logger.debug(f"school_info: collapsed='{query_collapsed}', normalized='{query_normalized}'")

            # Fetch all active schools and match against query
            db = get_postgres_db()
            all_schools = await db.fetch_all(
                "SELECT id, ma_truong, ten_truong, ten_khong_dau, loai_truong, dia_chi, website, mo_ta "
                "FROM truong WHERE active = true"
            )

            # Prepare normalized names, use ma_truong as abbreviation from DB
            query_lower = query.lower().strip()
            school_candidates = []
            for s in all_schools:
                ten_kd = s.get("ten_khong_dau") or VietnameseTextProcessor.normalize_text(s["ten_truong"])
                ten_kd = ten_kd.strip().lower()
                s["_ten_kd"] = ten_kd
                s["_ma"] = s.get("ma_truong", "").lower()
                school_candidates.append(s)
            school_candidates.sort(key=lambda s: len(s["_ten_kd"]), reverse=True)

            # Find best matching school: try full name first, then ma_truong (viết tắt)
            school = None
            for s in school_candidates:
                if s["_ten_kd"] in query_normalized:
                    school = s
                    break

            if not school:
                for s in school_candidates:
                    if s["_ma"] and s["_ma"] in query_lower:
                        school = s
                        logger.debug(f"school_info: matched by ma_truong '{s['_ma']}'")
                        break

            if not school:
                logger.debug(f"school_info: no school matched in query '{query_normalized}'")
                return {}

            logger.debug(f"school_info: found '{school['ten_truong']}' (id={school['id']})")

            # Fetch majors for this school
            nganh_list = await db.fetch_all(
                "SELECT ma_nganh, ten_nganh, mo_ta "
                "FROM nganh "
                "WHERE truong_id = :truong_id AND active = true "
                "ORDER BY ten_nganh",
                {"truong_id": school["id"]},
            )

            danh_sach_nganh = ", ".join(
                [f"{n['ten_nganh']} ({n['ma_nganh']})" for n in nganh_list]
            ) if nganh_list else "Chưa có thông tin"

            # Generate response using LLM
            info_prompt = SCHOOL_INFO_PROMPT.format(
                ten_truong=school.get("ten_truong", ""),
                mo_ta=school.get("mo_ta") or "Chưa có mô tả",
                dia_chi=school.get("dia_chi") or "Chưa có thông tin",
                website=school.get("website") or "Chưa có thông tin",
                danh_sach_nganh=danh_sach_nganh,
                query=query,
            )

            response = await self.llm_service.generate(prompt=info_prompt)

            logger.info(f"School info generated for '{school['ten_truong']}'")

            return {
                "response": response,
                "sources": [{"type": "database", "table": "truong", "school": school.get("ten_truong")}],
            }

        except Exception as e:
            logger.error(f"School info node error: {e}")
            return {}

    def _after_school_info(self, state: ConversationState) -> str:
        """Decide what to do after school info node.

        Args:
            state: Current state.

        Returns:
            Next node name.
        """
        if state.get("response"):
            return "end"
        # No response means school not found, fallback to RAG
        logger.info("School info fallback to RAG")
        return "rag"

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

        logger.debug(f"_combine_node: sql has results={bool(sql_result.get('results'))}, rag has answer={bool(rag_result.get('answer'))}")

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
        conversation_history: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Process a user query through the supervisor.

        Args:
            query: User's question.
            session_id: Session ID for memory.
            context: Optional additional context.
            conversation_history: Recent messages from DB (list of {role, content}).

        Returns:
            Response dictionary.
        """
        logger.debug(f"SupervisorAgent.process: query='{query[:50]}...', history={len(conversation_history or [])} messages")

        # Build messages list: history (last 5) + current user message
        prior_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in (conversation_history or [])[-5:]
        ]
        messages = prior_messages + [{"role": "user", "content": query}]

        # Initialize state
        initial_state: ConversationState = {
            "messages": messages,
            "current_query": query,
            "intent": None,
            "agent_type": None,
            "sql_result": None,
            "rag_result": None,
            "response": None,
            "sources": [],
            "chart_data": None,
            "needs_clarification": False,
            "error": None,
            "iteration": 0,
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "query": query,
                "response": final_state.get("response", "Xin lỗi, tôi không thể xử lý yêu cầu này."),
                "intent": final_state.get("intent"),
                "sources": final_state.get("sources", []),
                "chart_data": final_state.get("chart_data"),
                "error": final_state.get("error"),
            }

        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            return {
                "query": query,
                "response": "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
                "error": str(e),
            }

    async def process_stream(
        self,
        query: str,
        session_id: str = "default",
        conversation_history: Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream xử lý query — two-phase: routing+retrieval → stream LLM tokens.

        Yields SSE events:
          {"type": "meta",  "intent": str, "sources": list}
          {"type": "token", "content": str}
          {"type": "done",  "chart_data": dict|None}
          {"type": "error", "message": str}
        """
        from src.core.llm import ServiceUnavailableError
        from src.agents.rag_agent import ANSWER_PROMPT, INTENT_INSTRUCTIONS

        prior_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in (conversation_history or [])[-5:]
        ]
        messages = prior_messages + [{"role": "user", "content": query}]

        initial_state: ConversationState = {
            "messages": messages,
            "current_query": query,
            "intent": None,
            "agent_type": None,
            "sql_result": None,
            "rag_result": None,
            "response": None,
            "sources": [],
            "chart_data": None,
            "needs_clarification": False,
            "error": None,
            "iteration": 0,
        }

        try:
            # Phase 1: Routing (fast, ~100ms)
            route_result = await self._route_node(initial_state)
            intent = route_result.get("intent", "general")
            agent_type = route_result.get("agent_type", AgentType.GENERAL)
            needs_clarification = route_result.get("needs_clarification", False)

            yield {"type": "meta", "intent": intent, "sources": []}

            # Phase 2: Retrieval + Stream LLM
            if needs_clarification:
                response_text = (
                    "Tôi cần thêm thông tin để trả lời câu hỏi của bạn.\n\n"
                    "Bạn muốn hỏi về:\n"
                    "1. Điểm chuẩn/chỉ tiêu tuyển sinh?\n"
                    "2. Tiêu chuẩn/điều kiện xét tuyển?\n"
                    "3. Quy trình/thủ tục đăng ký?\n\n"
                    "Vui lòng nói rõ hơn để tôi có thể giúp bạn tốt hơn."
                )
                yield {"type": "token", "content": response_text}
                yield {"type": "done", "chart_data": None}
                return

            if agent_type == AgentType.GENERAL:
                prompt = GENERAL_PROMPT.format(query=query)
                async for token in self.llm_service.generate_stream(prompt=prompt):
                    yield {"type": "token", "content": token}
                yield {"type": "done", "chart_data": None}
                return

            if agent_type == AgentType.SQL:
                sql_raw = await self.sql_agent.process_query(query, stream=True)
                results = sql_raw.get("raw_results") or []
                entities = sql_raw.get("entities", {})
                chart_data = sql_raw.get("chart_data")

                if not results:
                    yield {"type": "token", "content": "Không tìm thấy dữ liệu phù hợp với yêu cầu của bạn."}
                    yield {"type": "done", "chart_data": None}
                    return

                table = self.sql_agent._build_markdown_table(results)
                score_context = f"\nNgười dùng hỏi với điểm số: {entities['score']}" if entities.get("score") else ""
                prompt = (
                    f"Trả lời câu hỏi dưới đây bằng 1-3 câu ngắn gọn bằng tiếng Việt.\n"
                    f"KHÔNG liệt kê lại dữ liệu vì đã có bảng chi tiết bên dưới.\n"
                    f"Chỉ viết nhận xét/phân tích ngắn.{score_context}\n\n"
                    f"Câu hỏi: {query}\n"
                    f"Dữ liệu ({len(results)} dòng): {json.dumps(results[:20], ensure_ascii=False)}"
                )
                system = "Bạn là trợ lý tư vấn tuyển sinh quân sự. Chỉ viết phần nhận xét, không liệt kê lại bảng dữ liệu."
                async for token in self.llm_service.generate_stream(prompt=prompt, system_prompt=system):
                    yield {"type": "token", "content": token}
                # Append table as final chunk
                yield {"type": "token", "content": f"\n\n{table}"}
                yield {"type": "done", "chart_data": chart_data}
                return

            if agent_type == AgentType.SCHOOL_INFO:
                # Run school info node (DB lookup + LLM) — stream the LLM part
                school_state = dict(initial_state)
                school_result = await self._school_info_node(school_state)
                if school_result.get("response"):
                    sources = school_result.get("sources", [])
                    yield {"type": "meta", "intent": intent, "sources": sources}
                    yield {"type": "token", "content": school_result["response"]}
                    yield {"type": "done", "chart_data": None}
                    return
                # Fallback to RAG if school not found
                agent_type = AgentType.RAG

            # RAG path
            rag_raw = await self.rag_agent.process_query(query, stream=True)
            sources = rag_raw.get("sources", [])
            rag_intent = rag_raw.get("intent", "general")

            yield {"type": "meta", "intent": intent, "sources": sources}

            # Cache hit: rag_agent trả về 'answer' thay vì 'context'
            cached_answer = rag_raw.get("answer")
            if cached_answer:
                yield {"type": "token", "content": cached_answer}
                yield {"type": "done", "chart_data": None}
                return

            context = rag_raw.get("context", "")
            if not context:
                yield {"type": "token", "content": "Không tìm thấy thông tin liên quan trong tài liệu."}
                yield {"type": "done", "chart_data": None}
                return

            intent_instruction = INTENT_INSTRUCTIONS.get(rag_intent, "")
            answer_prompt = ANSWER_PROMPT.format(
                context=context,
                question=query,
                intent_instruction=intent_instruction,
            )
            async for token in self.llm_service.generate_stream(prompt=answer_prompt):
                yield {"type": "token", "content": token}
            yield {"type": "done", "chart_data": None}

        except ServiceUnavailableError as e:
            yield {"type": "error", "message": "Hệ thống AI đang tạm thời bận. Vui lòng thử lại sau ít phút."}
        except Exception as e:
            logger.error(f"process_stream error: {e}", exc_info=True)
            yield {"type": "error", "message": "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại."}


# Factory function
_supervisor_instance: Optional[SupervisorAgent] = None


def get_supervisor_agent() -> SupervisorAgent:
    """Get global Supervisor Agent instance."""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = SupervisorAgent(enable_memory=False)
    return _supervisor_instance
