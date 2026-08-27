#!/usr/bin/env python3
"""Build the deterministic Orrae Sans typeface with FontTools.

The caps-only system uses a shared modular geometry. Lowercase code points
intentionally map to uppercase glyphs.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


UPM = 1000
ASCENDER = 800
DESCENDER = -200
CAP = 700
STROKE = 112
THIN = 62
ROUND = 250
VERSION = "0.200"
FAMILY = "Orrae Sans"
STYLE = "Regular"
PS_NAME = "OrraeSans-Regular"
BUILD_TIMESTAMP = 3_870_547_200  # 2026-08-26 00:00:00 UTC, seconds since 1904.


def cubic_pen():
    target = TTGlyphPen(None)
    return target, Cu2QuPen(target, max_err=1.0, reverse_direction=False)


def contour(pen, points):
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.closePath()


def rect(pen, x0, y0, x1, y1):
    contour(pen, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def round_rect(pen, x0, y0, x1, y1, radius, reverse=False):
    radius = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
    k = 0.5522847498307936
    commands = [
        ("M", (x0 + radius, y0)),
        ("L", (x1 - radius, y0)),
        ("C", (x1 - radius + k * radius, y0), (x1, y0 + radius - k * radius), (x1, y0 + radius)),
        ("L", (x1, y1 - radius)),
        ("C", (x1, y1 - radius + k * radius), (x1 - radius + k * radius, y1), (x1 - radius, y1)),
        ("L", (x0 + radius, y1)),
        ("C", (x0 + radius - k * radius, y1), (x0, y1 - radius + k * radius), (x0, y1 - radius)),
        ("L", (x0, y0 + radius)),
        ("C", (x0, y0 + radius - k * radius), (x0 + radius - k * radius, y0), (x0 + radius, y0)),
    ]
    if reverse:
        # Reversing the geometric command list by recording through a temporary
        # pen would be unnecessarily opaque. Draw the same rounded rectangle
        # counterclockwise explicitly so counters retain correct winding.
        pen.moveTo((x0 + radius, y0))
        pen.curveTo((x0 + radius - k * radius, y0), (x0, y0 + radius - k * radius), (x0, y0 + radius))
        pen.lineTo((x0, y1 - radius))
        pen.curveTo((x0, y1 - radius + k * radius), (x0 + radius - k * radius, y1), (x0 + radius, y1))
        pen.lineTo((x1 - radius, y1))
        pen.curveTo((x1 - radius + k * radius, y1), (x1, y1 - radius + k * radius), (x1, y1 - radius))
        pen.lineTo((x1, y0 + radius))
        pen.curveTo((x1, y0 + radius - k * radius), (x1 - radius + k * radius, y0), (x1 - radius, y0))
        pen.closePath()
        return
    for command in commands:
        if command[0] == "M":
            pen.moveTo(command[1])
        elif command[0] == "L":
            pen.lineTo(command[1])
        else:
            pen.curveTo(command[1], command[2], command[3])
    pen.closePath()


def stroke_line(pen, x0, y0, x1, y1, width=STROKE):
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    nx = -dy / length * width / 2
    ny = dx / length * width / 2
    contour(
        pen,
        [
            (x0 - nx, y0 - ny),
            (x1 - nx, y1 - ny),
            (x1 + nx, y1 + ny),
            (x0 + nx, y0 + ny),
        ],
    )


def clipped_stroke_outline(x0, y0, x1, y1, width, max_y):
    """Return a stroked line polygon clipped below max_y, top-right first."""
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    nx = -dy / length * width / 2
    ny = dx / length * width / 2
    polygon = [
        (x0 - nx, y0 - ny),
        (x1 - nx, y1 - ny),
        (x1 + nx, y1 + ny),
        (x0 + nx, y0 + ny),
    ]

    clipped = []
    for current, following in zip(polygon, polygon[1:] + polygon[:1]):
        current_inside = current[1] <= max_y
        following_inside = following[1] <= max_y
        if current_inside:
            clipped.append(current)
        if current_inside != following_inside:
            ratio = (max_y - current[1]) / (following[1] - current[1])
            clipped.append(
                (
                    current[0] + ratio * (following[0] - current[0]),
                    max_y,
                )
            )

    # Sutherland-Hodgman preserves the original polygon direction. Reverse it
    # so the outline splices into the bowl from the top-right attachment.
    return list(reversed(clipped))


def rounded_bar(pen, x0, y0, x1, y1, radius=None):
    round_rect(pen, x0, y0, x1, y1, radius or min((x1 - x0), (y1 - y0)) / 2)


def open_bowl(
    pen, width, bottom=294, top=CAP, radius=180, stroke=STROKE,
    include_stem=False, leg_outline=None,
):
    """Draw an open-left C-shaped bowl as one contour."""
    inner_radius = radius - stroke
    center_x = width - radius

    def arc(center_y, arc_radius, start_degrees, end_degrees, steps=10):
        return [
            (
                center_x + arc_radius * math.cos(math.radians(angle)),
                center_y + arc_radius * math.sin(math.radians(angle)),
            )
            for angle in [
                start_degrees + (end_degrees - start_degrees) * index / steps
                for index in range(1, steps + 1)
            ]
        ]

    points = [(0, top), (center_x, top)]
    points.extend(arc(top - radius, radius, 90, 0))
    points.append((width, bottom + radius))
    points.extend(arc(bottom + radius, radius, 0, -90))
    if leg_outline:
        points.extend(leg_outline)
    if include_stem:
        points.extend(
            [
                (stroke, bottom),
                (stroke, 0),
                (0, 0),
                (0, bottom + stroke),
            ]
        )
    else:
        points.extend([(0, bottom), (0, bottom + stroke)])
    points.append((center_x, bottom + stroke))
    points.extend(arc(bottom + radius, inner_radius, -90, 0))
    points.append((width - stroke, top - radius))
    points.extend(arc(top - radius, inner_radius, 0, 90))
    points.append((0, top - stroke))
    contour(pen, points)


def glyph_from(draw):
    target, pen = cubic_pen()
    draw(pen)
    return target.glyph()


def empty_glyph():
    target = TTGlyphPen(None)
    return target.glyph()


def draw_notdef(pen):
    round_rect(pen, 60, 0, 660, CAP, 70)
    round_rect(pen, 175, 115, 545, CAP - 115, 32, reverse=True)
    stroke_line(pen, 175, 115, 545, CAP - 115, 58)
    stroke_line(pen, 175, CAP - 115, 545, 115, 58)


def draw_o(pen, width=930):
    round_rect(pen, 0, 0, width, CAP, ROUND)
    round_rect(pen, STROKE, STROKE, width - STROKE, CAP - STROKE, ROUND - STROKE, reverse=True)


def draw_c(pen, width=790):
    r = ROUND
    ir = ROUND - STROKE
    x0 = 0
    x1 = width
    y0 = 0
    y1 = CAP
    k = 0.5522847498307936
    pen.moveTo((x1, y1))
    pen.lineTo((r, y1))
    pen.curveTo((r - k * r, y1), (x0, y1 - r + k * r), (x0, y1 - r))
    pen.lineTo((x0, r))
    pen.curveTo((x0, r - k * r), (r - k * r, y0), (r, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, STROKE))
    pen.lineTo((STROKE + ir, STROKE))
    pen.curveTo((STROKE + ir - k * ir, STROKE), (STROKE, STROKE + ir - k * ir), (STROKE, STROKE + ir))
    pen.lineTo((STROKE, CAP - STROKE - ir))
    pen.curveTo((STROKE, CAP - STROKE - ir + k * ir), (STROKE + ir - k * ir, CAP - STROKE), (STROKE + ir, CAP - STROKE))
    pen.lineTo((x1, CAP - STROKE))
    pen.closePath()


def draw_d(pen, width=820):
    r = ROUND
    ir = ROUND - STROKE
    k = 0.5522847498307936
    pen.moveTo((0, 0))
    pen.lineTo((width - r, 0))
    pen.curveTo((width - r + k * r, 0), (width, r - k * r), (width, r))
    pen.lineTo((width, CAP - r))
    pen.curveTo((width, CAP - r + k * r), (width - r + k * r, CAP), (width - r, CAP))
    pen.lineTo((0, CAP))
    pen.closePath()
    pen.moveTo((STROKE, STROKE))
    pen.lineTo((STROKE, CAP - STROKE))
    pen.lineTo((width - STROKE - ir, CAP - STROKE))
    pen.curveTo((width - STROKE - ir + k * ir, CAP - STROKE), (width - STROKE, CAP - STROKE - ir + k * ir), (width - STROKE, CAP - STROKE - ir))
    pen.lineTo((width - STROKE, STROKE + ir))
    pen.curveTo((width - STROKE, STROKE + ir - k * ir), (width - STROKE - ir + k * ir, STROKE), (width - STROKE - ir, STROKE))
    pen.closePath()


def draw_e(pen, width=745):
    # The floating cap is intentional, not a damaged connection.
    rect(pen, 0, CAP - STROKE, width, CAP)
    rect(pen, 0, 0, STROKE, 405)
    rect(pen, 0, 294, width - 70, 406)
    rect(pen, 0, 0, width, STROKE)


def draw_f(pen, width=720):
    rect(pen, 0, CAP - STROKE, width, CAP)
    rect(pen, 0, 0, STROKE, 405)
    rect(pen, 0, 294, width - 45, 406)


def draw_h(pen, width=790):
    rect(pen, 0, 0, STROKE, CAP)
    rect(pen, width - STROKE, 0, width, CAP)
    rect(pen, 0, 294, width, 406)


def draw_i(pen, width=STROKE):
    rect(pen, 0, 0, width, CAP)


def draw_j(pen, width=650):
    r = 170
    k = 0.5522847498307936
    pen.moveTo((width - STROKE, CAP))
    pen.lineTo((width, CAP))
    pen.lineTo((width, r))
    pen.curveTo((width, r - k * r), (width - r + k * r, 0), (width - r, 0))
    pen.lineTo((r, 0))
    pen.curveTo((r - k * r, 0), (0, r - k * r), (0, r))
    pen.lineTo((0, 245))
    pen.lineTo((STROKE, 245))
    pen.lineTo((STROKE, r))
    pen.curveTo((STROKE, r - k * (r - STROKE)), (r - k * (r - STROKE), STROKE), (r, STROKE))
    pen.lineTo((width - r, STROKE))
    pen.curveTo((width - r + k * (r - STROKE), STROKE), (width - STROKE, r - k * (r - STROKE)), (width - STROKE, r))
    pen.closePath()


def draw_k(pen, width=790):
    rect(pen, 0, 0, STROKE, CAP)
    stroke_line(pen, STROKE * 0.65, 320, width - 28, CAP - 48, STROKE)
    stroke_line(pen, STROKE * 0.70, 365, width - 15, 48, STROKE)


def draw_l(pen, width=640):
    rect(pen, 0, 0, STROKE, CAP)
    rect(pen, 0, 0, width, STROKE)


def draw_m(pen, width=980):
    rect(pen, 0, 0, STROKE, CAP)
    rect(pen, width - STROKE, 0, width, CAP)
    stroke_line(pen, STROKE * 0.62, CAP - 48, width / 2, 285, STROKE)
    stroke_line(pen, width / 2, 285, width - STROKE * 0.62, CAP - 48, STROKE)


def draw_n(pen, width=820):
    rect(pen, 0, 0, STROKE, CAP)
    rect(pen, width - STROKE, 0, width, CAP)
    stroke_line(pen, STROKE * 0.64, CAP - 48, width - STROKE * 0.64, 48, STROKE)


def draw_p(pen, width=820):
    open_bowl(pen, width, include_stem=True)


def draw_q(pen, width=930):
    draw_o(pen, width)
    stroke_line(pen, width * 0.58, 205, width + 35, -55, 82)


def draw_r(pen, width=820):
    # Floating cap and half-height left stem.
    leg_outline = clipped_stroke_outline(528, 350, 716, 45, STROKE, 294)
    open_bowl(pen, width, include_stem=True, leg_outline=leg_outline)


def draw_s(pen, width=760):
    radius = STROKE / 2
    rounded_bar(pen, 0, CAP - STROKE, width, CAP, radius)
    rounded_bar(pen, 0, CAP / 2 - STROKE / 2, width, CAP / 2 + STROKE / 2, radius)
    rounded_bar(pen, 0, 0, width, STROKE, radius)
    # Vertical and horizontal capsules meet at common centre points, yielding
    # proper round joins after deterministic overlap removal.
    rounded_bar(pen, 0, CAP / 2 - STROKE / 2, STROKE, CAP, radius)
    rounded_bar(pen, width - STROKE, 0, width, CAP / 2 + STROKE / 2, radius)


def draw_t(pen, width=780):
    rect(pen, 0, CAP - STROKE, width, CAP)
    rect(pen, width / 2 - STROKE / 2, 0, width / 2 + STROKE / 2, CAP)


def draw_u(pen, width=820):
    r = 210
    k = 0.5522847498307936
    pen.moveTo((0, CAP))
    pen.lineTo((STROKE, CAP))
    pen.lineTo((STROKE, r))
    pen.curveTo((STROKE, r - k * (r - STROKE)), (r - k * (r - STROKE), STROKE), (r, STROKE))
    pen.lineTo((width - r, STROKE))
    pen.curveTo((width - r + k * (r - STROKE), STROKE), (width - STROKE, r - k * (r - STROKE)), (width - STROKE, r))
    pen.lineTo((width - STROKE, CAP))
    pen.lineTo((width, CAP))
    pen.lineTo((width, r))
    pen.curveTo((width, r - k * r), (width - r + k * r, 0), (width - r, 0))
    pen.lineTo((r, 0))
    pen.curveTo((r - k * r, 0), (0, r - k * r), (0, r))
    pen.closePath()


def draw_v(pen, width=900):
    contour(
        pen,
        [
            (0, CAP),
            (width / 2 - 64, 0),
            (width / 2 + 64, 0),
            (width, CAP),
            (width - 128, CAP),
            (width / 2, 150),
            (128, CAP),
        ],
    )


def draw_w(pen, width=1160):
    stroke_line(pen, 70, CAP - 48, width * 0.25, 48, STROKE)
    stroke_line(pen, width * 0.25, 48, width * 0.5, 425, STROKE)
    stroke_line(pen, width * 0.5, 425, width * 0.75, 48, STROKE)
    stroke_line(pen, width * 0.75, 48, width - 70, CAP - 48, STROKE)


def draw_x(pen, width=900):
    stroke_line(pen, 70, CAP - 48, width - 70, 48, STROKE)
    stroke_line(pen, width - 70, CAP - 48, 70, 48, STROKE)


def draw_y(pen, width=900):
    stroke_line(pen, 70, CAP - 48, width / 2, 330, STROKE)
    stroke_line(pen, width - 70, CAP - 48, width / 2, 330, STROKE)
    rect(pen, width / 2 - STROKE / 2, 0, width / 2 + STROKE / 2, 350)


def draw_z(pen, width=780):
    rect(pen, 0, CAP - STROKE, width, CAP)
    stroke_line(pen, width - 70, CAP - 70, 70, 70, STROKE)
    rect(pen, 0, 0, width, STROKE)


def draw_a(pen, width=920):
    contour(
        pen,
        [
            (0, 0),
            (142, 0),
            (width / 2, 565),
            (width - 142, 0),
            (width, 0),
            (width / 2 + 70, CAP),
            (width / 2 - 70, CAP),
        ],
    )
    # The crossbar is deliberately finer than the main structural stroke.
    rect(pen, width * 0.28, 265, width * 0.72, 265 + THIN)


def draw_b(pen, width=760):
    # One continuous silhouette avoids the seams produced by intersecting two
    # independently rounded bowls.
    pen.moveTo((0, 0))
    pen.lineTo((width - 130, 0))
    pen.curveTo((width - 50, 0), (width, 50), (width, 125))
    pen.lineTo((width, 240))
    pen.curveTo((width, 300), (width - 35, 330), (width - 92, 350))
    pen.curveTo((width - 35, 370), (width, 400), (width, 460))
    pen.lineTo((width, 575))
    pen.curveTo((width, 650), (width - 50, 700), (width - 130, 700))
    pen.lineTo((0, 700))
    pen.closePath()
    round_rect(pen, 130, 112, width - 120, 294, 34, reverse=True)
    round_rect(pen, 130, 406, width - 120, 588, 34, reverse=True)


def draw_g(pen, width=820):
    draw_c(pen, width)
    rect(pen, width * 0.52, 294, width, 406)
    rect(pen, width - STROKE, 0, width, 406)


def draw_zero(pen):
    draw_o(pen, 790)
    stroke_line(pen, 225, 95, 565, 605, 62)


def draw_one(pen):
    stroke_line(pen, 150, 560, 355, CAP, STROKE)
    rect(pen, 300, 0, 412, CAP)
    rect(pen, 100, 0, 610, STROKE)


def draw_two(pen):
    width = 720
    rounded_bar(pen, 0, CAP - STROKE, width, CAP, STROKE / 2)
    rounded_bar(pen, width - STROKE, 350, width, CAP, STROKE / 2)
    stroke_line(pen, width - STROKE / 2, 390, STROKE / 2, STROKE / 2, STROKE)
    rect(pen, 0, 0, width, STROKE)


def draw_three(pen):
    width = 700
    rounded_bar(pen, 0, CAP - STROKE, width, CAP, STROKE / 2)
    rounded_bar(pen, 80, 294, width, 406, STROKE / 2)
    rounded_bar(pen, 0, 0, width, STROKE, STROKE / 2)
    rounded_bar(pen, width - STROKE, CAP / 2, width, CAP, STROKE / 2)
    rounded_bar(pen, width - STROKE, 0, width, CAP / 2, STROKE / 2)


def draw_four(pen):
    width = 760
    stroke_line(pen, STROKE / 2, 260, 530, CAP, STROKE)
    rect(pen, 0, 240, width, 352)
    rect(pen, width - 180, 0, width - 68, CAP)


def draw_five(pen):
    width = 720
    rounded_bar(pen, 0, CAP - STROKE, width, CAP, STROKE / 2)
    rounded_bar(pen, 0, 294, width, 406, STROKE / 2)
    rounded_bar(pen, 0, 0, width, STROKE, STROKE / 2)
    rounded_bar(pen, 0, CAP / 2, STROKE, CAP, STROKE / 2)
    rounded_bar(pen, width - STROKE, 0, width, CAP / 2, STROKE / 2)


def draw_six(pen):
    draw_c(pen, 760)
    rounded_bar(pen, 0, 0, 760, STROKE, STROKE / 2)
    rounded_bar(pen, 760 - STROKE, 0, 760, 390, STROKE / 2)
    rounded_bar(pen, 0, 294, 760, 406, STROKE / 2)


def draw_seven(pen):
    width = 760
    rect(pen, 0, CAP - STROKE, width, CAP)
    stroke_line(pen, width - STROKE / 2, CAP - STROKE / 2, 235, 0, STROKE)


def draw_eight(pen):
    width = 760
    round_rect(pen, 0, 0, width, CAP, 175)
    round_rect(pen, STROKE, STROKE, width - STROKE, CAP / 2 - THIN / 2, 68, reverse=True)
    round_rect(pen, STROKE, CAP / 2 + THIN / 2, width - STROKE, CAP - STROKE, 68, reverse=True)


def draw_nine(pen):
    width = 760
    round_rect(pen, 0, 294, width, CAP, 145)
    round_rect(pen, STROKE, 406, width - STROKE, CAP - STROKE, 55, reverse=True)
    rounded_bar(pen, width - STROKE, 0, width, CAP, STROKE / 2)
    rounded_bar(pen, 0, 294, width, 406, STROKE / 2)


LETTER_DRAWERS = {
    "A": draw_a,
    "B": draw_b,
    "C": draw_c,
    "D": draw_d,
    "E": draw_e,
    "F": draw_f,
    "G": draw_g,
    "H": draw_h,
    "I": draw_i,
    "J": draw_j,
    "K": draw_k,
    "L": draw_l,
    "M": draw_m,
    "N": draw_n,
    "O": draw_o,
    "P": draw_p,
    "Q": draw_q,
    "R": draw_r,
    "S": draw_s,
    "T": draw_t,
    "U": draw_u,
    "V": draw_v,
    "W": draw_w,
    "X": draw_x,
    "Y": draw_y,
    "Z": draw_z,
}

LETTER_WIDTHS = {
    "A": 920,
    "B": 760,
    "C": 790,
    "D": 820,
    "E": 745,
    "F": 720,
    "G": 820,
    "H": 790,
    "I": 112,
    "J": 650,
    "K": 790,
    "L": 640,
    "M": 980,
    "N": 820,
    "O": 930,
    "P": 820,
    "Q": 965,
    "R": 820,
    "S": 760,
    "T": 780,
    "U": 820,
    "V": 900,
    "W": 1160,
    "X": 900,
    "Y": 900,
    "Z": 780,
}

DIGIT_DRAWERS = {
    "zero": draw_zero,
    "one": draw_one,
    "two": draw_two,
    "three": draw_three,
    "four": draw_four,
    "five": draw_five,
    "six": draw_six,
    "seven": draw_seven,
    "eight": draw_eight,
    "nine": draw_nine,
}

DIGIT_WIDTHS = {name: 790 if name in {"zero", "six", "eight", "nine"} else 760 for name in DIGIT_DRAWERS}


def punctuation():
    return {
        "period": (lambda p: round_rect(p, 0, 0, STROKE, STROKE, 28), 112),
        "comma": (lambda p: (round_rect(p, 0, 0, STROKE, STROKE, 28), stroke_line(p, 70, 35, 5, -135, 48)), 125),
        "colon": (lambda p: (round_rect(p, 0, 80, STROKE, 192, 28), round_rect(p, 0, 508, STROKE, 620, 28)), 112),
        "semicolon": (lambda p: (round_rect(p, 0, 80, STROKE, 192, 28), round_rect(p, 0, 508, STROKE, 620, 28), stroke_line(p, 70, 115, 5, -55, 48)), 125),
        "hyphen": (lambda p: rect(p, 0, 294, 430, 406), 430),
        "underscore": (lambda p: rect(p, 0, -90, 620, -28), 620),
        "slash": (lambda p: stroke_line(p, 0, -60, 460, 760, 76), 460),
        "backslash": (lambda p: stroke_line(p, 0, 760, 460, -60, 76), 460),
        "plus": (lambda p: (rect(p, 0, 294, 620, 406), rect(p, 254, 40, 366, 660)), 620),
        "equal": (lambda p: (rect(p, 0, 205, 620, 317), rect(p, 0, 423, 620, 535)), 620),
        "parenleft": (lambda p: (stroke_line(p, 260, CAP, 70, CAP / 2, 78), stroke_line(p, 70, CAP / 2, 260, 0, 78)), 330),
        "parenright": (lambda p: (stroke_line(p, 70, CAP, 260, CAP / 2, 78), stroke_line(p, 260, CAP / 2, 70, 0, 78)), 330),
        "exclam": (lambda p: (rect(p, 0, 180, STROKE, CAP), round_rect(p, 0, 0, STROKE, STROKE, 28)), 112),
        "question": (lambda p: (rounded_bar(p, 0, CAP - STROKE, 510, CAP, STROKE / 2), rounded_bar(p, 398, 380, 510, CAP, STROKE / 2), stroke_line(p, 454, 410, 250, 255, 86), rect(p, 205, 180, 317, 290), round_rect(p, 205, 0, 317, STROKE, 28)), 510),
    }


def build(output_path: Path):
    glyphs = {".notdef": glyph_from(draw_notdef), "space": empty_glyph()}
    metrics = {".notdef": (780, 30), "space": (420, 0)}
    cmap = {32: "space"}

    side = 88
    for char, draw in LETTER_DRAWERS.items():
        glyphs[char] = glyph_from(draw)
        metrics[char] = (LETTER_WIDTHS[char] + side * 2, side)
        cmap[ord(char)] = char
        cmap[ord(char.lower())] = char

    # A narrower display alternate is available through OpenType ss01.
    glyphs["A.label"] = glyph_from(lambda pen: draw_a(pen, 860))
    metrics["A.label"] = (860 + side * 2, side)

    digit_names = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    for value, name in enumerate(digit_names):
        glyphs[name] = glyph_from(DIGIT_DRAWERS[name])
        metrics[name] = (DIGIT_WIDTHS[name] + side * 2, side)
        cmap[ord(str(value))] = name

    punctuation_map = {
        "period": ".",
        "comma": ",",
        "colon": ":",
        "semicolon": ";",
        "hyphen": "-",
        "underscore": "_",
        "slash": "/",
        "backslash": "\\",
        "plus": "+",
        "equal": "=",
        "parenleft": "(",
        "parenright": ")",
        "exclam": "!",
        "question": "?",
    }
    for name, (draw, width) in punctuation().items():
        glyphs[name] = glyph_from(draw)
        metrics[name] = (width + side * 2, side)
        cmap[ord(punctuation_map[name])] = name

    glyph_order = list(glyphs)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER, lineGap=100)
    fb.setupNameTable(
        {
            "familyName": FAMILY,
            "styleName": STYLE,
            "uniqueFontIdentifier": f"Orrae Labs LLC:{PS_NAME}:{VERSION}",
            "fullName": f"{FAMILY} {STYLE}",
            "psName": PS_NAME,
            "version": f"Version {VERSION}",
            "manufacturer": "Orrae Labs LLC",
            "designer": "Orrae Labs LLC",
            "description": "Custom caps-only Orrae Sans typeface.",
            "copyright": "Copyright 2026 Orrae Labs LLC. All rights reserved.",
            "licenseDescription": "Copyright Orrae Labs LLC. All rights reserved.",
        }
    )
    fb.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sTypoLineGap=100,
        usWinAscent=ASCENDER,
        usWinDescent=abs(DESCENDER),
        usWeightClass=400,
        usWidthClass=7,
        fsSelection=0x40,
        sxHeight=500,
        sCapHeight=CAP,
        achVendID="ORRA",
    )
    fb.setupPost(italicAngle=0, underlinePosition=-110, underlineThickness=62, isFixedPitch=0)
    fb.setupMaxp()
    fb.setupHead(
        fontRevision=float(VERSION),
        created=BUILD_TIMESTAMP,
        modified=BUILD_TIMESTAMP,
    )
    addOpenTypeFeaturesFromString(
        fb.font,
        """
        feature kern {
          pos O R 45;
          pos R R 43;
          pos R A -9;
          pos A E 5;
          pos L A 45;
          pos L A.label 45;
          pos A B -10;
          pos A.label B 50;
          pos B S 70;
        } kern;
        feature ss01 {
          sub A by A.label;
        } ss01;
        """,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fb.save(output_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_font.py OUTPUT.ttf")
    build(Path(sys.argv[1]).resolve())
