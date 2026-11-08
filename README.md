# MedTimer — Daily Medicine Companion

A calm, accessible medicine tracker built with Python and Streamlit for **HealthBridge Inc.**
Scenario 2 of the IDAI102 Python Programming summative assessment.

MedTimer turns a daily medication routine from a source of stress into something clear and
encouraging: colour‑coded status, a live adherence score, a consecutive‑day streak, and
turtle‑style vector art that celebrates a good day.

---

## Why it exists

Older adults and people with chronic conditions juggle several medicines a day. The pain
points are simple but serious: forgetting a dose, not being sure whether one was already
taken, and feeling anxious about an unclear schedule.

MedTimer answers three questions at a glance:

1. **What do I take today?**
2. **Have I taken it?**
3. **How am I doing this week?**

The tone is deliberately warm — never clinical, never guilt‑inducing.

---

## Features

### Compulsory (from the brief)
| Requirement | Where it lives |
|---|---|
| Add / edit / delete daily medicines | `app.py` → *Add a medicine* form, per‑dose **Edit** and **Delete** |
| Visual checklist of scheduled vs taken vs missed | `app.py` → *Today's plan*, one card per dose |
| Colour‑coded status | Green = taken, Amber = upcoming, Red = missed (`medtimer/models.py::Status.tone`) |
| Turtle drawing on good adherence | `medtimer/turtle_graphics.py` — `smiley_svg()`, `trophy_svg()` |
| Weekly adherence score | `models.weekly_average()` + `models.streak()`, shown in the KPI row |
| Motivational tips | Rotating daily thought panel, `QUOTES` in `app.py` |

### Extras
- Live countdown copy for upcoming doses ("in 42 min", "12 min overdue")
- Perfect‑day trophy and 60 %+ smiley rewards
- Seven‑day adherence bar chart
- Flash confirmations for every action
- **Undo** for a mistaken tap, and the time each dose was actually logged ("Taken at 7:42 AM")
- The day's ticks, the medicine list and the weekly history survive a page refresh
- Tips that react to your day (overdue, part-logged, all done) instead of a fixed quote
- Midnight is handled: leaving the page open overnight rolls over to a clean day by itself
- Fully responsive, high‑contrast, large‑type layout
- Light and dark themes, switched from the **Appearance** control (or by opening `?theme=dark`)

---

## Project structure

```
.
├── app.py                     # Streamlit entry point — layout only
├── medtimer/
│   ├── __init__.py            # Public package exports
│   ├── models.py              # Domain model + adherence maths (no Streamlit)
│   ├── state.py               # Session store + JSON persistence, seeding, day rollover
│   ├── components.py          # Reusable HTML/SVG presentation helpers
│   ├── styles.py              # The whole design system as one CSS source
│   └── turtle_graphics.py     # Turtle pen engine that renders to SVG
├── tests/
│   └── test_core.py           # Standard-library unit tests for the domain model
├── data/
│   └── medtimer.json          # Runtime state, git-ignored (written on first save)
├── .streamlit/config.toml     # Theme + server configuration
├── requirements.txt
└── README.md
```

The split matters: **business rules never import Streamlit**, so they can be unit tested
directly, and the presentation layer never computes adherence itself.

---

## Running locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open <http://localhost:8501>.

Run the tests with:

```bash
python3 -m unittest discover -s tests -v
```

---

## Design decisions

**Why a custom turtle engine instead of `import turtle`.**
Python's `turtle` module requires an interactive Tk display. Streamlit Cloud runs headless
Linux, so `turtle.Screen()` raises `TclError` there and the reward art would crash the app on
the deployed URL. `medtimer/turtle_graphics.py` therefore reimplements the turtle pen
primitives — `forward`, `left`, `right`, `goto`, `circle`, `penup`, `pendown`,
`begin_fill`/`end_fill` — against an SVG canvas. The drawing code is written in ordinary
turtle style, stays vector‑sharp at any size, and works identically on macOS, Windows and
Streamlit Cloud.

**Why session state plus a small JSON file.**
The brief asks for a single‑user daily companion with no authentication, but `st.session_state`
alone is wiped by a page refresh — which also made the weekly average and the streak
meaningless, because the recorded history never outlived the session. `medtimer/state.py`
keeps the live copy in session state and mirrors the whole `AppState` to `data/medtimer.json`
after every change: an atomic temp‑file write, wrapped so a read‑only disk cannot break the
app. `models.AppState` is a plain dataclass with `to_dict`/`from_dict`, so moving to SQLite
later means touching one file. `data/` is git‑ignored because it is runtime state, not source.

**Why CSS tokens rather than Streamlit's theme config.**
Streamlit's theme lives in `.streamlit/config.toml` and is fixed at boot, so a runtime
toggle cannot use it. `medtimer/styles.py` instead generates the whole stylesheet from a
token dictionary — every colour is a `var(--…)` — and `build_css(dark=True)` swaps the
palette. The control writes to `st.session_state["medtimer.mode"]`, which the script reads
before it injects CSS, so the theme is applied on the very rerun the switch triggers. This
also keeps the reward art and charts themed, which a config file could never do.

Streamlit paints its own view containers with the boot-time theme, so the stylesheet also
forces `--canvas`/`--ink` onto `stApp`, `stAppViewContainer` and `stMain`; otherwise a dark
switch would recolour the cards but leave a white page behind them.

**Accessibility.**
Minimum 0.85 rem body type, 12–20 px corner radii, a single accent colour for primary
actions, colour never used as the *only* signal (every pill also carries a text label),
buttons sized for comfortable touch targets (46 px minimum) and visible focus rings for
keyboard users. Times can be set to any minute rather than quarter hours, and long delays
are written as "7 hr 51 min overdue" instead of "471 min".

---

## Deployment (Streamlit Cloud)

The app is hosted for free on [Streamlit Cloud](https://share.streamlit.io) so anyone with
the link can open it on a phone, tablet or laptop — no install, no login.

### First-time setup (one-off, by the repo owner)

1. Push this repository to GitHub.
2. Open <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app** (or **Create app**).
4. Pick this repository, the `main` branch, and main file path `app.py`.
5. Click **Deploy**. Streamlit builds the app from `requirements.txt`.

No secrets, API keys or environment variables are needed — the app stores everything
locally in the browser session and in a small JSON file the user controls.

### After deploy

- The live URL lands on the **Live app** section below. Paste it there, commit, and push
  so the link travels with the repo.
- Every subsequent git push to `main` auto-redeploys the app.
- Anyone with the link can open the app in any modern browser. If they want their own
  copy, they can **Fork** the repo on GitHub and deploy their fork the same way — each
  copy keeps its own data.

---

## Live app

Open this link on any device — phone, tablet or laptop:

_TODO — replace with the Streamlit Cloud URL after the first deploy, for example:_

`[https://<app-name>.streamlit.app/](https://idai102-medtimer-qrdghps6pmchor2mt9xqwt.streamlit.app/)`
