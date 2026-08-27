#!/usr/bin/env fontforge
"""Normalize overlaps and emit production font containers with FontForge."""

import fontforge
import sys


if len(sys.argv) != 4:
    raise SystemExit("usage: clean_font.py INPUT.ttf OUTPUT.ttf OUTPUT.otf")

source, ttf_output, otf_output = sys.argv[1:]
font = fontforge.open(source)
font.selection.all()
font.unlinkReferences()
font.removeOverlap()
font.simplify()
font.removeOverlap()
font.correctDirection()
font.addExtrema()
font.round()

# Font-level overlap removal can leave a zero-area contour where a straight bar
# and a curved band meet. Resolve only glyphs that still report an intersection;
# this preserves the otherwise stable cleanup behavior across the family.
for glyph in font.glyphs():
    if glyph.selfIntersects():
        glyph.removeOverlap()
        glyph.simplify()
        glyph.removeOverlap()
        glyph.correctDirection()
        glyph.addExtrema()
        glyph.round()

font.generate(ttf_output, flags=("opentype",))
font.generate(otf_output, flags=("opentype",))
font.close()
