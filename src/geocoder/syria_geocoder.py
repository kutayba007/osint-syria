"""
OSINT Syria - Geographic Coder
Converts location names to coordinates using Nominatim (OpenStreetMap).
Optimized for Syrian geography.
"""

import logging
import time
from typing import Optional, Tuple, Dict
from functools import lru_cache

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from config.settings import config
from src.models import OSINTEvent

logger = logging.getLogger("osint.geocoder")

# === Pre-mapped Syrian locations for instant lookup ===
SYRIA_COORDS: Dict[str, Tuple[float, float]] = {
    # Governorates
    "دمشق": (33.5138, 36.2765),
    "حلب": (36.2021, 37.1343),
    "حمص": (34.7369, 36.7131),
    "حماة": (35.1318, 36.7478),
    "اللاذقية": (35.5314, 35.7796),
    "دير الزور": (35.3359, 40.1408),
    "الرقة": (35.9594, 39.0090),
    "درعا": (32.6180, 36.1021),
    "السويداء": (32.7088, 36.5708),
    "القنيطرة": (33.1257, 35.8248),
    "طرطوس": (34.8922, 35.8844),
    "إدلب": (35.9306, 36.6339),

    # Cities & Towns
    "حمص": (34.7369, 36.7131),
    "تدمر": (34.5500, 38.2667),
    "بو Kamal": (34.4722, 40.9333),
    "التنف": (33.0769, 36.1975),
    "عفرين": (36.3789, 36.8567),
    "منبج": (36.5289, 37.9508),
    "رأس العين": (36.8433, 40.0689),
    "القامشلي": (37.0483, 41.2294),
    "عامودا": (37.0942, 41.2822),
    "سلvik": (36.3478, 36.7653),
    "إسكندرون": (36.1667, 36.1667),
    "دوما": (33.5717, 36.4025),
    "يبرود": (33.9267, 36.4631),
    "قناطرة": (33.1257, 35.8248),
    "جبلة": (35.3639, 35.9264),
    "بانياس": (35.1822, 35.9444),
    "صافيتا": (34.8317, 36.1042),
    "الحلكة": (34.7353, 36.6958),
    "المهرة": (34.4217, 40.3944),
    "صوران": (33.4117, 36.2367),
    "معضمية الشام": (33.5150, 36.2217),
    "جرمانا": (33.4817, 36.2556),
    "سaira": (33.4333, 36.2333),

    # English names
    "Damascus": (33.5138, 36.2765),
    "Aleppo": (36.2021, 37.1343),
    "Homs": (34.7369, 36.7131),
    "Hama": (35.1318, 36.7478),
    "Latakia": (35.5314, 35.7796),
    "Deir ez-Zor": (35.3359, 40.1408),
    "Raqqa": (35.9594, 39.0090),
    "Daraa": (32.6180, 36.1021),
    "Idlib": (35.9306, 36.6339),
    "Tartus": (34.8922, 35.8844),
    "Quneitra": (33.1257, 35.8248),
    "Suwayda": (32.7088, 36.5708),
    "Palmyra": (34.5500, 38.2667),
    "Qamishli": (37.0483, 41.2294),
    "Tadmur": (34.5500, 38.2667),
    "Afrin": (36.3789, 36.8567),
    "Manbij": (36.5289, 37.9508),

    # Golan & border areas
    "الجولان": (33.1257, 35.8248),
    "Golan Heights": (33.1257, 35.8248),
    "ش baghdad": (33.0769, 36.1975),

    # Damascus suburbs
    "ريف دمشق": (33.5500, 36.3500),
    "القلمون": (33.9000, 36.6000),
    "الencviental Ghouta": (33.5000, 36.4500),
}


class SyriaGeocoder:
    """
    Geocoding engine optimized for Syrian locations.
    Uses a local cache first, then falls back to Nominatim.
    """

    def __init__(self):
        self.geocoder = Nominatim(user_agent=config.geo.user_agent)
        self._last_request_time = 0
        self._min_interval = 1.1  # Nominatim requires 1 req/sec

    def geocode_event(self, event: OSINTEvent) -> OSINTEvent:
        """
        Enrich an event with geographic coordinates.
        Priority: 1) AI-extracted location, 2) Nominatim, 3) Manual lookup.
        """
        # Try the location extracted by AI
        location = event.location_name or event.city or event.governorate

        if not location:
            logger.debug("No location to geocode")
            return event

        coords = self._lookup_location(location)

        if coords:
            event.latitude, event.longitude = coords
            logger.info(f"📍 Geocoded '{location}' → ({coords[0]:.4f}, {coords[1]:.4f})")
        else:
            logger.warning(f"⚠️ Could not geocode: '{location}'")

        return event

    def _lookup_location(self, name: str) -> Optional[Tuple[float, float]]:
        """
        Look up coordinates for a location name.
        1) Check local cache
        2) Fuzzy match in local cache
        3) Fall back to Nominatim
        """
        # Exact match in local cache
        if name in SYRIA_COORDS:
            return SYRIA_COORDS[name]

        # Case-insensitive match
        for key, coords in SYRIA_COORDS.items():
            if key.lower() == name.lower():
                return coords

        # Partial match (e.g., "دمشق rural" → "دمشق")
        for key, coords in SYRIA_COORDS.items():
            if name in key or key in name:
                return coords

        # Fallback: Nominatim API
        return self._nominatim_lookup(name)

    def _nominatim_lookup(self, name: str) -> Optional[Tuple[float, float]]:
        """Query Nominatim for coordinates."""
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        try:
            # Add Syria context to improve accuracy
            query = f"{name}, Syria"
            location = self.geocoder.geocode(query, timeout=config.geo.timeout)
            self._last_request_time = time.time()

            if location:
                return (location.latitude, location.longitude)

            # Try without "Syria" suffix
            location = self.geocoder.geocode(name, timeout=config.geo.timeout)
            if location:
                return (location.latitude, location.longitude)

        except GeocoderTimedOut:
            logger.warning(f"⏱️ Nominatim timeout for '{name}'")
        except GeocoderServiceError as e:
            logger.error(f"❌ Nominatim error: {e}")

        return None

    def geocode_batch(self, events: list) -> list:
        """Geocode multiple events."""
        return [self.geocode_event(e) for e in events]
