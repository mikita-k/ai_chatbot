#!/usr/bin/env python
"""
Stage 1: RAG Chatbot with FAISS (Information Retrieval Only)

This stage answers INFORMATIONAL questions about parking using:
- FAISS vector database for fast document retrieval
- Sentence-transformers for embeddings
- Optional OpenAI LLM for enhanced responses

**NOTE**: This stage is for QUESTIONS ONLY, not for reservations!
For making reservations, use Stage 2:
  python scripts/stage2/run_stage2.py

Configuration:
- USE_LLM: Enable/disable OpenAI LLM (from .env)
- OPENAI_API_KEY: OpenAI API key (from .env)

Example questions:
  - What is the parking cost?
  - When are you open?
  - How do I make a reservation?

Do NOT use for:
  - Making reservations (use Stage 2)
  - Checking reservation status (use Stage 2 or Stage 4)
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.stage1.rag_chatbot import DocumentStore, SimpleRAGChatbot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main entry point for Stage 1 RAG Chatbot."""

    # Get configuration from environment
    use_llm = os.getenv("USE_LLM", "false").lower() == "true"

    print("\n" + "="*80)
    print("🤖 STAGE 1: RAG Chatbot with FAISS")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  LLM Enabled: {'✅' if use_llm else '❌'}")
    if use_llm and not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  Warning: USE_LLM=true but OPENAI_API_KEY not set")
    print()

    # Initialize components
    print("Initializing RAG Chatbot...")
    try:
        # Load documents from file
        doc_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "static_docs.txt")
        doc_path = os.path.abspath(doc_path)

        if os.path.exists(doc_path):
            doc_store = DocumentStore.from_file(doc_path)
        else:
            print(f"⚠️  Warning: Document file not found at {doc_path}")
            # Create store with sample data
            doc_store = DocumentStore(docs=[
                "Parking is available 24/7",
                "Price: $10 per day",
                "Reservation: Call 555-0123",
                "Accepts: Cash, Card, Digital",
                "Rules: No overnight camping"
            ])

        rag_chatbot = SimpleRAGChatbot(doc_store, use_llm=use_llm)
        print(f"✅ Loaded {len(doc_store.docs)} documents")
    except Exception as e:
        print(f"❌ Error initializing RAG Chatbot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print()

    # Interactive chatbot
    print("-"*80)
    print("Interactive Mode - Type 'exit' to quit, 'help' for commands")
    print("-"*80 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            if user_input.lower() == "help":
                print("\nAvailable commands:")
                print("  Type any question about parking")
                print("  'exit'  - Exit the chatbot")
                print("  'help'  - Show this message\n")
                continue

            # Check if user is trying to make a reservation
            if user_input.lower().startswith("reserve"):
                print("\n❌ Reservations are handled in Stage 2, not here.")
                print("   To make a reservation, run: python scripts/stage2/run_stage2.py\n")
                continue

            # Get RAG response
            response = rag_chatbot.answer(user_input)
            print(f"\nBot: {response}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()

