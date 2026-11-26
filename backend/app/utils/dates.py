import re
from datetime import datetime, timedelta
from typing import Optional

def normalize_relative_deadline(deadline_str: Optional[str], reference_date: Optional[datetime] = None) -> Optional[str]:
    """
    Normalizes human relative deadlines (e.g. 'tomorrow', 'next week', 'by friday')
    into standardized, actionable deadline annotations while preserving original phrasing.
    """
    if not deadline_str:
        return None

    clean = deadline_str.strip().lower()
    now = reference_date or datetime.now()

    # Tomorrow / next day
    if "tomorrow" in clean:
        target = now + timedelta(days=1)
        return f"{deadline_str} ({target.strftime('%Y-%m-%d')})"

    # Today / this afternoon / later today
    if "today" in clean or "afternoon" in clean or "tonight" in clean or "end of the day" in clean or "eod" in clean:
        return f"{deadline_str} ({now.strftime('%Y-%m-%d')})"

    # In X hours / days
    hour_match = re.search(r'in\s+(\d+)\s+hour', clean)
    if hour_match:
        hrs = int(hour_match.group(1))
        target = now + timedelta(hours=hrs)
        return f"{deadline_str} ({target.strftime('%Y-%m-%d %H:%M')})"

    # Next week
    if "next week" in clean:
        target = now + timedelta(days=7)
        return f"{deadline_str} (approx. {target.strftime('%Y-%m-%d')})"

    # Specific weekday (e.g. by friday, on monday)
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for day_name, day_num in weekdays.items():
        if day_name in clean:
            days_ahead = (day_num - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = now + timedelta(days=days_ahead)
            return f"{deadline_str} ({target.strftime('%Y-%m-%d')})"

    return deadline_str
