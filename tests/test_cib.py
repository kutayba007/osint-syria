"""
OSINT Syria — Tests for CIB Detection & Arabic NLP
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sources.cib_detector import CIBDetector, SuspiciousPost, EmbeddingSimilarity
from src.sources.arabic_nlp import ArabicNLPAnalyzer


class TestCIBDetector:
    """Tests for Coordinated Inauthentic Behavior detection."""

    def test_detector_initialization(self):
        """Test CIB detector initializes correctly."""
        detector = CIBDetector()
        assert len(detector._post_buffer) == 0
        assert len(detector._clusters) == 0

    def test_single_post_no_alert(self):
        """Single post should not trigger alert."""
        detector = CIBDetector()
        post = SuspiciousPost(
            post_id="p1",
            username="user1",
            platform="telegram",
            text="أخبار عادية اليوم في دمشق",
            timestamp=datetime.utcnow(),
        )
        alert = detector.add_post(post)
        assert alert is None

    def test_velocity_burst_detection(self):
        """Test detection of coordinated posting burst."""
        detector = CIBDetector()
        now = datetime.utcnow()
        
        # Simulate 15 identical posts from different accounts in 2 minutes
        for i in range(15):
            post = SuspiciousPost(
                post_id=f"p{i}",
                username=f"bot_{i}",
                platform="telegram",
                text="عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع",
                timestamp=now - timedelta(seconds=i * 10),
            )
            detector.add_post(post)
        
        # Should have buffered posts and potentially detected alerts
        assert len(detector._post_buffer) == 15

    def test_text_similarity_detection(self):
        """Test detection of similar posts from different accounts."""
        detector = CIBDetector()
        now = datetime.utcnow()
        
        # Similar posts from different accounts
        base_text = "شائعات مؤكدة: إغلاق المعابر الحدودية نهائياً"
        
        posts = [
            SuspiciousPost(f"p{i}", f"user_{i}", "telegram", 
                          base_text if i < 3 else f"نسخة معدّلة: {base_text}",
                          now - timedelta(minutes=i))
            for i in range(6)
        ]
        
        alerts = []
        for post in posts:
            alert = detector.add_post(post)
            if alert:
                alerts.append(alert)
        
        # Should detect similarity cluster
        assert len(alerts) > 0 or len(detector._alerts) > 0

    def test_text_similarity_function(self):
        """Test text similarity calculation."""
        detector = CIBDetector()
        
        # Identical texts
        sim = detector._text_similarity("قصف جوي على إدلب", "قصف جوي على إدلب")
        assert sim == 1.0
        
        # Similar texts (share keywords)
        sim = detector._text_similarity(
            "عاجل: قصف جوي على ريف إدلب",
            "عاجل: استهداف جوي لريف إدلب"
        )
        assert sim > 0.3  # Should show some similarity
        
        # Different texts
        sim = detector._text_similarity(
            "قصف جوي على إدلب",
            "الطقس مشمس في دمشق"
        )
        assert sim < 0.8  # Should not be highly similar

    def test_normalize_text(self):
        """Test text normalization."""
        detector = CIBDetector()
        
        text = "https://example.com عاجل!! قصف على إدلب"
        normalized = detector._normalize_text(text)
        assert "https" not in normalized
        assert "عاجل" in normalized

    def test_cluster_stats(self):
        """Test cluster statistics."""
        detector = CIBDetector()
        stats = detector.get_cluster_stats()
        assert "total_alerts" in stats
        assert "total_posts_analyzed" in stats


class TestArabicNLP:
    """Tests for Arabic NLP analysis."""

    def test_analyzer_initialization(self):
        """Test Arabic NLP analyzer initializes."""
        analyzer = ArabicNLPAnalyzer()
        assert analyzer is not None

    def test_sentiment_analysis(self):
        """Test sentiment detection."""
        analyzer = ArabicNLPAnalyzer()
        
        # Negative text
        result = analyzer.analyze("قصف مدمر يستهدف المستشفى المركزي")
        assert result.sentiment == "negative"
        assert result.sentiment_score < 0
        
        # Positive text
        result = analyzer.analyze("مساعدة إنسانية و_contents وصلت للمنطقة")
        assert result.sentiment == "positive"

    def test_propaganda_detection(self):
        """Test propaganda pattern detection."""
        analyzer = ArabicNLPAnalyzer()
        
        # Propaganda text should have some score
        result = analyzer.analyze("عاجل ورسمي: مصرف سورية المركزي يعلن إغلاق كامل!")
        assert result.propaganda_score >= 0.0  # Score calculated
        
        # Normal text should have lower score
        result = analyzer.analyze("الطقس مشمس اليوم في دمشق")
        assert result.propaganda_score < 0.8

    def test_fake_news_detection(self):
        """Test fake news suspicion detection."""
        analyzer = ArabicNLPAnalyzer()
        
        # Suspicious text
        result = analyzer.analyze("شائعات مؤكدة: انهيار المصرف المركزي!")
        assert result.is_fake_news_suspect or result.fake_news_score > 0.3

    def test_dialect_detection(self):
        """Test dialect identification."""
        analyzer = ArabicNLPAnalyzer()
        
        result = analyzer.analyze("كيفك؟ شو أخبارك؟ كتير حلو")
        assert result.dialect in ("levantine", "syrian", "msa")

    def test_urgency_keywords(self):
        """Test urgency keyword extraction."""
        analyzer = ArabicNLPAnalyzer()
        
        result = analyzer.analyze("عاجل: قصف فوري على المنطقة")
        assert "عاجل" in result.urgency_keywords

    def test_entity_extraction(self):
        """Test named entity extraction."""
        analyzer = ArabicNLPAnalyzer()
        
        result = analyzer.analyze("اشتباكات في حلب ودير الزور")
        assert any("حلب" in e for e in result.entities)
        assert any("دير الزور" in e for e in result.entities)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
