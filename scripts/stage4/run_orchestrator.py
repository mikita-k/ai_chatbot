#!/usr/bin/env python
"""
Stage 4: Run Orchestration

Main entry point for the complete LangGraph orchestration system.
Combines all stages (RAG, Admin Approval, Storage) into a unified workflow.

Usage:
    python scripts/stage4/run_orchestrator.py
    python scripts/stage4/run_orchestrator.py --use-llm
    python scripts/stage4/run_orchestrator.py --use-telegram
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage4.orchestrator import create_orchestrator


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(
        description="Stage 4: LangGraph Orchestration for Parking Reservation System"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable OpenAI LLM for better responses (requires OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--use-telegram",
        action="store_true",
        help="Enable Telegram notifications for admin (requires TELEGRAM_BOT_TOKEN)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print detailed workflow information"
    )

    args = parser.parse_args()

    # Check environment
    if args.use_llm:
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Warning: OPENAI_API_KEY not set, LLM disabled")
            args.use_llm = False

    if args.use_telegram:
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            print("⚠️  Warning: TELEGRAM_BOT_TOKEN not set, using simulated admin")
            args.use_telegram = False

    # Create orchestrator
    print("\n" + "="*80)
    print("🚀 INITIALIZING STAGE 4: LANGGRAPH ORCHESTRATION")
    print("="*80)
    print(f"\n⚙️  Configuration:")
    print(f"   LLM Enabled: {'✅' if args.use_llm else '❌'}")
    print(f"   Telegram: {'✅' if args.use_telegram else '❌ (Simulated Admin)'}")
    print(f"   Verbose: {'✅' if args.verbose else '❌'}")
    print()

    orchestrator = create_orchestrator(
        use_llm=args.use_llm,
        use_telegram=args.use_telegram,
        verbose=args.verbose,
    )

    # Run interactive mode
    orchestrator.interactive_mode()


if __name__ == "__main__":
    main()

