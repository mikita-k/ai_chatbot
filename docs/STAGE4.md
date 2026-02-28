# Stage 4: LangGraph Orchestration

Complete orchestration of all components (RAG chatbot, admin approval, storage) using LangGraph state machine.

**Status**: ✅ Complete | **Tests**: ✅ Passing

## Quick Start

For scripts and commands, see [SCRIPTS.md](SCRIPTS.md).

For configuration details, see [../.env.example](../.env.example).

**Basic Usage** (configuration from .env):
```bash
python scripts/stage4/run_orchestrator.py
```

**Example Interaction**:
```
# Test reservation request
You: reserve Иван Иванов RS1234 с 1 марта по 3 марта 2026

# Check reservation status
You: status REQ-XXX-###
```

---

## 📋 Reservation Format Guide

The system supports flexible date formats for making reservations. Users can specify any dates - different months, different years!

### Format

```
reserve <FirstName> <LastName> <CarNumber> <DateRange>
```

### Supported Date Formats

#### Russian - Short Format (same month)
```
reserve Иван Петров RS1234 с 5 по 12 июля 2026
```

#### Russian - Full Format (any months/years)
```
reserve Иван Петров RS1234 с 20 марта 2026 по 21 апреля 2027
```

#### English - Short Format (same month)
```
reserve John Smith ABC123 from 5 march to 12 march 2026
```

#### English - Full Format (any months/years)
```
reserve John Smith ABC123 from 20 march 2026 to 21 april 2027
```

### What's Supported

**Names:**
- ✅ Russian (Cyrillic): Иван, Петров, Александр
- ✅ English (ASCII): John, Smith, Michael
- ✅ Multi-word names properly extracted

**Car Numbers:**
- ✅ ABC123 (letters+numbers)
- ✅ 1234TY (numbers+letters)
- ✅ RS-1234 (with dash)
- ✅ ABC-XY-1234 (multiple parts)

**Date Ranges:**
- ✅ Russian: `с 5 по 12 июля 2026` (same month)
- ✅ Russian: `с 20 марта 2026 по 21 апреля 2027` (full format)
- ✅ English: `from 5 march to 12 march 2026` (same month)
- ✅ English: `from 20 march 2026 to 21 april 2027` (full format)

### Examples That Work

| Input | Parsed As |
|-------|-----------|
| reserve Иван Петров RS1234 с 5 по 12 июля 2026 | Иван Петров, RS1234, 2026-07-05 to 2026-07-12 |
| reserve Иван Петров RS1234 с 20 марта 2026 по 21 апреля 2027 | Иван Петров, RS1234, 2026-03-20 to 2027-04-21 |
| reserve John Smith ABC123 from 5 march to 12 march 2026 | John Smith, ABC123, 2026-03-05 to 2026-03-12 |
| reserve John Smith ABC123 from 20 march 2026 to 21 april 2027 | John Smith, ABC123, 2026-03-20 to 2027-04-21 |

### Other Request Types

**Check Reservation Status:**
```
check status REQ-20260227192458-001
```

**Ask Information:**
```
What are the parking prices?
How much does parking cost?
```

---

## Architecture Overview

### LangGraph State Machine

The orchestration is built on LangGraph, a state machine framework that manages the complete workflow:

```
┌─────────────────────────────────────────────────────┐
│                    START                            │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────▼──────────┐
       │   Initialize     │
       │     Node         │
       └───────┬──────────┘
               │
       ┌───────▼──────────┐
       │     Router       │◄─── Classifies request type
       │     Node         │     (info/reservation/status)
       └───┬───────────┬──┘
           │           │
      ┌────▼──┐  ┌─────▼────────┐
      │ Info  │  │ Reservation  │
      │ Path  │  │ Path         │
      └────┬──┘  └─────┬────────┘
           │           │
      ┌────▼──┐  ┌─────▼────────┐
      │  RAG  │  │  Collection  │
      │ Node  │  │    Node      │
      └────┬──┘  └─────┬────────┘
           │           │
           │      ┌────▼────────┐
           │      │ Approval    │
           │      │ Node        │
           │      └─────┬───────┘
           │            │
           │      ┌─────▼───────┐
           │      │  Storage    │ (if approved)
           │      │  Node       │
           │      └─────┬───────┘
           │            │
      ┌────▼────────┬──┘
      │   Response  │
      │    Node     │
      └────┬────────┘
           │
       ┌───▼──────────┐
       │      END     │
       └──────────────┘
```

### Workflow Components

#### 1. **Router Node** (Request Classification)
```python
# Classifies incoming requests:
# - "info" - Questions about parking info
# - "reservation" - New parking reservation request
# - "status_check" - Check reservation status
# - "unknown" - Could not classify
```

#### 2. **RAG Node** (Information Retrieval)
```python
# Uses Stage 1 RAG Chatbot
# Retrieves parking information using FAISS
# Returns answer with sources
```

#### 3. **Collection Node** (Data Gathering)
```python
# Gathers reservation details
# In demo: simulates user input
# In production: would handle multi-turn conversation
```

#### 4. **Approval Node** (Admin Decision)
```python
# Uses Stage 2 Admin Agent
# Submits reservation to admin for approval
# Waits for human decision (approved/rejected)
```

#### 5. **Storage Node** (Data Persistence)
```python
# Uses Stage 3 ReservationStorage
# Saves approved reservations to SQLite
# Only triggered if approval_status == "approved"
```

#### 6. **Response Node** (Final Output)
```python
# Generates user response based on outcome
# Different messages for:
#   - Info responses (RAG answer)
#   - Approved reservations (confirmation + ID)
#   - Rejected reservations (rejection reason)
```

---

## Data Flow Examples

### Example 1: Information Request

```
User: "What are the parking prices?"
       ↓
   Router: request_type = "info"
       ↓
   RAG Node: query FAISS index
       ↓
   Response: "$2/hour, $20/day maximum"
       ↓
    END
```

### Example 2: Reservation Request

```
User: "I want to reserve a parking spot"
       ↓
   Router: request_type = "reservation"
       ↓
   Collection: Gather name, car number, dates
       ↓
   Approval: Submit to admin
       ↓
   [Admin approves]
       ↓
   Storage: Save to database
       ↓
   Response: "Reservation approved! ID: REQ-..."
       ↓
    END
```

---

## State Schema

### WorkflowState (TypedDict)

```python
class WorkflowState(TypedDict):
    # Input
    user_input: UserInput  # {user_id, message, timestamp}
    
    # Classification
    request_type: Literal["info", "reservation", "status_check", "unknown"]
    
    # Responses
    rag_response: Optional[RAGResponse]  # {answer, sources, confidence}
    reservation_details: Optional[ReservationDetails]  # {name, car, dates...}
    approval_result: Optional[ApprovalResult]  # {status, feedback, time}
    
    # Storage result
    storage_success: bool
    storage_message: str
    
    # Final response to user
    final_response: str
    
    # Metadata
    request_id: str  # Unique workflow ID
    errors: List[str]  # Error tracking
    state_history: List[str]  # Node execution history
```

---

## API Reference

### LangGraphOrchestrator Class

Main interface for using the orchestration system:

```python
from src.stage4.orchestrator import create_orchestrator

# Create orchestrator
orchestrator = create_orchestrator(
    use_llm=False,        # Enable OpenAI LLM
    use_telegram=False,   # Enable Telegram notifications
    verbose=True          # Print debug info
)

# Process a request
result = orchestrator.process_request(
    user_message="What's the price?",
    user_id="user_123"
)

# Access response
print(result['final_response'])  # User-facing message
print(result['request_type'])     # Type: info/reservation/status
print(result['state_history'])    # Nodes visited: [initialize, router, rag, response]

# Track requests
requests = orchestrator.list_requests()  # All processed requests
status = orchestrator.get_request_status("FLOW-20260225120000-ABC123")

# Interactive mode
orchestrator.interactive_mode()  # Start chat interface
```

### Methods

```python
# Process a single request
process_request(user_message: str, user_id: str = "user_001") -> Dict

# Get request history
get_request_status(request_id: str) -> Optional[Dict]
list_requests() -> List[Dict]

# Pretty print summary
print_summary()

# Interactive chatbot mode
interactive_mode()
```

### Return Value Format

```python
{
    'final_response': str,           # Message to user
    'request_id': str,              # Unique flow ID
    'request_type': str,            # info/reservation/status/unknown
    'approval_status': str,         # approved/rejected/N/A
    'storage_success': bool,        # Was data saved
    'storage_message': str,         # Storage outcome
    'state_history': List[str],     # Path through graph
    'errors': List[str],            # Any errors
}
```

---

## Testing

For testing information, see [../readme.md](../readme.md) (Testing section).

---

## Integration with Stages 1-3

### Stage 1 Integration
- **RAG Chatbot**: Used in RAG Node for information retrieval
- **FAISS Index**: Loaded automatically, serves documents
- **Embeddings**: Sentence-transformers for semantic search

### Stage 2 Integration
- **Admin Agent**: Used in Approval Node
- **Approval Channels**: Simulated or Telegram-based
- **Database**: Stores pending/approved requests

### Stage 3 Integration
- **ReservationStorage**: Used in Storage Node
- **SQLite Database**: Saves approved reservations
- **Simple API**: Automatic persistence

---

## Next Steps

This is Stage 4 of a multi-stage project:
- [Stage 1: RAG Chatbot](STAGE1.md) (completed)
- [Stage 2: Human-in-the-loop approval workflow](STAGE2.md) (completed)
- [Stage 3: Persistent reservation storage](STAGE3.md) (completed)
- **Stage 4: LangGraph Orchestration**(current)

## Related Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Design Decisions
- [../readme.md](../readme.md) - Main Project README
