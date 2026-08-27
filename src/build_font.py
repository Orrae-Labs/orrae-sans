#!/usr/bin/env python3
"""Generate the deterministic Orrae Sans UFO source.

The caps-only system uses a shared modular geometry. Lowercase code points
intentionally map to uppercase glyphs.
"""

from __future__ import annotations

import math
import sys
import unicodedata
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.pens.transformPen import TransformPen
from ufoLib2 import Font
from ufoLib2.objects import Anchor, Component


UPM = 1000
ASCENDER = 950
DESCENDER = -300
CAP = 700
STROKE = 112
THIN = 62
ROUND = 250
VERSION_MAJOR = 1
VERSION_MINOR = 0
FAMILY = "Orrae Sans"
STYLE = "Regular"
PS_NAME = "OrraeSans-Regular"
COPYRIGHT = (
    "Copyright 2026 The Orrae Sans Project Authors "
    "(https://github.com/Orrae-Labs/orrae-sans)"
)
LICENSE = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)


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


def draw_quote(pen, double=False, low=False):
    y0 = 40 if low else 510
    y1 = 235 if low else CAP
    rounded_bar(pen, 0, y0, 72, y1, 32)
    stroke_line(pen, 42, y0 + 40, 2, y0 - 55, 34)
    if double:
        rounded_bar(pen, 150, y0, 222, y1, 32)
        stroke_line(pen, 192, y0 + 40, 152, y0 - 55, 34)


def draw_bracket(pen, right=False):
    x = 230 if right else 0
    rect(pen, x, 0, x + 70, CAP)
    rect(pen, 0, CAP - 70, 300, CAP)
    rect(pen, 0, 0, 300, 70)


def draw_brace(pen, right=False):
    target = TransformPen(pen, (-1, 0, 0, 1, 300, 0)) if right else pen
    rounded_bar(target, 0, CAP - 70, 170, CAP, 35)
    rounded_bar(target, 0, 0, 170, 70, 35)
    rounded_bar(target, 100, 315, 230, 385, 35)
    rect(target, 0, 70, 70, 630)


def draw_chevron(pen, right=False, double=False):
    starts = [0, 210] if double else [0]
    for start in starts:
        if right:
            stroke_line(pen, start + 15, 630, start + 240, 350, 72)
            stroke_line(pen, start + 240, 350, start + 15, 70, 72)
        else:
            stroke_line(pen, start + 240, 630, start + 15, 350, 72)
            stroke_line(pen, start + 15, 350, start + 240, 70, 72)


def draw_ring_outline(pen, diameter=250, stroke=62, y=225):
    round_rect(pen, 0, y, diameter, y + diameter, diameter / 2)
    round_rect(
        pen,
        stroke,
        y + stroke,
        diameter - stroke,
        y + diameter - stroke,
        diameter / 2 - stroke,
        reverse=True,
    )


def draw_percent(pen):
    draw_ring_outline(pen, 220, 55, 465)
    draw_ring_outline(TransformPen(pen, (1, 0, 0, 1, 430, -465)), 220, 55, 465)
    stroke_line(pen, 125, 35, 535, 665, 70)


def draw_ampersand(pen):
    round_rect(pen, 80, 270, 570, CAP, 150)
    round_rect(pen, 180, 375, 470, 595, 55, reverse=True)
    round_rect(pen, 0, 0, 670, 420, 150)
    round_rect(pen, 115, 105, 515, 310, 55, reverse=True)
    stroke_line(pen, 390, 255, 720, -10, 92)


def draw_at(pen):
    round_rect(pen, 0, -35, 850, CAP, 250)
    round_rect(pen, STROKE, 77, 738, CAP - STROKE, 140, reverse=True)
    draw_o(TransformPen(pen, (0.55, 0, 0, 0.55, 282, 155)), 650)
    rounded_bar(pen, 630, 160, 742, 475, 50)


def draw_hash(pen):
    stroke_line(pen, 210, -25, 310, 725, 70)
    stroke_line(pen, 510, -25, 610, 725, 70)
    rect(pen, 65, 205, 735, 285)
    rect(pen, 85, 440, 755, 520)


def draw_asterisk(pen):
    stroke_line(pen, 300, 125, 300, 620, 70)
    stroke_line(pen, 85, 250, 515, 495, 70)
    stroke_line(pen, 515, 250, 85, 495, 70)


def draw_currency(pen, kind):
    if kind in {"cent", "dollar"}:
        draw_c(pen, 620)
        stroke_line(pen, 335, -80, 335, 780, 58)
        if kind == "dollar":
            rect(pen, 275, 0, 620, STROKE)
            rect(pen, 0, CAP - STROKE, 355, CAP)
    elif kind == "pound":
        rounded_bar(pen, 115, 0, 700, STROKE, 45)
        rounded_bar(pen, 95, 285, 585, 385, 45)
        stroke_line(pen, 245, 30, 350, 610, 100)
        rounded_bar(pen, 295, 588, 650, CAP, 50)
    elif kind == "yen":
        draw_y(pen, 720)
        rect(pen, 130, 235, 590, 305)
        rect(pen, 160, 375, 560, 445)
    elif kind == "euro":
        draw_c(pen, 730)
        rect(pen, 0, 225, 570, 305)
        rect(pen, 0, 395, 570, 475)


def draw_section(pen):
    draw_s(TransformPen(pen, (0.82, 0, 0, 0.82, 55, 145)), 760)
    draw_s(TransformPen(pen, (0.82, 0, 0, 0.82, 55, -145)), 760)


def draw_pilcrow(pen):
    round_rect(pen, 0, 280, 650, CAP, 190)
    round_rect(pen, 112, 392, 430, 588, 65, reverse=True)
    rect(pen, 430, 0, 542, CAP)
    rect(pen, 255, 0, 367, 390)


def draw_copyright_like(pen, letter):
    draw_ring_outline(pen, 700, 78, 0)
    drawer = draw_c if letter == "C" else draw_r
    inner_width = 430 if letter == "C" else 450
    drawer(TransformPen(pen, (0.56, 0, 0, 0.56, 145, 155)), inner_width)


def draw_trademark(pen):
    draw_t(TransformPen(pen, (0.6, 0, 0, 0.6, 0, 280)), 600)
    draw_m(TransformPen(pen, (0.55, 0, 0, 0.55, 430, 280)), 850)


def draw_math_cross(pen):
    stroke_line(pen, 70, 90, 550, 610, 82)
    stroke_line(pen, 550, 90, 70, 610, 82)


def draw_divide(pen):
    rect(pen, 0, 310, 620, 390)
    round_rect(pen, 260, 520, 360, 620, 30)
    round_rect(pen, 260, 80, 360, 180, 30)


def draw_question(pen, inverted=False):
    target = TransformPen(pen, (1, 0, 0, -1 if inverted else 1, 0, CAP if inverted else 0))
    rounded_bar(target, 0, CAP - STROKE, 510, CAP, STROKE / 2)
    rounded_bar(target, 398, 380, 510, CAP, STROKE / 2)
    stroke_line(target, 454, 410, 250, 255, 86)
    rect(target, 205, 180, 317, 290)
    round_rect(target, 205, 0, 317, STROKE, 28)


def draw_exclam(pen, inverted=False):
    target = TransformPen(pen, (1, 0, 0, -1 if inverted else 1, 0, CAP if inverted else 0))
    rect(target, 0, 180, STROKE, CAP)
    round_rect(target, 0, 0, STROKE, STROKE, 28)


def draw_generic_symbol(pen, cp):
    # Remaining symbols use a restrained, legible construction from the same
    # stroke vocabulary as the alphabet.
    if cp == 0x00B0:
        draw_ring_outline(pen, 250, 62, 420)
    elif cp == 0x00B7:
        round_rect(pen, 0, 294, STROKE, 406, 28)
    elif cp == 0x2022:
        round_rect(pen, 0, 235, 230, 465, 115)
    elif cp == 0x2026:
        for x in (0, 210, 420):
            round_rect(pen, x, 0, x + STROKE, STROKE, 28)
    else:
        draw_ring_outline(pen, 360, 70, 170)


def draw_dotted_circle(pen):
    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        x = 300 + 225 * math.cos(radians)
        y = 350 + 225 * math.sin(radians)
        round_rect(pen, x - 42, y - 42, x + 42, y + 42, 30)


COMBINING_MARK_NAMES = {
    0x0300: "gravecomb",
    0x0301: "acutecomb",
    0x0302: "circumflexcomb",
    0x0303: "tildecomb",
    0x0304: "macroncomb",
    0x0306: "brevecomb",
    0x0307: "dotaccentcomb",
    0x0308: "dieresiscomb",
    0x030A: "ringcomb",
    0x030B: "hungarumlautcomb",
    0x030C: "caroncomb",
    0x0326: "commaaccentcomb",
    0x0327: "cedillacomb",
    0x0328: "ogonekcomb",
}

SPACING_TO_COMBINING = {
    0x0060: 0x0300,
    0x00A8: 0x0308,
    0x00AF: 0x0304,
    0x00B4: 0x0301,
    0x00B8: 0x0327,
    0x02C6: 0x0302,
    0x02C7: 0x030C,
    0x02D8: 0x0306,
    0x02D9: 0x0307,
    0x02DA: 0x030A,
    0x02DB: 0x0328,
    0x02DC: 0x0303,
    0x02DD: 0x030B,
}


def draw_mark(pen, cp):
    if cp == 0x0300:
        stroke_line(pen, -125, 895, 60, 750, 58)
    elif cp == 0x0301:
        stroke_line(pen, -60, 750, 125, 895, 58)
    elif cp == 0x0302:
        stroke_line(pen, -150, 765, 0, 900, 52)
        stroke_line(pen, 0, 900, 150, 765, 52)
    elif cp == 0x0303:
        stroke_line(pen, -175, 795, -55, 865, 48)
        stroke_line(pen, -55, 865, 55, 795, 48)
        stroke_line(pen, 55, 795, 175, 865, 48)
    elif cp == 0x0304:
        rounded_bar(pen, -175, 805, 175, 865, 25)
    elif cp == 0x0306:
        pen.moveTo((-175, 885))
        pen.curveTo((-130, 735), (130, 735), (175, 885))
        pen.lineTo((115, 900))
        pen.curveTo((75, 810), (-75, 810), (-115, 900))
        pen.closePath()
    elif cp == 0x0307:
        round_rect(pen, -55, 790, 55, 900, 35)
    elif cp == 0x0308:
        round_rect(pen, -150, 790, -50, 890, 32)
        round_rect(pen, 50, 790, 150, 890, 32)
    elif cp == 0x030A:
        round_rect(pen, -100, 755, 100, 955, 100)
        round_rect(pen, -42, 813, 42, 897, 42, reverse=True)
    elif cp == 0x030B:
        stroke_line(pen, -170, 750, -25, 895, 50)
        stroke_line(pen, 25, 750, 170, 895, 50)
    elif cp == 0x030C:
        stroke_line(pen, -150, 895, 0, 760, 52)
        stroke_line(pen, 0, 760, 150, 895, 52)
    elif cp in {0x0326, 0x0327}:
        stroke_line(pen, 45, -45, -45, -205, 54)
        rounded_bar(pen, -45, -205, 70, -145, 25)
    elif cp == 0x0328:
        stroke_line(pen, 45, -15, -45, -165, 54)
        rounded_bar(pen, -45, -205, 85, -145, 25)


CORE_CODEPOINTS = {
    0x0024,0x0025,0x0026,0x002B,0x003C,0x003D,0x003E,0x0040,0x005E,0x007C,0x007E,0x00A2,
    0x00A3,0x00A5,0x00A7,0x00A9,0x00AE,0x00B0,0x00B6,0x00D7,0x00F7,0x20AC,0x2122,0x2212,
    0x0020,0x00A0,0x0021,0x0022,0x0023,0x0027,0x0028,0x0029,0x002A,0x002C,0x002D,0x002E,
    0x002F,0x003A,0x003B,0x003F,0x005B,0x005C,0x005D,0x005F,0x007B,0x007D,0x00A1,0x00AB,
    0x00B7,0x00BB,0x00BF,0x2013,0x2014,0x2018,0x2019,0x201A,0x201C,0x201D,0x201E,0x2022,
    0x2026,0x2039,0x203A,0x0030,0x0031,0x0032,0x0033,0x0034,0x0035,0x0036,0x0037,0x0038,
    0x0039,0x0060,0x00A8,0x00AF,0x00B4,0x00B8,0x02C6,0x02C7,0x02D8,0x02D9,0x02DA,0x02DB,
    0x02DC,0x02DD,0x0300,0x0301,0x0302,0x0303,0x0304,0x0306,0x0307,0x0308,0x030A,0x030B,
    0x030C,0x0326,0x0327,0x0328,0x0041,0x0042,0x0043,0x0044,0x0045,0x0046,0x0047,0x0048,
    0x0049,0x004A,0x004B,0x004C,0x004D,0x004E,0x004F,0x0050,0x0051,0x0052,0x0053,0x0054,
    0x0055,0x0056,0x0057,0x0058,0x0059,0x005A,0x0061,0x0062,0x0063,0x0064,0x0065,0x0066,
    0x0067,0x0068,0x0069,0x006A,0x006B,0x006C,0x006D,0x006E,0x006F,0x0070,0x0071,0x0072,
    0x0073,0x0074,0x0075,0x0076,0x0077,0x0078,0x0079,0x007A,0x00AA,0x00BA,0x00C0,0x00C1,
    0x00C2,0x00C3,0x00C4,0x00C5,0x00C6,0x00C7,0x00C8,0x00C9,0x00CA,0x00CB,0x00CC,0x00CD,
    0x00CE,0x00CF,0x00D0,0x00D1,0x00D2,0x00D3,0x00D4,0x00D5,0x00D6,0x00D8,0x00D9,0x00DA,
    0x00DB,0x00DC,0x00DD,0x00DE,0x00DF,0x00E0,0x00E1,0x00E2,0x00E3,0x00E4,0x00E5,0x00E6,
    0x00E7,0x00E8,0x00E9,0x00EA,0x00EB,0x00EC,0x00ED,0x00EE,0x00EF,0x00F0,0x00F1,0x00F2,
    0x00F3,0x00F4,0x00F5,0x00F6,0x00F8,0x00F9,0x00FA,0x00FB,0x00FC,0x00FD,0x00FE,0x00FF,
    0x0100,0x0101,0x0102,0x0103,0x0104,0x0105,0x0106,0x0107,0x010A,0x010B,0x010C,0x010D,
    0x010E,0x010F,0x0110,0x0111,0x0112,0x0113,0x0116,0x0117,0x0118,0x0119,0x011A,0x011B,
    0x011E,0x011F,0x0120,0x0121,0x0122,0x0123,0x0126,0x0127,0x012A,0x012B,0x012E,0x012F,
    0x0130,0x0131,0x0136,0x0137,0x0139,0x013A,0x013B,0x013C,0x013D,0x013E,0x0141,0x0142,
    0x0143,0x0144,0x0145,0x0146,0x0147,0x0148,0x0150,0x0151,0x0152,0x0153,0x0154,0x0155,
    0x0158,0x0159,0x015A,0x015B,0x015E,0x015F,0x0160,0x0161,0x0164,0x0165,0x016A,0x016B,
    0x016E,0x016F,0x0170,0x0171,0x0172,0x0173,0x0174,0x0175,0x0176,0x0177,0x0178,0x0179,
    0x017A,0x017B,0x017C,0x017D,0x017E,0x0218,0x0219,0x021A,0x021B,0x0237,0x1E80,0x1E81,
    0x1E82,0x1E83,0x1E84,0x1E85,0x1E9E,0x1EF2,0x1EF3,
}


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


def glyph_name(cp):
    return UV2AGL.get(cp) or f"uni{cp:04X}"


def add_anchor(glyph, name, x, y):
    glyph.anchors.append(Anchor(x=x, y=y, name=name))


def add_outline(font, name, unicodes, draw, design_width, side=88, anchors=False):
    glyph = font.newGlyph(name)
    glyph.width = design_width + side * 2
    glyph.unicodes = list(unicodes)
    draw(TransformPen(glyph.getPen(), (1, 0, 0, 1, side, 0)))
    if anchors:
        add_anchor(glyph, "top", glyph.width / 2, CAP)
        add_anchor(glyph, "bottom", glyph.width / 2, 0)
    return glyph


def add_components(font, name, unicodes, width, components, top_y=CAP):
    glyph = font.newGlyph(name)
    glyph.width = width
    glyph.unicodes = list(unicodes)
    for base, transform in components:
        glyph.components.append(Component(base, transformation=transform))
    add_anchor(glyph, "top", width / 2, top_y)
    add_anchor(glyph, "bottom", width / 2, 0)
    return glyph


def draw_ae(pen):
    draw_a(pen, 900)
    rect(pen, 510, CAP - STROKE, 1120, CAP)
    rect(pen, 510, 294, 1050, 406)
    rect(pen, 510, 0, 1120, STROKE)


def draw_oe(pen):
    draw_o(pen, 840)
    rect(pen, 505, CAP - STROKE, 1120, CAP)
    rect(pen, 505, 294, 1050, 406)
    rect(pen, 505, 0, 1120, STROKE)


def draw_eth(pen):
    draw_d(pen, 820)
    rect(pen, -45, 294, 500, 406)


def draw_oslash(pen):
    draw_o(pen, 930)
    stroke_line(pen, 95, -45, 835, 745, 78)


def draw_hbar(pen):
    draw_h(pen, 790)
    rect(pen, -45, 480, 835, 560)


def draw_lslash(pen):
    draw_l(pen, 640)
    stroke_line(pen, -20, 190, 520, 510, 78)


def symbol_drawers():
    existing = punctuation()
    symbols = {
        0x0021: ("exclam", 112, lambda p: draw_exclam(p)),
        0x0022: ("quotedbl", 222, lambda p: draw_quote(p, double=True)),
        0x0023: ("numbersign", 800, draw_hash),
        0x0024: ("dollar", 620, lambda p: draw_currency(p, "dollar")),
        0x0025: ("percent", 650, draw_percent),
        0x0026: ("ampersand", 720, draw_ampersand),
        0x0027: ("quotesingle", 72, draw_quote),
        0x0028: ("parenleft", existing["parenleft"][1], existing["parenleft"][0]),
        0x0029: ("parenright", existing["parenright"][1], existing["parenright"][0]),
        0x002A: ("asterisk", 600, draw_asterisk),
        0x002B: ("plus", existing["plus"][1], existing["plus"][0]),
        0x002C: ("comma", existing["comma"][1], existing["comma"][0]),
        0x002D: ("hyphen", existing["hyphen"][1], existing["hyphen"][0]),
        0x002E: ("period", existing["period"][1], existing["period"][0]),
        0x002F: ("slash", existing["slash"][1], existing["slash"][0]),
        0x003A: ("colon", existing["colon"][1], existing["colon"][0]),
        0x003B: ("semicolon", existing["semicolon"][1], existing["semicolon"][0]),
        0x003C: ("less", 620, lambda p: draw_chevron(TransformPen(p, (1, 0, 0, 1, 170, 0)))),
        0x003D: ("equal", existing["equal"][1], existing["equal"][0]),
        0x003E: ("greater", 620, lambda p: draw_chevron(TransformPen(p, (1, 0, 0, 1, 170, 0)), right=True)),
        0x003F: ("question", 510, lambda p: draw_question(p)),
        0x0040: ("at", 850, draw_at),
        0x005B: ("bracketleft", 300, draw_bracket),
        0x005C: ("backslash", existing["backslash"][1], existing["backslash"][0]),
        0x005D: ("bracketright", 300, lambda p: draw_bracket(p, right=True)),
        0x005F: ("underscore", existing["underscore"][1], existing["underscore"][0]),
        0x007B: ("braceleft", 300, draw_brace),
        0x007C: ("bar", 112, lambda p: rect(p, 0, -90, STROKE, 790)),
        0x007D: ("braceright", 300, lambda p: draw_brace(p, right=True)),
        0x00A1: ("exclamdown", 112, lambda p: draw_exclam(p, inverted=True)),
        0x00A2: ("cent", 620, lambda p: draw_currency(p, "cent")),
        0x00A3: ("sterling", 700, lambda p: draw_currency(p, "pound")),
        0x00A5: ("yen", 720, lambda p: draw_currency(p, "yen")),
        0x00A7: ("section", 730, draw_section),
        0x00A9: ("copyright", 700, lambda p: draw_copyright_like(p, "C")),
        0x00AB: ("guillemotleft", 490, lambda p: draw_chevron(p, double=True)),
        0x00AE: ("registered", 700, lambda p: draw_copyright_like(p, "R")),
        0x00B0: ("degree", 250, lambda p: draw_generic_symbol(p, 0x00B0)),
        0x00B6: ("paragraph", 650, draw_pilcrow),
        0x00B7: ("periodcentered", 112, lambda p: draw_generic_symbol(p, 0x00B7)),
        0x00BB: ("guillemotright", 490, lambda p: draw_chevron(p, right=True, double=True)),
        0x00BF: ("questiondown", 510, lambda p: draw_question(p, inverted=True)),
        0x00D7: ("multiply", 620, draw_math_cross),
        0x00F7: ("divide", 620, draw_divide),
        0x2013: ("endash", 650, lambda p: rect(p, 0, 310, 650, 390)),
        0x2014: ("emdash", 1000, lambda p: rect(p, 0, 310, 1000, 390)),
        0x2018: ("quoteleft", 72, draw_quote),
        0x2019: ("quoteright", 72, draw_quote),
        0x201A: ("quotesinglbase", 72, lambda p: draw_quote(p, low=True)),
        0x201C: ("quotedblleft", 222, lambda p: draw_quote(p, double=True)),
        0x201D: ("quotedblright", 222, lambda p: draw_quote(p, double=True)),
        0x201E: ("quotedblbase", 222, lambda p: draw_quote(p, double=True, low=True)),
        0x2022: ("bullet", 230, lambda p: draw_generic_symbol(p, 0x2022)),
        0x2026: ("ellipsis", 532, lambda p: draw_generic_symbol(p, 0x2026)),
        0x2039: ("guilsinglleft", 280, lambda p: draw_chevron(p)),
        0x203A: ("guilsinglright", 280, lambda p: draw_chevron(p, right=True)),
        0x20AC: ("Euro", 730, lambda p: draw_currency(p, "euro")),
        0x2122: ("trademark", 900, draw_trademark),
        0x2212: ("minus", 620, lambda p: rect(p, 0, 310, 620, 390)),
    }
    return symbols


def configure_info(font):
    info = font.info
    info.familyName = FAMILY
    info.styleName = STYLE
    info.styleMapFamilyName = FAMILY
    info.styleMapStyleName = "regular"
    info.unitsPerEm = UPM
    info.ascender = ASCENDER
    info.descender = DESCENDER
    info.capHeight = CAP
    info.xHeight = CAP
    info.versionMajor = VERSION_MAJOR
    info.versionMinor = VERSION_MINOR
    info.copyright = COPYRIGHT
    info.openTypeHeadCreated = "2026/08/26 00:00:00"
    info.openTypeHeadLowestRecPPEM = 8
    info.openTypeHheaAscender = ASCENDER
    info.openTypeHheaDescender = DESCENDER
    info.openTypeHheaLineGap = 0
    info.openTypeNameDescription = "A wide caps-only display typeface."
    info.openTypeNameDesigner = "TJ Challstrom"
    info.openTypeNameDesignerURL = "https://github.com/Orrae-Labs/orrae-sans"
    info.openTypeNameManufacturer = "Orrae Labs LLC"
    info.openTypeNameManufacturerURL = "https://orrae.com"
    info.openTypeNameLicense = LICENSE
    info.openTypeNameLicenseURL = "https://openfontlicense.org"
    info.openTypeNameUniqueID = "1.000;NONE;OrraeSans-Regular"
    info.openTypeNameVersion = "Version 1.000"
    info.openTypeOS2CodePageRanges = [0]
    # Bit 6 (Regular) is derived from styleMapStyleName by the compiler.
    info.openTypeOS2Selection = [7]
    info.openTypeOS2Type = []
    info.openTypeOS2TypoAscender = ASCENDER
    info.openTypeOS2TypoDescender = DESCENDER
    info.openTypeOS2TypoLineGap = 0
    info.openTypeOS2VendorID = "NONE"
    info.openTypeOS2WeightClass = 400
    info.openTypeOS2WidthClass = 7
    info.openTypeOS2WinAscent = 1000
    info.openTypeOS2WinDescent = 300
    info.openTypeGaspRangeRecords = [
        {"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}
    ]
    info.postscriptBlueValues = [0, 0, 700, 700]
    info.postscriptFontName = PS_NAME
    info.postscriptFullName = f"{FAMILY} {STYLE}"
    info.postscriptIsFixedPitch = False
    info.postscriptUnderlinePosition = -110
    info.postscriptUnderlineThickness = 62
    info.postscriptWeightName = STYLE


def build(output_path: Path):
    font = Font()
    configure_info(font)
    side = 88

    add_outline(font, ".notdef", [], draw_notdef, 720, side=30)
    for name, unicodes, width in (
        ("space", [0x0020], 420),
        ("nbspace", [0x00A0], 420),
    ):
        glyph = font.newGlyph(name)
        glyph.width = width
        glyph.unicodes = unicodes

    for char, draw in LETTER_DRAWERS.items():
        extra = []
        if char == "I":
            extra.append(0x0131)
        if char == "J":
            extra.append(0x0237)
        add_outline(
            font,
            char,
            [ord(char), ord(char.lower()), *extra],
            draw,
            LETTER_WIDTHS[char],
            anchors=True,
        )

    add_outline(font, "A.label", [], lambda p: draw_a(p, 860), 860, anchors=True)

    for value, name in enumerate(DIGIT_DRAWERS):
        add_outline(font, name, [ord(str(value))], DIGIT_DRAWERS[name], DIGIT_WIDTHS[name])

    for cp, (name, width, draw) in symbol_drawers().items():
        add_outline(font, name, [cp], draw, width)

    add_outline(font, "uni25CC", [0x25CC], draw_dotted_circle, 600, anchors=True)

    SPACING_TO_COMBINING.update({0x005E: 0x0302, 0x007E: 0x0303})
    for cp, mark_cp in sorted(SPACING_TO_COMBINING.items()):
        name = glyph_name(cp)
        glyph = font.newGlyph(name)
        glyph.width = 420
        glyph.unicodes = [cp]
        draw_mark(TransformPen(glyph.getPen(), (1, 0, 0, 1, 210, -40)), mark_cp)

    for cp, name in COMBINING_MARK_NAMES.items():
        glyph = font.newGlyph(name)
        glyph.width = 0
        glyph.unicodes = [cp]
        draw_mark(glyph.getPen(), cp)
        if cp < 0x0320:
            add_anchor(glyph, "_top", 0, CAP)
            add_anchor(glyph, "top", 0, 960)
        else:
            add_anchor(glyph, "_bottom", 0, 0)
            add_anchor(glyph, "bottom", 0, -220)

    caron_alt = font.newGlyph("caron.alt")
    caron_alt.width = 0
    stroke_line(caron_alt.getPen(), 55, 885, -25, 715, 54)
    add_anchor(caron_alt, "_top", 0, CAP)

    specials = [
        ("AE", [0x00C6, 0x00E6], draw_ae, 1120),
        ("Eth", [0x00D0, 0x00F0, 0x0110, 0x0111], draw_eth, 820),
        ("Oslash", [0x00D8, 0x00F8], draw_oslash, 930),
        ("Thorn", [0x00DE, 0x00FE], draw_p, 820),
        ("germandbls", [0x00DF, 0x1E9E], draw_b, 760),
        ("Hbar", [0x0126, 0x0127], draw_hbar, 790),
        ("Lslash", [0x0141, 0x0142], draw_lslash, 640),
        ("OE", [0x0152, 0x0153], draw_oe, 1120),
    ]
    handled = set()
    for name, unicodes, draw, width in specials:
        add_outline(font, name, unicodes, draw, width, anchors=True)
        handled.update(unicodes)

    add_components(
        font,
        "ordfeminine",
        [0x00AA],
        720,
        [("A", (0.6, 0, 0, 0.6, 30, 260))],
        top_y=CAP,
    )
    add_components(
        font,
        "ordmasculine",
        [0x00BA],
        720,
        [("O", (0.6, 0, 0, 0.6, 15, 260))],
        top_y=CAP,
    )
    handled.update({0x00AA, 0x00BA, 0x0131, 0x0237})

    composite_groups = {}
    for cp in sorted(CORE_CODEPOINTS):
        if cp in handled or any(cp in glyph.unicodes for glyph in font):
            continue
        decomposed = unicodedata.normalize("NFD", chr(cp))
        if len(decomposed) < 2:
            continue
        base = decomposed[0].upper()
        marks = tuple(ord(char) for char in decomposed[1:])
        if base in LETTER_DRAWERS and all(mark in COMBINING_MARK_NAMES for mark in marks):
            composite_groups.setdefault((base, marks), []).append(cp)

    for (base, marks), unicodes in composite_groups.items():
        preferred = next((cp for cp in unicodes if chr(cp).isupper()), unicodes[0])
        name = glyph_name(preferred)
        width = font[base].width
        components = [(base, (1, 0, 0, 1, 0, 0))]
        top_count = 0
        bottom_count = 0
        for mark in marks:
            if mark < 0x0320:
                y_offset = top_count * 190
                top_count += 1
            else:
                y_offset = -bottom_count * 170
                bottom_count += 1
            mark_name = COMBINING_MARK_NAMES[mark]
            if mark == 0x030C and base in {"D", "L", "T"}:
                mark_name = "caron.alt"
            components.append((mark_name, (1, 0, 0, 1, width / 2, y_offset)))
        add_components(
            font,
            name,
            unicodes,
            width,
            components,
            top_y=CAP + top_count * 190,
        )
        handled.update(unicodes)

    missing = CORE_CODEPOINTS - {cp for glyph in font for cp in glyph.unicodes}
    if missing:
        formatted = ", ".join(f"U+{cp:04X}" for cp in sorted(missing))
        raise RuntimeError(f"GF Latin Core coverage is incomplete: {formatted}")

    font.features.text = """
languagesystem DFLT dflt;
languagesystem latn dflt;

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
  featureNames {
    name "Narrow A";
  };
  sub A by A.label;
} ss01;
""".strip() + "\n"

    font.glyphOrder = [glyph.name for glyph in font]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(output_path, overwrite=True, validate=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_font.py OUTPUT.ufo")
    build(Path(sys.argv[1]).resolve())
