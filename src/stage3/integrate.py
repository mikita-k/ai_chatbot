"""
Stage 3: Integration with Stage 2

Reads approved reservations from Stage 2 (approvals.db) and saves to Stage 3 (reservations.db).
"""

import sqlite3
from src.stage3.storage import ReservationStorage


def get_approved_from_stage2() -> list:
    """
    Read APPROVED reservations from Stage 2 database.

    Returns:
        List of approved reservation dicts from approvals.db
    """
    try:
        conn = sqlite3.connect("data/dynamic/approvals.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all APPROVED requests from Stage 2
        cursor.execute("""
            SELECT 
                request_id as reservation_id,
                (name || ' ' || surname) as user_name,
                car_number,
                period,
                response_time as approval_time,
                created_at
            FROM reservation_requests
            WHERE status = 'approved'
        """)

        rows = cursor.fetchall()
        conn.close()

        # Parse period into start_date and end_date
        result = []
        for row in rows:
            row_dict = dict(row)
            # Period format: "2026-02-26 10:00 - 2026-02-26 12:00"
            try:
                period_parts = row_dict['period'].split(' - ')
                start_part = period_parts[0].strip()  # "2026-02-26 10:00"
                end_part = period_parts[1].strip() if len(period_parts) > 1 else start_part  # "2026-02-26 12:00"

                start_date = start_part.split()[0]  # "2026-02-26"
                end_date = end_part.split()[0]  # "2026-02-26"
            except:
                start_date = row_dict['period']
                end_date = row_dict['period']

            row_dict['start_date'] = start_date
            row_dict['end_date'] = end_date
            row_dict.pop('period', None)  # Remove period field

            result.append(row_dict)

        return result
    except Exception as e:
        print(f"❌ Error reading from Stage 2 DB: {e}")
        return []


def process_approved_reservation(reservation: dict) -> bool:
    """
    Save a single approved reservation to Stage 3 database.

    Args:
        reservation: Dict with keys from Stage 2:
            - reservation_id: Unique ID
            - user_name: Customer name
            - car_number: Vehicle registration
            - start_date: YYYY-MM-DD
            - end_date: YYYY-MM-DD
            - approval_time: When admin approved

    Returns:
        True if saved successfully
    """
    storage = ReservationStorage()
    return storage.save(reservation)


def sync_approved_to_stage3() -> int:
    """
    Sync all APPROVED reservations from Stage 2 to Stage 3.

    Returns:
        Number of reservations synced
    """
    # Get approved from Stage 2
    approved = get_approved_from_stage2()

    if not approved:
        print("ℹ️  No approved reservations in Stage 2")
        return 0

    # Save each to Stage 3
    synced = 0
    for res in approved:
        if process_approved_reservation(res):
            synced += 1
            print(f"✅ Synced: {res['reservation_id']} - {res['user_name']}")
        else:
            print(f"❌ Failed: {res['reservation_id']}")

    return synced


def get_all_approved_reservations() -> list:
    """Get all approved reservations from Stage 3 database."""
    storage = ReservationStorage()
    return storage.get_all()


def get_reservation(res_id: str) -> dict:
    """Get specific reservation by ID from Stage 3."""
    storage = ReservationStorage()
    return storage.get_by_id(res_id)


