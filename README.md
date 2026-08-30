# 🇸🇾 OSINT Syria — منصة استخبارات مصادر مفتوحة وإنذار مبكر

> **Open Source Intelligence & Early Warning System for Syria**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Cost](https://img.shields.io/badge/Cost-%240-brightgreen)](#)
[![Status](https://img.shields.io/badge/Status-Active-red)](#)

---

## 🎯 ما هو هذا المشروع؟

منصة استخبارات مصادر مفتوحة تقوم بـ:

1. **📡 رصد لحظي** — مراقبة قنوات تليجرام الإخبارية السورية
2. **🤖 تحليل ذكي** — تصنيف الأحداث وتصنيف خطورتها بالذكاء الاصطناعي
3. **🗺️ خريطة تفاعلية** — إسقاط الأحداث على خريطة حية مضيئة
4. **🚨 إنذار فوري** — إرسال تنبيهات عاجلة للحوادث عالية الخطورة
5. **💾 أرشفة سحابية** — تخزين البيانات والوسائط في السحابة

**الميزانية: $0 بالكامل — 100% مجاني ومستدام** 🆓

---

## 🏗️ البنية التقنية

```
┌─────────────────────────────────────────────────────┐
│              🇸🇾 OSINT Syria Pipeline               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📡 Telethon ──→ 🤖 Groq API ──→ 📍 Geopy         │
│  (Scrape)        (Analyze)       (Geocode)          │
│       │              │               │               │
│       ▼              ▼               ▼               │
│  ┌──────────────────────────────────────────┐       │
│  │         💾 Supabase (PostgreSQL)          │       │
│  └──────────────────────────────────────────┘       │
│       │              │               │               │
│       ▼              ▼               ▼               │
│  🚨 Telegram    📊 Streamlit    📤 Google Drive     │
│  (Alerts)       (Dashboard)     (Archive)            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 الدليل السريع للتشغيل

### الخطوة 1: استنساخ المشروع

```bash
git clone https://github.com/your-repo/osint-syria.git
cd osint-syria
```

### الخطوة 2: تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### الخطوة 3: إعداد المفاتيح (مجانية بالكامل)

| الخدمة | الرابط | الخطوات |
|---------|--------|---------|
| **Telegram API** | [my.telegram.org](https://my.telegram.org) | إنشاء تطبيق → نسخ API_ID و API_HASH |
| **Telegram Bot** | @BotFather في تليجرام | إنشاء بوت → نسخ التوكن |
| **Groq API** | [console.groq.com](https://console.groq.com) | تسجيل مجاني → إنشاء مفتاح |
| **Supabase** | [supabase.com](https://supabase.com) | إنشاء مشروع → نسخ URL و Key |

### الخطوة 4: إعداد متغيرات البيئة

```bash
cp .env.example .env
nano .env  # أو أي محرر آخر
```

املأ المفاتيح في ملف `.env`

### الخطوة 5: إعداد قاعدة البيانات

1. افتح Supabase Dashboard
2. اذهب إلى SQL Editor
3. الصق محتوى `scripts/setup_supabase.sql`
4. اضغط **Run**

### الخطوة 6: تشغيل النظام

```bash
# تشغيل محرك الرصد والتحليل
python -m src.pipeline

# تشغيل لوحة التحكم (في نافذة أخرى)
streamlit run dashboard/app.py
```

---

## 📡 قنوات المراقبة

القنوات الافتراضية (يمكن تعديلها في `config/settings.py`):

| القناة | الوصف |
|--------|-------|
| @syrianews | أخبار سوريا |
| @syriastories | قصص سوريا |
| @SyrianDirect | نشرات مباشرة |
| @syria_sitrep | تقارير الموقف |
| @SONA_NEWS | أخبار محلي |

### إضافة قنوات جديدة

.edit في `config/settings.py`:

```python
monitored_channels: List[str] = [
    "https://t.me/channel_name",
    # أضف المزيد...
]
```

---

## 📊 لوحة التحكم

اللوحة تقدم:

- **🗺️ خريطة تكتيكية حية** — مضيئة حسب مستوى الخطورة
- **📈 إحصائيات لحظية** — توزيع الأحداث حسب النوع والمحافظة
- **⏱ خط زمني** — متابعة تطور الأحداث
- **📋 سيل الأحداث** — آخر الأحداث مع التفاصيل

```bash
streamlit run dashboard/app.py
```

---

## 🚨 نظام الإنذار

عند رصد حدث عالي الخطورة، يُرسل تنبيه فوري:

```
🚨 إنذار عاجل — حدث عالي الخطورة 🚨

🔴 نوع الحدث: اشتباكات
📅 التاريخ: 2024-01-15 14:30 UTC
📢 المصدر: @syrianews

📝 الملخص:
اشتباكات عنيفة بين فصيلين في ريف حلب الشمالي

📍 الموقع: عفرين (36.3789, 36.8567)
🏛 المحافظة: حلب
📊 مستوى الخطورة: CRITICAL
```

---

## 🌐 النشر السحابي (مجاني 24/7)

### الخيار 1: Render (الأسهل)

1. ادفع الكود إلى GitHub
2. اذهب إلى [render.com](https://render.com)
3. أنشئ **Background Worker** جديد
4. اربط مستودع GitHub
5. أضف متغيرات البيئة
6. سيقوم Render بنشره تلقائياً

### الخيار 2: Hugging Face Spaces

1. أنشئ Space جديد على [huggingface.co](https://huggingface.co)
2. اختر **Docker** كأداة
3. ارفع الملفات
4. أضف متغيرات البيئة في Settings

### لوحة التحكم على Streamlit Cloud

1. اذهب إلى [share.streamlit.io](https://share.streamlit.io)
2. اربط مستودع GitHub
3. حدد `dashboard/app.py`
4. مجاني دائماً! ✅

---

## 📁 هيكل المشروع

```
osint-syria/
├── 📄 README.md              # هذا الملف
├── 📄 requirements.txt       # المتطلبات
├── 📄 Dockerfile             # للنشر السحابي
├── 📄 render.yaml            # إعدادات Render
├── 📄 Procfile               # للنشر على Heroku/Railway
├── 📄 .env.example           # قالب متغيرات البيئة
│
├── 📂 config/
│   ├── __init__.py
│   └── settings.py           # الإعدادات المركزية
│
├── 📂 src/
│   ├── __init__.py
│   ├── models.py             # نماذج البيانات (Pydantic)
│   ├── pipeline.py           # المحرك الرئيسي المتسلسل
│   │
│   ├── 📂 scraper/
│   │   ├── __init__.py
│   │   └── telegram_scraper.py  # رصد تليجرام
│   │
│   ├── 📂 analyzer/
│   │   ├── __init__.py
│   │   └── groq_analyzer.py     # تحليل الذكاء الاصطناعي
│   │
│   ├── 📂 geocoder/
│   │   ├── __init__.py
│   │   └── syria_geocoder.py    # تحديد المواقع
│   │
│   ├── 📂 database/
│   │   ├── __init__.py
│   │   └── supabase_client.py   # قاعدة البيانات
│   │
│   ├── 📂 alerts/
│   │   ├── __init__.py
│   │   └── telegram_alerts.py   # نظام الإنذار
│   │
│   └── 📂 media/
│       ├── __init__.py
│       └── drive_archiver.py    # أرشفة Google Drive
│
├── 📂 dashboard/
│   └── app.py                 # لوحة التحكم (Streamlit)
│
├── 📂 scripts/
│   ├── setup_supabase.sql     # إعداد قاعدة البيانات
│   └── setup_telegram_channels.sh
│
└── 📂 tests/
    └── test_pipeline.py       # اختبارات
```

---

## 💰 كلفة التشغيل

| المكون | التكلفة | الملاحظات |
|--------|---------|-----------|
| Telethon (Scraping) | **$0** | مجاني تماماً |
| Groq API | **$0** | باقة مجانية دائمة |
| Nominatim | **$0** | مجاني (1 طلب/ثانية) |
| Supabase | **$0** | 500MB + 50K مستخدم شهرياً |
| Google Drive | **$0** | 5TB مساحة |
| Render (Pipeline) | **$0** | باقة مجانية |
| Streamlit Cloud | **$0** | مجاني دائماً |
| **الإجمالي** | **$0** | ✅ |

---

## 🔧 التخصيص

### تعديل قنوات المراقبة

في `config/settings.py`:

```python
monitored_channels = [
    "https://t.me/your_channel",
]
```

### تعديل مناطق التتبع الجغرافي

في `src/geocoder/syria_geocoder.py`:

```python
SYRIA_COORDS["اسم_المكان"] = (خط_العرض, خط_الطول)
```

### تعديل أ prompts الذكاء الاصطناعي

في `src/analyzer/groq_analyzer.py` — عدّل `SYSTEM_PROMPT`

---

## 🛡️ ملاحظات قانونية وأخلاقية

- هذا المشروع يراقب **قنوات تليجرام العامة** فقط
- لا يجمع بيانات شخصية
- الهدف هو **المراقبة والإنذار المبكر** لتحسين الوعي بالأحداث
- يُنصح بالالتزام بقوانين الخصوصية في بلدك

---

## 📝 ترخيص

MIT License — يمكنك استخدامه وتعديله بحرية

---

<p align="center">
🇸🇾 <strong>OSINT Syria</strong> — Early Warning System<br/>
Built with ❤️ for awareness and safety
</p>
