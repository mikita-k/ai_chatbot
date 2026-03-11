# Parking Space Reservation System

An AI-powered parking reservation system built in 4 stages using RAG, LangChain, and LangGraph.

## 🚀 Quick Start (30 seconds)

```bash
# Install
pip install -r requirements.txt

# Run complete system
python scripts/stage4/run_orchestrator.py

# Try it:
You: What is the parking cost?
You: reserve John Smith ABC123 from 5 march to 12 march 2026
You: check status REQ-...
You: exit
```

---

## 📚 Implementation Overview

### Stage 1: RAG Chatbot ✅
- **What**: Semantic search for parking info
- **How**: FAISS vectors + sentence-transformers embeddings
- **Features**: 
  - Static (FAISS) + dynamic (SQLite) data
  - Guard rails (email/number redaction)
  - Optional OpenAI LLM
  - **Response quality evaluation** with `EVAL_VERBOSE` parameter
- **Tests**: ✅
- **Details**: See [docs/STAGE1.md](docs/STAGE1.md)

**Response Quality Metrics (controlled by `EVAL_VERBOSE` in `.env`):**
- `EVAL_VERBOSE=false` (default): Basic latency metrics only
- `EVAL_VERBOSE=true`: Detailed LLM Judge evaluation (relevance, faithfulness, completeness, conciseness)

Example with `EVAL_VERBOSE=true`:
```
⏱️ Latency: retrieval=0.027s | docs=3 | similarity=0.85
🎯 Faithfulness: 0.88/1.00 (hallucinations: none)
📋 Relevance: 0.92 | Completeness: 0.85
✅ Overall: 0.88/1.00 - Very Good ⭐⭐
```

### Stage 2: Admin Approval ✅
- **What**: Human-in-the-loop approval workflow
- **How**: LangChain AdminAgent with tools
- **Features**:
  - Simulated approval (default, no config needed)
  - Real Telegram notifications (optional)
  - SQLite request tracking
- **Tests**: ✅
- **Details**: See [docs/STAGE2.md](docs/STAGE2.md)

### Stage 3: Persistent Storage ✅
- **What**: Save approved reservations
- **How**: SQLite database with simple API
- **Features**:
  - ReservationStorage class
  - Integration with Stage 2
  - Zero external dependencies
- **Tests**: ✅
- **Details**: See [docs/STAGE3.md](docs/STAGE3.md)

### Stage 4: LangGraph Orchestration ✅
- **What**: Complete system integration
- **How**: LangGraph StateGraph with intelligent routing
- **Features**:
  - Intelligent request routing
  - Request history + status tracking
  - End-to-end workflow
- **Tests**: ✅
- **Details**: See [docs/STAGE4.md](docs/STAGE4.md)

---

## 🏃 Running Individual Stages

**For development or testing specific stages:**

```bash
# Stage 1 only
python scripts/stage1/run_chatbot.py

# Stage 1 + 2
python scripts/stage2/run_stage2.py

# All stages (recommended)
python scripts/stage4/run_orchestrator.py
```

For all available scripts, see [docs/SCRIPTS.md](docs/SCRIPTS.md)

---

## 🎯 Response Quality Evaluation

Response evaluation system with LLM judge. See [EVAL_README.md](EVAL_README.md) for details.

```bash
pytest tests/test_response_evaluation.py -v  # 22 tests ✅
python scripts/stage1/example_evaluation.py   # 5 examples
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific stage tests
pytest tests/test_stage1.py -v
pytest tests/test_stage2.py -v
pytest tests/test_stage3.py -v
pytest tests/test_stage4.py -v
```

**Status**: All tests passing ✅

---

## ⚙️ Configuration (Optional)

Everything works out of the box. Optional features can be enabled via `.env` file:

```bash
cp .env.example .env
# Edit .env and set:
# - USE_LLM=true to enable OpenAI LLM
# - USE_TELEGRAM=true to enable Telegram notifications
```

See [.env.example](.env.example) for all available options.

---

## 📁 Project Structure

```
hw/
├── src/
│   ├── stage1/        # RAG chatbot
│   ├── stage2/        # Admin agent
│   ├── stage3/        # Storage
│   └── stage4/        # LangGraph orchestration
├── scripts/
│   ├── stage1/        # RAG debugging and utilities
│   ├── stage2/        # Chatbot and Telegram bot
│   ├── stage3/        # Database utilities
│   └── stage4/        # Main orchestrator
├── tests/             # Unit tests for all stages
├── data/
│   ├── static_docs.txt   # Parking info
│   ├── reservations.db   # Approved bookings
│   └── dynamic/
│       ├── parking.db    # Availability
│       └── approvals.db  # Pending requests
└── docs/
    ├── STAGE1.md       # RAG details
    ├── STAGE2.md       # Admin approval details
    ├── STAGE3.md       # Storage details
    ├── STAGE4.md       # LangGraph details
    └── SCRIPTS.md      # All available scripts
```

For detailed script information, see [docs/SCRIPTS.md](docs/SCRIPTS.md)

---

## 🔍 System Flow

```
User Input
    ↓
[STAGE 4] Classify request type (info/reservation/status)
    ↓
    ├→ Info query ──→ [STAGE 1] RAG search ────────────────────────────────┐
    │                                                                      ├→ Response
    ├→ Reservation ──→ [STAGE 2] Admin approval ──→ [STAGE 3] Save to DB ──┤
    │                                                                      ├→ Response
    └→ Status check ──→ History lookup ────────────────────────────────────┘
```

---

## 📖 Full Documentation

- **[IMPLEMENTATION.md](docs/IMPLEMENTATION.md)** - Architecture guide
- **[STAGE1.md](docs/STAGE1.md)** - RAG Chatbot implementation
- **[STAGE2.md](docs/STAGE2.md)** - Admin approval workflow
- **[STAGE3.md](docs/STAGE3.md)** - Storage system
- **[STAGE4.md](docs/STAGE4.md)** - LangGraph orchestration
- **[SCRIPTS.md](docs/SCRIPTS.md)** - Available scripts and commands

---

## ✨ Key Features

✅ **RAG-based** - Semantic search using FAISS  
✅ **LangChain integration** - Professional admin agent  
✅ **LangGraph orchestration** - Clear state management  
✅ **SQLite storage** - Persistent data  
✅ **Guard rails** - Sensitive data protection  
✅ **Zero config** - Works without setup (Telegram/LLM optional)  
✅ **Multi-language** - English + Russian support  
✅ **60 tests** - Comprehensive test coverage  

---

## 🎯 Status

| Component | Status |
|-----------|--------|
| Stage 1: RAG | ✅ Complete |
| Stage 2: Admin | ✅ Complete |
| Stage 3: Storage | ✅ Complete |
| Stage 4: Orchestration | ✅ Complete |
| **Tests** | **✅ All Passing** |

---

## 📝 License

Built as learning project for LLM systems

---

## 🔗 Quick Links

- **Run everything**: `python scripts/stage4/run_orchestrator.py`
- **Run tests**: `pytest tests/ -v`

