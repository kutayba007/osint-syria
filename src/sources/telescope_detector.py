"""
OSINT Syria — Telescope-style Threat Detector
Rule-based real-time detection on Telegram channels.
Inspired by the open-source Telescope project for Telegram OSINT.

Detects:
- Military operations & escalation keywords
- Disinformation patterns
- Urgency indicators
- Geopolitical threat signals
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.models import OSINTEvent

logger = logging.getLogger("osint.sources.telescope")


@dataclass
class ThreatRule:
    """A detection rule for threat identification."""
    id: str
    name_ar: str
    name_en: str
    category: str  # security, disinfo, infrastructure, humanitarian
    severity: str  # critical, high, medium, low
    patterns: List[str]  # Regex patterns (Arabic + English)
    confidence_boost: float = 0.0  # Additional confidence when matched
    description: str = ""


# ============================================
# === THREAT DETECTION RULES ===
# ============================================

THREAT_RULES: List[ThreatRule] = [
    # === CRITICAL: Active Military Operations ===
    ThreatRule(
        id="RULE-001",
        name_ar="استهداف مباشر",
        name_en="Direct Airstrike",
        category="security",
        severity="critical",
        patterns=[
            r"غ[اى]رة\s+(جوية|جوي|عسكرية)",
            r"قصف\s+(جوي|مدفعي|ennent)",
            r"airstrike|air\s+strike|aerial\s+attack",
            r"استهداف\s+(مباشر|جوي|مدفعي)",
            r"طيران\s+(حر|عسكري)",
            r"MQ-9|F-16|Su-24|MiG|无人机",
            r"محمد\s+400|Shahed",
        ],
        confidence_boost=0.25,
        description="Direct military airstrikes or aerial bombardment detected",
    ),
    ThreatRule(
        id="RULE-002",
        name_ar="اشتباكات مسلحة",
        name_en="Active Firefight",
        category="security",
        severity="critical",
        patterns=[
            r"اشتباكات?\s+(عناصر|مسلحة|عنيفة|مباشرة)",
            r"مواجهات?\s+(مسلحة|عنيفة)",
            r"تبادل\s+( إطلاق | نيران | قصف )",
            r"active\s+fighting|firefight|gunbattle",
            r"سقوط\s+(قذائف|صواريخ|عبوات)",
            r"استشهاد|استشهد|شهيد",
        ],
        confidence_boost=0.20,
        description="Active armed confrontation or firefight",
    ),
    ThreatRule(
        id="RULE-003",
        name_ar="عبوات ناسفة",
        name_en="IED / VBIED",
        category="security",
        severity="critical",
        patterns=[
            r"عبوة\s+(ناسفة|تفجيرية|متفجرة)",
            r"سيارة\s+مفخخة",
            r"انفجار\s+(عبوة|سيارة|نابل)",
            r"IED|VBIED|roadside\s+bomb",
            r"تفجير\s+( עצמי | انتحاري )",
        ],
        confidence_boost=0.22,
        description="Improvised explosive device or vehicle-borne IED",
    ),

    # === HIGH: Escalation & Movement ===
    ThreatRule(
        id="RULE-010",
        name_ar="تحركات عسكرية",
        name_en="Military Mobilization",
        category="security",
        severity="high",
        patterns=[
            r"تحريك\s+(قوات|دبابات|مدرعات)",
            r"حشد\s+(عسكري|enuity)",
            r"move?ment\s+(of\s+)?troops|troop\s+buildup",
            r"columns?\s+of\s+(armor|tanks|military)",
            r"デプロイ|reinforc",
            r"تجمع\s+(قوات|عناصر)",
        ],
        confidence_boost=0.15,
        description="Military force movement or mobilization detected",
    ),
    ThreatRule(
        id="RULE-011",
        name_ar="انفجار ميداني",
        name_en="Explosion / Blast",
        category="security",
        severity="high",
        patterns=[
            r"انفجار\s+(هائل|كبير|غامض|مستهدف)",
            r"أعمدة\s+(الدخان|دخان)",
            r"explosion|detonation|blast",
            r"صوت\s+انفجار",
            r"اهتزاز",
        ],
        confidence_boost=0.12,
        description="Explosion or blast event detected",
    ),
    ThreatRule(
        id="RULE-012",
        name_ar="إغلاق طرق",
        name_en="Road Closure / Blockade",
        category="infrastructure",
        severity="high",
        patterns=[
            r"إغلاق\s+(الطريق|الطرقات|المحاور)",
            r"حاجز\s+أمني",
            r"road\s+closure|roadblock|barricade",
            r"منع\s+(المرور|التنقل)",
            r"双向封闭",
        ],
        confidence_boost=0.10,
        description="Road closure or security checkpoint blockade",
    ),

    # === MEDIUM: Tension & Disinformation ===
    ThreatRule(
        id="RULE-020",
        name_ar="شائعات تضليلية",
        name_en="Disinformation Keywords",
        category="disinfo",
        severity="medium",
        patterns=[
            r"عاجل\s+و?رسمي",
            r"شائعات?\s+(ت trận|مؤكدة|خاطئة)",
            r"خبر\s+كاذب",
            r"فيزيك",
            r"fake\s+news|disinformation|misinformation",
            r"تعمية",
        ],
        confidence_boost=0.08,
        description="Potential disinformation or rumor activity",
    ),
    ThreatRule(
        id="RULE-021",
        name_ar="تصعيد لفظي",
        name_en="Rhetorical Escalation",
        category="security",
        severity="medium",
        patterns=[
            r"تهديد\s+(واضح|مباشر|عسكري)",
            r"تحذير\s+(من\s+رد\s+عسكري)",
            r"ultimatum|threaten|escalat",
            r"إنذار\s+(أخير|من\s+رد)",
        ],
        confidence_boost=0.05,
        description="Verbal escalation or military threat rhetoric",
    ),
    ThreatRule(
        id="RULE-022",
        name_ar="أزمة إنسانية",
        name_en="Humanitarian Crisis",
        category="humanitarian",
        severity="medium",
        patterns=[
            r"أزمة\s+(إنسانية|غذائية|صحية)",
            r"نازحون?\s+(بضعة|جديد|万余)",
            r"shortage|famine|humanitarian\s+crisis",
            r"Missing\s+water|lack\s+of\s+medicine",
            r"displaced|refugee",
        ],
        confidence_boost=0.05,
        description="Humanitarian emergency or displacement event",
    ),

    # === LOW: Routine Monitoring ===
    ThreatRule(
        id="RULE-030",
        name_ar="إعلان رسمي",
        name_en="Official Statement",
        category="civilian",
        severity="low",
        patterns=[
            r"بيان\s+(رسمي|رسمي)",
            r" conferences?|statement|press\s+release",
            r"-Spokesperson| المتحدث",
        ],
        confidence_boost=0.02,
        description="Official government or organizational statement",
    ),
]


class TelescopeDetector:
    """
    Rule-based threat detection engine.
    Scans text against predefined patterns and assigns threat levels.
    """

    def __init__(self):
        self.rules = THREAT_RULES
        self._compiled_rules = self._compile_rules()

    def _compile_rules(self) -> List[Tuple[ThreatRule, List[re.Pattern]]]:
        """Pre-compile regex patterns for performance."""
        compiled = []
        for rule in self.rules:
            patterns = [
                re.compile(p, re.IGNORECASE | re.UNICODE)
                for p in rule.patterns
            ]
            compiled.append((rule, patterns))
        return compiled

    def scan_text(self, text: str) -> Dict[str, any]:
        """
        Scan text against all threat rules.
        Returns matched rules and calculated threat assessment.
        """
        if not text or len(text.strip()) < 5:
            return {"matches": [], "threat_level": "low", "confidence": 0.0}

        matches = []
        max_severity = "low"
        total_confidence_boost = 0.0

        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        for rule, patterns in self._compiled_rules:
            for pattern in patterns:
                if pattern.search(text):
                    matches.append({
                        "rule_id": rule.id,
                        "name_ar": rule.name_ar,
                        "name_en": rule.name_en,
                        "category": rule.category,
                        "severity": rule.severity,
                        "description": rule.description,
                    })
                    total_confidence_boost += rule.confidence_boost

                    if severity_order.get(rule.severity, 0) > severity_order.get(max_severity, 0):
                        max_severity = rule.severity
                    break  # One match per rule is enough

        return {
            "matches": matches,
            "threat_level": max_severity,
            "confidence": min(0.95, total_confidence_boost),
            "matched_rules_count": len(matches),
        }

    def enrich_event(self, event: OSINTEvent) -> OSINTEvent:
        """Enrich an OSINT event with Telescope detection results."""
        # Scan both Arabic and English text
        full_text = f"{event.raw_text} {event.summary_ar} {event.summary_en}"

        result = self.scan_text(full_text)

        if result["matches"]:
            # Update threat level if detection is higher
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            current_order = severity_order.get(event.threat_level, 0)
            detected_order = severity_order.get(result["threat_level"], 0)

            if detected_order > current_order:
                event.threat_level = result["threat_level"]

            # Boost confidence
            event.confidence = min(0.99, event.confidence + result["confidence"])

            # Add detection metadata
            if event.raw_entities is None:
                event.raw_entities = {}
            event.raw_entities["telescope_detections"] = result["matches"]
            event.raw_entities["telescope_confidence_boost"] = result["confidence"]

            logger.info(
                f"🔭 Telescope: {len(result['matches'])} rules matched — "
                f"[{result['threat_level'].upper()}] {event.raw_text[:60]}"
            )

        return event

    def scan_batch(self, events: List[OSINTEvent]) -> List[OSINTEvent]:
        """Scan multiple events."""
        return [self.enrich_event(e) for e in events]

    def get_rules_summary(self) -> List[Dict]:
        """Get summary of all active detection rules."""
        return [
            {
                "id": rule.id,
                "name_ar": rule.name_ar,
                "name_en": rule.name_en,
                "category": rule.category,
                "severity": rule.severity,
                "patterns_count": len(rule.patterns),
            }
            for rule in self.rules
        ]
