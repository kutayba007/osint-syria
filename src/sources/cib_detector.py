"""
OSINT Syria — Coordinated Inauthentic Behavior (CIB) Detector
Detects coordinated campaigns, bot networks, and astroturfing.

Uses:
- AraBERT / CAMeL for Arabic NLP understanding
- Sentence Transformers for text similarity
- DBSCAN for clustering coordinated posts
- Velocity detection for timing anomalies

Inspired by HuggingFace models:
- aubmindlab/bert-base-arabertv2
- CAMeL-Lab/bert-base-arabic-camelbert-da
- sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("osint.sources.cib")


@dataclass
class SuspiciousPost:
    """A post flagged as potentially part of a coordinated campaign."""
    post_id: str
    username: str
    platform: str
    text: str
    timestamp: datetime
    url: str = ""
    similarity_score: float = 0.0
    cluster_id: str = ""


@dataclass
class CIBCluster:
    """A cluster of coordinated posts detected."""
    cluster_id: str
    posts: List[SuspiciousPost] = field(default_factory=list)
    similarity_threshold: float = 0.0
    time_window_seconds: int = 0
    account_count: int = 0
    platform_count: int = 0
    severity: str = "low"
    narrative: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CIBAlert:
    """An alert for a detected coordinated campaign."""
    alert_type: str  # "velocity_burst", "text_cluster", "bot_network"
    severity: str    # "critical", "high", "medium"
    title: str
    description: str
    cluster: CIBCluster
    detected_at: datetime = field(default_factory=datetime.utcnow)


# ============================================
# === VELOCITY THRESHOLDS ===
# ============================================

VELOCITY_THRESHOLDS = {
    "critical": {
        "min_posts": 20,
        "time_window_seconds": 300,  # 5 minutes
        "min_accounts": 10,
        "description": "20+ identical posts from 10+ accounts in 5 minutes"
    },
    "high": {
        "min_posts": 10,
        "time_window_seconds": 600,  # 10 minutes
        "min_accounts": 5,
        "description": "10+ similar posts from 5+ accounts in 10 minutes"
    },
    "medium": {
        "min_posts": 5,
        "time_window_seconds": 1800,  # 30 minutes
        "min_accounts": 3,
        "description": "5+ similar posts from 3+ accounts in 30 minutes"
    }
}


class CIBDetector:
    """
    Coordinated Inauthentic Behavior Detection Engine.
    
    Detection Methods:
    1. Text Similarity Clustering (DBSCAN-style)
    2. Velocity Burst Detection
    3. Bot Account Pattern Analysis
    4. Cross-Platform Synchronization
    """

    def __init__(self):
        self._post_buffer: List[SuspiciousPost] = []
        self._clusters: Dict[str, CIBCluster] = {}
        self._alerts: List[CIBAlert] = []
        
        # Similarity keywords for quick pre-filtering
        self.COORDINATION_KEYWORDS = [
            "عاجل", "رسمي", "شائعات", "مصرف سورية", "إغلاق",
            "انهيار", "إنذار", "حصار", "▵", "♻️", "⚠️",
        ]

    def add_post(self, post: SuspiciousPost) -> Optional[CIBAlert]:
        """
        Add a post and check for coordination patterns.
        Returns an alert if coordination is detected.
        """
        self._post_buffer.append(post)
        
        # Keep buffer manageable (last 1000 posts)
        if len(self._post_buffer) > 1000:
            self._post_buffer = self._post_buffer[-1000:]
        
        # Check for velocity bursts
        alert = self._check_velocity_burst(post)
        if alert:
            self._alerts.append(alert)
            return alert
        
        # Check for text similarity clusters
        alert = self._check_text_similarity(post)
        if alert:
            self._alerts.append(alert)
            return alert
        
        return None

    def _check_velocity_burst(self, new_post: SuspiciousPost) -> Optional[CIBAlert]:
        """
        Detect velocity bursts: many similar posts in short time window.
        Threshold: >20 identical posts from 10+ accounts in 5 minutes = CRITICAL
        """
        for severity, thresholds in VELOCITY_THRESHOLDS.items():
            time_window = timedelta(seconds=thresholds["time_window_seconds"])
            cutoff = new_post.timestamp - time_window
            
            # Get posts in time window with similar text
            recent_posts = [
                p for p in self._post_buffer
                if self._normalize_timestamp(p.timestamp) >= cutoff
                and self._text_similarity(p.text, new_post.text) > 0.7
            ]
            
            unique_accounts = set(p.username for p in recent_posts)
            
            if (len(recent_posts) >= thresholds["min_posts"] and
                len(unique_accounts) >= thresholds["min_accounts"]):
                
                # Create cluster
                cluster = CIBCluster(
                    cluster_id=f"CIB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    posts=recent_posts,
                    similarity_threshold=0.7,
                    time_window_seconds=thresholds["time_window_seconds"],
                    account_count=len(unique_accounts),
                    platform_count=len(set(p.platform for p in recent_posts)),
                    severity=severity,
                    narrative=new_post.text[:100],
                )
                
                alert = CIBAlert(
                    alert_type="velocity_burst",
                    severity=severity,
                    title=f"🚨 Velocity Burst Detected — {severity.upper()}",
                    description=thresholds["description"],
                    cluster=cluster,
                )
                
                logger.warning(
                    f"🚨 CIB DETECTED: {severity.upper()} — "
                    f"{len(recent_posts)} posts from {len(unique_accounts)} accounts "
                    f"in {thresholds['time_window_seconds']}s"
                )
                
                return alert
        
        return None

    def _check_text_similarity(self, new_post: SuspiciousPost) -> Optional[CIBAlert]:
        """
        Check if new post is textually similar to recent posts from different accounts.
        Uses simple text similarity (can be upgraded to embeddings).
        """
        recent_posts = [
            p for p in self._post_buffer[-100:]  # Check last 100 posts
            if p.username != new_post.username
            and abs((self._normalize_timestamp(p.timestamp) - self._normalize_timestamp(new_post.timestamp)).total_seconds()) < 3600
        ]
        
        similar_posts = [
            p for p in recent_posts
            if self._text_similarity(p.text, new_post.text) > 0.85
        ]
        
        if len(similar_posts) >= 3:
            unique_accounts = set(p.username for p in similar_posts)
            unique_accounts.add(new_post.username)
            
            if len(unique_accounts) >= 3:
                cluster = CIBCluster(
                    cluster_id=f"CIB-SIM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    posts=similar_posts + [new_post],
                    similarity_threshold=0.85,
                    account_count=len(unique_accounts),
                    severity="high",
                    narrative=new_post.text[:100],
                )
                
                return CIBAlert(
                    alert_type="text_cluster",
                    severity="high",
                    title="🕸️ Text Similarity Cluster Detected",
                    description=f"{len(unique_accounts)} accounts posting similar content",
                    cluster=cluster,
                )
        
        return None

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using Jaccard + keyword overlap.
        Can be upgraded to use sentence-transformers embeddings.
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        t1 = self._normalize_text(text1)
        t2 = self._normalize_text(text2)
        
        # Quick check: if texts are identical
        if t1 == t2:
            return 1.0
        
        # Jaccard similarity on words
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Boost for shared coordination keywords
        keyword_matches = sum(1 for kw in self.COORDINATION_KEYWORDS if kw in t1 and kw in t2)
        keyword_boost = min(0.2, keyword_matches * 0.05)
        
        return min(1.0, jaccard + keyword_boost)

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'https?://\S+', '', text)  # Remove URLs
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)  # Keep Arabic + alphanumeric
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _normalize_timestamp(self, ts: datetime) -> datetime:
        """Normalize timestamp to offset-naive for comparison."""
        if ts.tzinfo is not None:
            return ts.replace(tzinfo=None)
        return ts

    def get_active_alerts(self) -> List[CIBAlert]:
        """Get all active CIB alerts."""
        return self._alerts[-50:]  # Last 50 alerts

    def get_cluster_stats(self) -> Dict:
        """Get statistics about detected clusters."""
        return {
            "total_alerts": len(self._alerts),
            "critical": sum(1 for a in self._alerts if a.severity == "critical"),
            "high": sum(1 for a in self._alerts if a.severity == "high"),
            "medium": sum(1 for a in self._alerts if a.severity == "medium"),
            "total_posts_analyzed": len(self._post_buffer),
        }


# ============================================
# === EMBEDDING-BASED SIMILARITY (Optional) ===
# ============================================

class EmbeddingSimilarity:
    """
    Advanced text similarity using sentence-transformers.
    Requires: pip install sentence-transformers
    
    Uses: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    """
    
    def __init__(self):
        self._model = None
        self._available = False
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._available = True
            logger.info("✅ Embedding similarity loaded (MiniLM-L12)")
        except ImportError:
            logger.info("⚠️ sentence-transformers not installed — using fallback similarity")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load embedding model: {e}")

    def compute_similarity(self, texts: List[str]) -> List[List[float]]:
        """Compute pairwise similarity matrix for a list of texts."""
        if not self._available or not self._model:
            return [[0.0] * len(texts) for _ in texts]
        
        embeddings = self._model.encode(texts, convert_to_tensor=True)
        
        # Cosine similarity
        from torch.nn.functional import cosine_similarity
        similarity_matrix = []
        for i, emb_i in enumerate(embeddings):
            row = []
            for j, emb_j in enumerate(embeddings):
                sim = cosine_similarity(emb_i.unsqueeze(0), emb_j.unsqueeze(0)).item()
                row.append(sim)
            similarity_matrix.append(row)
        
        return similarity_matrix

    def find_clusters(self, texts: List[str], threshold: float = 0.8) -> List[List[int]]:
        """Find clusters of similar texts using DBSCAN-style grouping."""
        if len(texts) < 2:
            return []
        
        sim_matrix = self.compute_similarity(texts)
        visited = set()
        clusters = []
        
        for i in range(len(texts)):
            if i in visited:
                continue
            
            cluster = [i]
            visited.add(i)
            
            for j in range(i + 1, len(texts)):
                if j not in visited and sim_matrix[i][j] >= threshold:
                    cluster.append(j)
                    visited.add(j)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        return clusters
