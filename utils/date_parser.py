from datetime import datetime
from typing import Optional


def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None