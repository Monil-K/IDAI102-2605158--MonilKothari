"""Turtle-style drawing engine that renders to SVG.

The assignment asks for Turtle graphics. Python's :mod:`turtle` module needs an
interactive Tk display, which does not exist on Streamlit Cloud (headless
Linux) and is fragile behind a web server. This module therefore re-implements
the turtle pen primitives — ``forward``, ``left``/``right``, ``circle``,
``penup``/``pendown``, ``goto``, ``begin_fill``/``end_fill`` — on an SVG canvas.

The drawing code reads exactly like ordinary turtle code::

    pen.penup(); pen.goto(0, -96); pen.pendown()
    pen.color("#FFD9E0"); pen.begin_fill(); pen.circle(96); pen.end_fill()

The output is vector, high-DPI, theme-aware and safe to embed with
``st.html``/``st.markdown``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

Point = tuple[float, float]


@dataclass
class _Shape:
    points: list[Point]
    colour: str
    width: float
    fill: str | None = None
    closed: bool = False


@dataclass
class TurtlePen:
    """A minimal turtle whose canvas is an SVG document."""

    canvas_width: int = 400
    canvas_height: int = 400
    background: str = "transparent"

    _x: float = 0.0
    _y: float = 0.0
    _heading: float = 0.0
    _down: bool = True
    _colour: str = "#0B1220"
    _fill_colour: str | None = None
    _stroke: float = 3.0
    _segment: list[Point] = field(default_factory=list, init=False)
    _shapes: list[_Shape] = field(default_factory=list, init=False)
    _filling: bool = field(default=False, init=False)
    _fill_start: Point | None = field(default=None, init=False)

    # -- pen state -----------------------------------------------------
    def penup(self) -> None:
        self._flush()
        self._down = False

    def pendown(self) -> None:
        self._down = True

    def color(self, colour: str) -> None:
        self._colour = colour
        self._fill_colour = colour

    def pencolor(self, colour: str) -> None:
        self._colour = colour

    def fillcolor(self, colour: str) -> None:
        self._fill_colour = colour

    def width(self, value: float) -> None:
        self._stroke = value

    def speed(self, *_: object) -> None:  # turtle API compatibility
        return None

    def hideturtle(self) -> None:  # turtle API compatibility
        return None

    # -- movement ------------------------------------------------------
    def goto(self, x: float, y: float) -> None:
        if self._down:
            if not self._segment:
                self._segment.append((self._x, self._y))
            self._segment.append((float(x), float(y)))
        else:
            self._flush()
        self._x, self._y = float(x), float(y)

    def forward(self, distance: float) -> None:
        angle = math.radians(self._heading)
        self.goto(self._x + distance * math.cos(angle),
                  self._y + distance * math.sin(angle))

    def backward(self, distance: float) -> None:
        self.forward(-distance)

    def left(self, degrees: float) -> None:
        self._heading = (self._heading + degrees) % 360

    def right(self, degrees: float) -> None:
        self._heading = (self._heading - degrees) % 360

    def setheading(self, degrees: float) -> None:
        self._heading = degrees % 360

    def home(self) -> None:
        self.goto(0.0, 0.0)
        self._heading = 0.0

    def circle(self, radius: float, extent: float = 360.0) -> None:
        """Draw an arc; positive radii sweep anticlockwise like turtle."""
        if radius == 0 or extent == 0:
            return
        sign = 1 if radius > 0 else -1
        r = abs(radius)
        heading = math.radians(self._heading)
        cx = self._x - sign * r * math.sin(heading)
        cy = self._y + sign * r * math.cos(heading)
        start = math.atan2(self._y - cy, self._x - cx)
        steps = max(16, int(abs(extent) / 4))
        for index in range(1, steps + 1):
            theta = start + sign * math.radians(extent) * index / steps
            self.goto(cx + r * math.cos(theta), cy + r * math.sin(theta))
        self._heading = (self._heading + sign * extent) % 360

    def polyline(self, points: list[Point]) -> None:
        """Convenience helper: stroke a run of connected points."""
        if len(points) < 2:
            return
        self.penup()
        self.goto(*points[0])
        self.pendown()
        for point in points[1:]:
            self.goto(*point)
        self.penup()

    # -- fills ---------------------------------------------------------
    def begin_fill(self) -> None:
        self._filling = True
        self._fill_start = (self._x, self._y)

    def end_fill(self) -> None:
        if self._segment:
            self._shapes.append(
                _Shape(
                    points=list(self._segment),
                    colour="none",
                    width=0.0,
                    fill=self._fill_colour or self._colour,
                    closed=True,
                )
            )
        self._filling = False
        self._fill_start = None
        self._segment = []

    # -- output --------------------------------------------------------
    def _flush(self) -> None:
        if len(self._segment) > 1:
            self._shapes.append(
                _Shape(
                    points=list(self._segment),
                    colour=self._colour,
                    width=self._stroke,
                )
            )
        self._segment = []

    def to_svg(self) -> str:
        self._flush()
        half_w, half_h = self.canvas_width / 2, self.canvas_height / 2
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" '
            f'viewBox="{-half_w} {-half_h} {self.canvas_width} {self.canvas_height}" '
            f'role="img" aria-label="drawing">'
        ]
        if self.background != "transparent":
            parts.append(
                f'<rect x="{-half_w}" y="{-half_h}" width="{self.canvas_width}" '
                f'height="{self.canvas_height}" rx="24" fill="{self.background}"/>'
            )
        for shape in self._shapes:
            if not shape.points:
                continue
            if shape.fill and len(shape.points) == 1:
                x, y = shape.points[0]
                parts.append(f'<circle cx="{x:.2f}" cy="{-y:.2f}" r="4" fill="{shape.fill}"/>')
                continue
            path = " ".join(
                f'{"M" if index == 0 else "L"} {x:.2f} {-y:.2f}'
                for index, (x, y) in enumerate(shape.points)
            )
            if shape.fill:
                parts.append(f'<path d="{path} Z" fill="{shape.fill}"/>')
            else:
                parts.append(
                    f'<path d="{path}" fill="none" stroke="{shape.colour}" '
                    f'stroke-width="{shape.width}" stroke-linecap="round" '
                    f'stroke-linejoin="round"/>'
                )
        parts.append("</svg>")
        return "".join(parts)


# ---------------------------------------------------------------------------
# Figure builders — written in plain turtle style
# ---------------------------------------------------------------------------
def _arc(cx: float, cy: float, radius: float, start: float, end: float,
         steps: int = 64) -> list[Point]:
    return [
        (cx + radius * math.cos(math.radians(start + (end - start) * i / steps)),
         cy + radius * math.sin(math.radians(start + (end - start) * i / steps)))
        for i in range(steps + 1)
    ]


def smiley_svg(size: int = 400, background: str | None = None) -> str:
    """Cheerful smiley face shared when today's adherence is strong."""
    pen = TurtlePen(size, size, background=background or "#EFFBF6")

    # Blush
    pen.penup()
    for x in (-64, 64):
        pen.goto(x, -14)
        pen.pendown()
        pen.color("#FFC2CE")
        pen.begin_fill()
        pen.circle(15)
        pen.end_fill()
        pen.penup()

    # Face
    pen.goto(0, -96)
    pen.pendown()
    pen.color("#FFD9E0")
    pen.begin_fill()
    pen.circle(96)
    pen.end_fill()
    pen.penup()

    # Eyes
    for x in (-34, 34):
        pen.goto(x, 26)
        pen.pendown()
        pen.color("#22303C")
        pen.begin_fill()
        pen.circle(11)
        pen.end_fill()
        pen.penup()

    # Eye highlights
    for x in (-37, 31):
        pen.goto(x, 30)
        pen.pendown()
        pen.color("#FFFFFF")
        pen.begin_fill()
        pen.circle(3.6)
        pen.end_fill()
        pen.penup()

    # Smile
    pen.color("#22303C")
    pen.width(7)
    pen.polyline(_arc(0, 8, 58, 202, 338))
    pen.width(3)

    return pen.to_svg()


def trophy_svg(size: int = 400, background: str | None = None) -> str:
    """Gold trophy awarded for a perfect adherence week."""
    pen = TurtlePen(size, size, background=background or "#FFF9EC")
    gold, gold_dark, star = "#F5B70A", "#DE9B05", "#FF8A2B"

    # Handles
    pen.color(gold)
    pen.width(14)
    pen.polyline(_arc(-58, 26, 24, -70, 70))
    pen.polyline(_arc(58, 26, 24, 110, 250))
    pen.width(3)
    pen.penup()

    # Cup body
    pen.color(gold)
    pen.goto(-46, 70)
    pen.pendown()
    pen.begin_fill()
    pen.goto(46, 70)
    pen.goto(37, -6)
    for point in _arc(0, -6, 37, 0, -180):
        pen.goto(*point)
    pen.goto(-46, 70)
    pen.end_fill()
    pen.penup()

    # Stem
    pen.goto(-12, -42)
    pen.pendown()
    pen.color(gold_dark)
    pen.begin_fill()
    pen.goto(12, -42)
    pen.goto(8, -70)
    pen.goto(-8, -70)
    pen.goto(-12, -42)
    pen.end_fill()
    pen.penup()

    # Base
    pen.goto(-44, -70)
    pen.pendown()
    pen.color(gold_dark)
    pen.begin_fill()
    pen.goto(44, -70)
    pen.goto(34, -90)
    pen.goto(-34, -90)
    pen.goto(-44, -70)
    pen.end_fill()
    pen.penup()

    # Star
    pen.goto(0, 96)
    pen.pendown()
    pen.color(star)
    pen.begin_fill()
    for _ in range(5):
        pen.forward(19)
        pen.right(144)
    pen.end_fill()
    pen.penup()

    return pen.to_svg()
