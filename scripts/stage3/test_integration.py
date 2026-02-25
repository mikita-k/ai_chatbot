#!/usr/bin/env python
"""
Stage 3 - Sync Approved Reservations

Reads APPROVED reservations from Stage 2 (approvals.db)
and saves them to Stage 3 (reservations.db).

Usage:
    python scripts/stage3/test_integration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.stage3.integrate import (
    get_approved_from_stage2,
    sync_approved_to_stage3,
    get_all_approved_reservations
)


def main():
    """Sync approved reservations from Stage 2 to Stage 3."""
    print("\n" + "="*70)
    print("🎯 STAGE 3 - SYNC APPROVED RESERVATIONS FROM STAGE 2")
    print("="*70)

    # Step 1: Check what's approved in Stage 2
    print("\n📥 Reading APPROVED reservations from Stage 2...")
    print("   Source: data/dynamic/approvals.db\n")

    approved = get_approved_from_stage2()

    if not approved:
        print("ℹ️  No approved reservations found in Stage 2")
        print("\n📝 To create approvals:")
        print("   1. Run: python run_stage2.py")
        print("   2. Type: reserve")
        print("   3. Fill in the data")
        print("   4. In Telegram, send bot: approve REQ-xxx")
        print("   5. Then run this script again\n")
        return 1

    print(f"✅ Found {len(approved)} approved reservations:\n")
    for res in approved:
        print(f"   • {res['reservation_id']}: {res['user_name']} ({res['car_number']})")
        print(f"     {res['start_date']} → {res['end_date']}")

    # Step 2: Sync to Stage 3
    print("\n" + "="*70)
    print("💾 Syncing to Stage 3...")
    print("="*70 + "\n")

    synced = sync_approved_to_stage3()

    # Step 3: Show what's in Stage 3
    print("\n" + "="*70)
    print("📋 ALL RESERVATIONS IN STAGE 3 DATABASE:")
    print("="*70 + "\n")

    all_res = get_all_approved_reservations()
    if all_res:
        for i, res in enumerate(all_res, 1):
            print(f"{i}. {res['id']}")
            print(f"   User: {res['user_name']}")
            print(f"   Car: {res['car_number']}")
            print(f"   Period: {res['start_date']} → {res['end_date']}")
            print(f"   Approved: {res['approved_at']}")
            print()
    else:
        print("No reservations in Stage 3 yet.")

    print("="*70)
    if synced > 0:
        print(f"✅ Synced {synced} reservation(s)!")
    else:
        print("ℹ️  No new reservations to sync")
    print("   Source: data/dynamic/approvals.db")
    print("   Destination: data/reservations.db")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

