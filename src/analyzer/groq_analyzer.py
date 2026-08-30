"""
OSINT Syria - Groq AI Analyzer
Uses Groq Cloud API with Llama-3.1-8B for fast event analysis and classification.
"""

import json
import logging
from typing import Optional

from groq import Groq

from config.settings import config
from src.models import OSINTEvent

logger = logging.getLogger("osint.analyzer")

# === System prompt for the AI analyst ===
SYSTEM_PROMPT = """أنت محلل استخبارات سوري متخصص. مهمتك تحليل النصوص المستخرجة من قنوات تليجرام и تصنيفها.

أعطِ ردك دائماً بالشكل JSON التالي (بدون أي نص إضافي قبل أو بعد):
{
    "event_type": "نوع الحدث",
    "summary_ar": "ملخص مختصر بالعربي (جملة واحدة)",
    "summary_en": "Brief English summary (one sentence)",
    "threat_level": "critical|high|medium|low",
    "confidence": 0.85,
    "location_name": "اسم المكان كما ورد",
    "governorate": "المحافظة",
    "city": "المدينة أو البلدة",
    "key_details": ["تفاصيل مهمة 1", "تفاصيل مهمة 2"],
    "people_mentioned": ["أسماء الأشخاص المذكورين إن وجد"],
    "units_mentioned": ["القوات أو الفصائل المذكورة"]
}

تصنيف أنواع الأحداث:
- اشتباكات: مواجهات مسلحة بين أطراف
- قصف: غارات جوية أو قصف مدفعي
- إغلاق طريق: حواجز أمنية أو إغلاق طرق
- انفجار: عبوات ناسفة أو سيارات مفخخة
- تحركات عسكرية: حشود أو انتقالات قوات
- توتر: تصعيد لفظي أو تهديدات
- إعلان رسمي: بيانات حكومية أو عسكرية
- نازحين: تهجير أو نزوح
- إنساني: مساعدات أو أزمة إنسانية
- اقتصادي: أسعار أو عقوبات أو اقتصاد
- سياسي: اتفاقيات أو مفاوضات
- أمني: اختطاف أو اعتقال أو مداهمة
- غير محدد: لا ينتمي لأي فئة سابقة

تصنيف الخطورة:
- critical: هجوم نشط / قصف مباشر / خسائر بشرية م confirms
- high: اشتباكات / تحركات عسكرية كبيرة / تهديد وشيك
- medium: توتر / إغلاق طرق / أنباء غير مؤكدة
- low: أخبار عامة / أحداث过去了 / معلومات غير حساسة
"""


class GroqAnalyzer:
    """
    AI-powered event analyzer using Groq Cloud + Llama 3.1.
    Provides extremely fast inference for real-time classification.
    """

    def __init__(self):
        self.client = Groq(api_key=config.groq.api_key)
        self.model = config.groq.model

    async def analyze_event(self, event: OSINTEvent) -> OSINTEvent:
        """
        Analyze a raw OSINT event and enrich it with AI-extracted data.
        """
        if not event.raw_text or len(event.raw_text.strip()) < 10:
            logger.debug("Skipping very short message")
            event.threat_level = "low"
            event.confidence = 0.3
            return event

        try:
            analysis = self._call_groq(event.raw_text)
            if analysis:
                event.event_type = analysis.get("event_type", "غير محدد")
                event.summary_ar = analysis.get("summary_ar", "")
                event.summary_en = analysis.get("summary_en", "")
                event.threat_level = analysis.get("threat_level", "low")
                event.confidence = float(analysis.get("confidence", 0.5))
                event.location_name = analysis.get("location_name", "")
                event.governorate = analysis.get("governorate", "")
                event.city = analysis.get("city", "")
                event.raw_entities = analysis

                logger.info(
                    f"🤖 Analyzed: [{event.threat_level.upper()}] "
                    f"{event.event_type} — {event.summary_ar[:60]}"
                )
            else:
                event.threat_level = "low"
                event.confidence = 0.2

        except Exception as e:
            logger.error(f"❌ Groq analysis failed: {e}")
            event.threat_level = "low"
            event.confidence = 0.1

        return event

    def _call_groq(self, text: str) -> Optional[dict]:
        """Make synchronous Groq API call."""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"حلل هذا النص:\n\n{text}"}
                ],
                model=self.model,
                max_tokens=config.groq.max_tokens,
                temperature=config.groq.temperature,
                response_format={"type": "json_object"},
            )

            response_text = chat_completion.choices[0].message.content.strip()
            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Groq response: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return None

    async def analyze_batch(self, events: list) -> list:
        """Analyze multiple events sequentially."""
        results = []
        for event in events:
            analyzed = await self.analyze_event(event)
            results.append(analyzed)
        return results
