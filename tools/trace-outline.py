#!/usr/bin/env python3
"""Trace one BDF strike into an outline TrueType font.

Usage: trace-outline.py IN.bdf OUT.ttf

WHY OUTLINES AT ALL
    The .otb files this repo also builds are bitmap-only, and a bitmap-only
    font is invisible to most of the system: fontconfig's
    /etc/fonts/conf.d/70-no-bitmaps-except-emoji.conf rejects anything with
    outline=false, and no browser renders an embedded bitmap strike.  An
    outline font works everywhere, including in a web specimen.

WHY ONE FILE PER STRIKE
    Outlines cannot vary with cell size.  The only mechanism that would --
    a variable font's `opsz` axis -- needs interpolation-compatible masters,
    and the same glyph at 5x9 and 10x20 is a different number of rectangles
    in different places.  So each strike becomes its own font file,
    carrying the metrics of that strike alone.

THE EM IS A WHOLE NUMBER OF PIXELS
    upem = cell_height * 64, so one pixel is exactly 64 units -- 896 for
    7x14.  At ppem equal to the cell height a pixel edge at unit k*64 lands
    on device pixel k exactly: no rounding, no antialiasing, indistinguish-
    able from the strike.  The mapping is linear, so every integer multiple
    is exact too (14, 28, 42 px).  Only sizes between multiples blur.

THE TRACE IS AN EXACT RECTANGLE UNION, NOT A CURVE FIT
    potrace and friends fit smooth curves to pixel edges, which is precisely
    the wrong thing for a pixel font.  Here each lit pixel contributes the
    sides that border an unlit pixel, directed so the ink stays on the left;
    the directed edges are then walked into closed loops and collinear runs
    are merged.  Every coordinate is an integer multiple of 64 and every
    segment is axis-aligned, by construction.

    THE ONE HARD CASE is two pixels touching only at a corner.  That vertex
    carries two incoming and two outgoing edges, so a naive point-keyed
    lookup loses one and the walk dies with a KeyError.  Resolve it by
    pairing each arrival with the sharpest RIGHT turn.  Either pairing is
    correct -- the winding number of any point is a sum over edges and does
    not depend on how the edges are grouped into loops -- so the choice only
    decides whether such a shape comes out as one pinched ring or as several
    rectangles whose union is the same region.  Do not chase minimal
    contours; tools/check-outlines.py proves the fill instead, by comparing
    the signed area against the lit pixel count.

THE OUTPUT MUST BE BYTE-REPRODUCIBLE
    The acceptance test for any future change to the glyph store is that the
    files the build emits are byte-identical before and after -- that is what
    proves a restructuring moved no pixel.  Once outlines exist, the files
    that test compares are these .ttf, so a wall-clock stamp anywhere in them
    would silently destroy the test: every build would differ and nothing
    could ever be compared again.  A release artefact could not be
    re-derived from its tag either.

    head.created and head.modified are therefore never "now".  They come
    from SOURCE_DATE_EPOCH when the environment sets it -- the
    reproducible-builds convention, which also lets CI pin them -- and from
    the fixed constant below when it does not.  fontTools' own default IS
    the wall clock, so this must be set explicitly; leaving it to
    FontBuilder is the bug this paragraph exists to prevent.

    Everything else here is already order-stable by construction: glyph
    order is sorted by codepoint, the edge list is built from `sorted(lit)`,
    and the contour walk consumes that list in order.  No dict or set
    iteration order reaches the output.

WHY NOT fonttosfnt + repair-tamzen.py
    This path never runs fonttosfnt, so it does not inherit its broken name
    table either: nameID 6 (PostScript name) is written, nameID 5 carries the
    real version rather than "Version 0.0", and nameID 10 is a whole
    sentence.  head.macStyle and OS/2 fsSelection are set from one place, so
    they cannot disagree.
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs      # noqa: E402  (needs the path insert above)

PX = 64                      # font units per pixel; see the docstring

# The build stamp when SOURCE_DATE_EPOCH is unset.  A committed constant, not
# the clock -- see "THE OUTPUT MUST BE BYTE-REPRODUCIBLE" above.  This is
# 2026-01-01T00:00:00Z, the year Smalti forked from Tamzen.
FALLBACK_EPOCH = 1767225600


def build_epoch():
    """Unix seconds to stamp into head.created / head.modified."""
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is None or not raw.strip():
        return FALLBACK_EPOCH
    try:
        return int(raw.strip())
    except ValueError:
        raise SystemExit(f"SOURCE_DATE_EPOCH is not an integer: {raw!r}")

# ---------------------------------------------------------------- BDF input


class Glyph:
    __slots__ = ("name", "codepoint", "dwidth", "bbx", "rows")

    def __init__(self, name, codepoint, dwidth, bbx, rows):
        self.name = name
        self.codepoint = codepoint
        self.dwidth = dwidth
        self.bbx = bbx           # (w, h, xoff, yoff) in pixels
        self.rows = rows         # list of ints, one per row, top row first

    def lit(self):
        """The lit pixels as a set of integer cells, x right, y up."""
        w, h, xoff, yoff = self.bbx
        out = set()
        for r, bits in enumerate(self.rows):
            y = yoff + h - 1 - r
            for c in range(w):
                if bits >> (w - 1 - c) & 1:
                    out.add((xoff + c, y))
        return out


def parse_bdf(path):
    """Return (properties, [Glyph, ...]).  Properties are strings or ints."""
    props, glyphs = {}, []
    with open(path, encoding="latin-1") as fh:
        lines = fh.read().splitlines()

    i, n = 0, len(lines)
    while i < n:
        line = lines[i].strip()
        if line.startswith("STARTCHAR"):
            name = line.split(None, 1)[1] if " " in line else ""
            cp, dwidth, bbx, rows = None, None, None, []
            i += 1
            while i < n and not lines[i].strip().startswith("ENDCHAR"):
                f = lines[i].split()
                if not f:
                    i += 1
                    continue
                if f[0] == "ENCODING":
                    cp = int(f[1])
                elif f[0] == "DWIDTH":
                    dwidth = int(f[1])
                elif f[0] == "BBX":
                    bbx = tuple(int(v) for v in f[1:5])
                elif f[0] == "BITMAP":
                    i += 1
                    while i < n and not lines[i].strip().startswith("ENDCHAR"):
                        rows.append(int(lines[i].strip(), 16))
                        i += 1
                    break
                i += 1
            if bbx is None:
                raise SystemExit(f"{path}: glyph {name} has no BBX")
            w, h = bbx[0], bbx[1]
            if len(rows) != h:
                raise SystemExit(
                    f"{path}: glyph {name} has {len(rows)} rows, BBX says {h}")
            # BDF pads each row to a whole number of bytes; drop the padding.
            pad = (-w) % 8
            rows = [v >> pad for v in rows]
            glyphs.append(Glyph(name, cp, dwidth, bbx, rows))
        elif line.startswith("ENDPROPERTIES") or line.startswith("CHARS "):
            i += 1
        else:
            m = re.match(r'^([A-Z_0-9]+)\s+(.*)$', line)
            if m and not glyphs:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                props[key] = val
        i += 1
    return props, glyphs


# ------------------------------------------------------------- the tracer


def _edges(lit):
    """Directed unit edges bordering the ink, ink on the left (CCW outers)."""
    out = []
    for (x, y) in sorted(lit):
        if (x, y - 1) not in lit:
            out.append(((x, y), (x + 1, y)))            # bottom, rightwards
        if (x + 1, y) not in lit:
            out.append(((x + 1, y), (x + 1, y + 1)))    # right, upwards
        if (x, y + 1) not in lit:
            out.append(((x + 1, y + 1), (x, y + 1)))    # top, leftwards
        if (x - 1, y) not in lit:
            out.append(((x, y + 1), (x, y)))            # left, downwards
    return out


def _dir(edge):
    (ax, ay), (bx, by) = edge
    return (bx - ax, by - ay)


def _turn_rank(d, e):
    """0 = sharpest right, 1 = straight on, 2 = left, 3 = reverse."""
    cross = d[0] * e[1] - d[1] * e[0]
    if cross < 0:
        return 0
    if cross > 0:
        return 2
    return 1 if (d[0] * e[0] + d[1] * e[1]) > 0 else 3


def _successors(edges):
    """Pair every incoming edge with an outgoing one at each vertex.

    Degree is 1 or 2 in each direction (a vertex has four neighbouring
    pixels, and an edge is emitted per litness change around it, so the
    count of changes is 0, 2 or 4).  Degree 2 is the corner-touch case:
    pair each arrival with the sharpest right turn.
    """
    ins, outs = defaultdict(list), defaultdict(list)
    for e in edges:
        outs[e[0]].append(e)
        ins[e[1]].append(e)

    succ = {}
    for v, o_list in outs.items():
        i_list = ins[v]
        assert len(i_list) == len(o_list) <= 2, (v, i_list, o_list)
        if len(o_list) == 1:
            succ[i_list[0]] = o_list[0]
            continue
        taken = set()
        for e in i_list:
            d = _dir(e)
            best = min((o for o in o_list if id(o) not in taken),
                       key=lambda o: _turn_rank(d, _dir(o)))
            taken.add(id(best))
            succ[e] = best
        assert len(taken) == len(o_list)
    return succ


def _walk(edges, succ):
    """Consume every edge into closed loops of vertices."""
    loops, seen = [], set()
    for start in edges:
        if id(start) in seen:
            continue
        loop, e = [], start
        while id(e) not in seen:
            seen.add(id(e))
            loop.append(e[0])
            e = succ[e]
        assert e is start, "walk did not close on its own start"
        loops.append(loop)
    return loops


def _simplify(loop):
    """Drop the interior points of every collinear run."""
    n = len(loop)
    out = []
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
            out.append(b)
    return out


def trace(lit):
    """Lit pixel cells -> list of contours, each a list of (x, y) in units."""
    edges = _edges(lit)
    if not edges:
        return []
    loops = _walk(edges, _successors(edges))
    return [[(x * PX, y * PX) for (x, y) in _simplify(loop)] for loop in loops]


def signed_area(contours):
    """Twice the signed area, in square font units, doubled (shoelace sum)."""
    total = 0
    for c in contours:
        for i in range(len(c)):
            (x1, y1), (x2, y2) = c[i - 1], c[i]
            total += x1 * y2 - x2 * y1
    return total


# ------------------------------------------------------------- font output

def glyph_name(cp):
    return "uni%04X" % cp if cp <= 0xFFFF else "u%05X" % cp


STYLES = {
    ("Medium", "R"): ("Regular",     0x0000, 0x0040, 400, 5),
    ("Bold",   "R"): ("Bold",        0x0001, 0x0020, 700, 8),
    ("Medium", "I"): ("Italic",      0x0002, 0x0001, 400, 5),
    ("Bold",   "I"): ("Bold Italic", 0x0003, 0x0021, 700, 8),
}

DESCRIPTION = (
    "Smalti is a pixel font.  Its outlines are an exact union of the pixels "
    "of a %(cell)s bitmap, one pixel to %(px)d units of a %(upem)d-unit em, "
    "so at %(ppem)d ppem and every integer multiple of it the outline lands "
    "on whole device pixels and renders exactly as the bitmap does."
)

LICENSE = (
    "This font is free.  You are hereby granted permission to use, copy, "
    "modify, and distribute it as you see fit."
)


def build_font(props, glyphs, out_path, family_base=None):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable
    from fontTools.misc.timeTools import timestampSinceEpoch

    cell_w = int(props["QUAD_WIDTH"])
    ascent_px = int(props["FONT_ASCENT"])
    descent_px = int(props["FONT_DESCENT"])
    cell_h = ascent_px + descent_px
    upem = cell_h * PX

    weight_name = props.get("WEIGHT_NAME", "Medium")
    slant = props.get("SLANT", "R")
    try:
        style, mac_style, fs_sel, weight_class, panose_weight = \
            STYLES[(weight_name, slant)]
    except KeyError:
        raise SystemExit(f"unknown face: WEIGHT_NAME={weight_name} SLANT={slant}")

    family = family_base or props.get("FAMILY_NAME", "Smalti")
    ps_family = re.sub(r"[^A-Za-z0-9]", "", family)
    ps_style = style.replace(" ", "")
    version = props.get("FONT_VERSION", "1.0")

    # The oblique faces are a shear of two pixels over the cell height; see
    # tools/slant-bdf.py.  post.italicAngle is negative for a right lean.
    import math
    italic_angle = -round(math.degrees(math.atan2(2, cell_h)), 1) if slant == "I" else 0.0

    by_cp = {}
    notdef_glyph = None
    for g in glyphs:
        if g.codepoint is None or g.codepoint < 0:
            continue
        if g.codepoint == 0:
            notdef_glyph = g
        else:
            by_cp[g.codepoint] = g

    order = [".notdef"] + [glyph_name(cp) for cp in sorted(by_cp)]
    sources = {".notdef": notdef_glyph}
    sources.update({glyph_name(cp): g for cp, g in by_cp.items()})

    tt_glyphs, metrics, points = {}, {}, 0
    for name in order:
        g = sources.get(name)
        contours = trace(g.lit()) if g is not None else []
        pen = TTGlyphPen(None)
        for c in contours:
            pen.moveTo(c[0])
            for pt in c[1:]:
                pen.lineTo(pt)
            pen.closePath()
        tt_glyphs[name] = pen.glyph()
        points += sum(len(c) for c in contours)
        advance = (g.dwidth if g is not None and g.dwidth else cell_w) * PX
        lsb = min((x for c in contours for x, _ in c), default=0)
        metrics[name] = (advance, lsb)

    fb = FontBuilder(upem, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp: glyph_name(cp) for cp in by_cp})
    fb.setupGlyf(tt_glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent_px * PX,
                             descent=-descent_px * PX,
                             lineGap=0)

    full = f"{family} {style}"
    ps_name = f"{ps_family}-{ps_style}"
    fb.setupNameTable({
        "copyright": props.get("COPYRIGHT", ""),
        "familyName": family,
        "styleName": style,
        "uniqueFontIdentifier": f"{full}; Version {version}",
        "fullName": full,
        "version": f"Version {version}",
        "psName": ps_name,
        "description": DESCRIPTION % {
            "cell": f"{cell_w}x{cell_h}", "px": PX,
            "upem": upem, "ppem": cell_h},
        "licenseDescription": LICENSE,
    })

    fb.setupOS2(
        version=4,
        sTypoAscender=ascent_px * PX,
        sTypoDescender=-descent_px * PX,
        sTypoLineGap=0,
        usWinAscent=ascent_px * PX,
        usWinDescent=descent_px * PX,
        sxHeight=int(props.get("X_HEIGHT", 0)) * PX,
        sCapHeight=int(props.get("CAP_HEIGHT", 0)) * PX,
        xAvgCharWidth=cell_w * PX,
        usWeightClass=weight_class,
        usWidthClass=5,
        fsType=0,
        fsSelection=fs_sel,
        achVendID="OETI",
        panose=dict(bFamilyType=2, bSerifStyle=11, bWeight=panose_weight,
                    bProportion=9, bContrast=0, bStrokeVariation=0,
                    bArmStyle=0, bLetterForm=0, bMidline=0, bXHeight=0),
        ulCodePageRange1=0x00000001,
    )
    fb.setupPost(italicAngle=italic_angle,
                 underlinePosition=-PX,
                 underlineThickness=PX,
                 isFixedPitch=1)
    fb.font["OS/2"].recalcUnicodeRanges(fb.font)

    head = fb.font["head"]
    head.macStyle = mac_style
    head.lowestRecPPEM = cell_h
    # Not float(version): a semantic version has three parts and float() dies
    # on the second dot.  See glyphstore.font_revision for the encoding.
    head.fontRevision = gs.font_revision(version)
    # Not the wall clock.  See the docstring: byte-identity of these files is
    # the acceptance test for every future glyph-store change.
    stamp = timestampSinceEpoch(build_epoch())
    head.created = head.modified = stamp
    # A pixel font has no curves to smooth and no hints to run: ask for
    # grey-scale rendering at every size and leave grid-fitting off.
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x0002}
    fb.font["gasp"] = gasp

    fb.save(out_path)
    return {"style": style, "glyphs": len(order), "points": points,
            "upem": upem, "advance": cell_w * PX}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bdf")
    ap.add_argument("ttf")
    ap.add_argument("--family", default=None,
                    help="family name; default is the BDF's FAMILY_NAME")
    args = ap.parse_args()

    props, glyphs = parse_bdf(args.bdf)
    info = build_font(props, glyphs, args.ttf, args.family)
    print(f"{args.ttf}  {info['style']}: {info['glyphs']} glyphs, "
          f"{info['points']} points "
          f"({info['points'] / info['glyphs']:.1f} per glyph), "
          f"upem {info['upem']}, advance {info['advance']}")


if __name__ == "__main__":
    main()
