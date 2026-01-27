"""
Relation canonicalizer for normalizing relation types.
Maps various Russian relation verbs to canonical relation types.

Updated for SEO/business entity extraction with semantic relation types.
"""

from typing import Optional, Dict, Set, List
from rapidfuzz import fuzz
from loguru import logger

from utils.text_normalizer import get_lemmas_list


# Canonical relation types with their lemma variants
# Optimized for SEO/business entity extraction
RELATION_GROUPS: Dict[str, Set[str]] = {
    # SERVICE/PRODUCT relations
    "offers": {
        "предлагать", "предоставлять", "оказывать", "выполнять",
        "обеспечивать", "давать", "гарантировать", "осуществлять",
        "реализовывать", "продавать", "оформлять",
    },

    # CONDITIONS (price, term, rate, guarantee)
    "has_condition": {
        "иметь", "обладать", "составлять", "равняться",
        "достигать", "начинаться", "стоить", "обходиться",
        "действовать", "длиться", "распространяться",
    },

    # REQUIREMENTS (what client needs)
    "has_requirement": {
        "требовать", "требоваться", "нуждаться", "необходимый",
        "нужный", "понадобиться", "потребовать", "предполагать",
        "подразумевать", "обязывать",
    },

    # DOCUMENTS
    "requires_document": {
        "оформлять", "подготовить", "предъявить", "предоставить",
        "приложить", "собрать", "принести", "подписать",
    },

    # PROCESS/STEPS (how it works)
    "done_via": {
        "осуществляться", "выполняться", "происходить", "проводиться",
        "делаться", "производиться", "реализоваться", "оформляться",
        "занимать", "включать", "состоять",
    },

    # CHANNELS (where/how to get)
    "available_in": {
        "находиться", "располагаться", "размещаться", "доступный",
        "работать", "открыть", "принимать", "обслуживать",
        "действовать", "функционировать",
    },

    # BENEFITS
    "gives_benefit": {
        "позволять", "помогать", "способствовать", "обеспечивать",
        "экономить", "сокращать", "упрощать", "ускорять",
        "гарантировать", "защищать",
    },

    # PROCESS STEPS
    "has_step": {
        "включать", "содержать", "состоять", "входить",
        "охватывать", "объединять", "предусматривать",
        "подразумевать", "означать",
    },

    # Legacy relations for backward compatibility
    "is": {
        "являться", "быть", "представлять", "относиться",
        "считаться", "называться", "выступать",
    },
    "has": {
        "иметь", "обладать", "располагать", "владеть",
    },
    "uses": {
        "использовать", "применять", "употреблять",
        "задействовать", "эксплуатировать",
    },
    "connects": {
        "соединять", "связывать", "объединять",
        "скреплять", "стыковать",
    },
    "supports": {
        "поддерживать", "совместимый", "подходить",
        "соответствовать",
    },
    # Additional legacy for old prompts/tests
    "includes": {
        "включать", "содержать", "состоять", "входить",
        "охватывать", "комплектоваться",
    },
    "provides": {
        "предоставлять", "оказывать", "выполнять",
        "гарантировать",
    },
    "requires": {
        "требовать", "нуждаться", "необходимый", "нужный",
        "требоваться", "понадобиться", "потребовать",
    },
}

# Build reverse lookup: lemma -> canonical relation
_LEMMA_TO_RELATION: Dict[str, str] = {}
for relation_type, lemmas in RELATION_GROUPS.items():
    for lemma in lemmas:
        _LEMMA_TO_RELATION[lemma] = relation_type


def canonicalize_relation(
    relation: str,
    fuzzy_fallback: bool = True,
    fuzzy_threshold: int = 85
) -> str:
    """
    Convert relation text to canonical relation type.

    Process:
    1. Normalize: underscore->space, lemmatize
    2. Try exact match with known lemmas
    3. If no match and fuzzy_fallback=True, try fuzzy matching
    4. If still no match, return lemmatized version

    Args:
        relation: Raw relation text (e.g., "предоставляет_услуги", "требуется")
        fuzzy_fallback: Try fuzzy matching if exact match fails
        fuzzy_threshold: Threshold for fuzzy matching (0-100)

    Returns:
        Canonical relation type (e.g., "provides", "requires")
        or lemmatized original if no match

    Examples:
        "предоставляет" -> "provides"
        "требуется_для" -> "requires"
        "включает_в_себя" -> "includes"
        "some_unknown_relation" -> "some unknown relation" (lemmatized)
    """
    if not relation or not relation.strip():
        return "unknown"

    # Normalize: underscore to space
    relation_clean = relation.replace("_", " ").replace("-", " ")

    # Get lemmas
    lemmas = get_lemmas_list(relation_clean)

    if not lemmas:
        return "unknown"

    # Try exact match on any lemma
    for lemma in lemmas:
        if lemma in _LEMMA_TO_RELATION:
            return _LEMMA_TO_RELATION[lemma]

    # Fuzzy fallback
    if fuzzy_fallback:
        best_match = None
        best_score = 0

        for lemma in lemmas:
            for known_lemma, rel_type in _LEMMA_TO_RELATION.items():
                score = fuzz.ratio(lemma, known_lemma)
                if score >= fuzzy_threshold and score > best_score:
                    best_match = rel_type
                    best_score = score

        if best_match:
            logger.debug(
                f"Fuzzy matched relation '{relation}' -> '{best_match}' "
                f"(score: {best_score})"
            )
            return best_match

    # No match - return joined lemmas
    return " ".join(lemmas)


def get_relation_variants(canonical_relation: str) -> List[str]:
    """
    Get all known variants for a canonical relation.

    Args:
        canonical_relation: Canonical relation type (e.g., "provides")

    Returns:
        List of variant lemmas
    """
    if canonical_relation in RELATION_GROUPS:
        return list(RELATION_GROUPS[canonical_relation])
    return []


def is_known_relation(canonical_relation: str) -> bool:
    """Check if relation is a known canonical type."""
    return canonical_relation in RELATION_GROUPS


# Export relation types for external use
CANONICAL_RELATIONS = list(RELATION_GROUPS.keys())
