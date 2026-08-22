#!/usr/bin/env python3
"""Prove a traced .ttf is the same shape as the .bdf strike it came from.

Usage: check-outlines.py FACE.bdf FACE.ttf [FACE.bdf FACE.ttf ...]

Three checks, run over EVERY glyph of every face given -- not a spot check:

  1. SIGNED FILLED AREA == LIT PIXEL COUNT.  The shoelace sum over the
     contours, divided by 64*64, must equal the number of `#` in the source
     bitmap.  This is the test that proves the fill: the winding number of
     any point is a sum over the directed edges, so the area being right
     means the ink is in exactly the right places, whatever the tracer did
     about corner-touching pixels and however many contours it emitted.
  2. EVERY SEGMENT IS AXIS-ALIGNED.  No diagonal, no curve -- every point
     on-curve, and consecutive points share an x or a y.
  3. EVERY COORDINATE IS ON THE PIXEL GRID, an integer multiple of 64.

It also reports the mean points per glyph, which is the file-size cost.

Reads the compiled font rather than the tracer's own data structures, so a
bug in the pen or in glyf compilation cannot hide from it.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "trace_outline",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace-outline.py"))
trace_outline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trace_outline)

PX = trace_outline.PX


def contours_of(glyf, glyph_name):
    """[(x, y, on_curve), ...] per contour, in glyf's own coordinates."""
    g = glyf[glyph_name]
    if g.numberOfContours == 0:
        return []
    if g.numberOfContours < 0:
        raise SystemExit(f"{glyph_name}: composite glyph, not expected here")
    coords, ends, flags = g.coordinates, g.endPtsOfContours, g.flags
    out, start = [], 0
    for end in ends:
        pts = [(coords[i][0], coords[i][1], bool(flags[i] & 0x01))
               for i in range(start, end + 1)]
        out.append(pts)
        start = end + 1
    return out


def check_face(bdf_path, ttf_path):
    from fontTools.ttLib import TTFont

    props, glyphs = trace_outline.parse_bdf(bdf_path)
    font = TTFont(ttf_path)
    glyf = font["glyf"]
    upem = font["head"].unitsPerEm

    lit_by_name = {}
    for g in glyphs:
        if g.codepoint is None or g.codepoint < 0:
            continue
        name = ".notdef" if g.codepoint == 0 else trace_outline.glyph_name(g.codepoint)
        lit_by_name[name] = len(g.lit())

    checked = area_bad = seg_bad = grid_bad = curve_bad = 0
    points = 0
    worst = (0, None)
    failures = []

    for name in font.getGlyphOrder():
        if name not in lit_by_name:
            failures.append(f"{name}: in the font but not in the BDF")
            continue
        cs = contours_of(glyf, name)
        n = sum(len(c) for c in cs)
        points += n
        if n > worst[0]:
            worst = (n, name)

        # 1. signed area
        two_a = 0
        for c in cs:
            for i in range(len(c)):
                x1, y1, _ = c[i - 1]
                x2, y2, _ = c[i]
                two_a += x1 * y2 - x2 * y1
        if two_a % (2 * PX * PX):
            failures.append(f"{name}: area {two_a / 2} units^2 is not a whole pixel")
            area_bad += 1
        elif two_a // (2 * PX * PX) != lit_by_name[name]:
            failures.append(f"{name}: area {two_a // (2 * PX * PX)} px "
                            f"!= {lit_by_name[name]} lit px")
            area_bad += 1

        # 2/3. geometry
        bad_seg = bad_grid = bad_curve = False
        for c in cs:
            for i in range(len(c)):
                x1, y1, on1 = c[i - 1]
                x2, y2, on2 = c[i]
                if not on2:
                    bad_curve = True
                if x1 != x2 and y1 != y2:
                    bad_seg = True
                if x2 % PX or y2 % PX:
                    bad_grid = True
        if bad_seg:
            seg_bad += 1
            failures.append(f"{name}: has a segment that is not axis-aligned")
        if bad_grid:
            grid_bad += 1
            failures.append(f"{name}: has a coordinate off the {PX}-unit grid")
        if bad_curve:
            curve_bad += 1
            failures.append(f"{name}: has an off-curve point")
        checked += 1

    style = font["name"].getDebugName(2)
    print(f"{os.path.basename(ttf_path)}  [{style}]  upem {upem}")
    print(f"    glyphs checked ............ {checked}")
    print(f"    area != lit pixel count ... {area_bad}")
    print(f"    non-axis-aligned segments . {seg_bad}")
    print(f"    off-grid coordinates ...... {grid_bad}")
    print(f"    off-curve points .......... {curve_bad}")
    print(f"    points .................... {points} "
          f"({points / checked:.1f} per glyph, worst {worst[0]} in {worst[1]})")
    for f in failures[:20]:
        print(f"    FAIL {f}")
    if len(failures) > 20:
        print(f"    ... and {len(failures) - 20} more")
    return checked, points, len(failures)


def main():
    args = sys.argv[1:]
    if not args or len(args) % 2:
        raise SystemExit(__doc__)
    total_g = total_p = total_f = 0
    for i in range(0, len(args), 2):
        g, p, f = check_face(args[i], args[i + 1])
        total_g += g
        total_p += p
        total_f += f
    print(f"\nTOTAL: {total_g} glyphs, {total_f} discrepancies, "
          f"{total_p / total_g:.1f} points per glyph")
    return 1 if total_f else 0


if __name__ == "__main__":
    sys.exit(main())
