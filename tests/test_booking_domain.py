from datetime import UTC, datetime

import pytest

from app.domain.booking import InvalidBookingInterval, occupied_interval


def test_occupied_interval_includes_buffers() -> None:
    starts_at = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    ends_at = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    interval = occupied_interval(starts_at, ends_at, buffer_before_min=15, buffer_after_min=30)

    assert interval.start == datetime(2026, 9, 1, 9, 45, tzinfo=UTC)
    assert interval.end == datetime(2026, 9, 1, 12, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    ("starts_at", "ends_at"),
    [
        (
            datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        ),
        (
            datetime(2026, 9, 1, 11, 0, tzinfo=UTC),
            datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        ),
    ],
)
def test_occupied_interval_rejects_non_positive_duration(
    starts_at: datetime, ends_at: datetime
) -> None:
    with pytest.raises(InvalidBookingInterval, match="strictly later"):
        occupied_interval(starts_at, ends_at)


def test_occupied_interval_rejects_naive_datetime() -> None:
    with pytest.raises(InvalidBookingInterval, match="timezone"):
        occupied_interval(
            datetime(2026, 9, 1, 10, 0),
            datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
        )


def test_occupied_interval_rejects_negative_buffer() -> None:
    with pytest.raises(InvalidBookingInterval, match="cannot be negative"):
        occupied_interval(
            datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
            buffer_before_min=-1,
        )
