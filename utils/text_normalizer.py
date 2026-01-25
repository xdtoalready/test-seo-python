"""
Text normalizer for Russian text with lemmatization and stopwords removal.
Creates canonical keys for entity matching and aggregation.
"""

import re
from typing import List, Optional, Set
from functools import lru_cache

from razdel import tokenize
from pymorphy3 import MorphAnalyzer
from loguru import logger


# Singleton MorphAnalyzer (heavy to initialize, reuse)
_morph: Optional[MorphAnalyzer] = None


def get_morph() -> MorphAnalyzer:
    """Get or create singleton MorphAnalyzer instance."""
    global _morph
    if _morph is None:
        logger.debug("Initializing MorphAnalyzer (singleton)...")
        _morph = MorphAnalyzer()
    return _morph


# Base Russian stopwords (service words)
BASE_STOPWORDS: Set[str] = {
    # Prepositions
    "в", "на", "для", "по", "с", "со", "к", "ко", "о", "об", "обо",
    "от", "из", "у", "за", "до", "при", "без", "над", "под", "между",
    "через", "про", "ради", "вне", "около", "после", "перед", "среди",
    # Conjunctions
    "и", "а", "но", "или", "да", "либо", "то", "ни", "чтобы", "если",
    "когда", "пока", "хотя", "что", "как", "потому", "поэтому",
    # Particles
    "не", "бы", "же", "ли", "вот", "вон", "даже", "лишь", "только",
    "уже", "ещё", "еще", "ведь", "разве", "неужели",
    # Pronouns (common)
    "я", "ты", "он", "она", "оно", "мы", "вы", "они",
    "это", "этот", "эта", "эти", "тот", "та", "те",
    "весь", "вся", "всё", "все", "сам", "сама", "само", "сами",
    "который", "которая", "которое", "которые",
    "какой", "какая", "какое", "какие", "чей", "чья", "чьё", "чьи",
    "свой", "своя", "своё", "свои", "наш", "наша", "наше", "наши",
    # Other common
    "быть", "также", "тоже", "можно", "нужно", "надо", "нельзя",
    "очень", "более", "менее", "самый", "другой", "любой", "каждый",
}

# Commercial/SEO stopwords (optional, configurable)
COMMERCIAL_STOPWORDS: Set[str] = {
    "купить", "заказать", "приобрести", "оформить",
    "каталог", "ассортимент", "выбор",
    "доставка", "самовывоз", "отправка",
    "оптом", "розница", "опт",
    "наличие", "склад", "запас",
    "продажа", "реализация",
    "интернет-магазин", "магазин", "сайт",
    "акция", "скидка", "распродажа", "спецпредложение",
    "бесплатно", "недорого", "дёшево", "дешево",
}


def normalize_phrase_ru(
    text: str,
    drop_commercial_stopwords: bool = True,
    custom_stopwords: Optional[Set[str]] = None
) -> str:
    """
    Normalize Russian phrase to canonical key.

    Process:
    1. Lowercase + yo->e normalization
    2. Remove punctuation
    3. Tokenize (razdel)
    4. Lemmatize (pymorphy2)
    5. Remove stopwords
    6. Sort lemmas alphabetically
    7. Join with space

    Args:
        text: Input text
        drop_commercial_stopwords: Remove commercial/SEO words
        custom_stopwords: Additional stopwords to remove

    Returns:
        Canonical key string (sorted lemmas)

    Example:
        "Петли для Дверей" -> "дверь петля"
        "дверные петли" -> "дверной петля" (adj kept if meaningful)
    """
    if not text or not text.strip():
        return ""

    # 1. Lowercase + normalize yo
    text = text.lower().strip()
    text = text.replace("ё", "е")

    # 2. Remove punctuation (keep only letters, digits, spaces)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return ""

    # 3. Tokenize
    tokens = [token.text for token in tokenize(text)]

    if not tokens:
        return ""

    # 4. Lemmatize
    morph = get_morph()
    lemmas = []

    for token in tokens:
        if not token.strip():
            continue
        # Get most probable lemma
        parsed = morph.parse(token)
        if parsed:
            lemma = parsed[0].normal_form
            lemmas.append(lemma)
        else:
            lemmas.append(token)

    # 5. Remove stopwords
    stopwords = BASE_STOPWORDS.copy()
    if drop_commercial_stopwords:
        stopwords.update(COMMERCIAL_STOPWORDS)
    if custom_stopwords:
        stopwords.update(custom_stopwords)

    filtered_lemmas = [lemma for lemma in lemmas if lemma not in stopwords]

    # If all words were stopwords, return original lemmas (sorted)
    if not filtered_lemmas:
        filtered_lemmas = lemmas

    # 6. Sort alphabetically (order-invariant key)
    filtered_lemmas.sort()

    # 7. Join
    return " ".join(filtered_lemmas)


def get_first_lemma(text: str) -> str:
    """
    Get first lemma from text (for bucketing).

    Args:
        text: Input text

    Returns:
        First lemma or empty string
    """
    if not text or not text.strip():
        return ""

    text = text.lower().strip().replace("ё", "е")
    text = re.sub(r'[^\w\s]', ' ', text).strip()

    tokens = [token.text for token in tokenize(text)]
    if not tokens:
        return ""

    morph = get_morph()
    parsed = morph.parse(tokens[0])

    if parsed:
        return parsed[0].normal_form
    return tokens[0]


@lru_cache(maxsize=10000)
def normalize_phrase_ru_cached(text: str, drop_commercial: bool = True) -> str:
    """
    Cached version of normalize_phrase_ru for repeated calls.

    Note: custom_stopwords not supported in cached version.
    """
    return normalize_phrase_ru(text, drop_commercial_stopwords=drop_commercial)


def get_lemmas_list(text: str) -> List[str]:
    """
    Get list of lemmas from text (without filtering/sorting).
    Useful for relation canonicalization.

    Args:
        text: Input text

    Returns:
        List of lemmas in original order
    """
    if not text or not text.strip():
        return []

    text = text.lower().strip().replace("ё", "е")
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = [token.text for token in tokenize(text)]
    morph = get_morph()

    lemmas = []
    for token in tokens:
        if not token.strip():
            continue
        parsed = morph.parse(token)
        if parsed:
            lemmas.append(parsed[0].normal_form)
        else:
            lemmas.append(token)

    return lemmas
