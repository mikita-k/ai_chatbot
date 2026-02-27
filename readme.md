# LLM Chatbot for Parking Space Reservation

A multi-stage project implementing a complete intelligent chatbot system for parking space reservations using RAG (Retrieval-Augmented Generation), human-in-the-loop approval, and persistent storage.

## 🎯 Project Status

| Stage | Status | Features |
|-------|--------|----------|
| **Stage 1** | ✅ COMPLETE | RAG Chatbot, FAISS, Dynamic Data, LLM Integration, 5 Tests |
| **Stage 2** | ✅ COMPLETE | Admin Approval, Telegram Integration, 16 Tests |
| **Stage 3** | ✅ COMPLETE | MCP Server, Storage (CSV/SQLite), Validation, API Server |
| **Stage 4** | ✅ COMPLETE | LangGraph Orchestration, 34 Tests, Full Integration |

## Quick Start

See [IMPLEMENTATION GUIDE](docs/IMPLEMENTATION.md) for detailed setup and usage instructions.

### Stage 1: RAG Chatbot with FAISS

**Basic usage (without LLM - uses pattern matching):**
```powershell
python -m src.stage1.rag_chatbot chat
```
Interactive chatbot that answers parking-related questions using RAG with FAISS vector database and sentence-transformers embeddings.

**With OpenAI LLM enabled:**
```powershell
python -m src.stage1.rag_chatbot chat --use-llm
# Or set USE_LLM=true in .env + OPENAI_API_KEY
```

**Check loaded documents:**
```powershell
python scripts/stage1/check_indices.py
```
Display all documents loaded in the DocumentStore.

**Debug retrieval:**
```powershell
python scripts/stage1/debug_retrieval.py
```
Test retrieval functionality with sample queries and similarity scores.

**Features:**
- Vector database (FAISS) with sentence-transformers embeddings
- Fast document retrieval with configurable top-k results
- Optional OpenAI LLM for natural language generation
- Dynamic document updates support
- Low latency (~10ms per query)

For detailed documentation, see [docs/STAGE1.md](docs/STAGE1.md)

### Stage 2: Admin Approval with Telegram Integration

**Default (Simulated Admin - No Setup Required):**
```powershell
python scripts/stage2/run_stage2.py
```
Interactive chatbot with auto-approval after 1 second. No external dependencies needed.

**Setup Telegram (Optional - For Real Admin Notifications):**
```powershell
# 1. Create bot via @BotFather on Telegram, get TOKEN and CHAT_ID
# 2. Create .env file with:
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
USE_LLM=true  # Optional: enable OpenAI LLM
```

**Run with Telegram (2 terminals):**
```powershell
# Terminal 1: Chatbot
python scripts/stage2/run_stage2.py

# Terminal 2: Admin bot (waits for Telegram messages)
python scripts/stage2/run_telegram_bot.py
```

**With OpenAI LLM enabled:**
```powershell
python scripts/stage2/run_stage2.py --use-llm
# Or set USE_LLM=true in .env + OPENAI_API_KEY
```

For detailed documentation, see [docs/STAGE2.md](docs/STAGE2.md) and [scripts/README.md](scripts/README.md)

### Stage 3: Save Approved Reservations to Database

**Simple & minimal**: Just saves admin-approved reservations to SQLite database.

**Start test:**
```powershell
python scripts/stage3/test_integration.py
```

**Use in code:**
```python
from src.stage3.integrate import process_approved_reservation

# After admin approval in Stage 2
process_approved_reservation({
    "reservation_id": "REQ-20260225100000-001",
    "user_name": "John Doe",
    "car_number": "ABC1234",
    "start_date": "2026-03-01",
    "end_date": "2026-03-07",
    "approval_time": "2026-02-25T10:00:00",
})
```

**Features:**
- ✅ SQLite storage (data/reservations.db)
- ✅ Simple 3-function API
- ✅ Zero external dependencies (sqlite3 is built-in)
- ✅ Ready for Stage 4

For detailed info, see [docs/STAGE3_SIMPLE.md](docs/STAGE3.md)

### Stage 4: LangGraph Orchestration

**Complete integration of all components into unified workflow!**

```powershell
# Basic usage (simulated admin approval)
python scripts/stage4/run_orchestrator.py

# With OpenAI LLM enabled
python scripts/stage4/run_orchestrator.py --use-llm

# With Telegram notifications  
python scripts/stage4/run_orchestrator.py --use-telegram
```

**What's Included:**
- Complete LangGraph state machine orchestrating all stages
- Automated routing between info requests and reservations
- End-to-end workflow: User → RAG → Admin → Storage → Response
- 34 comprehensive tests covering all scenarios
- Interactive chatbot interface

**Interactive Commands:**
```
User: help          - Show available commands
User: info          - Ask about parking information
User: reserve       - Make a parking reservation
User: status        - Check reservation status
User: summary       - Show all processed requests
User: debug         - Enable debug output
User: exit          - Exit the chatbot
```

**Features:**
- ✅ Intelligent request routing (info vs. reservation)
- ✅ RAG-based information retrieval (Stage 1)
- ✅ Human-in-the-loop approval workflow (Stage 2)
- ✅ Automatic data persistence (Stage 3)
- ✅ Full error handling and recovery
- ✅ Request history and status tracking
- ✅ Performance metrics

For detailed documentation, see [docs/STAGE4.md](docs/STAGE4.md)
