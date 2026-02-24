# Helper Scripts for Development

This directory contains utility scripts for local development and debugging. These scripts are **not required** for the main application and should **not be deployed**.

## Scripts

### `check_indices.py`
Displays all documents loaded in the DocumentStore and their indices.

**Usage:**
```bash
python check_indices.py
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

### `debug_retrieval.py`
Tests the retrieval functionality with a sample query and shows which documents are returned with their similarity scores.

**Usage:**
```bash
python debug_retrieval.py
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

## Notes

These are development-only utilities and can be safely deleted or ignored. They are included primarily to help developers understand and debug the retrieval system during development.

