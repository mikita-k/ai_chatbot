"""
Shared reservation parsing logic for Stage 2 and Stage 4.

Extracts name, surname, car number, and dates from reservation requests.
Supports both Russian and English formats.
"""

import re
from typing import Optional, Dict, Tuple


MONTHS = {
    'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
    'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
    'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12',
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12'
}


def parse_reservation(user_message: str) -> Optional[Dict[str, str]]:
    """
    Parse reservation details from user input.

    Format: reserve <Name> <Surname> <CarNumber> <DateRange>

    Returns:
        Dict with keys: name, surname, car_number, period
        None if parsing failed
    """
    user_message = user_message.strip()
    user_message_lower = user_message.lower()

    # Check if starts with "reserve"
    if not user_message_lower.startswith("reserve"):
        return None

    reservation_text = user_message[8:].strip()  # Remove "reserve "

    # Check if has dates
    has_dates = (
        " с " in reservation_text.lower() or
        " from " in reservation_text.lower() or
        " от " in reservation_text.lower()
    )

    if not has_dates:
        return None  # No dates found, can't parse

    # Try to parse dates and extract details
    name, surname, car_number = None, None, None
    start_date, end_date = None, None

    # Format 1 - Russian FULL: "с 20 марта 2026 по 21 апреля 2027"
    m = re.search(r'с\s+(\d+)\s+(\S+)\s+(\d{4})\s+по\s+(\d+)\s+(\S+)\s+(\d{4})', reservation_text.lower())
    if m:
        d1, m1_str, y1, d2, m2_str, y2 = m.groups()
        m1_num = MONTHS.get(m1_str, '02')
        m2_num = MONTHS.get(m2_str, '02')
        start_date = f"{y1}-{m1_num}-{d1.zfill(2)}"
        end_date = f"{y2}-{m2_num}-{d2.zfill(2)}"

    # Format 2 - Russian SHORT: "с 5 по 12 июля 2026" (same month)
    if not start_date:
        m = re.search(r'с\s+(\d+)\s+по\s+(\d+)\s+(\S+)\s+(\d{4})', reservation_text.lower())
        if m:
            d1, d2, month_str, year = m.groups()
            month_num = MONTHS.get(month_str, '02')
            start_date = f"{year}-{month_num}-{d1.zfill(2)}"
            end_date = f"{year}-{month_num}-{d2.zfill(2)}"

    # Format 3 - English FULL: "from 20 march 2026 to 21 april 2027"
    if not start_date:
        m = re.search(r'from\s+(\d+)\s+(\S+)\s+(\d{4})\s+to\s+(\d+)\s+(\S+)\s+(\d{4})', reservation_text.lower())
        if m:
            d1, m1_str, y1, d2, m2_str, y2 = m.groups()
            m1_num = MONTHS.get(m1_str, '02')
            m2_num = MONTHS.get(m2_str, '02')
            start_date = f"{y1}-{m1_num}-{d1.zfill(2)}"
            end_date = f"{y2}-{m2_num}-{d2.zfill(2)}"

    # Format 4 - English SHORT: "from 5 march to 12 march 2026" (same month)
    if not start_date:
        m = re.search(r'from\s+(\d+)\s+(\S+)\s+to\s+(\d+)\s+(\S+)\s+(\d{4})', reservation_text.lower())
        if m:
            d1, m1_str, d2, m2_str, year = m.groups()
            m1_num = MONTHS.get(m1_str, '02')
            m2_num = MONTHS.get(m2_str, '02')
            start_date = f"{year}-{m1_num}-{d1.zfill(2)}"
            end_date = f"{year}-{m2_num}-{d2.zfill(2)}"

    if not start_date:
        return None  # Could not parse dates

    # Extract name, surname, car
    name_match = re.search(
        r'reserve\s+(\S+)\s+(\S+)\s+([A-Za-z0-9\-]+)',
        user_message,
        re.IGNORECASE | re.UNICODE
    )

    if name_match:
        name = name_match.group(1).capitalize()
        surname = name_match.group(2).capitalize()
        car_number = name_match.group(3).upper()

    if not name or not surname or not car_number:
        return None  # Could not extract all required fields

    period = f"{start_date} 10:00 - {end_date} 12:00"

    return {
        "name": name,
        "surname": surname,
        "car_number": car_number,
        "period": period
    }

