"""
Stage 3: Simple Storage for Approved Reservations

Minimal implementation: just save approved reservations to SQLite.
No FastAPI, no over-engineering. Keep it simple.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ReservationStorage:
    """Simple SQLite storage for approved reservations."""

    def __init__(self, db_path: str = "data/reservations.db"):
        """Initialize storage."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create table if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id TEXT PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    car_number TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    approved_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save(self, reservation: Dict[str, Any]) -> bool:
        """Save approved reservation to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO reservations
                    (id, user_name, car_number, start_date, end_date, approved_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    reservation.get('reservation_id'),
                    reservation.get('user_name'),
                    reservation.get('car_number'),
                    reservation.get('start_date'),
                    reservation.get('end_date'),
                    reservation.get('approval_time', datetime.now().isoformat()),
                ))
                conn.commit()
            logger.info(f"✅ Saved: {reservation.get('reservation_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving reservation: {e}")
            return False

    def get_all(self) -> List[Dict[str, str]]:
        """Get all approved reservations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM reservations ORDER BY created_at DESC"
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching reservations: {e}")
            return []

    def get_by_id(self, res_id: str) -> Optional[Dict[str, str]]:
        """Get specific reservation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM reservations WHERE id = ?", (res_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching reservation: {e}")
            return None


