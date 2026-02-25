# Stage 3 Scripts

## test_integration.py

Синхронизирует ОДОБРЕННЫЕ резервации из Stage 2 в Stage 3.

### Как это работает

```
Stage 2 (approvals.db)          Stage 3 (reservations.db)
├─ REQ-xxx (approved)     ──→   ├─ REQ-xxx (сохранено)
├─ REQ-yyy (rejected)           └─ Только approved!
└─ REQ-zzz (pending)
```

**Важно:** Stage 3 сохраняет **только одобренные** резервации. Отклонённые и ожидающие не сохраняются.

### Пошаговый процесс

**Шаг 1: Создать одобренную резервацию в Stage 2**

```powershell
# Терминал 1
python run_stage2.py

You: reserve
Name: Иван Иванов
Car: ABC1234
Period: 2026-02-26 10:00 - 12:00

# Терминал 2
python run_telegram_bot.py

# В Telegram админу пришло уведомление
# Админ пишет: approve REQ-20260225100001-001

# В Терминал 1
✅ APPROVED!
```

**Шаг 2: Синхронизировать в Stage 3**

```powershell
# Терминал 3
python scripts/stage3/test_integration.py
```

Результат:
```
📥 Reading APPROVED reservations from Stage 2...
   Source: data/dynamic/approvals.db

✅ Found 1 approved reservations:
   • REQ-20260225100001-001: Иван Иванов (ABC1234)
     2026-02-26 → 2026-02-26

💾 Syncing to Stage 3...
✅ Synced: REQ-20260225100001-001 - Иван Иванов

📋 ALL RESERVATIONS IN STAGE 3 DATABASE:
1. REQ-20260225100001-001
   User: Иван Иванов
   Car: ABC1234
   Period: 2026-02-26 → 2026-02-26
   Approved: 2026-02-25T10:15:30.123456
```

## Архитектура

```
Stage 2 (approvals.db)
    └─ Вместо pending/approved/rejected
    
    ↓ Stage 3 читает (статус = approved)
    
Stage 3 (reservations.db)
    └─ Долгосрочное хранилище одобренных
```

## Базы данных

**Stage 2 (approvals.db):**
```
reservation_requests
├─ request_id
├─ user_name
├─ car_number
├─ start_date, end_date
├─ status (pending/approved/rejected)
└─ response_time
```

**Stage 3 (reservations.db):**
```
reservations
├─ id (reservation_id)
├─ user_name
├─ car_number
├─ start_date, end_date
├─ approved_at
└─ created_at
```

## Использование в коде

```python
from src.stage3.integrate import (
    get_approved_from_stage2,      # Читать из Stage 2
    sync_approved_to_stage3,        # Синхронизировать
    get_all_approved_reservations,  # Получить все из Stage 3
    get_reservation                 # Получить одну по ID
)

# Синхронизировать
synced_count = sync_approved_to_stage3()

# Получить все
all_reservations = get_all_approved_reservations()

# Получить одну
res = get_reservation("REQ-20260225100001-001")
```



