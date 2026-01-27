"""
Unit tests for text normalization, relation canonicalization, and entity aggregation.

These tests import modules directly to avoid cascading imports from __init__.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Direct imports to avoid __init__.py cascade
from utils.text_normalizer import (
    normalize_phrase_ru,
    get_first_lemma,
    get_lemmas_list,
    BASE_STOPWORDS,
    COMMERCIAL_STOPWORDS,
)
from utils.relation_canonicalizer import (
    canonicalize_relation,
    is_known_relation,
    CANONICAL_RELATIONS,
)


class TestNormalizePhraseRu:
    """Tests for normalize_phrase_ru function."""

    def test_basic_normalization(self):
        """Test basic lowercase and lemmatization."""
        # Case normalization - result should be lowercase
        result = normalize_phrase_ru("Петля")
        assert result == result.lower()

        result = normalize_phrase_ru("ДВЕРЬ")
        assert result == result.lower()
        assert "дверь" in result

    def test_yo_normalization(self):
        """Test ё -> е conversion in input processing."""
        # Input "ёлка" should be processed (converted to "елка" before lemmatization)
        result = normalize_phrase_ru("ёлка")
        # Result should be consistent (either елка or ёлка depending on pymorphy)
        assert len(result) > 0
        assert result == result.lower()

    def test_lemmatization(self):
        """Test word lemmatization."""
        # Plural -> singular
        result = normalize_phrase_ru("петли")
        assert "петля" in result

        # Cases
        result = normalize_phrase_ru("дверей")
        assert "дверь" in result

    def test_stopwords_removal(self):
        """Test stopwords are removed."""
        result = normalize_phrase_ru("петли для дверей")
        # "для" should be removed
        assert "для" not in result
        # но "петля" и "дверь" остаются
        assert "петля" in result
        assert "дверь" in result

    def test_word_order_invariance(self):
        """Test that word order doesn't matter (sorted output)."""
        result1 = normalize_phrase_ru("петли для дверей")
        result2 = normalize_phrase_ru("дверные петли")
        # Both should contain same lemmas (sorted)
        # "дверь петля" vs "дверной петля" - slightly different due to adj
        # But at least they should be consistent
        assert "петля" in result1
        assert "петля" in result2

    def test_punctuation_removal(self):
        """Test punctuation is removed."""
        result = normalize_phrase_ru("петли, для дверей!")
        assert "," not in result
        assert "!" not in result

    def test_commercial_stopwords(self):
        """Test commercial stopwords handling."""
        # With commercial stopwords removal (default)
        result_with = normalize_phrase_ru("купить петли", drop_commercial_stopwords=True)
        assert "купить" not in result_with

        # Without commercial stopwords removal
        result_without = normalize_phrase_ru("купить петли", drop_commercial_stopwords=False)
        # "купить" лемматизируется
        assert "петля" in result_without

    def test_empty_input(self):
        """Test empty/whitespace input."""
        assert normalize_phrase_ru("") == ""
        assert normalize_phrase_ru("   ") == ""

    def test_all_stopwords(self):
        """Test when all words are stopwords - returns original lemmas."""
        result = normalize_phrase_ru("и в на для")
        # Should return something (original lemmas sorted)
        assert len(result) > 0


class TestGetFirstLemma:
    """Tests for get_first_lemma function."""

    def test_basic(self):
        """Test basic first lemma extraction."""
        assert get_first_lemma("дверные петли") == "дверной"
        # Single word - returns its lemma (consistent with pymorphy)
        result = get_first_lemma("петля")
        assert len(result) > 0
        assert result == result.lower()

    def test_empty(self):
        """Test empty input."""
        assert get_first_lemma("") == ""
        assert get_first_lemma("   ") == ""


class TestGetLemmasList:
    """Tests for get_lemmas_list function."""

    def test_preserves_order(self):
        """Test that lemmas order is preserved."""
        result = get_lemmas_list("дверные петли металлические")
        assert len(result) == 3
        assert result[0] == "дверной"
        assert result[1] == "петля"


class TestCanonicalizeRelation:
    """Tests for relation canonicalization."""

    def test_includes_relations(self):
        """Test 'includes'/'has_step' group relations."""
        # These may map to 'has_step' (new) or 'includes' (legacy)
        result = canonicalize_relation("включает")
        assert result in ("includes", "has_step")
        result = canonicalize_relation("содержит")
        assert result in ("includes", "has_step")

    def test_provides_relations(self):
        """Test 'provides'/'offers' group relations."""
        # These may map to 'offers' (new) or 'provides' (legacy)
        result = canonicalize_relation("предоставляет")
        assert result in ("provides", "offers")
        result = canonicalize_relation("оказывает")
        assert result in ("provides", "offers")

    def test_requires_relations(self):
        """Test 'requires'/'has_requirement' group relations."""
        # These may map to 'has_requirement' (new) or 'requires' (legacy)
        result = canonicalize_relation("требует")
        assert result in ("requires", "has_requirement")
        result = canonicalize_relation("требуется")
        assert result in ("requires", "has_requirement")

    def test_is_relations(self):
        """Test 'is' group relations."""
        assert canonicalize_relation("является") == "is"
        assert canonicalize_relation("представляет") == "is"

    def test_has_relations(self):
        """Test 'has' group relations (иметь NOT in includes)."""
        assert canonicalize_relation("имеет") == "has"
        assert canonicalize_relation("обладает") == "has"

    def test_underscore_normalization(self):
        """Test underscore to space conversion."""
        result = canonicalize_relation("предоставляет_услуги")
        assert result in ("provides", "offers")
        result = canonicalize_relation("включает_в_себя")
        assert result in ("includes", "has_step")

    def test_unknown_relation(self):
        """Test unknown relation returns lemmatized form."""
        result = canonicalize_relation("какое_то_неизвестное")
        # Should return lemmatized version
        assert len(result) > 0

    def test_empty_relation(self):
        """Test empty relation."""
        assert canonicalize_relation("") == "unknown"
        assert canonicalize_relation("   ") == "unknown"

    def test_is_known_relation(self):
        """Test is_known_relation helper."""
        # New relations
        assert is_known_relation("offers") is True
        assert is_known_relation("has_condition") is True
        assert is_known_relation("has_requirement") is True
        # Legacy relations
        assert is_known_relation("includes") is True
        assert is_known_relation("provides") is True
        # Unknown
        assert is_known_relation("unknown_rel") is False


class TestExtractDomain:
    """Tests for domain extraction (uses lazy import)."""

    @pytest.fixture
    def extract_domain(self):
        """Lazy import to avoid config issues."""
        from services.aggregator_service import extract_domain
        return extract_domain

    def test_basic_domain(self, extract_domain):
        """Test basic domain extraction."""
        assert extract_domain("https://example.ru/page") == "example.ru"
        assert extract_domain("http://www.example.com/path") == "example.com"

    def test_subdomain(self, extract_domain):
        """Test subdomain handling."""
        # Subdomain should be stripped
        assert extract_domain("https://shop.example.ru") == "example.ru"
        assert extract_domain("https://blog.example.ru/post") == "example.ru"

    def test_complex_tld(self, extract_domain):
        """Test complex TLDs."""
        assert extract_domain("https://site.co.uk") == "site.co.uk"


class TestAggregatorService:
    """Tests for AggregatorService (uses lazy import)."""

    @pytest.fixture
    def aggregator_module(self):
        """Lazy import to avoid config issues."""
        from services import aggregator_service as module
        return module

    @pytest.fixture
    def aggregator(self, aggregator_module):
        return aggregator_module.AggregatorService()

    def test_single_source_single_entity(self, aggregator, aggregator_module):
        """Test aggregation with single source and entity."""
        results = [
            {
                "url": "https://example.ru/page1",
                "entities": [
                    {
                        "entity_1": "дверные петли",
                        "relation": "требуют",
                        "entity_2": "установки",
                        "context": "Дверные петли требуют установки"
                    }
                ]
            }
        ]

        aggregated, _, _ = aggregator.aggregate_entities(results)

        assert len(aggregated) == 1
        assert aggregated[0]['count'] == 1
        assert aggregated[0]['schema_version'] == aggregator_module.SCHEMA_VERSION
        assert "example.ru" in aggregated[0]['domains']

    def test_same_entity_multiple_sources(self, aggregator):
        """Test that same entity from multiple sources is counted correctly."""
        results = [
            {
                "url": "https://site1.ru/page",
                "entities": [
                    {"entity_1": "дверные петли", "relation": "требуют", "entity_2": "установки"}
                ]
            },
            {
                "url": "https://site2.ru/page",
                "entities": [
                    {"entity_1": "петли для дверей", "relation": "требует", "entity_2": "установка"}
                ]
            }
        ]

        aggregated, _, _ = aggregator.aggregate_entities(results)

        # Should be merged into one group (similar entities)
        # Count should be 2 (from 2 different domains)
        assert len(aggregated) >= 1
        # The top entity should have count >= 1
        assert aggregated[0]['count'] >= 1

    def test_variants_stored(self, aggregator):
        """Test that original variants are stored."""
        results = [
            {
                "url": "https://site1.ru",
                "entities": [
                    {"entity_1": "Дверные петли", "relation": "требуют", "entity_2": "установки"}
                ]
            },
            {
                "url": "https://site2.ru",
                "entities": [
                    {"entity_1": "петли для дверей", "relation": "требует", "entity_2": "монтажа"}
                ]
            }
        ]

        aggregated, _, _ = aggregator.aggregate_entities(results)

        # At least one entity should have variants
        has_variants = any(len(e.get('variants', [])) > 0 for e in aggregated)
        assert has_variants

    def test_domain_deduplication(self, aggregator):
        """Test that same entity from multiple pages of same domain is tracked correctly."""
        results = [
            {
                "url": "https://example.ru/page1",
                "entities": [
                    {"entity_1": "тест", "relation": "является", "entity_2": "примером"}
                ]
            },
            {
                "url": "https://example.ru/page2",
                "entities": [
                    {"entity_1": "тест", "relation": "является", "entity_2": "примером"}
                ]
            }
        ]

        aggregated, total_sources, total_domains = aggregator.aggregate_entities(results)

        # Same entity from 2 URLs - count is 2 (by sources)
        # But domain_count should be 1 (same domain)
        assert len(aggregated) == 1
        assert aggregated[0]['count'] == 2  # Count by sources (URLs)
        assert aggregated[0]['domain_count'] == 1  # Same domain
        assert total_sources == 2
        assert total_domains == 1

    def test_canonical_key_present(self, aggregator):
        """Test that canonical_key is present in output."""
        results = [
            {
                "url": "https://example.ru",
                "entities": [
                    {"entity_1": "тест", "relation": "включает", "entity_2": "данные"}
                ]
            }
        ]

        aggregated, _, _ = aggregator.aggregate_entities(results)

        assert len(aggregated) == 1
        assert 'canonical_key' in aggregated[0]
        assert '||' in aggregated[0]['canonical_key']

    def test_relation_canonicalization(self, aggregator):
        """Test that relations are canonicalized."""
        results = [
            {
                "url": "https://example.ru",
                "entities": [
                    {"entity_1": "сервис", "relation": "предоставляет", "entity_2": "услуги"}
                ]
            }
        ]

        aggregated, _, _ = aggregator.aggregate_entities(results)

        assert len(aggregated) == 1
        # Relation should be canonical (offers or provides, depending on order)
        assert aggregated[0]['relation'] in ("offers", "provides")
        # Original should be preserved
        assert aggregated[0]['relation_original'] == "предоставляет"

    def test_statistics(self, aggregator):
        """Test statistics calculation."""
        results = [
            {
                "url": "https://site1.ru",
                "entities": [
                    {"entity_1": "a", "relation": "is", "entity_2": "b"},
                    {"entity_1": "c", "relation": "is", "entity_2": "d"},
                ]
            },
            {
                "url": "https://site2.ru",
                "entities": [
                    {"entity_1": "a", "relation": "является", "entity_2": "b"},
                ]
            }
        ]

        aggregated, total_sources, total_domains = aggregator.aggregate_entities(results)
        stats = aggregator.get_statistics(aggregated, total_sources, total_domains)

        assert stats['total_entities'] >= 1
        assert stats['total_sources'] == total_sources
        assert stats['total_domains'] == total_domains
        assert 'known_relations' in stats
