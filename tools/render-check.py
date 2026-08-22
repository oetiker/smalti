#!/usr/bin/env python3
"""Rasterise a traced .ttf and prove it is pixel-identical to the strike.

Usage: render-check.py FACE.bdf FACE.ttf [--sizes 14,28,42]

check-outlines.py proves the OUTLINE is the right shape.  This proves the
claim that shape was chosen for: because upem is the cell height times 64,
at a ppem equal to the cell height -- and at every integer multiple of it --
FreeType lands every pixel edge on a device pixel boundary, so the rendered
coverage is 0 or 255 everywhere and matches the bitmap exactly.  No grey, no
rounding, nothing to hint.

Needs freetype-py; `make venv` installs it.
"""

import argparse
import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "trace_outline", os.path.join(_here, "trace-outline.py"))
trace_outline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trace_outline)


def rendered(face, cp, ppem):
    """Lit device pixels of one glyph, as cells relative to the origin."""
    import freetype
    face.set_pixel_sizes(0, ppem)
    face.load_char(cp, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    slot = face.glyph
    bmp = slot.bitmap
    lit, grey = set(), 0
    for r in range(bmp.rows):
        row = bmp.buffer[r * bmp.pitch:r * bmp.pitch + bmp.width]
        for c, v in enumerate(row):
            if v == 255:
                lit.add((slot.bitmap_left + c, slot.bitmap_top - 1 - r))
            elif v != 0:
                grey += 1
    return lit, grey, slot.advance.x >> 6


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bdf")
    ap.add_argument("ttf")
    ap.add_argument("--sizes", default="14,28,42")
    args = ap.parse_args()

    import freetype
    props, glyphs = trace_outline.parse_bdf(args.bdf)
    cell_w = int(props["QUAD_WIDTH"])
    face = freetype.Face(args.ttf)

    bad = 0
    for ppem in (int(s) for s in args.sizes.split(",")):
        s = ppem // (int(props["FONT_ASCENT"]) + int(props["FONT_DESCENT"]))
        mism = greyed = advbad = 0
        for g in glyphs:
            if not g.codepoint:                 # skip U+0000 / unencoded
                continue
            want = {(s * x + i, s * y + j)
                    for (x, y) in g.lit() for i in range(s) for j in range(s)}
            got, grey, adv = rendered(face, g.codepoint, ppem)
            if got != want:
                mism += 1
            if grey:
                greyed += 1
            if adv != s * cell_w:
                advbad += 1
        bad += mism + greyed + advbad
        print(f"    {ppem:3d} ppem ({s}x): {len(glyphs) - 1} glyphs, "
              f"{mism} differ from the bitmap, "
              f"{greyed} have an antialiased pixel, "
              f"{advbad} have a wrong advance")
    return 1 if bad else 0


if __name__ == "__main__":
    print(f"{os.path.basename(sys.argv[2] if len(sys.argv) > 2 else '')}")
    sys.exit(main())
