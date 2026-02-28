# Stage 1: RAG Chatbot

A semantic search-based chatbot for parking information using FAISS vector database and embeddings.

**Status**: ✅ Complete | **Tests**: ✅ Passing

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run

See [docs/SCRIPTS.md](SCRIPTS.md) (Stage 1 block) for detailed usage instructions:

- **`scripts/stage1/run_chatbot.py`** - Interactive RAG chatbot
- **`scripts/stage1/check_indices.py`** - Debug: show loaded documents
- **`scripts/stage1/debug_retrieval.py`** - Debug: test retrieval
- **`scripts/stage1/clean_faiss_db.py`** - Debug: rebuild FAISS index when docs change

## Features

- **Semantic Search**: Uses FAISS + sentence-transformers for intelligent document retrieval
- **Hybrid Data**: Static information (FAISS) + real-time parking data (SQLite)
- **Guard Rails**: Automatically redacts sensitive data (emails, long numbers)
- **Two Modes**:
  - **Local Mode**: Fast retrieval-based answers (no API key needed)
  - **LLM Mode**: AI-generated answers using OpenAI (requires API key)
- **Performance Tracking**: Shows retrieval latency for each query

## Usage Examples

### Local Mode
```powershell
python scripts/stage1/run_chatbot.py
```
```
You: How much does it cost per hour?
Pricing:
Hourly rate is $2. Daily maximum is $20. Monthly passes are available.
[similarity=0.500]

(Retrieval latency: 0.001s, top=3)

You: Where is the parking?
Location:
The parking is located at 123 Main Street, near the central mall.
[similarity=0.500]

(Retrieval latency: 0.001s, top=3)

You: exit
```

### LLM Mode (Better Quality Answers)

Set environment variable and run:
```powershell
# Option 1: Set environment variable
$env:USE_LLM = "true"
$env:OPENAI_API_KEY = "sk-your-key-here"

# Option 2: Use .env file
# Create .env with:
# USE_LLM=true
# OPENAI_API_KEY=sk-...

# run chatbot
python -m src.stage1.rag_chatbot chat
```
```
You: How much does it cost for 2 hours?
For 2 hours, you should pay $4, since the hourly rate is $2.

(Retrieval latency: 0.001s, top=3)

You: Is there parking available today?
Yes, parking is available today. Today's hours are 07:00 - 22:00.
The parking lot currently has 10 spaces available out of 10.

(Retrieval latency: 0.002s, top=3)

You: exit
```

### Single Query (QA Mode)
```powershell
python -m src.stage1.rag_chatbot qa --query "pricing information"
```

### Evaluation Mode
```powershell
python -m src.stage1.rag_chatbot eval
```
Tests retrieval quality on predefined sample queries.

## Architecture

**Data Flow:**
```
User Query
    ↓
Semantic Search (FAISS)
    ↓
Retrieve Top-3 Documents
    ↓
[Local Mode]              [LLM Mode]
↓                         ↓
Concatenate docs    →  OpenAI API  →  Generated Answer
↓
Guard Rails (redact PII)
↓
Final Answer
```

**Data Sources:**
- **Static Data**: `data/static_docs.txt` (parking info, rules, contact)
- **Dynamic Data**: SQLite database (availability, pricing, hours)

## Running & Testing

For scripts and commands, see [SCRIPTS.md](SCRIPTS.md).

For testing information, see [../readme.md](../readme.md) (Testing section).

## What's Included

| File | Purpose |
|------|---------|
| `src/stage1/rag_chatbot.py` | Main chatbot implementation |
| `data/static_docs.txt` | Static parking information |
| `data/dynamic/db.py` | Dynamic data management (availability, pricing) |
| `tests/test_stage1.py` | Unit tests |
| `requirements.txt` | Python dependencies |

## Key Technologies

- **FAISS**: Vector database for semantic search
- **sentence-transformers**: Pre-trained embeddings (all-MiniLM-L6-v2)
- **OpenAI API**: LLM for answer generation (optional)
- **SQLite**: Dynamic parking data storage
- **Python 3.10+**: Runtime

## Common Commands

| Command | Purpose |
|---------|---------|
| `python -m src.stage1.rag_chatbot chat` | Interactive chat |
| `python -m src.stage1.rag_chatbot qa --query "..."` | Single query |
| `pytest tests/test_stage1.py -v` | Run tests |
| `python scripts/check_indices.py` | Debug: show loaded documents |
| `python scripts/debug_retrieval.py` | Debug: test retrieval |

## Troubleshooting

**Q: "OPENAI_API_KEY not set"**
- A: Either set it in `.env` or: `$env:OPENAI_API_KEY = "sk-..."`

**Q: Tests fail**
- A: Install dependencies: `pip install -r requirements.txt`

**Q: Chat stops responding**
- A: Type `exit` to quit, restart the chatbot

## Performance

Typical latencies (local machine, no LLM):
- Retrieval: 0.5-2 ms
- With LLM: 0.5-2 seconds (depends on OpenAI API)

## Next Steps

This is Stage 1 of a multi-stage project:
- **Stage 1: RAG Chatbot** (current)
- [Stage 2: Human-in-the-loop approval workflow](STAGE2.md)
- [Stage 3: Persistent reservation storage](STAGE3.md)
- [Stage 4: LangGraph Orchestration](STAGE4.md)

## Related Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Design Decisions
- [../readme.md](../readme.md) - Main Project README