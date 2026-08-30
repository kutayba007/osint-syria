# 🇸🇾 دليل الإعداد السريع — OSINT Syria

## الخطوة 1: الحصول على مفاتيح Telegram API

### 1.1 — إنشاء تطبيق Telegram
1. افتح متصفحك وروح لـ **https://my.telegram.org**
2. سجّل دخول برقم تليجرام الخاص فيك
3. اضغط **API development tools**
4. املأ النموذج:
   - **App title**: `OSINT Syria`
   - **Short name**: `osintsyria`
   - اضغط **Create application**
5. ستحصل على:
   - **App api_id**: رقم (مثلاً `12345678`)
   - **App api_hash**: نص (مثلاً `abcdef1234567890abcdef`)

### 1.2 — إنشاء بوت تنبيهات (اختياري لكن مفيد)
1. افتح تليجرام وروح لـ **@BotFather**
2. أرسل `/newbot`
3. اختر اسم: `OSINT Syria Alert Bot`
4. اختر username: `osint_syria_bot`
5. ستحصل على **توكن البوت** (مثلاً `123456:ABC-DEF...`)

### 1.3 — الحصول على Chat ID
1. افتح البوت اللي أنشأته
2. أرسل أي رسالة للبوت
3. افتح هذا الرابط في المتصفح:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
4. ابحث عن `"chat":{"id":` — هذا هو **Chat ID** الخاص فيك

---

## الخطوة 2: إنشاء ملف .env

```bash
cd osint-syria
cp .env.example .env
```

ثم افتح الملف وعدّل:

```env
TG_API_ID=12345678
TG_API_HASH=abcdef1234567890abcdef
TG_PHONE_NUMBER=+963XXXXXXXXX

TG_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TG_ALERT_CHAT_ID=123456789
```

---

## الخطوة 3: اختبار الاتصال

```bash
cd osint-syria
python3 scripts/test_telegram.py
```

ستظهر لك رسالة نجاح ✅ إذا كل شيء يعمل.

---

## الخطوة 4: تشغيل النظام

```bash
# Terminal 1: تشغيل المحرك الرئيسي
python3 -m src.pipeline

# Terminal 2: تشغيل لوحة التحكم
streamlit run dashboard/app.py
```

---

## ❓ مشاكل شائعة

### "Phone code required"
- سجل دخول للمرة الأولى يحتاج كود تحقق يصلك بالتليجرام

### "FloodWaitError"
- تليجرام حذرنا ننتظر — انتظر المدة المطلوبة ثم أعد المحاولة

### "Channel private"
- القناة خاصة وما تقدر تراقبها — غيّرها لقناة عامة

---

## 📱 قنوات تليجرام سورية مجانية للمراقبة

| القناة | الرابط | الوصف |
|--------|--------|-------|
| Syrian News | @syrianews | أخبار سوريا العامة |
| Syria Stories | @syriastories | قصص وتوثيق |
| SONA News | @SONA_NEWS | أخبار محلية |
| Orient News | @OrientNews | نشرات إخبارية |
| Syria Direct | @SyrianDirect | تحليلات |
| Smart News | @SmartNewsAgency | أخبار ذكية |
| Halab Today | @HalabToday | أخبار حلب |
| Deir ez-Zor | @DeirEzzor24 | أخبار دير الزور |

**ملاحظة**: أضف القنوات اللي تبيها في `config/settings.py`
