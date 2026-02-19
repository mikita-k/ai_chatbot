# Implementation Guide - Multi-Stage Project

## Project Structure

The project is organized into 4 progressive stages:

```
src/
├── stage1/    # RAG Chatbot (COMPLETE)
├── stage2/    # Human-in-the-Loop (TODO)
├── stage3/    # MCP Server (TODO)
└── stage4/    # LangGraph Orchestration (TODO)
```

Each stage **builds upon and extends the previous one**.

---

## Stage 1: RAG Chatbot System ✅ COMPLETE

### What's Implemented

- RAG (Retrieval-Augmented Generation) architecture
- TF-IDF document retrieval with keyword fallback
- OpenAI LLM integration (optional)
- Guard rails (sensitive data redaction)
- Interactive chat and single-query modes
- Performance metrics (retrieval latency)
- Comprehensive test suite

### Quick Start

```powershell
# Activate environment
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Setup optional OpenAI integration
Copy-Item .env.example .env
# Edit .env and add OPENAI_API_KEY
```

### Running Stage 1

**Local mode (no API key required):**
```powershell
# Single query
python -m src.stage1.rag_chatbot qa --query "how much should I pay for 2 hours?"

# Interactive chat
python -m src.stage1.rag_chatbot chat
```

**LLM mode (requires OPENAI_API_KEY):**
```powershell
# Single query with OpenAI
python -m src.stage1.rag_chatbot qa --query "how much should I pay for 2 hours?" --use-llm

# Interactive chat with OpenAI
python -m src.stage1.rag_chatbot chat --use-llm
```

### Example Output

**Local Mode:**
```
Query: how much should I pay for 2 hours?

Pricing:
Hourly rate is $2. Daily maximum is $20. Monthly passes are available.
[score=0.500]

(Retrieval latency: 0.001s, top=3)
```

**LLM Mode:**
```
Query: how much should I pay for 2 hours?

For 2 hours, you should pay $4, as the hourly rate is $2.

(Retrieval latency: 0.001s, top=3)
```

### Testing

```powershell
# Run Stage 1 tests
pytest tests/test_stage1.py -v

# Run all tests
pytest -v
```

### Key Features

- ✅ RAG architecture with TF-IDF retrieval
- ✅ Fallback keyword-based search when TF-IDF has low scores
- ✅ Guard rails for email and number redaction
- ✅ OpenAI integration (gpt-3.5-turbo, gpt-4o-mini)
- ✅ Interactive CLI chat interface
- ✅ Performance monitoring (latency tracking)
- ✅ Comprehensive pytest tests (3+ test cases)

### File Structure

```
src/stage1/
├── __init__.py
└── rag_chatbot.py          # Main RAG implementation
```

### Data Files

```
data/
├── static_docs.txt         # Parking information
└── parking_spots.json      # Parking spots database
```

---

## Stage 2: Human-in-the-Loop Agent (TODO)

### What to Implement

1. **Admin Agent** using LangChain
   - Receive reservation requests from Stage 1 chatbot
   - Present admin with approval/rejection options
   - Send confirmation back to user

2. **Communication Channel**
   - Email notifications (SMTP)
   - Or REST API endpoint
   - Or messaging service (Slack, etc.)

3. **Integration with Stage 1**
   - When user wants to book, escalate to admin
   - Wait for admin response
   - Continue conversation based on approval/rejection

### Expected Structure

```
src/stage2/
├── __init__.py
├── admin_agent.py          # Admin-side agent
├── escalation.py           # Integration with Stage 1
└── notifications.py        # Email/API integration
```

### Architecture

```
Stage 1 Chatbot
    ↓ (User wants to book)
Stage 2 Admin Agent
    ↓ (Approve/Reject)
Back to Stage 1 (Notify user)
```

---

## Stage 3: MCP Server for Storage (TODO)

### What to Implement

1. **MCP Server** (FastAPI or similar)
   - Receive confirmed reservations from Stage 2
   - Validate and sanitize data
   - Write to persistent storage

2. **Storage** 
   - File-based (CSV, JSON)
   - Or Database (SQLite, PostgreSQL)
   - Format: `Name | Car Number | Reservation Period | Approval Time`

3. **Security**
   - Input validation
   - Access control
   - Error handling

### Expected Structure

```
src/stage3/
├── __init__.py
├── mcp_server.py           # FastAPI MCP server
├── storage.py              # File/DB operations
└── validators.py           # Data validation
```

### Architecture

```
Stage 2 Admin Approval
    ↓ (Confirmed reservation)
Stage 3 MCP Server
    ↓ (Process & Store)
Persistent Storage
    ↓ (reservations.csv / database)
```

---

## Stage 4: LangGraph Orchestration (TODO)

### What to Implement

1. **LangGraph Workflow**
   - Define graph nodes for each stage
   - Define edges (transitions between nodes)
   - Implement state management

2. **Node Structure**
   - **Node 1**: User interaction (Stage 1 RAG chatbot)
   - **Node 2**: Admin approval (Stage 2 agent)
   - **Node 3**: Data storage (Stage 3 MCP server)

3. **Edges**
   - User → Admin (if reservation requested)
   - Admin → Storage (if approved)
   - Admin → User (if rejected)

4. **Testing**
   - Load testing
   - Integration testing
   - End-to-end workflow testing

### Expected Structure

```
src/stage4/
├── __init__.py
├── orchestrator.py         # LangGraph setup
├── nodes.py                # Node implementations
└── workflow.py             # Complete pipeline
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           LangGraph Orchestrator                │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Stage 1: RAG]      [Stage 2: Admin]          │
│  ↓                   ↓                          │
│  Chatbot ─────→ Approval ─────→ [Stage 3: MCP]│
│  ↑                   ↓          ↓              │
│  └─────────────────────        Storage        │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Development Workflow

### For Each Stage

1. **Create module** in `src/stageX/`
2. **Write tests** in `tests/test_stageX.py`
3. **Document** in `docs/STAGEХ.md`
4. **Integrate** with previous stage
5. **Test** the integration

### Recommended Order

1. ✅ **Stage 1** - Complete RAG chatbot
2. → **Stage 2** - Add admin approval
3. → **Stage 3** - Add persistent storage
4. → **Stage 4** - Unify everything with LangGraph

---

## Testing Strategy

### Stage 1 Tests (COMPLETE)
```powershell
pytest tests/test_stage1.py -v
```

### Stage 2 Tests (TODO)
```powershell
pytest tests/test_stage2.py -v
```

### Stage 3 Tests (TODO)
```powershell
pytest tests/test_stage3.py -v
```

### Stage 4 Tests (TODO)
```powershell
pytest tests/test_stage4.py -v
```

### Run All Tests
```powershell
pytest -v
```

---

## Dependencies

Current:
```
scikit-learn>=1.3.0
pytest>=7.0
openai>=1.0.0
python-dotenv>=1.0.0
```

For Stage 2+:
```
langchain>=0.1.0
langraph>=0.0.1
fastapi>=0.100.0
pydantic>=2.0.0
```

---

## Troubleshooting

### "OPENAI_API_KEY not set"
- Create `.env` file with your key
- Or set in PowerShell: `$env:OPENAI_API_KEY = "sk-..."`

### Tests fail after restructuring
- Run `pytest --collect-only` to verify test discovery
- Check that `tests/conftest.py` adds project root to sys.path

---

## Next Steps

1. ✅ Stage 1 is complete
2. Start Stage 2 (Admin agent)
3. Update documentation as you progress
4. Keep tests updated for each stage

For detailed Stage 1 documentation, see [STAGE1.md](STAGE1.md).

