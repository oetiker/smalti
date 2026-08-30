#!/usr/bin/env python3
"""Generate the whole U+2800..U+28FF braille block into build/gen/.

Usage: gen-braille.py [SIZE]          (default 7x14)

CLI spinners cycle through braille patterns, so partial coverage makes the
spinner jitter between this font and the fallback.  The block is perfectly
regular -- the codepoint's low byte IS the dot bitmask -- so all 256 are
generated and there is no judgement involved anywhere in here.

The dot geometry (which columns and rows the two dot columns land in) is
drawn per size in GEOMETRY below, never scaled: a Braille cell is always
2x4 dots, but where they sit is a design decision, not an arithmetic one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'

# COLS masks are in gs.art()'s byte-packed bit order (bit stride(w)-1-c for
# column c) -- the same convention gen-arrows.py, embolden.py and
# slant-bdf.py all use. This file used to carry its own inline copy of
# gs.art() packed as '6 - c' instead, which happens to agree with the
# byte-packed convention at width 7 (both pad to a stride of 8) but silently
# disagrees at width 8: column 7 is bit 0 under byte packing and simply
# unreachable under '6 - c'. Kept as a plain '6 - c' packing plus an 8x16
# COLS entry, every column would have shifted by one and all 256 glyphs
# would have come out wrong with no error anywhere. Converting to gs.art()
# and re-basing COLS to byte packing removes that trap for every future size.
GEOMETRY = {
    '7x14': {
        # left dots -> cols 1,2; right -> cols 4,5 (one-pixel gap at col 3):
        # the only arrangement that fits 8 dots into 7x14 without touching.
        'cols': {0: 0b01100000, 1: 0b00001100},
        'bands': [(2, 3), (5, 6), (8, 9), (11, 12)],
    },
    '8x16': {
        # left dots -> cols 2,3; right -> cols 5,6 (one-pixel gap at col 4).
        # Ink window (2,6) width 5, centred on column 4 -- the stem rule
        # glyphs/8x16/README.md measures from upstream, and identical to
        # upstream's own 8x16 'I'. Row bands keep the 7x14 shape (2-row
        # dots, 1-row gaps, 11-row total span) but recentre it: ascent grew
        # 11->12 and descent 3->4, so the span shifts from rows 2..12 to
        # rows 3..13, spending the two extra rows of cell height as one more
        # row of margin top and bottom, rather than reusing rows 2..12
        # verbatim and leaving all of the extra height stranded at the
        # bottom. The baseline (after row 11) falls exactly in the gap
        # between the third and fourth dot band; the fourth band dips into
        # two of the four descent rows, leaving rows 14-15 clear.
        'cols': {0: 0b00110000, 1: 0b00000110},
        'bands': [(3, 4), (6, 7), (9, 10), (12, 13)],
    },
}
if SIZE not in GEOMETRY:
    sys.exit(f'gen-braille.py: the dot geometry below covers '
             f'{", ".join(sorted(GEOMETRY))}, not {SIZE}')

W, H = gs.cell(SIZE)
COLS = GEOMETRY[SIZE]['cols']
BANDS = GEOMETRY[SIZE]['bands']
# bit index -> (column, row band).  Dots 1-3 and 7 are the left column.
DOT = {0: (0, 0), 1: (0, 1), 2: (0, 2), 6: (0, 3),
       3: (1, 0), 4: (1, 1), 5: (1, 2), 7: (1, 3)}

out = gs.gen_dir(SIZE, 'regular')
for n in range(256):
    rows = [0] * H
    for bit, (col, band) in DOT.items():
        if n & (1 << bit):
            for r in range(*BANDS[band]):
                rows[r] |= COLS[col]
            rows[BANDS[band][1]] |= COLS[col]
    art = gs.art(rows, W)
    cp = 0x2800 + n
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp, art)
print(f'{out}: 256 braille patterns')
