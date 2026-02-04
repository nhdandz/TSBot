"""Query processing components (Analysis & Expansion)."""

import re
from typing import Any, Dict, List, Optional

class QueryAnalyzer:
    """Analyze query intent using regex patterns."""

    INTENT_PATTERNS = {
        "specific": [
            r"(thời hạn|deadline|bao lâu|khi nào|ngày nào|thời gian)",
            r"(điều kiện|yêu cầu|quy định|tiêu chuẩn) (gì|nào|là gì)",
            r"(có cần|phải|bắt buộc|yêu cầu).*không",
            r"(địa chỉ|nơi|ở đâu|liên hệ)",
            r"(số lượng|bao nhiêu|mấy)",
            r"(điểm chuẩn|bao nhiêu điểm|lấy bao nhiêu)",
        ],
        "comparison": [
            r"(khác nhau|khác biệt|so sánh|giống nhau)",
            r"(.*) và (.*) (khác|giống)",
            r"(chọn|lựa chọn).*(hay|hoặc)",
            r"(nên).*(hay).*",
        ],
        "list": [
            r"(có những|bao gồm|gồm có|liệt kê|danh sách)",
            r"(các|những) (.*) (nào|gì)",
            r"(tất cả|toàn bộ|đầy đủ)",
            r"(danh mục|hệ thống)",
        ],
        "explanation": [
            r"(tại sao|vì sao|lý do|nguyên nhân)",
            r"(như thế nào|thế nào|cách nào|làm sao)",
            r"(giải thích|giải|mô tả|nói rõ)",
            r"(ý nghĩa|nghĩa là gì|có nghĩa)",
            r"(hướng dẫn|cách thức|thủ tục)",
        ],
    }

    @staticmethod
    def analyze(query: str) -> Dict[str, Any]:
        """Analyze query and return intent + confidence.
        
        Args:
            query: User input query.
            
        Returns:
            Dictionary with 'intent', 'confidence', 'matched_patterns'.
        """
        query_lower = query.lower()
        scores = {}

        for intent, patterns in QueryAnalyzer.INTENT_PATTERNS.items():
            score = 0
            matched_patterns = []

            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
                    matched_patterns.append(pattern)

            scores[intent] = {
                "score": score,
                "patterns": matched_patterns
            }

        # Find best intent
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1]["score"])
            if best_intent[1]["score"] > 0:
                return {
                    "intent": best_intent[0],
                    "confidence": min(best_intent[1]["score"] / 2, 1.0),
                    "matched_patterns": best_intent[1]["patterns"]
                }

        return {
            "intent": "general",
            "confidence": 0.5,
            "matched_patterns": []
        }


class QueryExpander:
    """Expand queries using synonyms and intent-based rules."""

    # Default synonyms for military admissions domain
    SYNONYMS = {
        'học viện': ['trường', 'cơ sở đào tạo'],
        'thi vào': ['tuyển sinh', 'dự tuyển', 'xét tuyển', 'đăng ký'],
        'hồ sơ': ['giấy tờ', 'thủ tục'],
        'sức khỏe': ['thể lực', 'y tế'],
        'chính trị': ['lý lịch'],
        'điểm chuẩn': ['điểm trúng tuyển', 'điểm xét tuyển', 'mức điểm'],
        'ngành': ['chuyên ngành', 'lĩnh vực'],
    }

    @staticmethod
    def expand(query: str, intent: str) -> List[str]:
        """Generate query variations.
        
        Args:
            query: Original query.
            intent: Detected intent.
            
        Returns:
            List of query variations including original.
        """
        variations = [query]
        query_lower = query.lower()

        # 1. Synonym expansion
        for term, synonyms in QueryExpander.SYNONYMS.items():
            if term in query_lower:
                for synonym in synonyms[:1]:  # Limit to 1 synonym to avoid explosion
                    expanded = query_lower.replace(term, synonym)
                    if expanded not in variations:
                        variations.append(expanded)

        # 2. Intent-based expansion
        if intent == "specific":
            if "thời hạn" in query_lower:
                variations.append(f"{query} quy định")
                variations.append(f"thời gian {query}")
            elif any(word in query_lower for word in ['có thể', 'được không', 'có được']):
                variations.append(f"tiêu chuẩn {query}")
                variations.append(f"quy định {query}")

        elif intent == "list":
            variations.append(f"{query} bao gồm")
            variations.append(f"danh sách {query}")

        elif intent == "explanation":
            variations.append(f"giải thích {query}")
            variations.append(f"{query} như thế nào")
            variations.append(f"hướng dẫn {query}")

        # Deduplicate and limit
        # dict.fromkeys preserves order
        variations = list(dict.fromkeys(variations))
        return variations[:3]
