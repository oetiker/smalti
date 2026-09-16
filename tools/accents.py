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

# The six marks Tamzen does not draw anywhere, written out ONCE PER CELL
# WIDTH as {codepoint: (top row, art rows)}.  A pixel drawing cannot be
# scaled -- the same reason gen-braille.py, gen-arrows.py and
# gen-circled-digits.py each carry a per-size drawing instead of stretching
# one -- and here two separate things make a literal cell-specific.
#
# The visible one is that the letters differ.  7x14 draws its lowercase five
# columns wide starting at column 0; 8x16 draws it six wide starting at
# column 1.  A mark centred on one sits off centre on the other.
#
# The quiet one is that pack() puts literal column i at bit 7-i, and a cell
# reads column x from bit w-1-x.  So literal column i lands at cell column
# i-1 at width 7 and at cell column i at width 8: the same literal does not
# even land in the same place.  The 7x14 art below therefore carries a
# leading '.' that is off the left edge of its own cell.  That is how it has
# always been drawn and it is kept verbatim, because 7x14 is settled and
# shipped; the 8x16 art is written in its own frame instead, where literal
# column and cell column agree.
#
# The 8x16 drawings follow upstream's own 8x16 marks rather than being
# derived from 7x14: the caron is its circumflex turned over ('...##...' /
# '..#..#..' becomes '..#..#..' / '...##...'), the double acute is its acute
# twice over, and the dot above sits in column 4, which is where upstream's
# own 'i' puts its dot.  Only the columns changed -- every mark keeps the
# rows it already occupied, so nothing moves vertically.
HAND_MARKS = {
    7: {
        0x304: (3, ['.#####.']),                      # macron
        0x306: (2, ['.#...#.', '..###..']),           # breve
        0x307: (3, ['...#...']),                      # dot above
        0x30B: (2, ['..#.#..', '.#.#...']),           # double acute
        0x30C: (2, ['.#...#.', '..#.#..']),           # caron
    },
    8: {
        0x304: (3, ['.######.']),                     # macron
        0x306: (2, ['.#....#.', '..####..']),         # breve
        0x307: (3, ['....#...']),                     # dot above
        0x30B: (2, ['...#.#..', '..#.#...']),         # double acute
        0x30C: (2, ['..#..#..', '...##...']),         # caron
    },
}

# The ogonek hangs off the letter's bottom RIGHT, so it is aligned to the
# letter's right edge (column 4 at 7x14, column 6 at 8x16), not centred.
OGONEK = {
    7: ['...##..', '.....#.', '...##..'],
    8: ['....##..', '......#.', '....##..'],
}

def marks(g, h, w):
    """{(mark_codepoint, is_upper): h-row bitmap}.

    h is the caller's cell height (14 at 7x14, 16 at 8x16) -- passed in
    rather than measured off any one glyph in g, because upstream's own
    8x16 BDF gives several round/ascender lowercase letters (a b d g h l m
    n p q r u w y, plus O Q) a BBX one row TALLER than FONTBOUNDINGBOX -- a
    deliberate overshoot in Tamzen's own drawing, still 0 xoffset and the
    same yoffset as everything else, just one more row of ink above the cap
    line. Measuring h from such a glyph would silently make every hand-drawn
    mark composed against it come out that row too tall.

    w is the cell WIDTH, and it is needed for the same kind of reason: the
    marks Tamzen does not draw are written out per cell in HAND_MARKS, and
    picking the wrong set puts every one of them in the wrong column.
    """
    def above(lifted, base):
        """Keep only what the subtraction left ABOVE the base letter's ink.

        A mark above the letter sits above it by definition, so ink the
        subtraction leaves level with the letter is not mark -- it is the two
        donors disagreeing about the letterform.  They do disagree: upstream's
        8x16 'a' carries a spur on its last row that its own 'a-acute' does
        not, so 'a-acute minus a' keeps that pixel, and a mark holding a pixel
        at the letter's own height then collides with every base it is
        composed onto, sending compose() to its raised-comma fallback.

        Subtraction alone was enough at 7x14, where the donors agree above
        the x-height, so this clips nothing off any 7x14 LOWERCASE mark --
        tools/test-accents.py asserts that, and those are the only marks
        gen-latin-ext-a.py composes with.  It does clip 7x14's CAPITAL marks,
        which upstream really does contaminate by squashing the capital under
        its own accent; no output moves, because compose() has always started
        from the lowercase mark and raised it.

        Marks BELOW the letter (cedilla, ogonek) must not come through here.
        """
        top = next(i for i, v in enumerate(base) if v)
        return [v if i < top else 0 for i, v in enumerate(lifted)]

    m = {}
    for cc, lo, up in ((0x300, 0xE0, 0xC0), (0x301, 0xE1, 0xC1),
                       (0x302, 0xE2, 0xC2), (0x303, 0xE3, 0xC3),
                       (0x308, 0xE4, 0xC4), (0x30A, 0xE5, 0xC5)):
        m[cc, False] = above(sub(g[lo], g[0x61]), g[0x61])
        m[cc, True]  = above(sub(g[up], g[0x41]), g[0x41])
    # Cedilla hangs BELOW the letter, so it is lifted by subtraction alone.
    m[0x327, False] = sub(g[0xE7], g[0x63])
    m[0x327, True]  = sub(g[0xC7], g[0x43])

    def hand(cc, lo_top, lo, up_top=None, up=None):
        m[cc, False] = pack(['.' * w] * lo_top + lo
                            + ['.' * w] * (h - lo_top - len(lo)))
        up, up_top = up or lo, up_top if up_top is not None else lo_top - 2
        m[cc, True] = pack(['.' * w] * up_top + up
                           + ['.' * w] * (h - up_top - len(up)))

    for cc, (lo_top, lo) in HAND_MARKS[w].items():
        hand(cc, lo_top, lo)
    m[0x328, False] = m[0x328, True] = pack(          # ogonek, below
        ['.' * w] * (h - 3) + OGONEK[w])
    return m
