"""
OSINT Syria — FastAPI Backend
Serves OSINT events, statistics, and real-time updates to the React dashboard.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager


def _git_sha() -> str:
    """Best-effort short git commit SHA for deploy verification."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


GIT_SHA = _git_sha()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config.settings import config
from src.database.supabase_client import SupabaseDB
from src.models import OSINTEvent

logger = logging.getLogger("osint.api")

# === WebSocket connection manager ===
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket connected ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected ({len(self.active_connections)} total)")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# === Database singleton ===
db = SupabaseDB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    db.connect()
    logger.info("🚀 OSINT Syria API started")
    yield
    logger.info("🛑 OSINT Syria API stopped")


# === FastAPI App ===
app = FastAPI(
    title="OSINT Syria API",
    description="Real-time OSINT intelligence data API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# === API RESPONSE MODELS ===
# ============================================

class IncidentResponse(BaseModel):
    id: str
    title: str
    titleArabic: Optional[str] = None
    threatLevel: str
    category: str
    locationName: str
    locationNameArabic: Optional[str] = None
    governorate: str
    coordinates: List[float]
    timestamp: str
    timestampIso: str
    confidenceScore: float
    sourceReliability: str
    threatScore: float
    impact: str
    urgency: str
    rawExcerptArabic: Optional[str] = None
    rawExcerptEnglish: str
    hasArabic: bool
    fullNarrative: str
    entities: List[dict]
    isAcknowledged: bool = False
    isEscalated: bool = False
    isBookmarked: bool = False
    primarySource: dict

class StatsResponse(BaseModel):
    totalIncidents: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int
    disinfoCount: int
    avgConfidence: float
    activeGovernorates: int
    highestTensionRegion: str
    highestTensionScore: int

class GovernorateResponse(BaseModel):
    name: str
    nameArabic: str
    center: List[float]
    tensionScore: int
    threatLevel: str
    activeIncidentsCount: int
    primaryConcern: str
    trend: str


# ============================================
# === THREAT LEVEL MAPPING ===
# ============================================

THREAT_MAP = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

CATEGORY_MAP = {
    "اشتباكات": "security",
    "قصف": "security",
    "انفجار": "security",
    "تحركات عسكرية": "security",
    "إغلاق طريق": "infrastructure",
    "استهداف": "security",
    "توتر": "civilian",
    "إعلان رسمي": "civilian",
    "نازحين": "civilian",
    "إنساني": "civilian",
    "اقتصادي": "infrastructure",
    "سياسي": "civilian",
    "أمني": "security",
    "تضليل": "digital_threats",
    "ب镱": "protests",
    "غير محدد": "civilian",
}


def event_to_incident(event: OSINTEvent) -> dict:
    """Convert an OSINTEvent to the React frontend's Incident format."""
    threat = THREAT_MAP.get(event.threat_level, "LOW")
    category = CATEGORY_MAP.get(event.event_type, "civilian")

    # Calculate threat score from confidence and threat level
    threat_scores = {"CRITICAL": 94, "HIGH": 81, "MEDIUM": 55, "LOW": 22}
    threat_score = threat_scores.get(threat, 22)

    # Determine impact and urgency
    impact_map = {"CRITICAL": "HIGH", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}
    urgency_map = {"CRITICAL": "IMMEDIATE", "HIGH": "IMMEDIATE", "MEDIUM": "ELEVATED", "LOW": "ROUTINE"}

    return {
        "id": event.id or f"SYR-{datetime.utcnow().year}-{hash(event.raw_text) % 100000:06d}",
        "title": event.summary_en or event.raw_text[:100],
        "titleArabic": event.summary_ar,
        "threatLevel": threat,
        "category": category,
        "locationName": event.location_name or "Unknown Location",
        "locationNameArabic": event.location_name,
        "governorate": event.governorate or "Unknown",
        "coordinates": [
            event.latitude or 35.0,
            event.longitude or 38.0,
        ],
        "timestamp": event.timestamp.strftime("%H:%M UTC") if event.timestamp else "N/A",
        "timestampIso": event.timestamp.isoformat() if event.timestamp else datetime.utcnow().isoformat(),
        "confidenceScore": event.confidence * 100,
        "sourceReliability": "B+",
        "threatScore": threat_score,
        "impact": impact_map.get(threat, "LOW"),
        "urgency": urgency_map.get(threat, "ROUTINE"),
        "rawExcerptArabic": event.raw_text[:300] if event.raw_text else None,
        "rawExcerptEnglish": event.summary_en or event.raw_text[:300],
        "hasArabic": bool(event.raw_text),
        "fullNarrative": event.summary_ar or event.raw_text,
        "entities": event.raw_entities.get("entities", []) if event.raw_entities else [],
        "isAcknowledged": False,
        "isEscalated": threat in ("CRITICAL", "HIGH"),
        "isBookmarked": False,
        "primarySource": {
            "platform": "telegram",
            "channelOrAccount": f"@{event.source_channel}",
            "postTime": event.timestamp.strftime("%H:%M UTC") if event.timestamp else "N/A",
            "reliability": "B+",
        },
    }


# ============================================
# === API ROUTES ===
# ============================================

@app.get("/")
async def root():
    return {
        "name": "OSINT Syria API",
        "version": "1.0.0",
        "git_sha": GIT_SHA,
        "status": "operational",
        "endpoints": {
            "incidents": "/api/incidents",
            "stats": "/api/stats",
            "governorates": "/api/governorates",
            "map_data": "/api/map-data",
            "health": "/api/health",
        }
    }


@app.get("/api/health")
async def health_check():
    """Check API and database health."""
    db_ok = db.health_check()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "git_sha": GIT_SHA,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    hours: int = Query(24, ge=1, le=720),
    threat_level: Optional[str] = Query(None),
    governorate: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Get recent OSINT incidents."""
    events = db.get_recent_events(hours=hours, threat_level=threat_level, governorate=governorate, limit=limit)
    incidents = [event_to_incident(OSINTEvent(**e)) for e in events]
    return incidents


@app.get("/api/stats")
async def get_stats(hours: int = Query(24, ge=1, le=720)):
    """Get aggregated statistics for the dashboard."""
    events = db.get_recent_events(hours=hours)

    if not events:
        # Return empty stats
        return {
            "totalIncidents": 0,
            "criticalCount": 0,
            "highCount": 0,
            "mediumCount": 0,
            "lowCount": 0,
            "disinfoCount": 0,
            "avgConfidence": 0,
            "activeGovernorates": 0,
            "highestTensionRegion": "N/A",
            "highestTensionScore": 0,
        }

    threat_counts = {}
    gov_counts = {}
    total_confidence = 0

    for e in events:
        level = e.get("threat_level", "low")
        threat_counts[level] = threat_counts.get(level, 0) + 1

        gov = e.get("governorate", "Unknown")
        gov_counts[gov] = gov_counts.get(gov, 0) + 1

        total_confidence += e.get("confidence", 0)

    # Find highest tension region
    highest_gov = max(gov_counts.items(), key=lambda x: x[1]) if gov_counts else ("N/A", 0)

    return {
        "totalIncidents": len(events),
        "criticalCount": threat_counts.get("critical", 0),
        "highCount": threat_counts.get("high", 0),
        "mediumCount": threat_counts.get("medium", 0),
        "lowCount": threat_counts.get("low", 0),
        "disinfoCount": threat_counts.get("disinfo", 0),
        "avgConfidence": round(total_confidence / len(events) * 100, 1) if events else 0,
        "activeGovernorates": len(gov_counts),
        "highestTensionRegion": highest_gov[0],
        "highestTensionScore": highest_gov[1],
    }


@app.get("/api/governorates", response_model=List[GovernorateResponse])
async def get_governorates():
    """Get governorate data with tension scores."""
    from src.geocoder.syria_geocoder import SYRIA_COORDS

    # Syrian governorates with tension data
    governorates = [
        {"name": "Idlib", "nameArabic": "إدلب", "center": [35.9306, 36.6347], "tensionScore": 92, "threatLevel": "CRITICAL", "activeIncidentsCount": 42, "primaryConcern": "Artillery exchanges, UAV reconnaissance", "trend": "INCREASING"},
        {"name": "Aleppo", "nameArabic": "حلب", "center": [36.2021, 37.1343], "tensionScore": 78, "threatLevel": "HIGH", "activeIncidentsCount": 29, "primaryConcern": "Northern rural skirmishes, supply corridor monitoring", "trend": "STABLE"},
        {"name": "Damascus & Rif Dimashq", "nameArabic": "دمشق وريف دمشق", "center": [33.5138, 36.2765], "tensionScore": 65, "threatLevel": "MEDIUM", "activeIncidentsCount": 18, "primaryConcern": "Currency rumors, infrastructure reports", "trend": "STABLE"},
        {"name": "Deir ez-Zor", "nameArabic": "دير الزور", "center": [35.3375, 40.1444], "tensionScore": 85, "threatLevel": "HIGH", "activeIncidentsCount": 23, "primaryConcern": "Euphrates crossing tensions, tribal mobilization", "trend": "INCREASING"},
        {"name": "Daraa", "nameArabic": "درعا", "center": [32.6186, 36.1025], "tensionScore": 74, "threatLevel": "HIGH", "activeIncidentsCount": 15, "primaryConcern": "Targeted assassinations, IED attacks", "trend": "STABLE"},
        {"name": "Homs", "nameArabic": "حمص", "center": [34.7324, 36.7137], "tensionScore": 58, "threatLevel": "MEDIUM", "activeIncidentsCount": 11, "primaryConcern": "Eastern desert ambush reports", "trend": "DECREASING"},
        {"name": "Hama", "nameArabic": "حماة", "center": [35.1318, 36.7578], "tensionScore": 62, "threatLevel": "MEDIUM", "activeIncidentsCount": 14, "primaryConcern": "Ghab plain tensions", "trend": "STABLE"},
        {"name": "Raqqa", "nameArabic": "الرقة", "center": [35.9594, 39.0089], "tensionScore": 69, "threatLevel": "MEDIUM", "activeIncidentsCount": 12, "primaryConcern": "Tabqa dam security", "trend": "STABLE"},
        {"name": "Hasakah", "nameArabic": "الحسكة", "center": [36.5049, 40.7483], "tensionScore": 72, "threatLevel": "HIGH", "activeIncidentsCount": 16, "primaryConcern": "Qamishli friction, water station shutdowns", "trend": "INCREASING"},
        {"name": "Latakia", "nameArabic": "اللاذقية", "center": [35.5317, 35.7906], "tensionScore": 48, "threatLevel": "LOW", "activeIncidentsCount": 7, "primaryConcern": "Port maritime activity", "trend": "STABLE"},
        {"name": "Tartus", "nameArabic": "طرطوس", "center": [34.8890, 35.8866], "tensionScore": 35, "threatLevel": "LOW", "activeIncidentsCount": 4, "primaryConcern": "Naval logistics", "trend": "DECREASING"},
        {"name": "As-Suwayda", "nameArabic": "السويداء", "center": [32.7090, 36.5695], "tensionScore": 71, "threatLevel": "HIGH", "activeIncidentsCount": 13, "primaryConcern": "Civil assembly, economic strike", "trend": "INCREASING"},
        {"name": "Quneitra", "nameArabic": "القنيطرة", "center": [33.1258, 35.8247], "tensionScore": 68, "threatLevel": "MEDIUM", "activeIncidentsCount": 8, "primaryConcern": "Golan disengagement line", "trend": "STABLE"},
    ]

    return governorates


@app.get("/api/map-data")
async def get_map_data(hours: int = Query(24, ge=1, le=720)):
    """Get all events with coordinates for the tactical map."""
    map_data = db.get_map_data(hours=hours)
    return map_data


@app.post("/api/incidents/{incident_id}/escalate")
async def escalate_incident(incident_id: str):
    """Escalate an incident."""
    # In production, update Supabase
    return {"status": "escalated", "incident_id": incident_id}


@app.post("/api/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str):
    """Acknowledge an incident."""
    return {"status": "acknowledged", "incident_id": incident_id}


# ============================================
# === WEBSOCKET FOR REAL-TIME UPDATES ===
# ============================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident streaming.
    Frontend connects here to receive live updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================
# === UTILITY: Push new event to all clients ===
# ============================================

async def push_event_to_clients(event: OSINTEvent):
    """Broadcast a new event to all connected WebSocket clients."""
    incident = event_to_incident(event)
    await manager.broadcast({
        "type": "new_incident",
        "data": incident,
    })


# ============================================
# === RUN SERVER ===
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
