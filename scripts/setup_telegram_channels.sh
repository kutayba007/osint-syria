#!/bin/bash
# ============================================
# 🇸🇾 OSINT Syria — Quick Setup Script
# ============================================
# Run this from the project root directory
# Usage: bash scripts/setup_telegram_channels.sh

echo "🇸🇾 OSINT Syria — Setup Guide"
echo "=============================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "📋 SETUP CHECKLIST"
echo "========================================="
echo ""
echo "1️⃣  Telegram API:"
echo "   → Go to https://my.telegram.org"
echo "   → Create an application"
echo "   → Copy API_ID and API_HASH"
echo ""
echo "2️⃣  Telegram Bot (for alerts):"
echo "   → Open Telegram, search @BotFather"
echo "   → Create a new bot with /newbot"
echo "   → Copy the bot token"
echo "   → Send a message to your bot"
echo "   → Visit https://api.telegram.org/bot<TOKEN>/getUpdates"
echo "   → Find your chat_id"
echo ""
echo "3️⃣  Groq API (FREE):"
echo "   → Go to https://console.groq.com"
echo "   → Sign up / Login"
echo "   → Create an API key"
echo ""
echo "4️⃣  Supabase (FREE):"
echo "   → Go to https://supabase.com"
echo "   → Create a new project"
echo "   → Copy the URL and anon key"
echo "   → Go to SQL Editor"
echo "   → Paste & run the content of scripts/setup_supabase.sql"
echo ""
echo "5️⃣  Google Drive (optional):"
echo "   → Go to https://console.cloud.google.com"
echo "   → Enable Google Drive API"
echo "   → Create a service account"
echo ""
echo "========================================="
echo ""
echo "📝 Copy .env.example to .env and fill in your credentials:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "🚀 Start the pipeline:"
echo "   python -m src.pipeline"
echo ""
echo "📊 Start the dashboard:"
echo "   streamlit run dashboard/app.py"
echo ""
echo "========================================="
echo "🇸🇾 OSINT Syria — Early Warning System"
echo "========================================="
