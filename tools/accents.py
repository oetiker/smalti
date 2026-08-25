#!/usr/bin/env python3
"""Read a BDF and derive accent masks by subtracting a base letter.

Tamzen already draws grave, acute, circumflex, tilde, diaeresis, ring and
cedilla -- on 'a', 'A', 'c' and 'C'.  Subtracting the plain letter from the
accented one recovers the mark exactly as Tamzen drew it, which is far better
than inventing one.  Marks it does NOT have (macron, breve, dot above, double
acute, caron, ogonek) are defined here by hand, in the same weight.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

def load(path):
    """{codepoint: h-row bitmap}, every row re-anchored to the font's own
    FONTBOUNDINGBOX -- see _fit() for why that re-anchoring is needed.
    """
    text = open(path, encoding='latin1').read()
    cell = tuple(int(v) for v in re.search(
        r'^FONTBOUNDINGBOX (\d+) (\d+) (-?\d+) (-?\d+)', text, re.M).groups())
    out = {}
    for chunk in text.split('STARTCHAR ')[1:]:
        body = chunk.partition('ENDCHAR')[0]
        cp = int(re.search(r'^ENCODING (\d+)', body, re.M).group(1))
        bbx = tuple(int(v) for v in re.search(
            r'^BBX (\d+) (\d+) (-?\d+) (-?\d+)', body, re.M).groups())
        rows = [int(r.strip(), 16)
                for r in body.partition('BITMAP\n')[2].strip().split('\n')]
        out[cp] = _fit(rows, bbx, cell)
    return out

def _fit(rows, bbx, cell):
    """Re-express one glyph's rows in the font's own coordinate frame.

    BDF lets a glyph's own BBX diverge from FONTBOUNDINGBOX, and upstream's
    8x16 uses exactly that: sixteen round/ascender lowercase letters (a b d
    g h l m n p q r u w y, plus O Q) get a BBX one row TALLER than the font
    box -- height 17 where FONTBOUNDINGBOX says 16 -- a deliberate 1px
    overshoot at the cap line, same left edge (xoffset 0) and same baseline
    (yoffset -4) as everything else. 7x14 has none of this: every glyph's
    BBX there already equals FONTBOUNDINGBOX, so this is a no-op.

    Every row-index arithmetic downstream (sub(), compose(), raise_to(),
    hand()) assumes row i means the same absolute pixel row in every glyph
    it touches. Left unfit, subtracting a 16-row accented letter from its
    17-row plain base would zip() them index-for-index -- pairing the
    plain letter's extra overshoot row with the accented letter's cap-line
    row, one row off, and silently losing the plain letter's real bottom
    row instead. Anchoring on yoffset first, here, once, makes that
    assumption true instead of assumed.

    Column width and xoffset are NOT re-anchored: every BBX observed in
    either upstream font already agrees with FONTBOUNDINGBOX on both, so
    there is nothing yet to re-anchor there.  A future glyph that
    disagreed would need the same treatment on its columns; assert loudly
    rather than silently mis-render one.
    """
    bw, bh, bxo, byo = bbx
    cw, ch, cxo, cyo = cell
    assert (bw, bxo) == (cw, cxo), (
        f'accents.py: BBX {bbx} disagrees with FONTBOUNDINGBOX {cell} on '
        f'width or x-offset -- _fit() only re-anchors rows, not columns')
    off = (byo + bh) - (cyo + ch)
    return [rows[i + off] if 0 <= i + off < bh else 0 for i in range(ch)]

def sub(acc, base):
    return [a & ~b for a, b in zip(acc, base)]

# Was a fourth inline copy of gs.art(), with its column loop hardcoded to
# range(7) -- silently correct at width 7, silently missing the last column
# at any wider size.  gs.art() is the single definition of that conversion;
# w is the caller's cell width (gs.cell(SIZE)[0], or a BDF's own
# FONTBOUNDINGBOX width), never assumed here.
def art(rows, w):
    return gs.art(rows, w)

def pack(art_rows):
    return [sum(1 << (7 - i) for i, ch in enumerate(r) if ch == '#')
            for r in art_rows]

def marks(g, h):
    """{(mark_codepoint, is_upper): h-row bitmap}.

    h is the caller's cell height (14 at 7x14, 16 at 8x16) -- passed in
    rather than measured off any one glyph in g, because upstream's own
    8x16 BDF gives several round/ascender lowercase letters (a b d g h l m
    n p q r u w y, plus O Q) a BBX one row TALLER than FONTBOUNDINGBOX -- a
    deliberate overshoot in Tamzen's own drawing, still 0 xoffset and the
    same yoffset as everything else, just one more row of ink above the cap
    line. Measuring h from such a glyph would silently make every hand-drawn
    mark composed against it come out that row too tall.
    """
    m = {}
    for cc, lo, up in ((0x300, 0xE0, 0xC0), (0x301, 0xE1, 0xC1),
                       (0x302, 0xE2, 0xC2), (0x303, 0xE3, 0xC3),
                       (0x308, 0xE4, 0xC4), (0x30A, 0xE5, 0xC5)):
        m[cc, False] = sub(g[lo], g[0x61])
        m[cc, True]  = sub(g[up], g[0x41])
    m[0x327, False] = sub(g[0xE7], g[0x63])
    m[0x327, True]  = sub(g[0xC7], g[0x43])

    def hand(cc, lo_top, lo, up_top=None, up=None):
        m[cc, False] = pack(['.......'] * lo_top + lo
                            + ['.......'] * (h - lo_top - len(lo)))
        up, up_top = up or lo, up_top if up_top is not None else lo_top - 2
        m[cc, True] = pack(['.......'] * up_top + up
                           + ['.......'] * (h - up_top - len(up)))

    hand(0x304, 3, ['.#####.'])                       # macron
    hand(0x306, 2, ['.#...#.', '..###..'])            # breve
    hand(0x307, 3, ['...#...'])                       # dot above
    hand(0x30B, 2, ['..#.#..', '.#.#...'])            # double acute
    hand(0x30C, 2, ['.#...#.', '..#.#..'])            # caron
    m[0x328, False] = m[0x328, True] = pack(          # ogonek, below
        ['.......'] * (h - 3) + ['...##..', '.....#.', '...##..'])
    return m
