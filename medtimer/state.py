"""Session state plus a tiny JSON store for the MedTimer application.

Why a file? Streamlit keeps ``st.session_state`` per browser session, so a page
refresh used to wipe the day's ticks — and that made the 7-day average and the
streak meaningless, because the recorded history never outlived the session.

The whole :class:`~medtimer.models.AppState` is serialised to
``data/medtimer.json`` after every change, so the medicine list, today's ticks
(with their logged times) and the week's history survive a reload. Writes are
atomic (temp file + replace) and best-effort: a read-only filesystem must never
take the app down.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import streamlit as st

from medtimer.models import AppState, add_medicine, reset_day

_STATE_KEY = "medtimer.state"
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_STATE_FILE = _DATA_DIR / "medtimer.json"

# Realistic demo data so a first-time visitor sees a populated dashboard.
SAMPLE_MEDICINES: tuple[tuple[str, int, int], ...] = (
    ("Metformin 500 mg", 8, 0),
    ("Lisinopril 10 mg", 8, 30),
    ("Atorvastatin 20 mg", 20, 0),
)


def _seed() -> AppState:
    state = AppState()
    for name, hour, minute in SAMPLE_MEDICINES:
        add_medicine(state, name, hour, minute)
    return state


def _load() -> AppState | None:
    """Read the saved session, or ``None`` when there is nothing usable yet."""
    try:
        raw = _STATE_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError):
        return None
    return AppState.from_dict(data) if isinstance(data, dict) else None


def save_state(state: AppState) -> None:
    """Write the session to disk after a change (best effort, never raises)."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp = _STATE_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
        temp.replace(_STATE_FILE)
    except OSError:
        # Read-only disk (or a locked file): the app keeps working in memory.
        pass


def get_state() -> AppState:
    """Return this session's state, restoring it from disk on a fresh session."""
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = _load() or _seed()

    state: AppState = st.session_state[_STATE_KEY]

    today = date.today()
    if state.last_active < today:
        # A new day: clear the ticks, keep the medicine list and the history.
        reset_day(state)
        state.last_active = today
        save_state(state)

    return state


def clear_state() -> None:
    """Drop the session and the saved file (used by the reset action)."""
    st.session_state.pop(_STATE_KEY, None)
    try:
        _STATE_FILE.unlink()
    except OSError:
        pass
