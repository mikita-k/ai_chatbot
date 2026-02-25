"""
Stage 3: Save Approved Reservations to Database

Simple integration that stores admin-approved parking reservations in SQLite.
"""

from .storage import ReservationStorage
from .integrate import process_approved_reservation, get_all_approved_reservations, get_reservation

__all__ = [
    "ReservationStorage",
    "process_approved_reservation",
    "get_all_approved_reservations",
    "get_reservation",
]
__version__ = "1.0.0"

