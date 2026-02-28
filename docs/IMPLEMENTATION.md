# Implementation Guide

## Key Design Decisions

### 1. RAG Architecture (Stage 1)
- **FAISS** chosen for efficiency and ease of use over cloud alternatives
- **Sentence-transformers** for semantic similarity without LLM dependency
- **Dual data model**: static FAISS index + dynamic SQLite for real-time updates
- **Guard rails**: Email/number redaction to prevent sensitive data leakage

### 2. Admin Approval (Stage 2)
- **LangChain** agent with explicit tools
- **Simulated channel** by default to enable zero-config testing
- **Telegram** as optional real-world integration (not required)
- **Database-driven**: SQLite for request persistence, no in-memory state

### 3. Storage (Stage 3)
- **Minimal implementation**: No FastAPI/MCP overhead, just SQLite API
- **Stage 2 integration**: Works as extension of approval system
- **Simple schema**: One table for reservations, easy to extend

### 4. Orchestration (Stage 4)
- **LangGraph** over custom state machine for production-grade workflows
- **Conditional routing**: Router node classifies request type
- **No waiting**: Graph processes asynchronously, doesn't block on approvals
- **Complete integration**: All 4 stages as coherent workflow

### 5. Configuration
- **.env file** as single source of truth
- **No CLI flags**: Keeps code clean, configuration consistent
- **Zero-config by default**: System works without any setup

---

## Development Notes

### 2-Second Timeout Design
- **Rationale**: Keep chat responsive while waiting for admin
- **Behavior**: Requests immediately show PENDING status
- **UX**: Users can check status manually via `status <request_id>` command
- **Admin approval**: Happens in background, visible on next status check

### Request Flow
```
User Input
    ↓
[Stage 4] Router classifies request
    ├→ Info query ────→ [Stage 1] RAG search
    ├→ Reservation ──→ [Stage 2] Admin approval ──→ [Stage 3] Save
    └→ Status check ─→ History lookup
    ↓
Response to user
```

### Testing Strategy
- **Unit tests**: Each stage has isolated tests
- **Integration tests**: Stage 4 tests all 4 stages together
- **No external dependencies**: Tests run without Telegram/OpenAI

### Guard Rails Implementation
- **Email redaction**: Protects user privacy in logs
- **Number redaction**: Prevents sensitive data exposure
- **Database**: All fields stored safely in SQLite

---

## References

**Stage Documentation**:
- [STAGE1.md](STAGE1.md) - RAG Chatbot
- [STAGE2.md](STAGE2.md) - Admin Approval
- [STAGE3.md](STAGE3.md) - Storage
- [STAGE4.md](STAGE4.md) - LangGraph

**Usage**:
- [SCRIPTS.md](SCRIPTS.md) - All available scripts
- [../readme.md](../readme.md) - Main README

**Configuration**:
- [../.env.example](../.env.example) - Configuration template

