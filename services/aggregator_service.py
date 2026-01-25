"""
Aggregator service for entity frequency counting and clustering.
Uses canonical keys with lemmatization and fuzzy matching.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from loguru import logger

import tldextract

from utils.text_normalizer import normalize_phrase_ru_cached, get_first_lemma
from utils.relation_canonicalizer import canonicalize_relation, is_known_relation
from utils.entity_matcher import entity_matcher


# Current schema version for aggregated results
SCHEMA_VERSION = 2

# Maximum variants to store per entity group
MAX_VARIANTS = 10

# Maximum contexts to store per entity group
MAX_CONTEXTS = 3


def extract_domain(url: str) -> str:
    """
    Extract registrable domain from URL.
    Example: shop.example.ru -> example.ru

    Args:
        url: Full URL or domain

    Returns:
        Registrable domain
    """
    if not url:
        return "unknown"

    try:
        extracted = tldextract.extract(url)

        # Build domain from parts
        parts = [p for p in [extracted.domain, extracted.suffix] if p]

        if parts:
            domain = ".".join(parts)
            logger.debug(f"extract_domain: {url} -> {domain}")
            return domain.lower()
        else:
            # Fallback: try to extract from URL manually
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname or parsed.path.split('/')[0]
            if hostname:
                logger.debug(f"extract_domain (fallback): {url} -> {hostname}")
                return hostname.lower()

            logger.warning(f"Could not extract domain from {url}, using as-is")
            return url.lower()

    except Exception as e:
        logger.warning(f"Failed to extract domain from {url}: {e}")
        return url.lower() if url else "unknown"


class AggregatorService:
    """Service for entity aggregation with canonical keys and fuzzy clustering."""

    def __init__(self):
        self.matcher = entity_matcher

    def _create_canonical_key(
        self,
        entity_1: str,
        relation: str,
        entity_2: str
    ) -> Tuple[str, str, str, str]:
        """
        Create canonical key components for entity grouping.

        Args:
            entity_1: First entity
            relation: Relation
            entity_2: Second entity

        Returns:
            (full_key, e1_key, rel_key, e2_key)
        """
        e1_key = normalize_phrase_ru_cached(entity_1, drop_commercial=True)
        e2_key = normalize_phrase_ru_cached(entity_2, drop_commercial=True)
        rel_key = canonicalize_relation(relation)

        full_key = f"{e1_key}||{rel_key}||{e2_key}"

        return full_key, e1_key, rel_key, e2_key

    def _find_matching_group(
        self,
        e1_key: str,
        rel_key: str,
        e2_key: str,
        buckets: Dict[str, List[str]],
        groups: Dict[str, Dict]
    ) -> Optional[str]:
        """
        Find existing group that matches the entity (fuzzy).

        Uses bucketing by first lemma to reduce comparisons.

        Args:
            e1_key: Canonical key for entity_1
            rel_key: Canonical relation
            e2_key: Canonical key for entity_2
            buckets: Dict mapping bucket_key -> list of full_keys
            groups: Dict mapping full_key -> group data

        Returns:
            Matching full_key or None
        """
        # Get bucket by first lemma of e1
        bucket_key = e1_key.split()[0] if e1_key else ""

        if not bucket_key or bucket_key not in buckets:
            return None

        # Only search within bucket (reduces O(n^2))
        candidates = buckets[bucket_key]

        for candidate_key in candidates:
            if candidate_key not in groups:
                continue

            group = groups[candidate_key]

            # Component-wise matching
            is_match, scores = self.matcher.entities_match(
                e1_key, e2_key, rel_key,
                group['e1_key'], group['e2_key'], group['rel_key'],
                check_relation=True
            )

            if is_match:
                logger.debug(
                    f"Fuzzy matched: '{e1_key}||{rel_key}||{e2_key}' -> "
                    f"'{candidate_key}' (scores: {scores})"
                )
                return candidate_key

        return None

    def aggregate_entities(
        self,
        results: List[Dict[str, Any]],
        use_fuzzy_matching: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Aggregate entities from multiple sources with canonical keys.

        Args:
            results: List of analysis results
                [
                    {
                        "url": str,
                        "entities": List[Dict],
                        ...
                    },
                    ...
                ]
            use_fuzzy_matching: Enable fuzzy clustering (default True)

        Returns:
            Aggregated list with schema_version=2:
            [
                {
                    "entity_1": str,           # First seen variant
                    "relation": str,           # Canonical relation
                    "entity_2": str,           # First seen variant
                    "canonical_key": str,      # Full canonical key
                    "count": int,              # Number of DOMAINS
                    "domains": List[str],      # Source domains
                    "frequency": float,        # count / total_domains
                    "variants": List[Dict],    # Original formulations
                    "contexts": List[str],     # Sample contexts
                    "schema_version": int,     # Version marker
                },
                ...
            ]
        """
        logger.info(f"Aggregating entities from {len(results)} sources")

        # Groups: full_key -> group_data
        groups: Dict[str, Dict] = {}

        # Buckets for fuzzy matching: first_lemma -> [full_keys]
        buckets: Dict[str, List[str]] = defaultdict(list)

        # Track unique domains
        all_domains: Set[str] = set()

        # First pass: collect all domains for logging
        for result in results:
            url = result.get('url', '')
            if url:
                domain = extract_domain(url)
                all_domains.add(domain)
                logger.debug(f"Source: {url} -> domain: {domain}")

        logger.info(f"Total unique domains: {len(all_domains)} -> {list(all_domains)[:10]}")

        for result in results:
            url = result.get('url', '')
            domain = extract_domain(url) if url else "unknown"

            entities = result.get('entities', [])
            logger.debug(f"Processing {len(entities)} entities from {domain} (url: {url[:50]}...)")

            for entity in entities:
                e1 = entity.get('entity_1', '')
                rel = entity.get('relation', '')
                e2 = entity.get('entity_2', '')
                context = entity.get('context', '')

                if not e1 or not e2:
                    continue

                # Create canonical key
                full_key, e1_key, rel_key, e2_key = self._create_canonical_key(
                    e1, rel, e2
                )

                if not e1_key or not e2_key:
                    continue

                # 1. Try exact match first
                if full_key in groups:
                    group = groups[full_key]
                    group['domains'].add(domain)

                    # Add variant (limit to MAX_VARIANTS)
                    if len(group['variants']) < MAX_VARIANTS:
                        variant = {"e1": e1, "rel": rel, "e2": e2}
                        if variant not in group['variants']:
                            group['variants'].append(variant)

                    # Add context
                    if context and len(group['contexts']) < MAX_CONTEXTS:
                        if context not in group['contexts']:
                            group['contexts'].append(context)

                    continue

                # 2. Try fuzzy match (if enabled)
                matched_key = None
                if use_fuzzy_matching:
                    matched_key = self._find_matching_group(
                        e1_key, rel_key, e2_key, buckets, groups
                    )

                if matched_key:
                    group = groups[matched_key]
                    group['domains'].add(domain)

                    if len(group['variants']) < MAX_VARIANTS:
                        variant = {"e1": e1, "rel": rel, "e2": e2}
                        if variant not in group['variants']:
                            group['variants'].append(variant)

                    if context and len(group['contexts']) < MAX_CONTEXTS:
                        if context not in group['contexts']:
                            group['contexts'].append(context)

                    continue

                # 3. Create new group
                bucket_key = e1_key.split()[0] if e1_key else ""

                groups[full_key] = {
                    "entity_1": e1,
                    "relation": rel_key,
                    "relation_original": rel,
                    "entity_2": e2,
                    "canonical_key": full_key,
                    "e1_key": e1_key,
                    "e2_key": e2_key,
                    "rel_key": rel_key,
                    "domains": {domain},
                    "variants": [{"e1": e1, "rel": rel, "e2": e2}],
                    "contexts": [context] if context else [],
                }

                # Add to bucket for future fuzzy matching
                if bucket_key:
                    buckets[bucket_key].append(full_key)

        # Convert to output format
        total_domains = len(all_domains)
        aggregated = []

        for full_key, group in groups.items():
            count = len(group['domains'])
            frequency = count / total_domains if total_domains > 0 else 0

            aggregated.append({
                "entity_1": group['entity_1'],
                "relation": group['relation'],
                "relation_original": group['relation_original'],
                "entity_2": group['entity_2'],
                "canonical_key": group['canonical_key'],
                "count": count,
                "domains": list(group['domains']),
                "frequency": frequency,
                "variants": group['variants'],
                "contexts": group['contexts'][:MAX_CONTEXTS],
                "schema_version": SCHEMA_VERSION,
            })

        # Sort by count (most common first)
        aggregated.sort(key=lambda x: x['count'], reverse=True)

        # Log statistics
        if aggregated:
            max_count = aggregated[0]['count']
            logger.info(f"Aggregated {len(aggregated)} unique entity groups")
            logger.info(f"Most common: {max_count}/{total_domains} domains")
            logger.info(
                f"Universal (all domains): "
                f"{sum(1 for e in aggregated if e['count'] == total_domains)}"
            )
        else:
            logger.warning("No entities aggregated")

        return aggregated

    def filter_by_frequency(
        self,
        aggregated: List[Dict[str, Any]],
        min_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Filter entities by minimum domain count.

        Args:
            aggregated: Aggregated entities
            min_count: Minimum number of domains

        Returns:
            Filtered list
        """
        filtered = [e for e in aggregated if e['count'] >= min_count]

        logger.info(
            f"Filtered: {len(filtered)}/{len(aggregated)} entities "
            f"with count >= {min_count}"
        )

        return filtered

    def get_statistics(
        self,
        aggregated: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statistics for aggregated entities.

        Args:
            aggregated: Aggregated entities

        Returns:
            Statistics dict
        """
        if not aggregated:
            return {
                "total_entities": 0,
                "total_domains": 0,
                "max_count": 0,
                "min_count": 0,
                "avg_count": 0,
                "universal_entities": 0,
                "common_entities": 0,
                "rare_entities": 0,
                "schema_version": SCHEMA_VERSION,
            }

        counts = [e['count'] for e in aggregated]
        max_count = max(counts)

        # Get total domains from first entity (all should have same total)
        total_domains = max_count  # Approximation

        stats = {
            "total_entities": len(aggregated),
            "total_domains": total_domains,
            "max_count": max_count,
            "min_count": min(counts),
            "avg_count": round(sum(counts) / len(counts), 2),
            "universal_entities": sum(1 for c in counts if c == max_count),
            "common_entities": sum(1 for c in counts if c > max_count / 2),
            "rare_entities": sum(1 for c in counts if c <= 2),
            "known_relations": sum(
                1 for e in aggregated if is_known_relation(e.get('relation', ''))
            ),
            "schema_version": SCHEMA_VERSION,
        }

        logger.info(f"Statistics: {stats}")

        return stats

    # Legacy method for backward compatibility
    def _create_entity_key(self, entity: Dict) -> str:
        """Legacy key creation (for old code)."""
        full_key, _, _, _ = self._create_canonical_key(
            entity.get('entity_1', ''),
            entity.get('relation', ''),
            entity.get('entity_2', '')
        )
        return full_key


# Global singleton instance
aggregator_service = AggregatorService()
