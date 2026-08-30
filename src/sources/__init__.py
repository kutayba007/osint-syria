"""
OSINT Syria — Data Sources Package
Integrates multiple free intelligence sources for comprehensive monitoring.
"""

from .acled_source import ACLEDSource
from .telescope_detector import TelescopeDetector
from .rss_feeds import RSSFeedAggregator
from .discord_webhook import DiscordWebhook
from .cib_detector import CIBDetector, EmbeddingSimilarity
from .arabic_nlp import ArabicNLPAnalyzer

__all__ = [
    "ACLEDSource",
    "TelescopeDetector",
    "RSSFeedAggregator",
    "DiscordWebhook",
    "CIBDetector",
    "EmbeddingSimilarity",
    "ArabicNLPAnalyzer",
]
