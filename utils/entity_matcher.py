"""
Entity matcher for fuzzy comparison using RapidFuzz.
Supports component-based matching (e1, e2, relation separately).
"""

from typing import List, Dict, Tuple, Optional
from rapidfuzz import fuzz
from loguru import logger

from utils.text_normalizer import normalize_phrase_ru_cached, get_first_lemma

# Try to import settings, fallback to defaults
try:
    from config import settings
    DEFAULT_SIMILARITY_THRESHOLD = getattr(settings, 'similarity_threshold', 85)
except Exception:
    DEFAULT_SIMILARITY_THRESHOLD = 85


# Thresholds for different components
ENTITY_SIMILARITY_THRESHOLD = 90   # e1, e2 matching
ENTITY2_SIMILARITY_THRESHOLD = 88  # e2 is often longer/more variable
RELATION_SIMILARITY_THRESHOLD = 85  # relations are shorter


class EntityMatcher:
    """Class for fuzzy entity comparison and matching."""

    def __init__(
        self,
        entity_threshold: int = None,
        entity2_threshold: int = None,
        relation_threshold: int = None
    ):
        """
        Args:
            entity_threshold: Threshold for e1 matching (0-100)
            entity2_threshold: Threshold for e2 matching (0-100)
            relation_threshold: Threshold for relation matching (0-100)
        """
        self.entity_threshold = entity_threshold or ENTITY_SIMILARITY_THRESHOLD
        self.entity2_threshold = entity2_threshold or ENTITY2_SIMILARITY_THRESHOLD
        self.relation_threshold = relation_threshold or RELATION_SIMILARITY_THRESHOLD

        # Legacy threshold for backward compatibility
        self.threshold = DEFAULT_SIMILARITY_THRESHOLD

    def get_similarity(self, text1: str, text2: str) -> int:
        """
        Calculate similarity between two texts using token_set_ratio.

        token_set_ratio is better for:
        - Word order variations ("петли дверные" vs "дверные петли")
        - Partial overlaps ("красные дверные петли" vs "дверные петли")

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-100)
        """
        if not text1 or not text2:
            return 0

        # Use token_set_ratio for better word order handling
        return fuzz.token_set_ratio(text1, text2)

    def get_similarity_normalized(
        self,
        text1: str,
        text2: str,
        drop_commercial: bool = True
    ) -> int:
        """
        Calculate similarity with canonical normalization.

        Args:
            text1: First text (raw)
            text2: Second text (raw)
            drop_commercial: Remove commercial stopwords

        Returns:
            Similarity score (0-100)
        """
        key1 = normalize_phrase_ru_cached(text1, drop_commercial)
        key2 = normalize_phrase_ru_cached(text2, drop_commercial)

        if not key1 or not key2:
            return 0

        return fuzz.token_set_ratio(key1, key2)

    def are_similar(
        self,
        text1: str,
        text2: str,
        threshold: int = None,
        use_normalization: bool = True
    ) -> bool:
        """
        Check if two texts are similar.

        Args:
            text1: First text
            text2: Second text
            threshold: Custom threshold (default: entity_threshold)
            use_normalization: Apply canonical normalization

        Returns:
            True if texts are similar
        """
        threshold = threshold or self.entity_threshold

        if use_normalization:
            similarity = self.get_similarity_normalized(text1, text2)
        else:
            similarity = self.get_similarity(text1, text2)

        return similarity >= threshold

    def find_best_match(
        self,
        query: str,
        candidates: List[str],
        threshold: int = None,
        use_normalization: bool = True
    ) -> Tuple[Optional[str], int]:
        """
        Find best matching candidate for query.

        Args:
            query: Text to match
            candidates: List of candidate texts
            threshold: Minimum similarity threshold
            use_normalization: Apply canonical normalization

        Returns:
            (best_match, score) or (None, 0) if no match found
        """
        threshold = threshold or self.entity_threshold

        if use_normalization:
            query_norm = normalize_phrase_ru_cached(query, True)
        else:
            query_norm = query.lower().strip()

        best_match = None
        best_score = 0

        for candidate in candidates:
            if use_normalization:
                candidate_norm = normalize_phrase_ru_cached(candidate, True)
            else:
                candidate_norm = candidate.lower().strip()

            # Exact match
            if query_norm == candidate_norm:
                return candidate, 100

            score = fuzz.token_set_ratio(query_norm, candidate_norm)

            if score >= threshold and score > best_score:
                best_match = candidate
                best_score = score

        return best_match, best_score

    def entities_match(
        self,
        e1_query: str,
        e2_query: str,
        rel_query: str,
        e1_candidate: str,
        e2_candidate: str,
        rel_candidate: str,
        check_relation: bool = True
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if two entity triples match (component-wise).

        Matching is done separately for each component with different thresholds:
        - e1: entity_threshold (90)
        - e2: entity2_threshold (88)
        - relation: relation_threshold (85)

        Args:
            e1_query, e2_query, rel_query: Query triple
            e1_candidate, e2_candidate, rel_candidate: Candidate triple
            check_relation: Whether to compare relations

        Returns:
            (is_match, scores_dict)
            scores_dict contains individual component scores
        """
        scores = {}

        # Match e1
        scores['e1'] = self.get_similarity_normalized(e1_query, e1_candidate)
        if scores['e1'] < self.entity_threshold:
            return False, scores

        # Match e2
        scores['e2'] = self.get_similarity_normalized(e2_query, e2_candidate)
        if scores['e2'] < self.entity2_threshold:
            return False, scores

        # Match relation (if required)
        if check_relation:
            # For relations, compare canonical forms directly
            # (they should already be canonicalized)
            if rel_query == rel_candidate:
                scores['rel'] = 100
            else:
                scores['rel'] = fuzz.token_set_ratio(rel_query, rel_candidate)

            if scores['rel'] < self.relation_threshold:
                return False, scores

        return True, scores

    def get_bucket_key(self, text: str) -> str:
        """
        Get bucket key for candidate grouping (first lemma).
        Used to reduce O(n^2) comparisons.

        Args:
            text: Entity text

        Returns:
            Bucket key (first lemma)
        """
        return get_first_lemma(text)

    # Legacy methods for backward compatibility
    def normalize_text(self, text: str) -> str:
        """Legacy normalize method."""
        return text.lower().strip()

    def find_similar_entity(
        self,
        entity: str,
        entity_list: List[str],
        threshold: int = None
    ) -> Tuple[Optional[str], int]:
        """Legacy find method."""
        return self.find_best_match(entity, entity_list, threshold)

    def entities_are_similar(
        self,
        entity1: Dict,
        entity2: Dict,
        check_relation: bool = True
    ) -> bool:
        """Legacy comparison method."""
        is_match, _ = self.entities_match(
            entity1['entity_1'], entity1['entity_2'], entity1.get('relation', ''),
            entity2['entity_1'], entity2['entity_2'], entity2.get('relation', ''),
            check_relation
        )
        return is_match


# Global singleton instance
entity_matcher = EntityMatcher()
