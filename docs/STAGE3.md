# Stage 3: Persistent Storage and Database Management

Persistent storage system for approved parking reservations. Extends Stage 2 with SQLite database management for reservation records.

**Status**: ✅ Complete | **Tests**: ✅ Passing

## Quick Start

For scripts and commands, see [SCRIPTS.md](SCRIPTS.md).

For testing information, see [../readme.md](../readme.md) (Testing section).

## Features

- **Persistent Storage**: SQLite database for approved reservations
- **Simple API**: Easy-to-use `ReservationStorage` class
- **Integration Ready**: Works seamlessly with Stage 2 approval workflow
- **Built-in**: No external dependencies, uses Python's sqlite3
- **Performance**: ~1-2ms per operation
- **Data Integrity**: Automatic timestamps and validation

## Usage Examples

### From Stage 2 (After Admin Approval)

```python
from src.stage3.integrate import process_approved_reservation

# When admin approves a reservation
approved_reservation = {
    "reservation_id": "REQ-20260225100000-001",
    "user_name": "John Doe",
    "car_number": "ABC1234",
    "start_date": "2026-03-01",
    "end_date": "2026-03-07",
    "approval_time": "2026-02-25T10:00:00",
}

# Save to database
if process_approved_reservation(approved_reservation):
    print("✅ Saved to database!")
```

### Direct Storage Usage

```python
from src.stage3.storage import ReservationStorage

storage = ReservationStorage()

# Save a reservation
storage.save(reservation_dict)

# Get all reservations
all_reservations = storage.get_all()

# Get specific reservation by ID
reservation = storage.get_by_id("REQ-20260225100001-001")
```

## Architecture

**Data Flow:**

```
Stage 1: User queries parking info
    ↓
Stage 2: Admin approves reservation
    ↓
Stage 3: ✅ SAVE TO DATABASE
    ↓
data/reservations.db (ready for Stage 4)
```

## Module Structure

```
src/stage3/
├── storage.py        # ReservationStorage class - database management
├── integrate.py      # Integration with Stage 2
└── __init__.py       # Exports
```

## Database Schema

**File**: `data/reservations.db`

**Table: reservations**

```sql
CREATE TABLE reservations (
    id TEXT PRIMARY KEY,           # REQ-20260225100000-001
    user_name TEXT NOT NULL,       # John Doe
    car_number TEXT NOT NULL,      # ABC1234
    start_date TEXT NOT NULL,      # 2026-03-01
    end_date TEXT NOT NULL,        # 2026-03-07
    approved_at TEXT NOT NULL,     # 2026-02-25T10:00:00
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

## API Reference

### ReservationStorage Class

```python
from src.stage3.storage import ReservationStorage

storage = ReservationStorage()
```

**Methods:**

- `save(reservation: dict) -> bool` - Save a reservation to database
- `get_all() -> list[dict]` - Get all saved reservations
- `get_by_id(reservation_id: str) -> dict | None` - Get specific reservation
- `init_db() -> None` - Initialize database schema

### Integration Functions

```python
from src.stage3.integrate import process_approved_reservation
```

- `process_approved_reservation(reservation: dict) -> bool` - Process and save approved reservation from Stage 2

## Integration with Stage 2

In `src/stage2/chatbot_with_approval.py`, after admin approval:

```python
from src.stage3.integrate import process_approved_reservation

if approval_status == "approved":
    process_approved_reservation({
        "reservation_id": reservation_id,
        "user_name": user_name,
        "car_number": car_number,
        "start_date": start_date,
        "end_date": end_date,
        "approval_time": datetime.now().isoformat(),
    })
```

## Testing

```bash
# Run Stage 3 tests
pytest tests/test_stage3.py -v
```

**Tests Cover:**
- ✅ Database initialization
- ✅ Save reservations
- ✅ Retrieve reservations
- ✅ Data integrity and constraints
- ✅ Error handling
- ✅ Integration functions

## Advantages

✅ **Simple** - Minimal, focused implementation  
✅ **Reliable** - Thoroughly tested  
✅ **Zero Dependencies** - Uses built-in sqlite3 only  
✅ **Fast** - ~1-2ms per operation  
✅ **Stage 4 Ready** - LangGraph can leverage for orchestration  

## Next Steps

This is Stage 3 of a multi-stage project:
- [Stage 1: RAG Chatbot](STAGE1.md) (completed)
- [Stage 2: Human-in-the-loop approval workflow](STAGE2.md) (completed)
- **Stage 3: Persistent reservation storage** (current)
- [Stage 4: LangGraph Orchestration](STAGE4.md)

## Related Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Design Decisions
- [../readme.md](../readme.md) - Main Project README