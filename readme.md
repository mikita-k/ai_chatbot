# LLM Chatbot for Parking Space Reservation

A complete AI-powered system for intelligent parking space reservation management using RAG (Retrieval-Augmented Generation), human-in-the-loop approval workflows, and persistent storage.

## 🏗️ Architecture Overview

The system is built in **4 integrated stages**, each adding capabilities:

```
┌─────────────────────────────────────────────────────────────┐
│ User Interface (Interactive Chatbot)                         │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│ Stage 4: LangGraph Orchestration (Complete Workflow)        │
│ - Routes requests intelligently                              │
│ - Manages end-to-end processes                               │
│ - Tracks request history                                     │
└────┬──────────────────────┬──────────────┬──────────────────┘
     │                      │              │
┌────▼──────────┐  ┌────────▼──────┐  ┌──▼─────────────┐
│ Stage 1: RAG  │  │ Stage 2:      │  │ Stage 3:       │
│ Chatbot       │  │ Admin         │  │ Storage        │
│               │  │ Approval      │  │                │
│ • FAISS DB    │  │ • LangChain   │  │ • SQLite       │
│ • Embeddings  │  │ • Telegram    │  │ • Persistence │
│ • LLM (opt)   │  │ • Approval DB │  │ • Validation   │
└───────────────┘  └───────────────┘  └────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Clone and install
python -m pip install -r requirements.txt

# Copy example config (optional - can run without)
cp .env.example .env
```

### Run the System

```bash
# Everything in one command
python scripts/stage4/run_orchestrator.py

# Now interact with the chatbot:

# Reservations (two ways)
reserve John Smith ABC123 from 5 march to 12 march 2026
reserve Иван Петров RS1234 с 5 по 12 июля 2026

# Questions (NO "info" prefix needed!)
What is the parking cost?
Сколько стоит парковка?
When are you open?
Когда вы работаете?

# Check status
check status REQ-...
```

### Configure Features (Optional)

Edit `.env` to enable:

```bash
# Use OpenAI LLM for better responses
USE_LLM=true
OPENAI_API_KEY=sk-...

# Use real Telegram for admin notifications
USE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...
```

Then run the same command - it reads from `.env`:

```bash
python scripts/stage4/run_orchestrator.py
```

---

## 📋 Project Status

| Stage | Status | Tests | What It Does |
|-------|--------|-------|---|
| **1: RAG Chatbot** | ✅ | 5/5 | Answer questions using FAISS + embeddings |
| **2: Admin Approval** | ✅ | 16/16 | Human approval workflow + optional Telegram |
| **3: Storage** | ✅ | 4/4 | Save approved reservations to SQLite |
| **4: Orchestration** | ✅ | 34/34 | Complete system integration with LangGraph |
| **TOTAL** | ✅ | **59/59** | All stages working together |

---

## 📖 Stage Documentation

- **[Stage 1: RAG Chatbot](docs/STAGE1.md)** - Information retrieval
- **[Stage 2: Admin Approval](docs/STAGE2.md)** - Approval workflow
- **[Stage 3: Storage](docs/STAGE3.md)** - Data persistence
- **[Stage 4: Orchestration](docs/STAGE4.md)** - Complete system

---

## 🎮 Usage Examples

```bash
# STAGE 2: Make a reservation (Two ways)

# Way 1: One-liner (fast) - no extra questions
reserve John Smith ABC123 from 5 march to 12 march 2026
reserve Иван Петров RS1234 с 5 по 12 июля 2026

# Way 2: Interactive (step-by-step) - system asks for details
reserve
# Bot will ask for name, surname, car, dates

# STAGE 4: Ask questions WITHOUT "info" prefix (now works!)

# English
What is the parking cost?
When are you open?
How much is parking per hour?

# Russian
Сколько стоит парковка?
Когда вы работаете?
Как долго можно припарковаться?

# Check status
check status REQ-20260227192458-001

# Get help
help
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run Stage 4 tests (34 tests)
python -m pytest tests/test_stage4.py -q

# Run other stages
python -m pytest tests/test_stage1.py -v
python -m pytest tests/test_stage2_langchain.py -v
```

---

## 🎯 Running Individual Stages

### Stage 1: RAG Chatbot (Information Only)
```bash
python scripts/stage1/run_chatbot.py
```
**Use this for**: Answering questions about parking
- What is the parking cost?
- What are the working hours?
- How do I book a space?

**NOT for reservations** - use Stage 2 instead!

### Stage 2: Approval Workflow (Reservations)
```bash
python scripts/stage2/run_stage2.py
```
**Use this for**: Making parking reservations

**Two ways to reserve:**

1️⃣ **One-liner (fast, no extra questions):**
```
reserve John Smith ABC123 from 5 march to 12 march 2026
reserve Иван Петров RS1234 с 5 по 12 июля 2026
```

2️⃣ **Interactive (system asks for details):**
```
reserve
[System prompts for: name, surname, car number, dates]
```

**Check status:**
```
status REQ-20260227192458-001
```

If `USE_TELEGRAM=true` in .env, admin receives notifications. Otherwise, reservations are auto-approved for testing.

### Other Stages
```bash
# Stage 3: Storage testing
python scripts/stage3/test_integration.py

# Stage 4: Full system (recommended - does everything)
python scripts/stage4/run_orchestrator.py
```

---


## ⚙️ Configuration

**Environment Variables** (all optional, sensible defaults provided):

```bash
# OpenAI API (optional - for better LLM responses)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Telegram (optional - for real admin notifications)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...

# Feature Flags (default: false)
USE_LLM=false          # Enable OpenAI LLM
USE_TELEGRAM=false     # Enable Telegram bot
```

---

## 🌟 Key Features

✅ **Works Out of the Box** - No setup required, simulated admin included
✅ **Optional Features** - Enable LLM and Telegram as needed via `.env`
✅ **Multi-language** - Russian and English support
✅ **Date Flexibility** - Any date ranges, across months and years
✅ **Fully Tested** - 59 tests across all components
✅ **Production Ready** - Error handling, validation, logging

---

## 📦 Technology Stack

- **Vector DB**: FAISS
- **Embeddings**: Sentence-Transformers
- **LLM**: OpenAI (optional)
- **Orchestration**: LangGraph
- **Approval Workflow**: LangChain
- **Notifications**: Telegram Bot API (optional)
- **Storage**: SQLite
- **Testing**: Pytest

---

## 📁 Project Layout

```
hw/
├── scripts/
│   ├── stage1/run_chatbot.py
│   ├── stage2/run_stage2.py
│   ├── stage3/test_integration.py
│   └── stage4/run_orchestrator.py
├── src/stage{1,2,3,4}/
├── tests/test_stage{1,2,3,4}.py
├── docs/STAGE{1,2,3,4}.md
├── data/ (SQLite, documents)
├── faiss_db/ (vector index)
└── .env.example
```

---

## 🎓 System Workflow

1. User submits request (reservation/info/status)
2. Stage 4 routes to appropriate handler
3. **Stage 1** (if info) - FAISS retrieval + optional LLM
4. **Stage 2** (if reservation) - Collect details + send for approval
5. **Stage 3** (if approved) - Store in SQLite
6. Response sent to user

---

## ⚡ Quick Commands

```bash
# Start the system
python scripts/stage4/run_orchestrator.py

# Run tests
python -m pytest tests/test_stage4.py -q

# Check what's in the database
python scripts/stage3/test_integration.py
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install -r requirements.txt` |
| "No OPENAI_API_KEY" | It's optional! Enable with `USE_LLM=true` in `.env` |
| "No TELEGRAM token" | It's optional! Enable with `USE_TELEGRAM=true` in `.env` |
| Tests failing | Run single test: `pytest tests/test_stage4.py::test_name -v` |

---

**Happy parking! 🚗**

