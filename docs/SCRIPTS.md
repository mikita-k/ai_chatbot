# Helper Scripts for Development

This directory contains utility scripts for development and debugging, organized by stage.

## Quick Reference

```
scripts/
├── stage1/
│   ├── run_chatbot.py           # RAG chatbot interactive mode
│   ├── check_indices.py         # Debug: Display loaded documents
│   ├── debug_retrieval.py       # Debug: Test retrieval with sample query
│   └── clean_faiss_db.py        # Maintenance: Clear FAISS vector database
│
├── stage2/
│   └── run_stage2.py            # Stage 1+2 chatbot with approval workflow
│
├── stage3/
│   └── view_db.py               # Maintenance: View stored reservations
│
└── stage4/
    └── run_orchestrator.py      # Complete system (all 4 stages)
```

## Stage 1: RAG Chatbot

### CLI Commands

Interactive use of RAG chatbot via command line:

```bash
# Interactive chat mode
python -m src.stage1.rag_chatbot chat

# Single query (QA mode)
python -m src.stage1.rag_chatbot qa --query "pricing information"

# Retrieval accuracy evaluation
python -m src.stage1.rag_chatbot eval
```

**Configuration (set in `.env`):**
- `USE_LLM=true` - Use OpenAI for answer generation
- `EVAL_VERBOSE=true` - Show detailed quality evaluation metrics
- `EVAL_VERBOSE=false` - Show only basic latency (default)

### `run_chatbot.py`
Interactive chat with the RAG chatbot (no admin approval).

```bash
python scripts/stage1/run_chatbot.py
```

**Usage:**
```
You: What is the parking cost?
Response: Hourly rate is $2. Daily maximum is $20...

You: exit
```

### `check_indices.py` (Debug)
Display all documents loaded in FAISS and their indices.

```bash
python scripts/stage1/check_indices.py
```

**Output example:**
```
Loaded documents in FAISS:
0: Working Hours: ...
1: Pricing: ...
2: Location: ...
...
```

### `debug_retrieval.py` (Debug)
Test retrieval with a sample query and show matching documents.

```bash
python scripts/stage1/debug_retrieval.py
```

**Output example:**
```
Query: how much should I pay for 2 hours?

Found documents:
Document 0 (similarity=0.512):
  Pricing: Hourly rate is $2...

Document 1 (similarity=0.489):
  Daily maximum is $20...
```

### `clean_faiss_db.py` (Debug)
Rebuild FAISS index when static_docs.txt changes.

```bash
python scripts/stage1/clean_faiss_db.py
```

**When to use:**
- After editing `data/static_docs.txt`
- If FAISS index becomes corrupted
- When you want fresh embeddings

**What it does:**
- Removes `faiss_db/index.faiss`
- Removes `faiss_db/docs.pkl`
- Next run will rebuild them automatically

## Stage 2: Admin Approval

### `run_stage2.py`
Combined chatbot with admin approval workflow (with 2-second timeout for responsiveness).

```bash
python scripts/stage2/run_stage2.py
```

**Usage:**
```
You: What are the working hours?
Response: 07:00 - 22:00

You: reserve John Smith ABC123 from 5 march to 12 march 2026
✅ Reservation request submitted!
   Request ID: REQ-20260225100000-001
⏳ YOUR REQUEST IS PENDING ADMIN REVIEW
   Use 'status REQ-20260225100000-001' to check status

You: status REQ-20260225100000-001
Status: PENDING
(If admin approves in Telegram, next check will show APPROVED)

You: exit
```

**How it works:**
- **Submission**: Waits 2 seconds for admin response (quick timeout, chat stays responsive)
- **Checking Status**: Use `status <request_id>` command to check anytime
- **Default**: Simulated approval (auto-approve after 1 sec)
- **With Telegram**: Set `USE_TELEGRAM=true` in `.env` (requires TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID)

When Telegram is enabled, admin gets notification and can approve/reject via Telegram. Your next `status` check will show the updated approval status.

## Stage 3: Storage

### `view_db.py` (Debug)
View all reservations currently stored in the database.

```bash
python scripts/stage3/view_db.py
```

**Output example:**
```
📋 STAGE 3: View Approved Reservations

✅ Found 2 reservation(s):

1. ID: REQ-20260225100000-001
   User: John Doe
   Car: ABC123
   Period: 2026-03-01 → 2026-03-07
   Approved: 2026-02-25T10:00:00
   Created: 2026-02-25T10:15:30

2. ID: REQ-20260225100000-002
   User: Jane Smith
   Car: XYZ789
   ...
```

**When to use:**
- After making reservations to verify they were saved
- For debugging approval workflow
- To check what data is in the database

Data is persisted to `data/reservations.db` when reservations are approved.

## Stage 4: Complete Orchestration

### `run_orchestrator.py`
Main entry point for the complete system integrating all 4 stages.

```bash
python scripts/stage4/run_orchestrator.py
```

For configuration, see [../.env.example](../.env.example)

**Usage:**
```
You: What is the parking cost?
Response: Hourly rate is $2. Daily maximum is $20...

You: reserve John Smith ABC123 from 5 march to 12 march 2026
✅ Reservation request submitted!
   Request ID: REQ-20260225100000-001
⏳ YOUR REQUEST IS PENDING ADMIN REVIEW
   Use 'status REQ-20260225100000-001' to check status anytime

You: status REQ-20260225100000-001
📋 **Request Status: REQ-20260225100000-001**
Status: PENDING
(If admin approves, next check will show APPROVED ✅)

You: exit
```

## Development & Testing

**For debugging Stage 1 retrieval:**
```bash
python scripts/stage1/debug_retrieval.py
python scripts/stage1/check_indices.py
```

**For testing approval workflow:**
```bash
python scripts/stage2/run_stage2.py
```

**For running tests**, see [../readme.md](../readme.md#-testing)

## Notes

- All scripts use relative imports and work from project root
- Stage 4 orchestrator is the recommended entry point for the complete system
- Telegram and OpenAI LLM are optional; system works without them

