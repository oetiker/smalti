#!/usr/bin/env python3
"""Generate Latin Extended-A by composing Tamzen letters with Tamzen marks.

Usage: gen-latin-ext-a.py BASE.bdf OUTDIR

Latin Extended-A is almost entirely base letter + diacritic, so the marks are
lifted out of the glyphs Tamzen already draws (a-grave minus a, and so on)
rather than invented.  That keeps the weight and the pixel rhythm identical to
the rest of the font.

Capitals need the mark higher: Tamzen's own accented capitals squash the
letter to make room, which cannot be reproduced for letters it never drew, so
here the mark is raised instead and the capital stays full height.

This is the one generator that produces the BOLD face as well as the regular
one, and for bold it beats emboldening: Tamzen's own bold letters and bold
accents already exist, so composing against the bold base font invents
nothing.  Run it against upstream's bold BDF and point OUTDIR at the bold
face.  Because tools/embolden.py also writes into that directory, this must
run AFTER it -- see the ordering note in the Makefile.

This writes only into build/gen/, so it is freely re-runnable and cannot
overwrite anyone's work.  To change one letter, draw it: a file in
glyphs/<size>/<face>/ outranks anything here.
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accents
import glyphstore as gs

if len(sys.argv) != 3:
    sys.exit(__doc__)
BDF, OUT = sys.argv[1], sys.argv[2]

# The real cell size, read from the BDF's own FONTBOUNDINGBOX rather than
# hand-parsed from a size string -- this script's only size-bearing input is
# BDF, not a SIZE argument, so gs.Bdf() is the one place that width and
# height can come from without inventing a second, possibly-disagreeing
# source of truth (and, unlike measuring a specific glyph, is not thrown off
# by upstream's own per-glyph overshoot -- see accents.marks()).
_meta = gs.Bdf(BDF)
W, CELLH = _meta.w, _meta.h

g = accents.load(BDF)
mark = accents.marks(g, CELLH)

def rows_used(bm):
    return [i for i, v in enumerate(bm) if v]

def raise_to(bm, bottom):
    """Shift a mark up so its lowest ink row lands on `bottom`."""
    used = rows_used(bm)
    shift = min(used[-1] - bottom, used[0])
    return bm[shift:] + [0] * shift

def compose(base_cp, mark_cp, upper):
    base = g[base_cp]
    # A mark above 'i' or 'j' replaces the dot -- that is the typographic
    # rule, and it is also the only way the mark fits.  Rows 0..4 are above
    # the x-height, so clearing them removes the dot and nothing else.
    if base_cp in (0x69, 0x6A) and mark_cp not in (0x327, 0x328):
        base = [0] * 5 + base[5:]
    # Always start from the LOWERCASE mark.  The uppercase extraction is
    # contaminated: Tamzen squashes the capital under its own accents, so
    # 'A-acute minus A' leaves fragments of the squashed A behind.
    m = mark[mark_cp, False]
    if mark_cp not in (0x327, 0x328):
        m = raise_to(m, 1 if upper else max(rows_used(m)))
    if all(a & b == 0 for a, b in zip(base, m)):
        return [a | b for a, b in zip(base, m)], None
    # Collision: the letter is tall.  Typography's own answer is a raised
    # comma beside the letter rather than a mark on top of it.
    free = [c for c in range(W) if not any(v & (1 << (7 - c)) for v in base)]
    if not free:
        return None, 'no free column'
    col = 1 << (7 - max(free))
    out = list(base)
    out[2] |= col
    out[3] |= col
    return out, f'tall letter -> raised comma in column {max(free)}'

# The letters below are drawn in the regular weight.  For the bold face they
# are emboldened the way Tamzen itself does it -- each stroke widened one pixel
# leftward -- because there is no bold original to copy them from.
BOLD = 'Bold' in re.search(r'^WEIGHT_NAME "([^"]*)"', open(BDF).read(), re.M).group(1)

# The literal art below is pixel-drawn at 7x14 -- unlike the composed
# accents above, there is no formula that stretches a drawing to a taller
# cell, only a person redrawing it (the same reason gen-braille.py,
# gen-arrows.py and gen-circled-digits.py carry a per-size GEOMETRY/guard
# rather than scaling their own drawings). At any other cell size H() is a
# no-op: the codepoint falls through to the ordinary "no decomposition and
# not hand-drawn" skip below, same as any other glyph this generator cannot
# yet produce -- nothing beats a wrong drawing, per glyphstore.py's own rule.
HAND_CELL = (7, 14)

hand = {}
def H(ch, art):
    if (W, CELLH) != HAND_CELL:
        return
    rows = art.strip('\n').split('\n')
    assert len(rows) == 14 and all(len(r) == 7 for r in rows), ch
    bm = accents.pack(rows)
    if BOLD:
        bm = [(v | (v << 1)) & 0xFE for v in bm]
    hand[ord(ch)] = bm

# Letters with no decomposition: drawn here, based on the plain letter.
H('Đ', "\n.......\n.......\n.......\n.####..\n.#...#.\n.#...#.\n####.#.\n.#...#.\n.#...#.\n.#...#.\n.####..\n.......\n.......\n.......")
H('đ', "\n.......\n.......\n...###.\n.....#.\n..####.\n..#..#.\n.#...#.\n.#...#.\n.#...#.\n.#...#.\n..####.\n.......\n.......\n.......")
H('Ħ', "\n.......\n.......\n.......\n.#...#.\n#######\n.#...#.\n.#...#.\n.#####.\n.#...#.\n.#...#.\n.#...#.\n.......\n.......\n.......")
H('ħ', "\n.......\n.......\n..#....\n.####..\n..#....\n..#.##.\n..##..#\n..#...#\n..#...#\n..#...#\n..#...#\n.......\n.......\n.......")
H('ı', "\n.......\n.......\n.......\n.......\n.......\n.###...\n...#...\n...#...\n...#...\n...#...\n.#####.\n.......\n.......\n.......")
H('Ł', "\n.......\n.......\n.......\n.#.....\n.#.....\n.#.....\n##.....\n##.....\n.#.....\n.#.....\n.####..\n.......\n.......\n.......")
H('ł', "\n.......\n.......\n..##...\n...#...\n...#...\n..###..\n..##...\n...#...\n...#...\n...#...\n..###..\n.......\n.......\n.......")
H('Ŋ', "\n.......\n.......\n.......\n.#...#.\n.##..#.\n.#.#.#.\n.#.#.#.\n.#..##.\n.#...#.\n.#...#.\n.#...#.\n.....#.\n..###..\n.......")
H('ŋ', "\n.......\n.......\n.......\n.......\n.......\n.#.##..\n.##..#.\n.#...#.\n.#...#.\n.#...#.\n.#...#.\n.....#.\n..###..\n.......")
H('Œ', "\n.......\n.......\n.......\n..#####\n.#..#..\n.#..#..\n.#..###\n.#..#..\n.#..#..\n.#..#..\n..#####\n.......\n.......\n.......")
H('œ', "\n.......\n.......\n.......\n.......\n.......\n..##.#.\n.#..#.#\n.#..###\n.#..#..\n.#..#.#\n..##.#.\n.......\n.......\n.......")
H('Ŧ', "\n.......\n.......\n.......\n.#####.\n...#...\n...#...\n..###..\n...#...\n...#...\n...#...\n...#...\n.......\n.......\n.......")
H('ŧ', "\n.......\n.......\n...#...\n...#...\n.#####.\n...#...\n..###..\n...#...\n...#...\n...#..#\n....##.\n.......\n.......\n.......")
H('ſ', "\n.......\n.......\n....##.\n...#...\n...#...\n...#...\n...#...\n...#...\n...#...\n...#...\n...#...\n.......\n.......\n.......")

H('Ŀ', "\n.......\n.......\n.......\n.#.....\n.#.....\n.#.....\n.#..#..\n.#..#..\n.#.....\n.#.....\n.####..\n.......\n.......\n.......")
H('ŀ', "\n.......\n.......\n..##...\n...#...\n...#...\n...#...\n...#.#.\n...#.#.\n...#...\n...#...\n..###..\n.......\n.......\n.......")
H('ĸ', "\n.......\n.......\n.......\n.......\n.......\n.#...#.\n.#..#..\n.#.#...\n.##....\n.#.#...\n.#..##.\n.......\n.......\n.......")

# Ligatures: two letterforms in seven columns.  There is no room for serifs,
# so both halves are reduced to plain stems -- cramped, but a cramped glyph in
# the right weight beats a correct one from a different font.
H('Ĳ', "\n.......\n.......\n.......\n###...#\n.#....#\n.#....#\n.#....#\n.#....#\n.#....#\n.#..#.#\n###.###\n.......\n.......\n.......")
H('ĳ', "\n.......\n.......\n.#...#.\n.#...#.\n.......\n.#...#.\n.#...#.\n.#...#.\n.#...#.\n.#...#.\n.#...#.\n.....#.\n..###..\n.......")
H('ŉ', "\n.......\n.......\n.#.....\n.#.....\n#......\n..#.##.\n..##..#\n..#...#\n..#...#\n..#...#\n..#...#\n.......\n.......\n.......")

blocks, notes, skipped = [], [], []
for cp in range(0x0100, 0x0180):
    ch = chr(cp)
    try:
        name = unicodedata.name(ch)
    except ValueError:
        continue
    if cp in hand:
        blocks.append((cp, name, hand[cp]))
        continue
    dec = unicodedata.decomposition(ch).split()
    if len(dec) != 2 or dec[0].startswith('<'):
        skipped.append((cp, name, 'no decomposition and not hand-drawn'))
        continue
    base_cp, mark_cp = int(dec[0], 16), int(dec[1], 16)
    if base_cp not in g:
        skipped.append((cp, name, f'base U+{base_cp:04X} not in font'))
        continue
    if (mark_cp, ch.isupper()) not in mark:
        skipped.append((cp, name, f'no mark for U+{mark_cp:04X}'))
        continue
    bm, note = compose(base_cp, mark_cp, ch.isupper())
    if bm is None:
        skipped.append((cp, name, note))
        continue
    if note:
        notes.append((cp, ch, note))
    blocks.append((cp, name, bm))

for cp, name, bm in blocks:
    gs.write_glyph(os.path.join(OUT, gs.filename(cp)), cp, accents.art(bm, W))

print(f'{OUT}: {len(blocks)} Latin Extended-A glyphs')
for cp, ch, note in notes:
    print(f'  note  U+{cp:04X} {ch}  {note}')
for cp, name, why in skipped:
    print(f'  SKIP  U+{cp:04X} {chr(cp)}  {why}')
