#!/usr/bin/env python
"""
Stage 2 LangChain Chatbot - Interactive CLI

Run this in one terminal:
    python scripts/stage2/run_stage2.py

In separate terminal run Telegram bot:
    python scripts/stage2/run_telegram_bot.py

Environment variables (optional):
    TELEGRAM_BOT_TOKEN - Bot token from @BotFather
    TELEGRAM_ADMIN_CHAT_ID - Chat ID where admin receives notifications
    USE_LLM - Set to 'true', '1', or 'yes' to enable OpenAI LLM
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.stage1.rag_chatbot import DocumentStore
from src.stage2.admin_agent import create_admin_agent
from src.stage2.chatbot_with_approval import Stage2Chatbot


def main(use_llm: bool = False, use_telegram: Optional[bool] = None):
    print("\n" + "="*70)
    print("🎯 STAGE 2: Admin Approval with Telegram Integration")
    print("="*70)

    # If not explicitly set, read from environment
    if use_telegram is None:
        use_telegram = os.getenv("USE_TELEGRAM", "false").lower() in ("true", "1", "yes")

    # Auto-detect Telegram if enabled
    if use_telegram and not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("⚠️  Warning: USE_TELEGRAM=true but TELEGRAM_BOT_TOKEN not set")
        use_telegram = False

    print(f"\n⚙️  Configuration:")
    print(f"   LLM Enabled: {'✅' if use_llm else '❌'}")
    print(f"   Telegram: {'✅' if use_telegram else '❌ (Simulated Admin)'}")

    if use_telegram:
        print("\nℹ️  Telegram mode: Run 'python scripts/stage2/run_telegram_bot.py' in another terminal")
    else:
        print("\n✅ Simulated mode: Auto-approval after 1 second (no Telegram needed)")

    # Initialize RAG store
    print("\n1. Initializing RAG Store (Stage 1)...")
    try:
        rag_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "static_docs.txt")
        rag_path = os.path.abspath(rag_path)
        store = DocumentStore.from_file(rag_path)
        print("   ✓ RAG Store loaded")
    except Exception as e:
        print(f"   ✗ Error loading RAG store: {e}")
        sys.exit(1)

    # Initialize admin agent
    print("2. Initializing LangChain Admin Agent (Stage 2)...")
    try:
        admin_agent = create_admin_agent(use_telegram=use_telegram)
        print("   ✓ Admin Agent initialized")
    except ValueError as e:
        print(f"   ✗ Error: {e}")
        print("   ℹ️  Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID to use Telegram")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ Error: {e}")
        sys.exit(1)

    # Create integrated chatbot
    print("3. Creating integrated chatbot...")
    try:
        chatbot = Stage2Chatbot(store, admin_agent, use_llm=use_llm)
        print("   ✓ Chatbot ready")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        sys.exit(1)

    # Show mode info
    print("\n" + "-"*70)
    if use_llm:
        print("LLM Mode: ✅ ENABLED (using OpenAI)")
    else:
        print("LLM Mode: ❌ DISABLED (using keyword matching)")

    # Run interactive chat
    try:
        chatbot.interactive_chat(use_llm=use_llm)
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 2 LangChain Chatbot")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use OpenAI LLM for responses (requires OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Force use of Telegram channel"
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Force use of simulated channel"
    )

    args = parser.parse_args()

    use_llm = args.use_llm or os.getenv("USE_LLM", "").lower() in ("true", "1", "yes")
    use_telegram = None
    if args.telegram:
        use_telegram = True
    elif args.no_telegram:
        use_telegram = False
    else:
        # Read from environment if not explicitly set via flags
        use_telegram = os.getenv("USE_TELEGRAM", "false").lower() in ("true", "1", "yes")

    main(use_llm=use_llm, use_telegram=use_telegram)

