"""
CineMetrics — Cross-Source Entity Resolution Module
Matches and merges movie records across IMDb, TMDB, and Kaggle using RapidFuzz & temporal blocking.
"""

import logging
import re
import unicodedata
import uuid
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
from rapidfuzz import fuzz

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("EntityResolution")


def normalize_title(title: Optional[str]) -> str:
    """
    Normalizes movie titles for fuzzy and exact hash matching.
    - Converts to lowercase and normalizes unicode (NFKD)
    - Replaces Roman numerals (II -> 2, III -> 3, IV -> 4)
    - Strips punctuation, subtitles, and excess whitespace
    - Removes leading articles ('the ', 'a ', 'an ')
    """
    if title is None or pd.isna(title):
        return ""

    s = str(title).strip().lower()
    if not s or s == "nan":
        return ""
    # Normalize unicode accents
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")

    # Replace common Roman numerals at word boundaries
    s = re.sub(r"\bpart\s+i\b", "part 1", s)
    s = re.sub(r"\bpart\s+ii\b", "part 2", s)
    s = re.sub(r"\bpart\s+iii\b", "part 3", s)
    s = re.sub(r"\bpart\s+iv\b", "part 4", s)
    s = re.sub(r"\bchapter\s+i\b", "chapter 1", s)
    s = re.sub(r"\bchapter\s+ii\b", "chapter 2", s)

    # Remove special characters
    s = re.sub(r"[^\w\s]", " ", s)

    # Remove leading articles
    s = re.sub(r"^(the|a|an)\s+", "", s)

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_title_year_key(normalized_title: str, year: Optional[int]) -> str:
    """Constructs blocking key: 'normalized_title::year'."""
    y_str = str(int(year)) if year and not pd.isna(year) else "unknown"
    return f"{normalized_title}::{y_str}"


def match_candidate(
    title: str,
    year: Optional[int],
    lookup_exact: Dict[str, str],
    lookup_by_year: Dict[int, List[Tuple[str, str]]],
    fuzzy_threshold: float = 88.0,
) -> Optional[str]:
    """
    Attempts to match a candidate movie title and year against an existing index.
    1. Exact Title + Exact Year
    2. Exact Title + Year +/- 1
    3. RapidFuzz Token Sort Ratio within Year +/- 1 window
    """
    norm_title = normalize_title(title)
    if not norm_title:
        return None

    yr = int(year) if year and not pd.isna(year) else None

    # 1. Exact match on title and exact year
    if yr is not None:
        key = build_title_year_key(norm_title, yr)
        if key in lookup_exact:
            return lookup_exact[key]

        # 2. Exact match with year +/- 1 (festival vs release year discrepancy)
        for delta in (-1, 1):
            neighbor_key = build_title_year_key(norm_title, yr + delta)
            if neighbor_key in lookup_exact:
                return lookup_exact[neighbor_key]

        # 3. Fuzzy search within temporal block (yr - 1 to yr + 1)
        candidate_pool = []
        for check_yr in (yr, yr - 1, yr + 1):
            if check_yr in lookup_by_year:
                candidate_pool.extend(lookup_by_year[check_yr])

        best_id = None
        best_score = 0.0

        for cand_title, cand_id in candidate_pool:
            score = fuzz.token_sort_ratio(norm_title, cand_title)
            if score > best_score and score >= fuzzy_threshold:
                best_score = score
                best_id = cand_id

        if best_id:
            return best_id
    else:
        # Fallback if year is completely missing
        for yr_key, cand_list in lookup_by_year.items():
            for cand_title, cand_id in cand_list:
                score = fuzz.ratio(norm_title, cand_title)
                if score >= 95.0:
                    return cand_id

    return None


def generate_canonical_id() -> str:
    """Generates a UUIDv4 canonical movie ID."""
    return str(uuid.uuid4())
