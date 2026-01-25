from .entity_matcher import entity_matcher, EntityMatcher
from .excel_generator import excel_generator, ExcelGenerator
from .region_manager import region_manager, RegionManager
from .text_normalizer import (
    normalize_phrase_ru,
    normalize_phrase_ru_cached,
    get_first_lemma,
    get_lemmas_list,
)
from .relation_canonicalizer import (
    canonicalize_relation,
    is_known_relation,
    CANONICAL_RELATIONS,
)

__all__ = [
    "entity_matcher",
    "EntityMatcher",
    "excel_generator",
    "ExcelGenerator",
    "region_manager",
    "RegionManager",
    "normalize_phrase_ru",
    "normalize_phrase_ru_cached",
    "get_first_lemma",
    "get_lemmas_list",
    "canonicalize_relation",
    "is_known_relation",
    "CANONICAL_RELATIONS",
]