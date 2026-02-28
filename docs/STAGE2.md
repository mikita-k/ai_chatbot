
# Stage 2: Human-in-the-Loop Admin Agent

Real-time parking reservation system with admin approval workflow. Extends Stage 1 with Telegram notifications and SQLite-based request tracking.

**Status**: ✅ Complete | **Tests**: ✅ Passing

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run

See [docs/SCRIPTS.md](SCRIPTS.md) for detailed usage instructions:

- **`scripts/stage2/run_stage2.py`** - Stage 1+2 chatbot with approval (default: simulated admin)

## Features

- **Integrated Chatbot**: RAG queries (Stage 1) + Reservation requests (Stage 2)
- **Approval Channels**:
  - **Simulated** (default): Auto-approval after 1 second - no dependencies
  - **Telegram** (optional): Set `USE_TELEGRAM=true` in `.env` for real notifications
- **Request Tracking**: SQLite database stores all reservation requests
- **Status Workflow**: pending → approved/rejected
- **Performance**: Fast retrieval latency, instant status updates

## Usage Examples

### Simulated Mode (Default)

```bash
python scripts/stage2/run_stage2.py
```

```
You: What are the parking hours?
Response: 07:00 - 22:00

You: reserve John Smith ABC123 from 5 march to 12 march 2026
✅ Reservation request submitted!
   Request ID: REQ-20260225100000-001
   Your request has been sent to the administrator for review.
   
⏳ YOUR REQUEST IS PENDING ADMIN REVIEW
   Request ID: REQ-20260225100000-001
   Use 'status REQ-20260225100000-001' to check status

You: status REQ-20260225100000-001
Request Status: REQ-20260225100000-001
Status: PENDING
Approved: ❌ No

(In simulated mode, approval happens after ~1 sec, check status again)

You: status REQ-20260225100000-001
Request Status: REQ-20260225100000-001
Status: APPROVED
Approved: ✅ Yes

You: exit
```

**How it works:**
1. **Submit**: User submits reservation, gets request ID
2. **Wait**: System waits 2 seconds for admin response
3. **Timeout**: Since no real admin responds in 2 seconds, shows PENDING
4. **Check Status**: User checks status manually using `status <request_id>` command
5. **Update**: Admin can approve via Telegram or simulated approval, status updates next check

### With Telegram Notifications (Optional)

First, set environment variables in `.env`:
```bash
USE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
```

Then run:
```bash
python scripts/stage2/run_stage2.py
```
```
User submits reservation → admin gets Telegram notification → can approve/reject via Telegram.

Request ID: REQ-20260224100000-001
Name: John Doe
Car Number: ABC123
Period: 2026-02-24 10:00 - 2026-02-24 12:00

Reply with:
approve REQ-20260224100000-001
reject REQ-20260224100000-001 <reason>
```

**Admin Responds:**
```
Admin: approve REQ-20260224100000-001
Bot: ✅ Request REQ-20260224100000-001 approved!
```

**Terminal - User Gets Update:**
```bash
status REQ-20260224100000-001
```
```
Status: APPROVED ✅
Details: Approved by admin
Response time: 2026-02-28T18:07:58.868795
```

### Check Status Anytime

```powershell
python -m src.stage2.chatbot_with_approval status --request-id REQ-20260224100000-001
```

```
Request Status: REQ-20260224100000-001
Status: APPROVED ✅
Name: John Doe
Car: ABC123
Period: 2026-02-24 10:00 - 12:00
```

## Architecture

```
USER INTERFACE
    ↓
Stage2Chatbot (chatbot_with_approval.py)
    ├─ Info Mode → RAG Chatbot (Stage 1)
    └─ Reserve Mode → AdminAgent
        ↓
AdminAgent (admin_agent.py)
    ├─ Submit request to DB
    ├─ Send notification via channel
    ├─ Process admin responses
    └─ Update request status
        ↓
ApprovalChannel (Abstract)
    ├─ SimulatedApprovalChannel (auto-approval, testing)
    └─ TelegramApprovalChannel (real Telegram bot)
        ↓
SQLite Database (data/dynamic/approvals.db)
    └─ reservation_requests table
```

## Database

Reservation requests stored in SQLite (`data/dynamic/approvals.db`).

**Schema:**
```sql
CREATE TABLE reservation_requests (
    request_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    car_number TEXT NOT NULL,
    period TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,              -- pending|approved|rejected
    admin_response TEXT,               -- optional rejection reason
    response_time TEXT,
    updated_at TEXT
);
```

**Query Examples:**
```powershell
# Count requests
sqlite3 data/dynamic/approvals.db "SELECT COUNT(*) FROM reservation_requests"

# List all pending
sqlite3 data/dynamic/approvals.db "SELECT request_id, status FROM reservation_requests WHERE status='pending'"

# Clear database
rm data/dynamic/approvals.db
```

## Telegram Bot Setup (Optional)

### Step 1: Create Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send: `/newbot`
3. Choose bot name, get **BOT_TOKEN**

### Step 2: Get Your Chat ID
1. Message your bot anything
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"id": 461212123` → copy as **CHAT_ID**

### Step 3: Create .env File
```env
TELEGRAM_BOT_TOKEN=7728212407:AAGhaclG82tGNjv2hv2x60EFOg0iWDQTYUg
TELEGRAM_ADMIN_CHAT_ID=461212123
```

### Step 4: Run Script
```powershell
python scripts/stage2/run_stage2.py
```

### Telegram Commands
```
/start               - Show help
/pending             - List pending requests
approve REQ-xxx      - Approve request
reject REQ-xxx text  - Reject with reason
```

## Python API

### Create Admin Agent
```python
from src.stage2.admin_agent import create_admin_agent

# Simulated (default)
admin = create_admin_agent(use_telegram=False)

# With Telegram
admin = create_admin_agent(use_telegram=True)
```

### Submit Reservation
```python
request_id = admin.submit_request(
    name="John",
    surname="Doe",
    car_number="ABC123",
    period="2026-02-24 10:00 - 2026-02-24 12:00"
)
print(f"Request: {request_id}")
```

### Check Status
```python
status = admin.check_status(request_id)
print(f"Status: {status['status']}")  # pending | approved | rejected
print(f"Approved: {status['approved']}")
```

### Get All Requests
```python
pending = admin.get_pending_requests()
all_requests = admin.get_all_requests()

for req in all_requests:
    print(f"{req.request_id}: {req.status}")
```

### Integrated Chatbot
```python
from src.stage2.chatbot_with_approval import Stage2Chatbot
from src.stage1.rag_chatbot import DocumentStore

# Initialize
store = DocumentStore.from_file("data/static_docs.txt")
admin = create_admin_agent(use_telegram=False)
chatbot = Stage2Chatbot(store, admin, use_llm=False)

# Ask question
answer = chatbot.answer_question("What are the prices?")

# Make reservation
result = chatbot.initiate_reservation({
    "name": "Alice",
    "surname": "Smith",
    "car_number": "XYZ789",
    "period": "2026-02-24 14:00 - 2026-02-24 16:00"
})

# Check status
status = chatbot.check_request_status(result['request_id'])
```

## Testing

### Run All Tests
```powershell
pytest tests/test_stage2.py -v
```

**Expected output:**
```
test_stage2.py::TestReservationRequest::test_creation PASSED
test_stage2.py::TestReservationRequest::test_string_representation PASSED
test_stage2.py::TestAdminApprovalDatabase::test_database_creation PASSED
test_stage2.py::TestAdminApprovalDatabase::test_save_and_retrieve_request PASSED
test_stage2.py::TestAdminApprovalDatabase::test_get_all_requests_filtered PASSED
test_stage2.py::TestSimulatedApprovalChannel::test_send_request PASSED
test_stage2.py::TestSimulatedApprovalChannel::test_auto_approval PASSED
test_stage2.py::TestAdminAgent::test_submit_request PASSED
test_stage2.py::TestAdminAgent::test_approval_workflow PASSED
test_stage2.py::TestAdminAgent::test_rejection_workflow PASSED
test_stage2.py::TestAdminAgent::test_pending_requests_list PASSED
test_stage2.py::TestAdminAgent::test_get_all_requests PASSED
test_stage2.py::TestCreateAdminAgent::test_create_with_simulated_channel PASSED
test_stage2.py::TestCreateAdminAgent::test_create_with_telegram_missing_vars PASSED
test_stage2.py::TestStage2Integration::test_full_workflow_with_chatbot PASSED

===================== 15 passed in 7.00s =====================
```

### Run Specific Test
```powershell
pytest tests/test_stage2.py::TestAdminAgent::test_approval_workflow -v
```

### Run with Coverage
```powershell
pytest tests/test_stage2.py --cov=src.stage2 --cov-report=html
```

### Run Examples
```powershell
python examples_stage2.py
python test_stage2_quick.py
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `python run_stage2.py` | Interactive chat (see .env for config) |
| `python run_telegram_bot.py` | Telegram bot (separate terminal) |
| `python -m src.stage2.chatbot_with_approval reserve` | Direct reservation |
| `python -m src.stage2.chatbot_with_approval status --request-id REQ-xxx` | Check status |
| `pytest tests/test_stage2.py -v` | Run all tests (15 tests) |
| `pytest tests/test_stage2.py --cov=src.stage2` | Coverage report |
| `python examples_stage2.py` | Run examples |


## Configuration (.env):
| Variable | Purpose |
|----------|---------|
| `USE_LLM=true/false` | Enable/disable OpenAI LLM |
| `USE_TELEGRAM=true/false` | Enable/disable Telegram |
| `OPENAI_API_KEY=sk-...` | OpenAI key (required if USE_LLM=true) |
| `TELEGRAM_BOT_TOKEN=...` | Telegram token (required if USE_TELEGRAM=true) |

## Workflow Example

```
1. USER INITIATES CHAT
   $ python run_stage2.py
   
2. USER ASKS QUESTION
   You: What are the opening hours?
   Assistant: [Answers from RAG data]
   
3. USER MAKES RESERVATION
   You: reserve
   Name: John Doe
   Car: ABC123
   Period: 2026-02-24 10:00 - 2026-02-24 12:00
   
   ✅ Request submitted: REQ-20260224100000-001
   ⏳ Waiting for admin...
   
4. ADMIN APPROVES (Optional Telegram)
   [Via Telegram Bot or simulated auto-approval]
   approve REQ-20260224100000-001
   
5. USER GETS NOTIFICATION
   ✅ YOUR REQUEST HAS BEEN APPROVED!
      Request ID: REQ-20260224100000-001
```

## Troubleshooting

### Telegram Notifications Not Working

**Problem**: Admin doesn't receive Telegram message

**Solution:**
1. Check `.env` file exists and has valid tokens:
   ```powershell
   cat .env
   ```
2. Verify bot token with:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```
3. Check terminal output for connection logs

### "python-telegram-bot not installed"

```powershell
pip install python-telegram-bot>=20.0
```

### "Database locked" Error

```powershell
# Delete and let system recreate
rm data/dynamic/approvals.db
```

### Tests Fail

```powershell
# Reinstall dependencies
pip install -r requirements.txt

# Run with verbose output
pytest tests/test_stage2.py -vv --tb=long
```

## Workflow Details

### Default: Simulated Admin (No Telegram)

```powershell
python scripts/stage2/run_stage2.py
```

- No external dependencies needed
- Auto-approves after ~1 second delay
- Perfect for testing and development
- No need for Telegram setup

### With Telegram Bot (Real Admin)

**Terminal:**
```powershell
python scripts/stage2/run_stage2.py
```

- Make sure `.env` has `USE_TELEGRAM=true` and valid tokens
- Admin gets real-time notifications in Telegram
- Admin can approve/reject with commands
- User gets status updates in chatbot

**Admin gets notified on Telegram immediately when user submits request** ✨

## Module Structure

```
src/stage2/
├── __init__.py                   # Package exports
├── admin_agent.py                # AdminAgent, ApprovalChannels
├── chatbot_with_approval.py      # Integrated chatbot
└── telegram_service.py           # Telegram bot

data/dynamic/
└── approvals.db                  # SQLite database (auto-created)

tests/
└── test_stage2.py               # 15 comprehensive tests

scripts/
├── run_stage2.py                # Main chatbot entry point
└── run_telegram_bot.py          # Telegram bot entry point
```

## Performance

Typical latencies:
- Retrieval (RAG): 0.5-2 ms
- DB write: < 1 ms
- Status check: < 1 ms
- Telegram notification: 0.1-0.5 seconds
- Admin approval processing: instant

## Design Decisions

### Why Two Scripts Instead of Threading?

1. **Simpler** - No asyncio complexity
2. **More reliable** - No race conditions
3. **Better debugging** - Separate terminal logs
4. **Flexible** - Run only chatbot if no Telegram
5. **Production-ready** - Can deploy as separate services

### Why SQLite?

1. **Lightweight** - No external database server
2. **Persistent** - Data survives restarts
3. **Fast** - No network overhead
4. **Simple** - Single file database

### Why Simulated Channel for Testing?

1. **No external dependencies** - Test without Telegram
2. **Fast feedback** - No network delays
3. **Deterministic** - Predictable behavior
4. **Isolated tests** - No test bot needed

## Next Steps

This is Stage 2 of a multi-stage project:
- [Stage 1: RAG Chatbot](STAGE1.md) (completed)
- **Stage 2: Human-in-the-loop approval workflow** (current)
- [Stage 3: Persistent reservation storage](STAGE3.md)
- [Stage 4: LangGraph Orchestration](STAGE4.md)

## Related Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Design Decisions
- [../readme.md](../readme.md) - Main Project README

---

## Quick Answers

**Q: How do I start?**  
A: `pip install -r requirements.txt` then `pytest tests/test_stage2.py -v`

**Q: How do I run the chatbot?**  
A: `python scripts/stage2/run_stage2.py`

**Q: How do I add Telegram notifications?**  
A: Create `.env` with bot token and chat ID, set `USE_TELEGRAM=true`.

**Q: What commands can I use in chatbot?**  
A: `help`, `reserve`, `status REQ-xxx`, `exit`

**Q: How do I check the database?**  
A: `sqlite3 data/dynamic/approvals.db "SELECT * FROM reservation_requests"`
