import sqlite3
from datetime import datetime
from pathlib import Path

# Path to database
DB_PATH = Path(__file__).parent / "parking.db"


def init_db():
    """Initialize parking database with dynamic data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create parking_spaces table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_spaces (
        id INTEGER PRIMARY KEY,
        space_number TEXT UNIQUE NOT NULL,
        is_available BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create pricing table (dynamic pricing based on time)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pricing (
        id INTEGER PRIMARY KEY,
        time_period TEXT NOT NULL,
        hourly_rate REAL NOT NULL,
        daily_max REAL NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create availability_schedule table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS availability_schedule (
        id INTEGER PRIMARY KEY,
        day_of_week TEXT NOT NULL,
        opening_time TEXT NOT NULL,
        closing_time TEXT NOT NULL
    )
    """)

    # Insert sample parking spaces
    sample_spaces = [
        ("A1",), ("A2",), ("A3",), ("A4",), ("A5",),
        ("B1",), ("B2",), ("B3",), ("B4",), ("B5",),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO parking_spaces (space_number, is_available) VALUES (?, 1)",
        sample_spaces
    )

    # Insert sample pricing (standard rate)
    cursor.executemany(
        """INSERT OR IGNORE INTO pricing (time_period, hourly_rate, daily_max) 
           VALUES (?, ?, ?)""",
        [
            ("standard", 2.0, 20.0),
            ("peak_hours", 3.0, 25.0),
            ("night", 1.0, 15.0),
        ]
    )

    # Insert sample schedule
    schedule = [
        ("Monday", "07:00", "22:00"),
        ("Tuesday", "07:00", "22:00"),
        ("Wednesday", "07:00", "22:00"),
        ("Thursday", "07:00", "22:00"),
        ("Friday", "07:00", "23:00"),
        ("Saturday", "08:00", "23:00"),
        ("Sunday", "09:00", "21:00"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO availability_schedule (day_of_week, opening_time, closing_time) VALUES (?, ?, ?)",
        schedule
    )

    conn.commit()
    conn.close()


def get_available_spaces() -> int:
    """Get number of currently available parking spaces."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM parking_spaces WHERE is_available = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_spaces():
    """Get all parking spaces with availability status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT space_number, is_available FROM parking_spaces ORDER BY space_number")
    spaces = cursor.fetchall()
    conn.close()
    return spaces


def book_space(space_number: str) -> bool:
    """Book a parking space (mark as unavailable)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE parking_spaces SET is_available = 0 WHERE space_number = ?",
            (space_number,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def release_space(space_number: str) -> bool:
    """Release a parking space (mark as available)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE parking_spaces SET is_available = 1 WHERE space_number = ?",
            (space_number,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_current_pricing() -> dict:
    """Get current pricing based on time of day."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # For simplicity, return standard pricing (can be extended to check time)
    cursor.execute(
        "SELECT time_period, hourly_rate, daily_max FROM pricing WHERE time_period = 'standard'"
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "period": row[0],
            "hourly_rate": row[1],
            "daily_max": row[2],
        }
    return {"period": "standard", "hourly_rate": 2.0, "daily_max": 20.0}


def get_opening_hours():
    """Get opening hours for today."""
    import datetime as dt

    today = dt.datetime.now().strftime("%A")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT opening_time, closing_time FROM availability_schedule WHERE day_of_week = ?",
        (today,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"opening": row[0], "closing": row[1]}
    return {"opening": "07:00", "closing": "22:00"}


def get_availability_summary() -> str:
    """Get a human-readable availability summary."""
    available = get_available_spaces()
    total = len(get_all_spaces())
    occupied = total - available

    return (
        f"Current Availability: {available}/{total} spaces available\n"
        f"Occupied: {occupied} spaces\n"
        f"Occupancy Rate: {(occupied/total)*100:.1f}%"
    )


if __name__ == "__main__":
    init_db()
    print("Database initialized!")
    print(get_availability_summary())
    print("\nCurrent Pricing:", get_current_pricing())
    print("Opening Hours Today:", get_opening_hours())

