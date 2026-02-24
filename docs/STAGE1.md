# Parking Space RAG Chatbot - Stage 1

A simple RAG chatbot that helps users find parking information and make reservations using semantic search and AI.

## Quick Start

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Run the Chatbot

**Interactive Chat (Local, no API key needed):**
```powershell
python -m src.stage1.rag_chatbot chat
```

**Single Query:**
```powershell
python -m src.stage1.rag_chatbot qa --query "where is the parking?"
```

**With OpenAI LLM (requires API key):**
```powershell
# Set API key first
$env:OPENAI_API_KEY = "sk-your-key-here"

# Then run
python -m src.stage1.rag_chatbot chat --use-llm
```

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
python -m src.stage1.rag_chatbot chat
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
```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
python -m src.stage1.rag_chatbot chat --use-llm
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

## Environment Variables

Create `.env` file for OpenAI integration (optional):
```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Or copy from template:
```powershell
Copy-Item .env.example .env
```

## Testing

Run all tests:
```powershell
python -m pytest tests/test_stage1.py -v
```

Expected output:
```
test_guard_rails_email_redaction PASSED
test_guard_rails_number_redaction PASSED
test_documentstore_retrieval PASSED
test_simple_rag_answer PASSED
test_dynamic_data_included PASSED

===================== 5 passed =====================
```

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
| `python -m src.stage1.rag_chatbot chat --use-llm` | Chat with OpenAI |
| `python -m pytest tests/test_stage1.py -v` | Run tests |
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
- **Stage 2**: Human-in-the-loop approval workflow
- **Stage 3**: Persistent reservation storage
- **Stage 4**: Multi-agent orchestration

