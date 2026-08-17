from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


class InvalidBookingInterval(ValueError):
    """Raised when a booking interval cannot represent a valid reservation."""


@dataclass(frozen=True, slots=True)
class OccupiedInterval:
    start: datetime
    end: datetime


def occupied_interval(
    starts_at: datetime,
    ends_at: datetime,
    buffer_before_min: int = 0,
    buffer_after_min: int = 0,
) -> OccupiedInterval:
    """Return the full resource-occupancy interval for a booking.

    The returned interval includes setup and cleanup buffers. Inputs must be
    timezone-aware, end strictly after start, and use non-negative buffers.
    """
    _ensure_aware(starts_at, "starts_at")
    _ensure_aware(ends_at, "ends_at")

    if ends_at <= starts_at:
        raise InvalidBookingInterval("ends_at must be strictly later than starts_at")
    if buffer_before_min < 0 or buffer_after_min < 0:
        raise InvalidBookingInterval("buffers cannot be negative")

    return OccupiedInterval(
        start=starts_at - timedelta(minutes=buffer_before_min),
        end=ends_at + timedelta(minutes=buffer_after_min),
    )


def _ensure_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidBookingInterval(f"{field_name} must include a timezone offset")
