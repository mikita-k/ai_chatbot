# Helper Scripts for Development

This directory contains utility scripts for development and debugging, organized by stage.

## Directory Structure

```
scripts/
├── stage1/                    # Stage 1 - RAG Chatbot utilities
│   ├── check_indices.py      # Display loaded documents
│   └── debug_retrieval.py    # Test retrieval functionality
└── stage2/                    # Stage 2 - Chatbot with approval
    ├── run_stage2.py         # Main chatbot process
    └── run_telegram_bot.py   # Telegram admin notification bot
```

## Stage 1 Scripts

### `stage1/check_indices.py`
Displays all documents loaded in the DocumentStore and their indices.

**Usage:**
```bash
python scripts/stage1/check_indices.py
```

**Output example:**
```
0: Working Hours:...
1: Pricing:...
2: Location:...
3: Booking Process:...
4: Contact Information:...
5: Availability:...
```

### `stage1/debug_retrieval.py`
Tests the retrieval functionality with a sample query and shows which documents are returned with their similarity scores.

**Usage:**
```bash
python scripts/stage1/debug_retrieval.py
```

**Output example:**
```
Query: how much should I pay for 2 hours?

Found documents:
Document 1 (similarity=0.5123):
Pricing: Hourly rate is $2. Daily maximum is $20...

Document 0 (similarity=0.0234):
Working Hours: Monday to Friday 7am-7pm...
```

## Stage 2 Scripts

### `stage2/run_stage2.py`
Main chatbot process with human-in-the-loop approval system.

**Usage:**
```bash
# Basic usage (simulated approval)
python scripts/stage2/run_stage2.py

# With OpenAI LLM enabled
python scripts/stage2/run_stage2.py --use-llm

# Force enable Telegram
python scripts/stage2/run_stage2.py --use-telegram

# Force disable Telegram (use simulated approval)
python scripts/stage2/run_stage2.py --no-telegram
```

**Environment Variables:**
- `USE_LLM` - Set to `true`, `1`, or `yes` to enable OpenAI LLM (can also use `--use-llm` flag)
- `OPENAI_API_KEY` - OpenAI API key (required if `USE_LLM=true`)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather (optional)
- `TELEGRAM_ADMIN_CHAT_ID` - Admin's Telegram chat ID (optional)

**Features:**
- Answer parking-related questions using RAG
- Submit reservation requests for admin approval
- Get real-time approval status
- Telegram notifications (optional)

### `stage2/run_telegram_bot.py`
Telegram bot that listens for admin responses and updates the approval database.

**Usage:**
```bash
python scripts/stage2/run_telegram_bot.py
```

**Admin Commands:**
- `/start` - Show help
- `/pending` - List all pending requests
- `approve REQ-xxx` - Approve a request
- `reject REQ-xxx <reason>` - Reject a request with a reason

**Requirements:**
- `TELEGRAM_BOT_TOKEN` environment variable must be set
- Bot must be running in a separate terminal while chatbot is running

**How it works:**
1. User submits reservation request in `run_stage2.py`
2. Admin receives Telegram notification
3. Admin sends `approve REQ-xxx` or `reject REQ-xxx reason`
4. Bot writes response directly to database
5. Chatbot polls database and notifies user

## Notes

These scripts are **development and testing utilities**. They should **not be deployed** to production. For production deployment, integrate the Stage 2 components directly into your application.

## Running Multiple Stages

If you want to test the complete flow:

**Terminal 1 (Chatbot):**
```bash
python scripts/stage2/run_stage2.py
```

**Terminal 2 (Telegram Admin Bot) - Optional:**
```bash
python scripts/stage2/run_telegram_bot.py
```

Or disable Telegram in Terminal 1:
```bash
python scripts/stage2/run_stage2.py --no-telegram
```

