"""
Database module for Stage 2 LangChain - SQLite persistence layer
"""

import os
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ReservationRequest:
    """Represents a parking reservation request."""
    request_id: str
    name: str
    surname: str
    car_number: str
    period: str
    created_at: str
    status: str = "pending"  # pending, approved, rejected
    admin_response: str = ""
    response_time: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"Request #{self.request_id}\n"
            f"Name: {self.name} {self.surname}\n"
            f"Car: {self.car_number}\n"
            f"Period: {self.period}\n"
            f"Status: {self.status}"
        )


class AdminApprovalDatabase:
    """SQLite database for storing all requests and responses."""

    def __init__(self, db_path: str = "data/dynamic/approvals.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reservation_requests (
                    request_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL,
                    car_number TEXT NOT NULL,
                    period TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    admin_response TEXT,
                    response_time TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

    def save_request(self, request: ReservationRequest):
        """Save or update a reservation request."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO reservation_requests
                    (request_id, name, surname, car_number, period, created_at, status, admin_response, response_time, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.request_id,
                    request.name,
                    request.surname,
                    request.car_number,
                    request.period,
                    request.created_at,
                    request.status,
                    request.admin_response,
                    request.response_time,
                    datetime.now().isoformat()
                ))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            print(f"Error saving request: {e}")

    def get_request(self, request_id: str) -> Optional[ReservationRequest]:
        """Retrieve a request by ID."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            try:
                cursor = conn.execute(
                    "SELECT * FROM reservation_requests WHERE request_id = ?",
                    (request_id,)
                )
                row = cursor.fetchone()
                if row:
                    return ReservationRequest(
                        request_id=row[0],
                        name=row[1],
                        surname=row[2],
                        car_number=row[3],
                        period=row[4],
                        created_at=row[5],
                        status=row[6],
                        admin_response=row[7],
                        response_time=row[8]
                    )
                return None
            finally:
                conn.close()
        except Exception as e:
            print(f"Error retrieving request: {e}")
            return None

    def get_all_requests(self, status: Optional[str] = None) -> List[ReservationRequest]:
        """Get all requests, optionally filtered by status."""
        query = "SELECT * FROM reservation_requests"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        try:
            conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
            try:
                cursor = conn.execute(query, params)
                requests = []
                for row in cursor.fetchall():
                    requests.append(ReservationRequest(
                        request_id=row[0],
                        name=row[1],
                        surname=row[2],
                        car_number=row[3],
                        period=row[4],
                        created_at=row[5],
                        status=row[6],
                        admin_response=row[7],
                        response_time=row[8]
                    ))
                return requests
            finally:
                conn.close()
        except Exception as e:
            print(f"Error retrieving requests: {e}")
            return []

