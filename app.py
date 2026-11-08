"""MedTimer — Daily Medicine Companion.

Scenario 2 of the IDAI102 Python Programming summative assessment.

Run locally with::

    streamlit run app.py
"""

from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

from medtimer.components import (
    art,
    bar_card,
    clock_strip,
    dose_row,
    empty_state,
    fmt_clock,
    fmt_time,
    footer,
    hero,
    inject_styles,
    legend,
    note,
    quote,
    ring_card,
    section,
    week_bars,
)
from medtimer.models import (
    AppState,
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
from medtimer.state import get_state, save_state
from medtimer.turtle_graphics import smiley_svg, trophy_svg

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MedTimer — Daily Medicine Companion",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Read the theme before anything renders so the stylesheet matches the control.
# `?theme=dark` in the URL is honoured too, as a fallback.
_default_mode = "Dark" if st.query_params.get("theme") == "dark" else "Light"
_mode = st.session_state.get("medtimer.mode", _default_mode)
dark = _mode == "Dark"
inject_styles(dark)



def daily_tip(state: AppState, now: datetime) -> str:
    """A motivational tip that responds to the day, rather than a fixed quote.

    The brief asks for motivational tips; a line that ignores the user's actual
    situation reads as decoration. This one changes with what is left to do.
    """
    if not state.medicines:
        return "Add your first medicine above — it takes ten seconds and the plan fills itself in."

    statuses = [medicine.status(now) for medicine in state.medicines]
    remaining = len(statuses) - state.doses_taken

    if all(status is Status.TAKEN for status in statuses):
        return "Every dose is logged. Rest easy — tomorrow starts with a clean page."
    if any(status is Status.MISSED for status in statuses):
        return (
            "A dose slipped past its time. That is not a failure — "
            "log it now and today still counts."
        )
    if state.doses_taken:
        return f"{state.doses_taken} done, {remaining} to go. Steady is enough."
    return "Nothing logged yet. Start with the dose closest to now."


# ---------------------------------------------------------------------------
# Live regions
# ---------------------------------------------------------------------------
# Streamlit only recomputes on a rerun, so anything time-dependent lives in a
# fragment with `run_every`. The clock ticks every second and the checklist
# re-reads the wall clock every 30 seconds, so a dose becomes due or missed on
# its own while the page is left open — no clicking to "refresh" the time.
@st.fragment(run_every=1.0)
def live_clock(state: AppState) -> None:
    current = datetime.now()
    if current.date() > state.last_active:
        # Midnight passed while the page was left open. A full rerun runs
        # get_state(), which clears the ticks and records the new day.
        st.rerun(scope="app")
    st.markdown(clock_strip(current, state.next_dose(current)), unsafe_allow_html=True)


@st.fragment(run_every=30.0)
def live_plan(state: AppState) -> None:
    current = datetime.now()
    for medicine in state.sorted_medicines:
        status = medicine.status(current)
        with st.container(border=True):
            st.markdown(dose_row(medicine, status, current), unsafe_allow_html=True)

            b1, b2, b3 = st.columns([2.5, 1, 0.9], vertical_alignment="center")

            with b1:
                if status is Status.TAKEN:
                    # Shows *when* it was logged, plus an undo for a mis-tap.
                    logged_at = fmt_clock(medicine.taken_at)
                    done_col, undo_col = st.columns(
                        [2.1, 1], vertical_alignment="center"
                    )
                    with done_col:
                        st.button(
                            f"Taken at {logged_at}" if logged_at else "Dose logged",
                            key=f"logged-{medicine.uid}",
                            disabled=True,
                            use_container_width=True,
                        )
                    with undo_col:
                        if st.button(
                            "Undo",
                            key=f"undo-{medicine.uid}",
                            use_container_width=True,
                            help="Tapped by mistake? This clears the tick.",
                        ):
                            undo_taken(state, medicine.uid)
                            save_state(state)
                            st.session_state["medtimer.flash"] = (
                                f"{medicine.name} unchecked"
                            )
                            st.rerun(scope="app")
                elif st.button(
                    "Mark as taken",
                    key=f"take-{medicine.uid}",
                    type="primary",
                    use_container_width=True,
                ):
                    mark_taken(state, medicine.uid)
                    save_state(state)
                    st.session_state["medtimer.flash"] = (
                        f"{medicine.name} logged at {fmt_clock(medicine.taken_at)}"
                    )
                    st.rerun(scope="app")

            with b2:
                with st.popover("Edit", use_container_width=True):
                    edited_name = st.text_input(
                        "Name", value=medicine.name, key=f"name-{medicine.uid}"
                    )
                    # Mirror the add form: a 12-hour clock with an explicit AM/PM
                    # pick, pre-filled from the medicine's current schedule.
                    cur = medicine.scheduled_24h
                    if cur.hour == 0:
                        edit_hour = 12
                        edit_meridian = "AM"
                    elif cur.hour < 12:
                        edit_hour = cur.hour
                        edit_meridian = "AM"
                    elif cur.hour == 12:
                        edit_hour = 12
                        edit_meridian = "PM"
                    else:
                        edit_hour = cur.hour - 12
                        edit_meridian = "PM"
                    edit_minute = cur.minute
                    edited_hour = st.number_input(
                        "Hour (1-12)",
                        min_value=1,
                        max_value=12,
                        value=edit_hour,
                        step=1,
                        key=f"edit-hour-{medicine.uid}",
                    )
                    edited_minute = st.number_input(
                        "Minute",
                        min_value=0,
                        max_value=59,
                        value=edit_minute,
                        step=1,
                        key=f"edit-minute-{medicine.uid}",
                    )
                    edited_meridian = st.radio(
                        "AM / PM",
                        options=("AM", "PM"),
                        index=0 if edit_meridian == "AM" else 1,
                        key=f"edit-meridian-{medicine.uid}",
                        horizontal=True,
                    )
                    if st.button(
                        "Save changes",
                        key=f"save-{medicine.uid}",
                        type="primary",
                        use_container_width=True,
                    ):
                        if not edited_name.strip():
                            st.error("Please enter a medicine name.")
                        else:
                            update_medicine(
                                state,
                                medicine.uid,
                                name=edited_name.strip(),
                                hour=int(edited_hour),
                                minute=int(edited_minute),
                                meridian=edited_meridian,
                            )
                            save_state(state)
                            st.session_state["medtimer.flash"] = "Medicine updated"
                            st.rerun(scope="app")

            with b3:
                if st.button(
                    "Delete",
                    key=f"delete-{medicine.uid}",
                    use_container_width=True,
                    help=f"Remove {medicine.name}",
                ):
                    delete_medicine(state, medicine.uid)
                    save_state(state)
                    st.session_state["medtimer.flash"] = "Medicine removed"
                    st.rerun(scope="app")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
state = get_state()
now = datetime.now()
today = date.today()

# Persist today's snapshot before reading the weekly figure so the chart and
# the checklist always agree.
record_today(state, today)

today_pct = today_adherence(state)
week_pct = weekly_average(state, today)
streak_days = streak(state, today)
dose_total = len(state.medicines)

flash = st.session_state.pop("medtimer.flash", None)
if flash:
    st.toast(flash, icon="✅")

# ---------------------------------------------------------------------------
# Appearance switch
# ---------------------------------------------------------------------------
# The control writes the same key that is read above, so switching reruns the
# script with the new theme already applied.
_, theme_row = st.columns([3.9, 2.1], vertical_alignment="center")
with theme_row:
    st.radio(
        "Appearance",
        ["Light", "Dark"],
        key="medtimer.mode",
        horizontal=True,
        help="Switches the whole app theme. You can also open ?theme=dark",
    )

# ---------------------------------------------------------------------------
# Hero + KPI row
# ---------------------------------------------------------------------------
hero(today, dose_total, streak_days)

k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.markdown(
        ring_card(
            "Today's adherence",
            today_pct,
            f"{state.doses_taken} of {dose_total} doses logged",
        ),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        bar_card(
            "Doses logged",
            f"{state.doses_taken}<small> / {dose_total}</small>",
            today_pct,
            "Tap 'Mark as taken' the moment you take one.",
        ),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        bar_card(
            "7-day average",
            f"{week_pct:.0f}<small> %</small>",
            week_pct,
            "Rolling average of your recorded days.",
        ),
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        bar_card(
            "Perfect streak",
            f"{streak_days}<small> {'day' if streak_days == 1 else 'days'}</small>",
            min(100.0, streak_days / 7 * 100),
            "Consecutive days at 100% adherence.",
        ),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main grid
# ---------------------------------------------------------------------------
left, right = st.columns([1.62, 1], gap="large")

# ------------------------------- left column -------------------------------
with left:
    section("Add a medicine", "Name it, set the time, and it joins today's plan.")

    with st.container(border=True):
        with st.form("add_medicine", clear_on_submit=True, border=False):
            c1, c2, c3 = st.columns([2.4, 1, 0.9], vertical_alignment="bottom")
            with c1:
                new_name = st.text_input(
                    "Medicine name",
                    placeholder="e.g. Metformin 500 mg",
                    key="add-name",
                )
            with c2:
                # 12-hour clock with an explicit AM/PM pick so the app never
                # confuses 8:00 AM with 8:00 PM. ``st.time_input`` alone only
                # knows the 24-hour value it was given, never the user's intent.
                add_hour = st.number_input(
                    "Hour (1-12)",
                    min_value=1,
                    max_value=12,
                    value=8,
                    step=1,
                    key="add-hour",
                    help="1 to 12 — type the hour you see on a 12-hour clock.",
                )
                add_minute = st.number_input(
                    "Minute",
                    min_value=0,
                    max_value=59,
                    value=0,
                    step=1,
                    key="add-minute",
                )
                add_meridian = st.radio(
                    "AM / PM",
                    options=("AM", "PM"),
                    index=0,
                    key="add-meridian",
                    horizontal=True,
                )
            with c3:
                submitted = st.form_submit_button(
                    "Add", type="primary", use_container_width=True
                )

        if submitted:
            if not new_name.strip():
                st.error("Please enter a medicine name.")
            else:
                add_medicine(
                    state,
                    new_name.strip(),
                    hour=int(add_hour),
                    minute=int(add_minute),
                    meridian=add_meridian,
                )
                save_state(state)
                st.session_state["medtimer.flash"] = f"Added {new_name.strip()}"
                st.rerun()

    live_clock(state)

    section(
        "Today's plan",
        f"{state.doses_taken} of {dose_total} logged · updates live with the clock",
    )

    if state.medicines:
        st.markdown(legend(), unsafe_allow_html=True)
        live_plan(state)
    else:
        empty_state("Nothing here yet — add your first medicine above.")

# ------------------------------ right column -------------------------------
with right:
    section("Your reward", "Turtle-style vector art, drawn with pen commands.")

    if today_pct >= 100 and dose_total:
        with st.container(border=True):
            art(trophy_svg(400, background="#2A2210" if dark else None))
            note("Perfect day — every dose logged. That is a trophy day. 🏆")
    elif today_pct >= 60:
        with st.container(border=True):
            art(smiley_svg(400, background="#123028" if dark else None))
            note("Nicely done — most of today's doses are logged. Keep going! 😊")
    else:
        with st.container(border=True):
            art(smiley_svg(400, background="#123028" if dark else None))
            note("A fresh page. Log a dose and this face starts to smile.")

    section("One gentle thought", "Changes with how your day is going.")
    with st.container(border=True):
        quote(daily_tip(state, now))

    section("Weekly rhythm", "Recorded days from the last week.")

    points = trend(state, days=7, day=today)
    if points:
        with st.container(border=True):
            st.markdown(week_bars(points), unsafe_allow_html=True)
    else:
        empty_state("Your weekly rhythm appears once you log a dose.")

    st.write("")
    if st.button("Start a fresh day", use_container_width=True):
        reset_day(state)
        state.history.pop(today, None)
        record_today(state, today)
        save_state(state)
        st.session_state["medtimer.flash"] = "Today's ticks cleared"
        st.rerun()

footer()
