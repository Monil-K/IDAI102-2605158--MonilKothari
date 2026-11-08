"""MedTimer — a daily medicine companion built with Streamlit.

The package is split so the domain rules stay testable without Streamlit:

    models        domain model, status rules and adherence maths
    state         session store plus JSON persistence
    components    reusable HTML/SVG presentation helpers
    styles        the whole design system as one CSS source
    turtle_graphics  turtle pen primitives that render to SVG
"""

from medtimer.models import (
    GRACE_MINUTES,
    AppState,
    Medicine,
    Status,
    add_medicine,
    delete_medicine,
    mark_taken,
    record_today,
    reset_day,
    streak,
    today_adherence,
    trend,
    undo_taken,
    update_medicine,
    weekly_average,
)

__all__ = [
    "GRACE_MINUTES",
    "AppState",
    "Medicine",
    "Status",
    "add_medicine",
    "delete_medicine",
    "mark_taken",
    "record_today",
    "reset_day",
    "streak",
    "today_adherence",
    "trend",
    "undo_taken",
    "update_medicine",
    "weekly_average",
]

__version__ = "2.2.0"
