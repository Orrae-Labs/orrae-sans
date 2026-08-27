#!/usr/bin/env python3
"""Apply deterministic, cross-platform OpenType production settings."""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.ttProgram import Program


BUILD_TIMESTAMP = 3_870_547_200  # 2026-08-26 00:00:00 UTC, seconds since 1904.


def normalize(path: Path):
    font = TTFont(path, recalcTimestamp=False)
    if "FFTM" in font:
        del font["FFTM"]
    font["head"].created = BUILD_TIMESTAMP
    font["head"].modified = BUILD_TIMESTAMP
    font["OS/2"].fsType = 0

    if "glyf" in font and "fpgm" not in font:
        gasp = newTable("gasp")
        gasp.gaspRange = {0xFFFF: 0x0F}
        font["gasp"] = gasp

        program = Program()
        program.fromAssembly(
            ["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"]
        )
        prep = newTable("prep")
        prep.program = program
        font["prep"] = prep

    meta = newTable("meta")
    meta.data = {"dlng": "Latn", "slng": "Latn"}
    font["meta"] = meta
    font.recalcTimestamp = False
    font.save(path, reorderTables=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: normalize_font.py FONT [FONT ...]")
    for filename in sys.argv[1:]:
        normalize(Path(filename).resolve())
