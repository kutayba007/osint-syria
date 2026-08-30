"""
OSINT Syria — Tests for Data Sources
Tests for ACLED, Telescope, RSS, and Discord integrations.
"""

import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import OSINTEvent
from src.sources.telescope_detector import TelescopeDetector, THREAT_RULES


class TestTelescopeDetector:
    """Tests for the Telescope rule-based threat detection."""

    def test_detector_initialization(self):
        """Test detector loads rules correctly."""
        detector = TelescopeDetector()
        assert len(detector.rules) > 0
        assert len(detector._compiled_rules) == len(detector.rules)

    def test_detect_airstrike(self):
        """Test detection of airstrike keywords."""
        detector = TelescopeDetector()
        result = detector.scan_text("قصف جوي مكثف على ريف إدلب الغربي")
        assert result["threat_level"] == "critical"
        assert len(result["matches"]) > 0
        assert any(m["rule_id"] == "RULE-001" for m in result["matches"])

    def test_detect_ied(self):
        """Test detection of IED keywords."""
        detector = TelescopeDetector()
        result = detector.scan_text("انفجار عبوة ناسفة على طريق دمشق درعا الدولي")
        assert result["threat_level"] == "critical"
        assert any(m["rule_id"] == "RULE-003" for m in result["matches"])

    def test_detect_disinfo(self):
        """Test detection of disinformation keywords."""
        detector = TelescopeDetector()
        result = detector.scan_text("عاجل ورسمي: مصرف سورية المركزي يعلن إغلاق الفروع")
        assert result["threat_level"] == "medium"
        assert any(m["category"] == "disinfo" for m in result["matches"])

    def test_detect_road_closure(self):
        """Test detection of road closure."""
        detector = TelescopeDetector()
        result = detector.scan_text("إغلاق الطريق الدولي بين حلب وادلب")
        assert result["threat_level"] == "high"
        assert any(m["rule_id"] == "RULE-012" for m in result["matches"])

    def test_no_match_on_clean_text(self):
        """Test that clean text doesn't trigger false positives."""
        detector = TelescopeDetector()
        result = detector.scan_text("الطقس مشمس اليوم في دمشق")
        assert result["threat_level"] == "low"
        assert len(result["matches"]) == 0

    def test_english_detection(self):
        """Test English keyword detection."""
        detector = TelescopeDetector()
        result = detector.scan_text("Active firefight reported near Saraqib junction")
        assert result["threat_level"] == "critical"
        assert any(m["rule_id"] == "RULE-002" for m in result["matches"])

    def test_enrich_event(self):
        """Test enriching an OSINTEvent with detection results."""
        detector = TelescopeDetector()
        event = OSINTEvent(
            raw_text="اشتباكات عنيفة بالأسلحة المتوسطة في ريف حلب",
            source_channel="test",
        )
        enriched = detector.enrich_event(event)
        assert enriched.threat_level == "critical"
        assert enriched.raw_entities is not None
        assert "telescope_detections" in enriched.raw_entities

    def test_rules_summary(self):
        """Test rules summary generation."""
        detector = TelescopeDetector()
        summary = detector.get_rules_summary()
        assert len(summary) > 0
        assert all("id" in r for r in summary)
        assert all("severity" in r for r in summary)


class TestRSSFeeds:
    """Tests for RSS feed configuration."""

    def test_feeds_configured(self):
        """Test that RSS feeds are configured."""
        from src.sources.rss_feeds import RSS_FEEDS
        assert len(RSS_FEEDS) > 5
        assert all("name" in f for f in RSS_FEEDS)
        assert all("url" in f for f in RSS_FEEDS)

    def test_syria_keywords(self):
        """Test Syria keyword detection."""
        from src.sources.rss_feeds import RSSFeedAggregator
        aggregator = RSSFeedAggregator()
        assert aggregator._is_syria_relevant("Breaking: Airstrike in Idlib, Syria")
        assert aggregator._is_syria_relevant("قصف على ريف حلب")
        assert not aggregator._is_syria_relevant("Weather forecast in London")


class TestDiscordWebhook:
    """Tests for Discord webhook configuration."""

    def test_unconfigured_webhook(self):
        """Test that unconfigured webhook doesn't crash."""
        from src.sources.discord_webhook import DiscordWebhook
        webhook = DiscordWebhook(webhook_url="")
        assert not webhook.is_configured


class TestACLEDSource:
    """Tests for ACLED source configuration."""

    def test_event_type_mapping(self):
        """Test ACLED event type mapping."""
        from src.sources.acled_source import ACLEDSource
        source = ACLEDSource()
        assert "Battles" in source.EVENT_TYPE_MAP
        assert "Explosions/Remote violence" in source.EVENT_TYPE_MAP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
