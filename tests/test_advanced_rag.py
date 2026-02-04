"""Test script for Advanced RAG Agent."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.rag_agent import get_rag_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_rag():
    print("-" * 50)
    print("Testing Advanced RAG Agent")
    print("-" * 50)
    
    agent = get_rag_agent()
    
    queries = [
        "Tiêu chuẩn sức khỏe thi vào Học viện Kỹ thuật Quân sự",
        # Test Cache hit (run same query again)
        "Tiêu chuẩn sức khỏe thi vào Học viện Kỹ thuật Quân sự", 
        # Test Intent (List)
        "Có những trường quân đội nào tuyển sinh nữ?",
        # Test Intent (Explanation)
        "Tại sao phải sơ tuyển khi thi quân đội?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        try:
            result = await agent.process_query(query)
            
            print(f"🎯 Intent: {result.get('intent', 'N/A')}")
            print(f"📚 Retrieved: {result.get('documents_retrieved')} docs")
            print(f"✅ Relevant: {result.get('documents_relevant')} docs")
            print(f"📝 Answer: {result.get('answer')[:150]}...")
            
            if 'sources' in result and result['sources']:
                print(f"🔗 Top Source: {result['sources'][0].get('content_preview', '')[:50]}...")
                
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            
if __name__ == "__main__":
    asyncio.run(test_rag())
