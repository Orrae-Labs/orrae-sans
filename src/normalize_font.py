#!/usr/bin/env python3
"""Remove converter timestamps so Orrae Sans binaries are reproducible."""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont


BUILD_TIMESTAMP = 3_870_547_200  # 2026-08-26 00:00:00 UTC, seconds since 1904.


def normalize(path: Path):
    font = TTFont(path, recalcTimestamp=False)
    if "FFTM" in font:
        del font["FFTM"]
    font["head"].created = BUILD_TIMESTAMP
    font["head"].modified = BUILD_TIMESTAMP
    font.recalcTimestamp = False
    font.save(path, reorderTables=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: normalize_font.py FONT [FONT ...]")
    for filename in sys.argv[1:]:
        normalize(Path(filename).resolve())
