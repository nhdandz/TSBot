"""Hybrid Reranking module combining Cross-Encoder and Metadata."""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import settings

logger = logging.getLogger(__name__)


class HybridReranker:
    """Reranker using Cross-Encoder + Retrieval Score + Metadata Score."""

    def __init__(self):
        """Initialize reranker."""
        self._model = None
        self.weights = settings.reranker_weights
        self.model_name = settings.reranker_model

    @property
    def model(self):
        """Lazy load CrossEncoder."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading Reranker: {self.model_name}")
                self._model = CrossEncoder(self.model_name, max_length=512)
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder: {e}")
                self._model = None
        return self._model

    def calculate_metadata_score(self, doc_metadata: Dict, query: str) -> float:
        """Calculate score based on document metadata structure.
        
        Priority:
        1. Hierarchy level (Point > Clause > Article > Chapter)
        2. Title matching
        """
        score = 0.0
        
        # 1. Structure Score
        # TSBot Chunking provides 'clause', 'article', 'section', 'chapter', 'chunk_index'
        if 'clause' in doc_metadata:
            score += 0.4  # Specific clause is good
        elif 'article' in doc_metadata:
            score += 0.3  # Article is okay
        elif 'chapter' in doc_metadata:
            score += 0.1  # Chapter is too broad
            
        # 2. Title Macthing (Simple keyword overlap)
        # Check title fields like 'article_title', 'chapter_title'
        query_lower = query.lower()
        titles = [
            doc_metadata.get('article_title', ''),
            doc_metadata.get('chapter_title', ''),
            doc_metadata.get('section_title', '')
        ]
        
        for title in titles:
            if title and title.lower() in query_lower:
                score += 0.3
                break
                
        # 3. Recency (Year) - if available
        if 'year' in doc_metadata:
             # Favor strict recency if relevant, but military admissions rules are usually current year
             pass

        return min(score, 1.0)

    def rerank(
        self,
        query: str,
        documents: List[Any],  # List[RetrievedDocument]
        top_k: int = 3
    ) -> List[Any]:
        """Perform hybrid reranking.
        
        Args:
            query: User question.
            documents: List of RetrievedDocument objects.
            top_k: Number of docs to return.
            
        Returns:
            Reranked list of documents.
        """
        if not documents:
             return []
             
        if not self.model:
            logger.warning("Reranker model not loaded, returning original order")
            return documents[:top_k]

        # 1. Cross-Encoder Scoring
        pairs = [(query, doc.content) for doc in documents]
        ce_scores = self.model.predict(pairs)

        # 2. Combine Scores
        scored_docs = []
        for i, doc in enumerate(documents):
            ce_score = float(ce_scores[i])
            # Sigmoid/Normalize CE score ?
            # CrossEncoder outputs logits (often between -10 and 10). 
            # We map -10..10 to 0..1 roughly for combination
            ce_norm = (ce_score + 10) / 20.0
            ce_norm = max(0.0, min(1.0, ce_norm))
            
            # Retrieval score (from Qdrant) is usually Cosine (0..1)
            # doc.score is from Qdrant
            retrieval_score = getattr(doc, 'score', 0.0)
            
            # Metadata score
            meta_score = self.calculate_metadata_score(doc.metadata, query)
            
            # Weighted Sum
            final_score = (
                self.weights['cross_encoder'] * ce_norm +
                self.weights['retrieval'] * retrieval_score +
                self.weights['metadata'] * meta_score
            )
            
            # Store details for debugging/UI
            doc.rerank_score = final_score
            doc.metadata['rerank_debug'] = {
                'ce': round(ce_norm, 3),
                'retrieval': round(retrieval_score, 3),
                'meta': round(meta_score, 3),
                'final': round(final_score, 3)
            }
            
            scored_docs.append(doc)
            
        # 3. Sort and slice
        scored_docs.sort(key=lambda x: x.rerank_score, reverse=True)
        return scored_docs[:top_k]
