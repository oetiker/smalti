#!/usr/bin/env python3
"""Generate the circled-digit dingbats, U+2776..U+2793, into build/gen/.

Usage: gen-circled-digits.py [SIZE]        (default 7x14)

Three runs of ten live in that range and Unicode separates them by a
distinction -- serif versus sans-serif -- that seven pixels cannot carry, so
U+2776..U+277F and U+278A..U+2793 come out identical here.  Both are the
NEGATIVE runs: a white digit knocked out of a black disc.  U+2780..U+2789 is
the positive run: a black digit inside a white ring.

The three TEN glyphs need a wider interior than the ring can give.  Two
digits take five columns -- a 3-wide zero, a 1-wide one and a gap -- and a
full ring takes the outer two, so the one would merge into the left wall and
the zero into the right.  The negative tens are fine as they are, because a
solid disc has no thin wall to merge with.  U+2789 gets an OPEN ring instead:
the top and bottom arcs only, drawn so that no arc pixel sits in a digit
column.  It keeps the family's height and still reads as an enclosure.

This writes only into build/gen/, so it is freely re-runnable and cannot
overwrite anyone's work.  To change one glyph, draw it: a file in
glyphs/<size>/regular/ outranks anything here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
if SIZE != '7x14':
    sys.exit(f'gen-circled-digits.py: the ring below is 7x14 only, not {SIZE}')

CELL_W, CELL_H = 7, 14
TOP = 3                      # the ring spans rows 3..11
BLANK = '.' * CELL_W

RING = ['..###..', '.#...#.', '#.....#', '#.....#', '#.....#',
        '#.....#', '#.....#', '.#...#.', '..###..']
# Same nine rows, but open at the sides so the five columns of "10" are free.
# Row 1 and row 7 hold the widest ink, at the two columns the digits skip.
ARCS = ['.#####.', '#.....#', '.......', '.......', '.......',
        '.......', '.......', '#.....#', '.#####.']
DISC = ['..###..', '.#####.', '#######', '#######', '#######',
        '#######', '#######', '.#####.', '..###..']

# 3 wide, 5 tall -- the largest that leaves a clear column beside the ring.
DIGIT = {
    '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['###', '..#', '###', '#..', '###'],
    '3': ['###', '..#', '###', '..#', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'],
    '5': ['###', '#..', '###', '..#', '###'],
    '6': ['###', '#..', '###', '#.#', '###'],
    '7': ['###', '..#', '..#', '..#', '..#'],
    '8': ['###', '#.#', '###', '#.#', '###'],
    '9': ['###', '#.#', '###', '..#', '###'],
}
# 5 wide -- only ever knocked out of a disc, never set inside a ring.
TEN = ['.#.###.', '.#.#.#.', '.#.#.#.', '.#.#.#.', '.#.###.']

NAMES = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
         'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN']


def compose(base, art, col, negative):
    """Draw art onto a copy of base at column col; negative knocks it out."""
    rows = [list(r) for r in base]
    for i, line in enumerate(art):
        for j, ch in enumerate(line):
            if ch == '#':
                rows[2 + i][col + j] = '.' if negative else '#'
    return [''.join(r) for r in rows]


def cell(rows):
    art = [BLANK] * CELL_H
    for i, r in enumerate(rows):
        art[TOP + i] = r
    return art


outdir = gs.gen_dir(SIZE, 'regular')
n = 0
for base_cp, negative in [(0x2776, True), (0x2780, False), (0x278A, True)]:
    for i, word in enumerate(NAMES):
        cp = base_cp + i
        if word == 'TEN':
            base = DISC if negative else ARCS
            rows = compose(base, TEN, 0, negative)
        else:
            base = DISC if negative else RING
            rows = compose(base, DIGIT[str(i + 1)], 2, negative)
        gs.write_glyph(os.path.join(outdir, gs.filename(cp)), cp, cell(rows))
        n += 1
print(f'{outdir}: {n} circled digits')
