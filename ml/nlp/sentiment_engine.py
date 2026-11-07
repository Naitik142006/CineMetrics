"""
CineMetrics — Multilingual Sentiment & Cinema Lexicon Engine
Provides domain-adapted sentiment analysis for audience trailer comments across:
- English
- Hindi (Devanagari script)
- Hinglish (Latin transliteration)
- Regional Indian cinema vocabulary (Telugu, Tamil, Kannada, Malayalam transliterations)
- Emoji sentiment & controversy scoring
"""

import os
import re
import math
import logging
from typing import Dict, List, Tuple, Any, Optional

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect, DetectorFactory

# Enforce deterministic language detection
DetectorFactory.seed = 42

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CinemaSentimentEngine")

# Specialized Cinema & Entertainment Sentiment Lexicon
# Calibrated for pre-release trailer commentary, fan reactions, and box-office discourse
CINEMA_LEXICON: Dict[str, float] = {
    # High Positive Domain Drivers (+2.0 to +3.8)
    "blockbuster": 3.6,
    "all time blockbuster": 3.8,
    "superhit": 3.2,
    "goosebumps": 3.4,
    "masterpiece": 3.5,
    "banger": 3.1,
    "paisa vasool": 3.3,
    "theatre blast": 3.4,
    "peak cinema": 3.5,
    "mind blowing": 3.3,
    "pure cinema": 3.4,
    "mass": 2.5,
    "pure mass": 3.0,
    "next level": 2.8,
    "chills": 2.7,
    "bgm fire": 3.2,
    "bgm goosebumps": 3.5,
    "fire": 2.6,
    "hype": 2.5,
    "insane": 2.4,
    "phenomenal": 3.2,
    "stunning": 2.8,
    "record breaker": 3.4,
    "box office blast": 3.5,
    "oscar": 3.0,
    "goat": 3.2,
    "legendary": 3.2,
    "whistles": 2.7,
    "clapping": 2.5,
    "must watch": 3.0,
    "cant wait": 2.9,
    "can't wait": 2.9,
    "first day first show": 3.0,
    "fdfs": 3.0,

    # Regional Indian Positive Expressions (Hinglish / Telugu / Tamil Transliteration)
    "zabardast": 3.0,
    "shandaar": 3.0,
    "bawaal": 3.2,
    "dhamaka": 3.2,
    "faad": 3.1,
    "faadu": 3.1,
    "dumdaar": 2.8,
    "chala bagundi": 3.0,
    "verithanam": 3.5,
    "marana mass": 3.6,
    "mass entry": 3.0,
    "vera level": 3.2,
    "adipoli": 3.2,
    "chindam": 2.8,

    # Devanagari Script Positive Words
    "धमाका": 3.2,
    "शानदार": 3.0,
    "जबरदस्त": 3.0,
    "माइंड ब्लोइंग": 3.2,
    "हिट": 2.5,
    "सुपरहिट": 3.0,

    # High Negative Domain Drivers (-2.0 to -3.8)
    "disaster": -3.6,
    "flop": -3.3,
    "epic disaster": -3.8,
    "cringe": -2.9,
    "cringeworthy": -3.2,
    "worst": -3.4,
    "cheap vfx": -3.2,
    "cartoony": -2.6,
    "cartoonish": -2.6,
    "overacting": -2.8,
    "boring": -2.7,
    "bore": -2.5,
    "disappointed": -2.7,
    "disappointing": -2.8,
    "waste of money": -3.5,
    "waste of time": -3.4,
    "bakwas": -3.2,
    "flop show": -3.4,
    "pathetic": -3.2,
    "terrible": -3.1,
    "avoid": -2.5,
    "skip": -2.4,
    "skip this": -2.6,
    "overrated": -2.2,
    "zero story": -3.0,
    "money grab": -2.8,
    "horrible": -3.2,
    "unbearable": -3.3,
    "headache": -2.8,

    # Regional Indian Negative Expressions
    "bekaar": -3.0,
    "ghatia": -3.2,
    "kachra": -3.3,
    "mood off": -2.6,
    "daridram": -3.2,
    "karumam": -3.2,
    "waste": -2.8,

    # Devanagari Script Negative Words
    "बकवास": -3.2,
    "फ्लॉप": -3.2,
    "घटिया": -3.2,
    "कचरा": -3.3,
}

# Emoji Valence Dictionary
EMOJI_SENTIMENT: Dict[str, float] = {
    "🔥": 1.5,
    "❤️": 1.2,
    "👏": 1.0,
    "💯": 1.2,
    "🤩": 1.4,
    "😍": 1.3,
    "🎉": 1.0,
    "🥳": 1.0,
    "🚀": 1.2,
    "👑": 1.3,
    " goosebumps ": 1.2,
    "💩": -1.5,
    "🤮": -1.8,
    "😴": -1.2,
    "👎": -1.3,
    "🤡": -1.4,
    "😭": 0.2,   # Often joyful crying in trailers, keep near-neutral
    "😡": -1.4,
    "🤦": -1.2,
}


class CinemaSentimentEngine:
    """
    High-performance, domain-adapted sentiment analyzer for theatrical trailer comments.
    Combines VADER, custom entertainment lexicons, emoji valence, and language routing.
    """

    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        # Inject cinema domain vocabulary into VADER lexicon
        self.sia.lexicon.update(CINEMA_LEXICON)
        logger.info(f"Initialized CinemaSentimentEngine with {len(CINEMA_LEXICON)} domain terms.")

    def detect_language(self, text: str) -> str:
        """Identifies language (en, hi, te, ta, kn, ml, etc.) with safe fallback."""
        cleaned = re.sub(r"[^\w\s]", "", text).strip()
        if not cleaned or len(cleaned) < 4:
            return "unknown"
        try:
            return detect(cleaned)
        except Exception:
            return "unknown"

    def preprocess_comment(self, text: str) -> Tuple[str, float]:
        """
        Cleans comment text while computing emoji sentiment bonus.
        Returns (cleaned_text, emoji_score).
        """
        if not text:
            return "", 0.0

        emoji_bonus = 0.0
        for emoji_char, weight in EMOJI_SENTIMENT.items():
            count = text.count(emoji_char)
            if count > 0:
                emoji_bonus += weight * min(count, 3) * 0.25

        # Normalize multiple spaces, keep casing for VADER CAPS emphasis
        cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
        cleaned = re.sub(r"@\w+", "", cleaned).strip()

        return cleaned, emoji_bonus

    def score_single_comment(self, text: str) -> Dict[str, Any]:
        """Scores a single comment string."""
        cleaned_text, emoji_bonus = self.preprocess_comment(text)
        if not cleaned_text:
            return {
                "compound": 0.0,
                "label": "neutral",
                "pos": 0.0,
                "neg": 0.0,
                "neu": 1.0,
                "lang": "unknown",
            }

        lang = self.detect_language(cleaned_text)
        scores = self.sia.polarity_scores(cleaned_text)

        compound = scores["compound"]
        if emoji_bonus != 0.0:
            compound = compound + (emoji_bonus * (1.0 - abs(compound)))
            compound = max(min(compound, 1.0), -1.0)

        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "compound": round(compound, 4),
            "label": label,
            "pos": round(scores["pos"], 3),
            "neg": round(scores["neg"], 3),
            "neu": round(scores["neu"], 3),
            "lang": lang,
        }

    def aggregate_movie_comments(
        self,
        comments: List[str],
    ) -> Dict[str, Any]:
        """
        Aggregates a list of trailer comments for a movie into standardized sentiment features.
        """
        if not comments:
            return {
                "total_comments_analyzed": 0,
                "comment_sentiment_positive_ratio": 0.33,
                "comment_sentiment_negative_ratio": 0.33,
                "comment_sentiment_neutral_ratio": 0.34,
                "comment_sentiment_net_polarity": 0.0,
                "comment_sentiment_controversy_score": 0.0,
                "dominant_language": "unknown",
                "top_positive_keywords": [],
                "top_negative_keywords": [],
            }

        scored = [self.score_single_comment(c) for c in comments]

        pos_count = sum(1 for s in scored if s["label"] == "positive")
        neg_count = sum(1 for s in scored if s["label"] == "negative")
        neu_count = sum(1 for s in scored if s["label"] == "neutral")
        total = len(scored)

        pos_ratio = pos_count / total
        neg_ratio = neg_count / total
        neu_ratio = neu_count / total

        # Net Polarity: in [-1.0, +1.0]
        net_polarity = round(pos_ratio - neg_ratio, 4)

        # Controversy Score: High when BOTH positive and negative are elevated
        # Max when pos = 0.5 and neg = 0.5 -> 4 * 0.5 * 0.5 = 1.0
        controversy = round(4.0 * min(pos_ratio, neg_ratio) * max(pos_ratio, neg_ratio), 4)

        # Language distribution
        langs = [s["lang"] for s in scored if s["lang"] != "unknown"]
        dominant_lang = max(set(langs), key=langs.count) if langs else "en"

        # Detect top cinema keywords
        all_text_lower = " ".join(comments).lower()
        matched_pos = [k for k, v in CINEMA_LEXICON.items() if v > 2.0 and k in all_text_lower][:5]
        matched_neg = [k for k, v in CINEMA_LEXICON.items() if v < -2.0 and k in all_text_lower][:5]

        return {
            "total_comments_analyzed": total,
            "comment_sentiment_positive_ratio": round(pos_ratio, 4),
            "comment_sentiment_negative_ratio": round(neg_ratio, 4),
            "comment_sentiment_neutral_ratio": round(neu_ratio, 4),
            "comment_sentiment_net_polarity": net_polarity,
            "comment_sentiment_controversy_score": controversy,
            "dominant_language": dominant_lang,
            "top_positive_keywords": matched_pos,
            "top_negative_keywords": matched_neg,
        }


def calculate_composite_buzz_score(
    view_count: int,
    like_count: int,
    comment_count: int,
    net_polarity: float,
    days_since_trailer: float = 30.0,
) -> float:
    """
    Computes unified Digital Buzz & Audience Anticipation Index (0.0 to 100.0).
    Fuses:
    1. Volume Reach (Log Views + Daily Velocity) - 50%
    2. Sentiment Polarity (Audience Reception) - 35%
    3. Engagement Passion (Like-to-View & Comment Ratios) - 15%
    """
    if view_count <= 0:
        return 50.0  # Neutral prior if no trailer data

    # 1. Volume Reach (0 to 100)
    # 100k views -> ~30, 1M views -> ~50, 10M views -> ~70, 50M+ views -> ~90-100
    log_v = math.log10(max(view_count, 1))
    volume_score = min(max((log_v - 4.0) * 20.0, 0.0), 100.0)

    # Velocity bonus (up to +15 pts for viral launches)
    daily_velocity = view_count / max(days_since_trailer, 1.0)
    if daily_velocity > 1_000_000:
        velocity_bonus = 15.0
    elif daily_velocity > 200_000:
        velocity_bonus = 10.0
    elif daily_velocity > 50_000:
        velocity_bonus = 5.0
    else:
        velocity_bonus = 0.0

    final_volume = min(volume_score + velocity_bonus, 100.0)

    # 2. Sentiment Polarity (0 to 100)
    # Net polarity is in [-1.0, +1.0] -> mapped to [0, 100]
    polarity_score = (net_polarity + 1.0) * 50.0

    # 3. Engagement Passion (0 to 100)
    # Like ratio: healthy is 1.5% to 4.0%
    like_ratio = like_count / max(view_count, 1)
    passion_score = min(max(like_ratio * 2500.0, 0.0), 100.0)

    # Weighted composite
    composite = (0.50 * final_volume) + (0.35 * polarity_score) + (0.15 * passion_score)
    return round(float(min(max(composite, 0.0), 100.0)), 2)
