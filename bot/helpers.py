import math
from datetime import datetime


def format_timestamp(ms_timestamp: int) -> str:
    """Converts a millisecond timestamp into a human-readable local time string."""
    try:
        return datetime.fromtimestamp(ms_timestamp / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def round_to_step(value: float, step_size: float) -> float:
    """Rounds a value to the precision determined by the step size (e.g. tick size or lot step size)."""
    if step_size <= 0:
        return value
    precision = int(round(-math.log10(step_size)))
    return round(math.floor(value / step_size) * step_size, precision)
