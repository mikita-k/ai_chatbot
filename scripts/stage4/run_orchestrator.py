#!/usr/bin/env python
"""
Stage 4: Complete LangGraph Orchestration

Main entry point for the complete system combining:
- RAG chatbot (Stage 1)
- Admin approval (Stage 2)
- Data storage (Stage 3)

Configuration (from .env):
- USE_LLM: Enable/disable OpenAI LLM
- USE_TELEGRAM: Enable/disable Telegram notifications
- OPENAI_API_KEY: OpenAI API key (required if USE_LLM=true)
- TELEGRAM_BOT_TOKEN: Telegram bot token (required if USE_TELEGRAM=true)

Usage:
    python scripts/stage4/run_orchestrator.py
"""

import sys
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage4.orchestrator import create_orchestrator


def main():
    """Main entry point for the orchestrator."""

    # Get configuration from environment
    use_llm = os.getenv("USE_LLM", "false").lower() in ("true", "1", "yes")
    use_telegram = os.getenv("USE_TELEGRAM", "false").lower() in ("true", "1", "yes")

    # Validate configuration
    if use_llm and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: USE_LLM=true but OPENAI_API_KEY not set")
        use_llm = False

    if use_telegram and not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("⚠️  Warning: USE_TELEGRAM=true but TELEGRAM_BOT_TOKEN not set")
        use_telegram = False

    # Create orchestrator
    print("\n" + "="*80)
    print("🚀 STAGE 4: LangGraph Orchestration")
    print("="*80)
    print(f"\n⚙️  Configuration:")
    print(f"   LLM Enabled: {'✅' if use_llm else '❌'}")
    print(f"   Telegram: {'✅' if use_telegram else '❌ (Simulated Admin)'}")
    print()
    orchestrator = create_orchestrator(
        use_llm=use_llm,
        use_telegram=use_telegram,
        verbose=True,
    )

    # Run interactive mode
    orchestrator.interactive_mode()


if __name__ == "__main__":
    main()

