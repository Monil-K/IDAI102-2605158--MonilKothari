"""Reusable presentation helpers.

Each function returns a single-line HTML string (or writes one into the page) so
the layout in ``app.py`` stays declarative and readable. All colours come from
CSS tokens, so every helper works in both light and dark themes.

Why single line? Streamlit renders markdown with markdown-it, which ends an HTML
block at a blank line and then treats indented text as a *code block*. A
multi-line f-string therefore leaks raw ``<div ...>`` markup onto the page. Every
helper squeezes its markup with :func:`_inline` before handing it over.
"""

from __future__ import annotations

import html
import math
from datetime import date, datetime

import streamlit as st

from medtimer.models import Medicine, Status
from medtimer.styles import build_css


def _inline(markup: str) -> str:
    """Collapse markup to one line so markdown cannot turn it into a code block."""
    return " ".join(markup.split())


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def fmt_clock(moment: datetime | None) -> str:
    """12-hour clock without a leading zero, e.g. ``8:30 AM``."""
    return moment.strftime("%I:%M %p").lstrip("0") if moment else ""


def fmt_time(medicine: Medicine) -> str:
    """The scheduled time of ``medicine``, e.g. ``8:30 AM``."""
    return medicine.scheduled.strftime("%I:%M %p").lstrip("0")


def humanise_duration(minutes: int) -> str:
    """A plain duration: ``471`` -> ``"7 hr 51 min"``, ``45`` -> ``"45 min"``."""
    minutes = abs(int(minutes))
    if minutes < 60:
        return f"{minutes} min"
    hours, remainder = divmod(minutes, 60)
    return f"{hours} hr" if remainder == 0 else f"{hours} hr {remainder} min"


def humanise_minutes(minutes: int) -> str:
    """Turn a minute delta into friendly copy.

    Long delays are expressed in hours: "7 hr 51 min overdue" is readable at a
    glance where "471 min overdue" is not — and this is the copy an older user
    sees when a dose was missed.
    """
    if minutes == 0:
        return "due now"
    if minutes < 0:
        return f"{humanise_duration(minutes)} overdue"
    return f"in {humanise_duration(minutes)}"


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------
def inject_styles(dark: bool = False) -> None:
    """Write the stylesheet for the active theme."""
    st.markdown(build_css(dark), unsafe_allow_html=True)


def hero(today: date, dose_total: int, streak_days: int) -> None:
    """Large gradient header with the session summary."""
    streak_copy = (
        f"{streak_days}-day perfect streak" if streak_days >= 1 else "Start your streak today"
    )
    markup = f"""
        <div class="mt-hero">
          <div class="mt-hero__brand"><span class="mt-logo">&#10010;</span> MedTimer</div>
          <h1 class="mt-hero__title">Your day, calmly on track.</h1>
          <p class="mt-hero__sub">
            A gentle companion for your daily medicines &mdash; clear status,
            a weekly adherence score, and a little celebration when you keep it up.
          </p>
          <div class="mt-hero__meta">
            <span class="mt-tag">{today.strftime('%A, %d %B %Y')}</span>
            <span class="mt-tag">{dose_total} medicine{'s' if dose_total != 1 else ''} scheduled</span>
            <span class="mt-tag mt-tag--brand">{streak_copy}</span>
          </div>
        </div>
        """
    st.markdown(_inline(markup), unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    sub = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    markup = f'<div class="mt-section"><h2>{html.escape(title)}</h2>{sub}</div>'
    st.markdown(_inline(markup), unsafe_allow_html=True)


def clock_strip(now: datetime, next_medicine: Medicine | None = None) -> str:
    """Live clock plus the next dose, refreshed by a ticking fragment."""
    clock = now.strftime("%I:%M:%S %p").lstrip("0")

    if next_medicine is None:
        message, tone = "All doses logged for today &#127881;", "ok"
    else:
        name = html.escape(next_medicine.name)
        remaining = next_medicine.minutes_until(now)
        if remaining < 0:
            message = f"{name} overdue by {humanise_duration(remaining)}"
            tone = "danger"
        elif remaining == 0:
            message = f"{name} due now"
            tone = "warn"
        else:
            message = (
                f"Next: {name} at {fmt_time(next_medicine)} "
                f"&middot; {humanise_minutes(remaining)}"
            )
            tone = "brand"

    markup = f"""
    <div class="mt-clock">
      <span class="mt-clock__pulse"></span>
      <span class="mt-clock__time">{clock}</span>
      <span class="mt-clock__sep">&middot;</span>
      <span class="mt-clock__next mt-clock__next--{tone}">{message}</span>
    </div>
    """
    return _inline(markup)


# ---------------------------------------------------------------------------
# Rings, bars and cards
# ---------------------------------------------------------------------------
def progress_ring(percent: float, size: int = 104, stroke: int = 11) -> str:
    """Circular progress indicator as inline SVG, coloured by CSS tokens."""
    percent = max(0.0, min(100.0, percent))
    radius = (size - stroke) / 2
    circumference = 2 * math.pi * radius
    offset = circumference * (1 - percent / 100)
    centre = size / 2
    markup = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img"
         aria-label="{percent:.0f} percent">
      <circle cx="{centre}" cy="{centre}" r="{radius}" fill="none"
              style="stroke:var(--track)" stroke-width="{stroke}"/>
      <circle cx="{centre}" cy="{centre}" r="{radius}" fill="none"
              style="stroke:var(--brand)" stroke-width="{stroke}" stroke-linecap="round"
              stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}"
              transform="rotate(-90 {centre} {centre})"/>
      <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central"
            style="fill:var(--ink)" font-size="{size * 0.27:.0f}" font-weight="800">
        {percent:.0f}%
      </text>
    </svg>
    """
    return _inline(markup)


def ring_card(label: str, percent: float, caption: str) -> str:
    markup = f"""
    <div class="mt-kpi">
      <div class="mt-kpi__label">{html.escape(label)}</div>
      <div class="mt-ring" style="margin-top:10px;">
        {progress_ring(percent)}
        <div class="mt-ring__caption">{html.escape(caption)}</div>
      </div>
    </div>
    """
    return _inline(markup)


def bar_card(label: str, value_html: str, percent: float, caption: str) -> str:
    """Stat card.

    ``value_html`` is intentionally **not** escaped: callers pass trusted
    markup such as ``"2<small> / 3</small>"``. Labels and captions are escaped.
    """
    markup = f"""
    <div class="mt-kpi">
      <div class="mt-kpi__label">{html.escape(label)}</div>
      <div class="mt-kpi__value">{value_html}</div>
      <div class="mt-kpi__foot">
        <div class="mt-bar"><span style="width:{max(0.0, min(100.0, percent)):.0f}%"></span></div>
        <div class="mt-ring__caption" style="margin-top:9px;">{html.escape(caption)}</div>
      </div>
    </div>
    """
    return _inline(markup)


def week_bars(points: list[tuple[date, float]]) -> str:
    """Vertical bar chart built from divs — themeable and dependency free."""
    columns = []
    for day, value in points:
        height = max(6.0, min(100.0, value) / 100 * 120)
        col = f"""
            <div class="mt-bcol" title="{day.strftime('%A')}: {value:.0f}%">
              <div class="mt-bval">{value:.0f}</div>
              <div class="mt-btrack"><span style="height:{height:.0f}px"></span></div>
              <div class="mt-bday">{day.strftime('%a')}</div>
            </div>
            """
        columns.append(_inline(col))
    return _inline(f'<div class="mt-bars">{"".join(columns)}</div>')


def dose_row(medicine: Medicine, status: Status, now: datetime) -> str:
    """Header block for one medicine: name, schedule and status pill."""
    detail = fmt_time(medicine)
    if status in (Status.UPCOMING, Status.MISSED):
        detail += f" &middot; {humanise_minutes(medicine.minutes_until(now))}"
    else:
        logged_at = fmt_clock(getattr(medicine, "taken_at", None))
        detail += f" &middot; logged at {logged_at}" if logged_at else " &middot; logged"

    markup = f"""
    <div class="mt-dose mt-dose--{status.tone}">
      <div>
        <div class="mt-dose__name">{html.escape(medicine.name)}</div>
        <div class="mt-dose__meta">{detail}</div>
      </div>
      <span class="mt-pill mt-pill--{status.tone}">
        <span class="mt-dot"></span>{status.label}
      </span>
    </div>
    """
    return _inline(markup)


def legend() -> str:
    """Small chip row that spells out what each status colour means."""
    chips = "".join(
        f'<span class="mt-legend__chip mt-legend__chip--{tone}">'
        f'<span class="mt-dot"></span>{label}</span>'
        for tone, label in (("ok", "Taken"), ("warn", "Upcoming"), ("danger", "Missed"))
    )
    return _inline(f'<div class="mt-legend">{chips}</div>')


def quote(text: str) -> None:
    st.markdown(
        _inline(f'<div class="mt-quote">{html.escape(text)}</div>'),
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.markdown(
        _inline(f'<div class="mt-empty">{html.escape(message)}</div>'),
        unsafe_allow_html=True,
    )


def art(svg: str) -> None:
    st.markdown(_inline(f'<div class="mt-art">{svg}</div>'), unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(_inline(f'<div class="mt-note">{html.escape(text)}</div>'), unsafe_allow_html=True)


def footer() -> None:
    markup = (
        '<div class="mt-foot">MedTimer v2.2 &middot; Built for HealthBridge Inc. '
        '&middot; Python &amp; Streamlit &middot; turtle-style vector graphics</div>'
    )
    st.markdown(_inline(markup), unsafe_allow_html=True)
