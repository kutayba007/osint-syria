"""
OSINT Syria — Arabic NLP Analyzer
Uses AraBERT and CAMeL for Arabic text analysis, fake news detection,
and propaganda identification.

Models used:
- aubmindlab/bert-base-arabertv2 (Arabic BERT)
- CAMeL-Lab/bert-base-arabic-camelbert-da (Arabic dialects)
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("osint.sources.arabic_nlp")


@dataclass
class ArabicAnalysis:
    """Result of Arabic NLP analysis."""
    text: str
    sentiment: str           # positive, negative, neutral
    sentiment_score: float   # -1.0 to 1.0
    is_propaganda: bool
    propaganda_score: float  # 0.0 to 1.0
    is_fake_news_suspect: bool
    fake_news_score: float   # 0.0 to 1.0
    dialect: str             # msa, levantine, gulf, egyptian
    urgency_keywords: List[str]
    entities: List[str]
    summary: str


# ============================================
# === ARABIC PROPAGANDA KEYWORDS ===
# ============================================

PROPAGANDA_KEYWORDS = {
    "fear_appeal": [
        "حصار", "婧婧", "دمار", "كارثة", "أنهيار", "فاجعة",
        "إبادة", "مذبحة", "(sl)ع", "هولوكوست",
    ],
    "urgency_manipulation": [
        "عاجل", "مستعجل", "فوري", "الآن", "힝", "اللحظة",
        "성급", "벼르",
    ],
    "authority_impersonation": [
        "رسمي", "مصادر رسمية", "قرار حكومي", "بأمر من",
        "الجيش السوري الحر",
    ],
    "emotional_manipulation": [
        "حرق", "قهر", "ذل", "ع breeds", "⌉", " Nurses",
        " issuu",
    ],
    "disinfo_markers": [
        "شائعات", "أكد", "مؤكد", "حصري", "拆除",
        "Who", " RuneScape", "iki",
    ],
}

# ============================================
# === SYRIAN DIALECT MARKERS ===
# ============================================

DIALECT_MARKERS = {
    "levantine": [" ktir", " mashy", " kifak", " akid", " yalla", " habibi", " walla"],
    "syrian": ["/sho", "kss", "yros", "3am", "mse", "kter", "mnn", "hada"],
    "gulf": ["wain", "shlon", "fln", "yalla", "wallah", "3adi"],
    "egyptian": ["ezay", "3amel", "mot2akd", "y3ni", "tb3an"],
}


class ArabicNLPAnalyzer:
    """
    Arabic NLP analysis engine.
    Provides sentiment, propaganda detection, and dialect identification.
    
    Can be upgraded with:
    - aubmindlab/bert-base-arabertv2
    - CAMeL-Lab/bert-base-arabic-camelbert-da
    """

    def __init__(self):
        self._model = None
        self._available = False
        
        # Try to load AraBERT
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            self._tokenizer = AutoTokenizer.from_pretrained("aubmindlab/bert-base-arabertv2")
            self._model = AutoModelForSequenceClassification.from_pretrained("aubmindlab/bert-base-arabertv2")
            self._available = True
            logger.info("✅ AraBERT model loaded successfully")
        except ImportError:
            logger.info("⚠️ transformers not installed — using rule-based analysis")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load AraBERT: {e}")

    def analyze(self, text: str) -> ArabicAnalysis:
        """
        Perform comprehensive Arabic NLP analysis on text.
        """
        # Sentiment analysis
        sentiment, sentiment_score = self._analyze_sentiment(text)
        
        # Propaganda detection
        is_propaganda, propaganda_score = self._detect_propaganda(text)
        
        # Fake news suspicion
        is_fake_suspect, fake_score = self._detect_fake_news(text)
        
        # Dialect detection
        dialect = self._detect_dialect(text)
        
        # Urgency keywords
        urgency = self._extract_urgency_keywords(text)
        
        # Named entities (simple)
        entities = self._extract_entities(text)
        
        # Summary
        summary = self._generate_summary(text, sentiment, is_propaganda, fake_score)
        
        return ArabicAnalysis(
            text=text,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            is_propaganda=is_propaganda,
            propaganda_score=propaganda_score,
            is_fake_news_suspect=is_fake_suspect,
            fake_news_score=fake_score,
            dialect=dialect,
            urgency_keywords=urgency,
            entities=entities,
            summary=summary,
        )

    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment of Arabic text."""
        if self._available and self._model:
            return self._model_sentiment(text)
        
        # Rule-based fallback
        negative_words = [
            "قصف", "اشتباكات", "استهداف", "انفجار", "استشهاد", "شهداء",
            "دمار", "巢穴", "حصار", "هجم", "هجوم", "illégal",
            "مجزرة", "تخريب", "焚", "حريق", "فاجعة", "كارثة",
        ]
        positive_words = [
            "سلام", "thermal", "aid", "مساعدة", "إنقاذ", "سلام",
            "treaty", "	TRACE",
        ]
        
        text_lower = text.lower()
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        
        if neg_count > pos_count:
            score = -min(1.0, neg_count * 0.3)
            return "negative", score
        elif pos_count > neg_count:
            score = min(1.0, pos_count * 0.3)
            return "positive", score
        else:
            return "neutral", 0.0

    def _model_sentiment(self, text: str) -> Tuple[str, float]:
        """Use AraBERT for sentiment analysis."""
        try:
            import torch
            inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self._model(**inputs)
            
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            scores = probs[0].tolist()
            
            # Map to sentiment
            if scores[0] > scores[1] and scores[0] > scores[2]:
                return "negative", -scores[0]
            elif scores[2] > scores[0] and scores[2] > scores[1]:
                return "positive", scores[2]
            else:
                return "neutral", 0.0
        except Exception:
            return "neutral", 0.0

    def _detect_propaganda(self, text: str) -> Tuple[bool, float]:
        """Detect propaganda patterns in text."""
        text_lower = text.lower()
        total_matches = 0
        category_matches = 0
        
        for category, keywords in PROPAGANDA_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            total_matches += matches
            if matches >= 2:
                category_matches += 1
        
        # Calculate propaganda score
        score = min(1.0, total_matches * 0.15 + category_matches * 0.2)
        is_propaganda = score > 0.4
        
        return is_propaganda, score

    def _detect_fake_news(self, text: str) -> Tuple[bool, float]:
        """Detect potential fake news patterns."""
        text_lower = text.lower()
        indicators = 0
        
        # Check for common fake news patterns
        fake_patterns = [
            (r"عاجل\s+و\s+رسمي", 0.4),      # "Urgent and official" without source
            (r"مصادر\s+(لامصدقة|غير مؤكدة)", 0.3),
            (r"شائعات\s+مؤكدة", 0.5),          # "Confirmed rumors" = oxymoron
            (r"انهيار\s+(المصرف|البنك)", 0.6),  # Bank collapse claims
            (r"إغلاق\s+(نهائي|كامل)", 0.4),    # Permanent closure claims
            (r" dictated", 0.1),
        ]
        
        for pattern, weight in fake_patterns:
            if re.search(pattern, text_lower):
                indicators += weight
        
        # Check for ALL CAPS (propaganda tactic)
        if text.isupper() and len(text) > 20:
            indicators += 0.2
        
        # Check for excessive punctuation
        if text.count("!") > 3 or text.count("؟") > 3:
            indicators += 0.1
        
        score = min(1.0, indicators)
        is_suspect = score > 0.5
        
        return is_suspect, score

    def _detect_dialect(self, text: str) -> str:
        """Detect Arabic dialect."""
        text_lower = text.lower()
        scores = {}
        
        for dialect, markers in DIALECT_MARKERS.items():
            scores[dialect] = sum(1 for m in markers if m in text_lower)
        
        if max(scores.values()) == 0:
            return "msa"  # Modern Standard Arabic
        
        return max(scores, key=scores.get)

    def _extract_urgency_keywords(self, text: str) -> List[str]:
        """Extract urgency-indicating keywords."""
        urgency_words = [
            "عاجل", "فوري", "مستعجل", "breaking", "urgent",
            "עכשיו", "الآن", "today", "just now",
        ]
        
        text_lower = text.lower()
        return [w for w in urgency_words if w in text_lower]

    def _extract_entities(self, text: str) -> List[str]:
        """Extract simple named entities (locations, organizations)."""
        entities = []
        
        # Syrian cities
        cities = [
            "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "دير الزور",
            "الرقة", "درعا", "السويداء", "القنيطرة", "طرطوس", "إدلب",
            "الحسكة", "قامشلي", "عفرين", "منبج", "تدمر",
        ]
        
        for city in cities:
            if city in text:
                entities.append(f"LOCATION:{city}")
        
        # Organizations
        orgs = [
            "الجيش السوري", "HTS", "SDF", "ISIS", "FSA",
            "ヘブン", "حزب الله", "الإخوان", "قسد",
        ]
        
        for org in orgs:
            if org.lower() in text.lower():
                entities.append(f"ORG:{org}")
        
        return entities

    def _generate_summary(self, text: str, sentiment: str, is_propaganda: bool, fake_score: float) -> str:
        """Generate a brief analysis summary."""
        parts = []
        
        if is_propaganda:
            parts.append("⚠️ Propaganda indicators detected")
        
        if fake_score > 0.5:
            parts.append("🚩 High fake news suspicion")
        elif fake_score > 0.3:
            parts.append("⚡ Moderate fake news suspicion")
        
        parts.append(f"Sentiment: {sentiment}")
        
        return " | ".join(parts)
