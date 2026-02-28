#!/usr/bin/env python
"""
Stage 3: View Reservations Database

Debug script to check what reservations are currently stored in the database.

Usage:
    python scripts/stage3/view_db.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.stage3.storage import ReservationStorage

def main():
    print("\n" + "="*70)
    print("📋 STAGE 3: View Approved Reservations")
    print("="*70)

    storage = ReservationStorage()

    print(f"\n📁 Database: {storage.db_path}")

    reservations = storage.get_all()

    if not reservations:
        print("\n❌ No reservations found in database")
        return

    print(f"\n✅ Found {len(reservations)} reservation(s):\n")

    for i, res in enumerate(reservations, 1):
        print(f"{i}. ID: {res.get('id')}")
        print(f"   User: {res.get('user_name')}")
        print(f"   Car: {res.get('car_number')}")
        print(f"   Period: {res.get('start_date')} → {res.get('end_date')}")
        print(f"   Approved: {res.get('approved_at')}")
        print(f"   Created: {res.get('created_at')}")
        print()

if __name__ == "__main__":
    main()

