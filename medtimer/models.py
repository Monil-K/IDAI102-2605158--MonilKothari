"""Domain model for MedTimer.

This module is deliberately free of any Streamlit dependency so the
business rules can be unit-tested in isolation (see ``tests/test_core.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Iterable
from uuid import uuid4

#: Minutes after the scheduled time before a dose counts as missed.
GRACE_MINUTES = 30


class Status(str, Enum):
    """Colour-coded state of a scheduled dose."""

    TAKEN = "taken"
    UPCOMING = "upcoming"
    MISSED = "missed"

    @property
    def label(self) -> str:
        return {
            Status.TAKEN: "Taken",
            Status.UPCOMING: "Upcoming",
            Status.MISSED: "Missed",
        }[self]

    @property
    def tone(self) -> str:
        """CSS modifier used by the presentation layer."""
        return {
            Status.TAKEN: "ok",
            Status.UPCOMING: "warn",
            Status.MISSED: "danger",
        }[self]


@dataclass
class Medicine:
    """A single recurring daily medication."""

    name: str
    hour: int
    minute: int
    uid: str = field(default_factory=lambda: uuid4().hex[:8])
    #: When today's dose was logged; ``None`` means "not taken yet".
    taken_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("A medicine needs a name.")
        if not (0 <= self.hour <= 23 and 0 <= self.minute <= 59):
            raise ValueError("Hour must be 0-23 and minute must be 0-59.")

    @property
    def taken(self) -> bool:
        """True once today's dose has been logged."""
        return self.taken_at is not None

    @taken.setter
    def taken(self, value: bool) -> None:
        """``med.taken = True`` logs the dose at the current time."""
        self.taken_at = datetime.now() if value else None

    @property
    def scheduled(self) -> time:
        return time(hour=self.hour, minute=self.minute)

    def scheduled_on(self, day: date) -> datetime:
        return datetime.combine(day, self.scheduled)

    def status(self, now: datetime | None = None) -> Status:
        """Return the dose status relative to ``now``.

        A dose is *not* missed the instant its minute arrives: the user gets
        ``GRACE_MINUTES`` to take it, and until then it stays upcoming (shown
        as "due now" or "N min overdue"). Marking it missed on the first
        second would punish a little clock drift and read as a false alarm.
        """
        now = now or datetime.now()
        if self.taken:
            return Status.TAKEN
        due = self.scheduled_on(now.date())
        if now < due + timedelta(minutes=GRACE_MINUTES):
            return Status.UPCOMING
        return Status.MISSED

    def minutes_until(self, now: datetime | None = None) -> int:
        """Whole minutes until this dose's next occurrence from *now*.

        For an untaken dose whose scheduled time today has already passed, the
        result is negative ("overdue by N minutes"). For a dose still upcoming
        today, the result is positive ("in N minutes"). A dose already logged
        today this is not the next dose and ``next_dose`` will skip it.
        """
        now = now or datetime.now()
        today_due = self.scheduled_on(now.date())
        if now < today_due:
            return int((today_due - now).total_seconds() // 60)
        # Today's scheduled time already passed. If the dose is still untaken,
        # report it as overdue (negative) — the card/user needs to know how late
        # this specific dose is, not when tomorrow's copy runs.
        if not self.taken:
            return int((today_due - now).total_seconds() // 60)
        # Dose already logged today: the next occurrence is tomorrow's.
        tomorrow_due = self.scheduled_on(now.date() + timedelta(days=1))
        return int((tomorrow_due - now).total_seconds() // 60)

    # -- storage -------------------------------------------------------
    def to_dict(self) -> dict[str, object]:
        """Plain-data form, so a session can be written to disk as JSON."""
        return {
            "uid": self.uid,
            "name": self.name,
            "hour": self.hour,
            "minute": self.minute,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Medicine":
        """Rebuild a medicine from :meth:`to_dict` output.

        Raises ``ValueError``/``KeyError``/``TypeError`` on malformed input so
        the caller can skip a single bad record instead of losing the file.
        """
        taken_at = data.get("taken_at")
        return cls(
            name=str(data["name"]),
            hour=int(data["hour"]),
            minute=int(data["minute"]),
            uid=str(data.get("uid") or uuid4().hex[:8]),
            taken_at=datetime.fromisoformat(taken_at) if taken_at else None,
        )


@dataclass
class AppState:
    """Everything the application needs to render one session."""

    medicines: list[Medicine] = field(default_factory=list)
    history: dict[date, float] = field(default_factory=dict)
    last_active: date = field(default_factory=date.today)

    # -- lookups -------------------------------------------------------
    def find(self, uid: str) -> Medicine | None:
        return next((m for m in self.medicines if m.uid == uid), None)

    @property
    def sorted_medicines(self) -> list[Medicine]:
        return sorted(self.medicines, key=lambda m: (m.hour, m.minute))

    @property
    def doses_taken(self) -> int:
        return sum(1 for m in self.medicines if m.taken)

    def next_dose(self, now: datetime | None = None) -> Medicine | None:
        """Earliest dose still to be taken today, or ``None`` when all are logged.

        Overdue doses stay here on purpose: the live strip should say "overdue"
        rather than claim the day is finished.
        """
        now = now or datetime.now()
        pending = [m for m in self.medicines if not m.taken]
        return min(pending, key=lambda m: (m.hour, m.minute), default=None)

    def to_dict(self) -> dict[str, object]:
        """Plain-data form of the whole session, ready for ``json.dumps``."""
        return {
            "medicines": [medicine.to_dict() for medicine in self.medicines],
            "history": {day.isoformat(): value for day, value in self.history.items()},
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppState":
        """Restore a session, skipping records that cannot be read."""
        state = cls()
        for item in data.get("medicines") or []:
            try:
                state.medicines.append(Medicine.from_dict(item))
            except (AttributeError, KeyError, TypeError, ValueError):
                continue

        history: dict[date, float] = {}
        for raw_day, raw_value in (data.get("history") or {}).items():
            try:
                history[date.fromisoformat(raw_day)] = float(raw_value)
            except (TypeError, ValueError):
                continue
        state.history = history

        try:
            state.last_active = date.fromisoformat(data["last_active"])
        except (KeyError, TypeError, ValueError):
            state.last_active = date.today()
        return state


# ---------------------------------------------------------------------------
# Mutations — every function takes the state it acts on and returns it
# ---------------------------------------------------------------------------
def add_medicine(state: AppState, name: str, hour: int, minute: int) -> Medicine:
    medicine = Medicine(name=name, hour=hour, minute=minute)
    state.medicines.append(medicine)
    return medicine


def update_medicine(
    state: AppState,
    uid: str,
    *,
    name: str | None = None,
    hour: int | None = None,
    minute: int | None = None,
) -> bool:
    medicine = state.find(uid)
    if medicine is None:
        return False
    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("A medicine needs a name.")
        medicine.name = cleaned
    if hour is not None:
        medicine.hour = hour
    if minute is not None:
        medicine.minute = minute
    return True


def delete_medicine(state: AppState, uid: str) -> bool:
    before = len(state.medicines)
    state.medicines = [m for m in state.medicines if m.uid != uid]
    return len(state.medicines) < before


def mark_taken(state: AppState, uid: str, at: datetime | None = None) -> bool:
    """Log a dose, remembering *when* it was logged (early, on time or late)."""
    medicine = state.find(uid)
    if medicine is None:
        return False
    medicine.taken_at = at or datetime.now()
    return True


def undo_taken(state: AppState, uid: str) -> bool:
    """Clear a mistaken tick so the dose can be logged again."""
    medicine = state.find(uid)
    if medicine is None or not medicine.taken:
        return False
    medicine.taken_at = None
    return True


def reset_day(state: AppState) -> None:
    """Clear today's ticks while keeping the medicine list."""
    for medicine in state.medicines:
        medicine.taken_at = None


# ---------------------------------------------------------------------------
# Adherence maths
# ---------------------------------------------------------------------------
def today_adherence(state: AppState) -> float:
    """Percentage of today's doses that have been taken."""
    if not state.medicines:
        return 0.0
    return round(state.doses_taken / len(state.medicines) * 100, 1)


def record_today(state: AppState, day: date | None = None) -> None:
    """Store today's snapshot so weekly figures and streaks can use it."""
    day = day or date.today()
    if state.medicines:
        state.history[day] = today_adherence(state)


def weekly_average(state: AppState, day: date | None = None) -> float:
    """Mean adherence across the last seven recorded days (today included)."""
    day = day or date.today()
    window: Iterable[date] = (day - timedelta(days=offset) for offset in range(7))
    values = [state.history[d] for d in window if d in state.history]
    return round(sum(values) / len(values), 1) if values else 0.0


def streak(state: AppState, day: date | None = None) -> int:
    """Consecutive days, ending today, with 100% adherence."""
    day = day or date.today()
    count = 0
    cursor = day
    while state.history.get(cursor, 0.0) >= 100.0:
        count += 1
        cursor -= timedelta(days=1)
    return count


def trend(state: AppState, days: int = 7, day: date | None = None) -> list[tuple[date, float]]:
    """Chronological (date, percentage) pairs for the weekly chart."""
    day = day or date.today()
    return [
        (d, state.history[d])
        for d in sorted(state.history)
        if day - timedelta(days=days - 1) <= d <= day
    ]
