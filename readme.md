# LLM Chatbot for Parking Space Reservation

A multi-stage project implementing a complete intelligent chatbot system for parking space reservations using RAG (Retrieval-Augmented Generation), human-in-the-loop approval, and persistent storage.

## 🎯 Project Status

| Stage | Status | Features |
|-------|--------|----------|
| **Stage 1** | ✅ COMPLETE | RAG Chatbot, FAISS, Dynamic Data, LLM Integration, 5 Tests |
| **Stage 2** | ✅ COMPLETE | Admin Approval, Telegram Integration, 16 Tests |
| **Stage 3** | ✅ COMPLETE | MCP Server, Storage (CSV/SQLite), Validation, API Server |
| **Stage 4** | ⏳ TODO | LangGraph Orchestration |

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

---

## Original Technical Specification

Development of a Chatbot for Parking Space Reservation. The goal is to develop an intelligent chatbot that can interact with users, provide information about parking spaces, handle the reservation process, and involve a human administrator for confirmation ("human-in-the-loop"). The project will be divided into 4 stages, with each stage implementing a specific functionality.

General Requirements:
Programming Language: Python.
Frameworks: LangChain, LangGraph.
Architecture: Based on Retrieval-Augmented Generation (RAG).
Vector database: Recommended options include Milvus, Pinecone, or Weaviate,
General Features:
The chatbot provides information (general information, working hours, prices, availability of parking spaces, location).
The reservation process is based on interactive collection of user data, including name, surname, car number, and reservation period.
The system should prevent exposure of sensitive data (e.g., private information stored in the vector database).
Evaluation of system performance (e.g., request latency, information retrieval accuracy).
Providing the result: 
for each task, please provide a link to your GitHub or EPAM GitLab repository in the answer field
you can earn extra points if you provide the following artifacts: 
a PowerPoint presentation explaining how the solution works, including relevant screenshots
a README file with clear project documentation (setup, usage, structure, etc.)
Automated test cases are implemented using pytest or unittest  (at least 2 tests per module)
CI/CD automation and/or Infrastructure as Code (e.g., Terraform)
If the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced


# Stage 4: Orchestrating All Components via LangGraph
Not Started
Starts Feb 14, 2026 Ends Feb 28, 2026 (14 days)

What should be done
*
Tasks:

Implement orchestration of all components using LangGraph.
Ensure complete integration of all stages:
The chatbot (RAG agent) interacts with users.
The system escalates reservation requests to the administrator via a human-in-the-loop agent (second agent).
The MCP server processes data after confirmation.
Implement the workflow logic for the entire pipeline:
Example graph structure:
Node for user interaction (context of RAG and chatbot).
Node for administrator approval.
Node for data recording.
Conduct testing of the entire system workflow.
Outcome:

A unified system where all components seamlessly interact with each other.
Stable operation of the entire pipeline.
﻿

Additional Details:
System Testing:

Conduct load tests to evaluate the performance of each component:
Chatbot in interactive dialogue mode.
Administrator confirmation functionality.
MCP server recording and storage process.
Perform integration testing of all steps during orchestration.

Documentation:
Prepare documentation for system usage:
Architecture description.
Agent and server logic.
Setup and deployment guidelines.




Providing the result: 
please provide a link to your GitHub or EPAM GitLab repository in the answer field
you can earn extra points if you provide the following artifacts: 
a PowerPoint presentation explaining how the solution works, including relevant screenshots
a README file with clear project documentation (setup, usage, structure, etc.)
Automated test cases are implemented using pytest or unittest  (at least 2 tests per module)
CI/CD automation and/or Infrastructure as Code (e.g., Terraform)

if the code is poor quality, or too basic to be practical, and includes critical errors, the grade may be reduced



# Final Screening
What should be done
Congratulations!

If you've made it till this point - it means you've completed the program and there is the last part left - the final screening. It will cover all the theory you’ve learned during the program, and you may also be asked questions about your task.

After your session is completed, please submit the word PASSED in the answer field.

Good luck!