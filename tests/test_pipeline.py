"""
OSINT Syria - Basic Tests
Unit tests for core pipeline components.
"""

import sys
import os
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import OSINTEvent, AlertMessage


class TestOSINTEvent:
    """Tests for the OSINTEvent data model."""

    def test_create_event(self):
        """Test creating a basic event."""
        event = OSINTEvent(
            raw_text="اشتباكات في ريف حلب الشمالي",
            source_channel="test_channel",
        )
        assert event.raw_text == "اشتباكات في ريف حلب الشمالي"
        assert event.source_channel == "test_channel"
        assert event.threat_level == "low"
        assert event.confidence == 0.0

    def test_event_with_location(self):
        """Test event with geographic data."""
        event = OSINTEvent(
            raw_text="قصف على مدينة إدلب",
            source_channel="test",
            location_name="إدلب",
            latitude=35.9306,
            longitude=36.6339,
            governorate="إدلب",
            city="إدلب",
        )
        assert event.latitude == 35.9306
        assert event.longitude == 36.6339
        assert event.governorate == "إدلب"

    def test_event_serialization(self):
        """Test JSON serialization."""
        event = OSINTEvent(
            raw_text="test",
            source_channel="test",
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        json_data = event.model_dump()
        assert "raw_text" in json_data
        assert json_data["raw_text"] == "test"

    def test_event_threat_levels(self):
        """Test all threat level values."""
        for level in ["critical", "high", "medium", "low"]:
            event = OSINTEvent(
                raw_text="test",
                source_channel="test",
                threat_level=level,
            )
            assert event.threat_level == level


class TestAlertMessage:
    """Tests for the AlertMessage model."""

    def test_create_alert(self):
        """Test creating an alert message."""
        alert = AlertMessage(
            event_id="test-123",
            title="Test Alert",
            body="This is a test",
            threat_level="high",
            location="Aleppo",
            source_channel="test",
        )
        assert alert.event_id == "test-123"
        assert alert.threat_level == "high"


class TestGeocoder:
    """Tests for the Syria geocoder (no API calls)."""

    def test_known_city_lookup(self):
        """Test looking up a known Syrian city."""
        from src.geocoder.syria_geocoder import SYRIA_COORDS

        assert "دمشق" in SYRIA_COORDS
        assert "حلب" in SYRIA_COORDS
        assert "Damascus" in SYRIA_COORDS

        damascus = SYRIA_COORDS["دمشق"]
        assert 33.0 < damascus[0] < 34.0  # Latitude
        assert 36.0 < damascus[1] < 37.0  # Longitude

    def test_english_names(self):
        """Test English city name lookup."""
        from src.geocoder.syria_geocoder import SYRIA_COORDS

        aleppo = SYRIA_COORDS["Aleppo"]
        assert 36.0 < aleppo[0] < 37.0


class TestConfig:
    """Tests for configuration."""

    def test_config_loads(self):
        """Test that config module loads without errors."""
        from config.settings import config

        assert config is not None
        assert hasattr(config, 'telegram')
        assert hasattr(config, 'groq')
        assert hasattr(config, 'supabase')
        assert hasattr(config, 'geo')
        assert hasattr(config, 'monitored_channels')
        assert len(config.monitored_channels) > 0

    def test_threat_levels(self):
        """Test threat level definitions."""
        from config.settings import config

        levels = config.threat_levels
        assert "critical" in levels
        assert "high" in levels
        assert "medium" in levels
        assert "low" in levels


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
