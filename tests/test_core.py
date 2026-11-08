"""Unit tests for the MedTimer domain model.

Run with:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medtimer.models import (  # noqa: E402
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


class MedicineTests(unittest.TestCase):
    def test_status_upcoming_before_schedule(self):
        medicine = Medicine("Aspirin", 11, 59, "PM")
        self.assertIs(medicine.status(datetime(2026, 1, 1, 23, 0)), Status.UPCOMING)

    def test_status_missed_after_schedule(self):
        medicine = Medicine("Aspirin", 12, 1, "AM")
        self.assertIs(medicine.status(datetime(2026, 1, 1, 8, 0)), Status.MISSED)

    def test_taken_overrides_time(self):
        medicine = Medicine("Aspirin", 11, 59, "PM")
        medicine.taken = True
        self.assertIs(medicine.status(datetime(2026, 1, 1, 0, 1)), Status.TAKEN)

    def test_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            Medicine("   ", 8, 0, "AM")

    def test_rejects_invalid_time(self):
        with self.assertRaises(ValueError):
            Medicine("Aspirin", 0, 0, "AM")  # hour 0 is invalid in the new 1-12 model


class MutationTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()

    def test_add_and_sort(self):
        # sorted_medicines orders by 24-hour time, so 8 AM comes before 8 PM.
        add_medicine(self.state, "Evening", 8, 0, "PM")
        add_medicine(self.state, "Morning", 8, 0, "AM")
        self.assertEqual([m.name for m in self.state.sorted_medicines], ["Morning", "Evening"])

    def test_mark_taken(self):
        medicine = add_medicine(self.state, "Aspirin", 8, 0, "AM")
        self.assertTrue(mark_taken(self.state, medicine.uid))
        self.assertTrue(medicine.taken)

    def test_mark_taken_unknown_id(self):
        self.assertFalse(mark_taken(self.state, "missing"))

    def test_update(self):
        medicine = add_medicine(self.state, "Aspirin", 8, 0, "AM")
        update_medicine(self.state, medicine.uid, name="Ibuprofen", hour=9, minute=15)
        self.assertEqual(medicine.name, "Ibuprofen")
        self.assertEqual((medicine.hour, medicine.minute, medicine.meridian), (9, 15, "AM"))

    def test_update_rejects_blank_name(self):
        medicine = add_medicine(self.state, "Aspirin", 8, 0, "AM")
        with self.assertRaises(ValueError):
            update_medicine(self.state, medicine.uid, name="  ")

    def test_delete(self):
        medicine = add_medicine(self.state, "Aspirin", 8, 0, "AM")
        self.assertTrue(delete_medicine(self.state, medicine.uid))
        self.assertEqual(self.state.medicines, [])

    def test_reset_day(self):
        medicine = add_medicine(self.state, "Aspirin", 8, 0, "AM")
        mark_taken(self.state, medicine.uid)
        reset_day(self.state)
        self.assertFalse(medicine.taken)
        self.assertEqual(len(self.state.medicines), 1)


class AdherenceTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.day = date(2026, 1, 5)

    def test_empty_state_is_zero(self):
        self.assertEqual(today_adherence(self.state), 0.0)

    def test_partial_adherence(self):
        for name in ("A", "B", "C"):
            add_medicine(self.state, name, 8, 0, "AM")
        mark_taken(self.state, self.state.medicines[0].uid)
        self.assertEqual(today_adherence(self.state), 33.3)

    def test_full_adherence(self):
        medicine = add_medicine(self.state, "A", 8, 0, "AM")
        mark_taken(self.state, medicine.uid)
        self.assertEqual(today_adherence(self.state), 100.0)

    def test_record_and_weekly_average(self):
        medicine = add_medicine(self.state, "A", 8, 0, "AM")
        mark_taken(self.state, medicine.uid)
        for offset in range(3):
            record_today(self.state, self.day - timedelta(days=offset))
        self.assertEqual(weekly_average(self.state, self.day), 100.0)

    def test_weekly_average_ignores_old_days(self):
        self.state.history[self.day - timedelta(days=30)] = 0.0
        self.state.history[self.day] = 100.0
        self.assertEqual(weekly_average(self.state, self.day), 100.0)

    def test_streak_counts_consecutive_perfect_days(self):
        for offset in range(3):
            self.state.history[self.day - timedelta(days=offset)] = 100.0
        self.assertEqual(streak(self.state, self.day), 3)

    def test_streak_breaks_on_gap(self):
        self.state.history[self.day] = 100.0
        self.state.history[self.day - timedelta(days=2)] = 100.0
        self.assertEqual(streak(self.state, self.day), 1)

    def test_trend_is_chronological(self):
        self.state.history[self.day - timedelta(days=1)] = 50.0
        self.state.history[self.day] = 100.0
        self.assertEqual(
            [value for _, value in trend(self.state, days=7, day=self.day)],
            [50.0, 100.0],
        )


class TurtleGraphicsTests(unittest.TestCase):
    def test_figures_render_valid_svg(self):
        from medtimer.turtle_graphics import smiley_svg, trophy_svg

        for builder in (smiley_svg, trophy_svg):
            svg = builder(400)
            self.assertTrue(svg.startswith("<svg"))
            self.assertTrue(svg.endswith("</svg>"))
            self.assertIn("<path", svg)


class RealTimeStatusTests(unittest.TestCase):
    """Dose status and the live strip must follow the wall clock."""

    def test_upcoming_before_due(self):
        from datetime import datetime

        from medtimer.models import Medicine, Status

        med = Medicine("A", 8, 0, "AM")
        self.assertIs(med.status(datetime(2026, 3, 4, 7, 59)), Status.UPCOMING)

    def test_grace_window_keeps_dose_actionable(self):
        from datetime import datetime

        from medtimer.models import GRACE_MINUTES, Medicine, Status

        med = Medicine("A", 8, 0, "AM")
        self.assertIs(med.status(datetime(2026, 3, 4, 8, 0)), Status.UPCOMING)
        self.assertIs(
            med.status(datetime(2026, 3, 4, 8, GRACE_MINUTES - 1)), Status.UPCOMING
        )
        self.assertIs(med.status(datetime(2026, 3, 4, 8, GRACE_MINUTES)), Status.MISSED)

    def test_taken_beats_the_clock(self):
        from datetime import datetime

        from medtimer.models import Medicine, Status

        med = Medicine("A", 8, 0, "AM")
        med.taken = True
        self.assertIs(med.status(datetime(2026, 3, 4, 23, 0)), Status.TAKEN)

    def test_next_dose_follows_what_is_left(self):
        from datetime import datetime

        from medtimer.models import AppState, add_medicine, mark_taken

        state = AppState()
        morning = add_medicine(state, "Morning", 8, 0, "AM")
        noon = add_medicine(state, "Noon", 12, 0, "PM")
        add_medicine(state, "Night", 8, 0, "PM")
        now = datetime(2026, 3, 4, 9, 0)

        self.assertEqual(state.next_dose(now).name, "Morning")
        mark_taken(state, morning.uid)
        self.assertEqual(state.next_dose(now).name, "Noon")
        mark_taken(state, noon.uid)
        self.assertEqual(state.next_dose(now).name, "Night")

    def test_next_dose_is_none_when_all_taken(self):
        from datetime import datetime

        from medtimer.models import AppState, add_medicine, mark_taken

        state = AppState()
        only = add_medicine(state, "Only", 8, 0, "AM")
        mark_taken(state, only.uid)
        self.assertIsNone(state.next_dose(datetime(2026, 3, 4, 9, 0)))


class PersistenceAndUndoTests(unittest.TestCase):
    """A dose remembers when it was logged, and a mis-tap can be undone."""

    def test_logging_records_when_it_was_taken(self):
        state = AppState()
        medicine = add_medicine(state, "A", 8, 0, "AM")
        moment = datetime(2026, 3, 4, 7, 40)  # taken early
        self.assertTrue(mark_taken(state, medicine.uid, at=moment))
        self.assertEqual(medicine.taken_at, moment)
        self.assertTrue(medicine.taken)

    def test_undo_clears_a_mistaken_tick(self):
        state = AppState()
        medicine = add_medicine(state, "A", 8, 0, "AM")
        mark_taken(state, medicine.uid)
        self.assertEqual(state.doses_taken, 1)
        self.assertTrue(undo_taken(state, medicine.uid))
        self.assertIsNone(medicine.taken_at)
        self.assertEqual(state.doses_taken, 0)
        self.assertIs(medicine.status(datetime(2026, 3, 4, 7, 0)), Status.UPCOMING)

    def test_undo_needs_something_to_undo(self):
        state = AppState()
        medicine = add_medicine(state, "A", 8, 0, "AM")
        self.assertFalse(undo_taken(state, medicine.uid))
        self.assertFalse(undo_taken(state, "missing"))

    def test_reset_day_clears_the_logged_time(self):
        state = AppState()
        medicine = add_medicine(state, "A", 8, 0, "AM")
        mark_taken(state, medicine.uid)
        reset_day(state)
        self.assertIsNone(medicine.taken_at)

    def test_state_survives_a_json_round_trip(self):
        state = AppState()
        medicine = add_medicine(state, "A", 8, 0, "AM")
        mark_taken(state, medicine.uid, at=datetime(2026, 3, 4, 8, 5))
        state.history[date(2026, 3, 4)] = 100.0
        state.last_active = date(2026, 3, 4)

        restored = AppState.from_dict(json.loads(json.dumps(state.to_dict())))
        self.assertEqual([m.name for m in restored.medicines], ["A"])
        self.assertEqual(restored.medicines[0].uid, medicine.uid)
        self.assertEqual(restored.medicines[0].taken_at, datetime(2026, 3, 4, 8, 5))
        self.assertEqual(restored.history, {date(2026, 3, 4): 100.0})
        self.assertEqual(restored.last_active, date(2026, 3, 4))
        self.assertEqual(restored.doses_taken, 1)
        # Round-tripped medicine must keep its meridian.
        self.assertEqual(restored.medicines[0].meridian, "AM")
        self.assertEqual(restored.medicines[0].hour, 8)

    def test_restore_skips_damaged_records(self):
        restored = AppState.from_dict(
            {
                "medicines": [
                    {"hour": 8},  # no name
                    {"name": "Good", "hour": 9, "minute": 0},
                ],
                "history": {"not-a-date": 50.0, "2026-03-04": 100.0},
                "last_active": "nonsense",
            }
        )
        self.assertEqual([m.name for m in restored.medicines], ["Good"])
        self.assertEqual(restored.history, {date(2026, 3, 4): 100.0})
        self.assertEqual(restored.last_active, date.today())
        # The damaged record "Good" had hour=9 (24h) with no meridian, so
        # from_dict infers AM and converts 9 -> 9 AM.
        self.assertEqual(restored.medicines[0].hour, 9)
        self.assertEqual(restored.medicines[0].meridian, "AM")


class FormattingTests(unittest.TestCase):
    def test_long_delays_read_in_hours(self):
        from medtimer.components import humanise_duration, humanise_minutes

        self.assertEqual(humanise_duration(471), "7 hr 51 min")
        self.assertEqual(humanise_duration(120), "2 hr")
        self.assertEqual(humanise_duration(45), "45 min")
        self.assertEqual(humanise_minutes(-471), "overdue by 7 hr 51 min")
        self.assertEqual(humanise_minutes(-30), "overdue by 30 min")
        self.assertEqual(humanise_minutes(0), "due now")
        self.assertEqual(humanise_minutes(42), "in 42 min")
        self.assertEqual(humanise_minutes(125), "in 2 hr 5 min")

    def test_dose_row_shows_when_a_dose_was_logged(self):
        from medtimer.components import dose_row
        from medtimer.models import Medicine, Status

        medicine = Medicine("Metformin", 8, 0, "AM")
        medicine.taken_at = datetime(2026, 1, 1, 7, 40)
        markup = dose_row(medicine, Status.TAKEN, datetime(2026, 1, 1, 9, 0))
        self.assertIn("logged at 7:40 AM", markup)


class ThemeAndMarkupTests(unittest.TestCase):
    def test_themes_are_distinct_palettes(self):
        from medtimer.styles import build_css

        light, dark = build_css(False), build_css(True)
        self.assertNotEqual(light, dark)
        self.assertIn("--canvas:#F6F8FA", light)
        self.assertIn("--canvas:#0A121A", dark)

    def test_both_themes_define_every_token(self):
        from medtimer.styles import DARK, LIGHT

        self.assertEqual(set(LIGHT), set(DARK))

    def test_bar_card_keeps_trusted_value_markup(self):
        from medtimer.components import bar_card

        markup = bar_card("Doses", "2<small> / 3</small>", 66.0, "cap")
        self.assertIn("<small>", markup)
        self.assertNotIn("&lt;small&gt;", markup)

    def test_bar_card_escapes_untrusted_text(self):
        from medtimer.components import bar_card

        markup = bar_card("<b>label</b>", "1", 10.0, "<i>cap</i>")
        self.assertIn("&lt;b&gt;", markup)
        self.assertIn("&lt;i&gt;", markup)

    def test_markup_is_single_line(self):
        """Markdown ends an HTML block at a blank line and code-blocks indented
        text, so injected markup must not contain newlines or indentation."""
        from datetime import date as date_, datetime as datetime_

        from medtimer import components as c
        from medtimer.models import Status

        class FakeMedicine:
            name = "Metformin 500 mg"
            scheduled = datetime_(2026, 1, 1, 8, 0)

            def minutes_until(self, now):
                return 30

        # hero()/quote()/note() write straight to Streamlit, so only the
        # value-returning builders can be inspected here.
        samples = [
            c.progress_ring(42.0),
            c.ring_card("Adherence", 42.0, "caption"),
            c.bar_card("Doses", "2<small> / 3</small>", 66.0, "caption"),
            c.week_bars([(date_(2026, 1, 1), 50.0), (date_(2026, 1, 2), 100.0)]),
            c.dose_row(FakeMedicine(), Status.UPCOMING, datetime_(2026, 1, 1, 6, 0)),
            c.legend(),
        ]
        for markup in samples:
            self.assertNotIn("\n", markup)
            self.assertEqual(markup, markup.strip())
            self.assertTrue(markup.startswith("<div") or markup.startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
