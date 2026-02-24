#!/usr/bin/env python
"""
Stage 2 LangChain - Telegram Admin Bot

Run in separate terminal:
    python scripts/stage2/run_telegram_bot.py

Requires environment variables:
    TELEGRAM_BOT_TOKEN - Bot token from @BotFather
    TELEGRAM_ADMIN_CHAT_ID - Your chat ID with the bot

The bot will listen for admin commands and process reservations.
"""

import sys
import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.stage2.telegram_service import run_telegram_bot

if __name__ == "__main__":
    run_telegram_bot()

