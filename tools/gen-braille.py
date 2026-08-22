#!/usr/bin/env python3
"""Generate the whole U+2800..U+28FF braille block into build/gen/.

Usage: gen-braille.py [SIZE]          (default 7x14)

CLI spinners cycle through braille patterns, so partial coverage makes the
spinner jitter between this font and the fallback.  The block is perfectly
regular -- the codepoint's low byte IS the dot bitmask -- so all 256 are
generated and there is no judgement involved anywhere in here.

Layout: two dot columns (1..2 and 4..5) and four dot rows, each dot a 2x2 block
with a one-pixel gap, which is the only arrangement that fits 8 dots into 7x14
without them touching.

This writes only into build/gen/, so it is freely re-runnable and cannot
overwrite anyone's work.  To change one pattern, draw it: a file in
glyphs/<size>/regular/ outranks anything here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
if SIZE != '7x14':
    sys.exit(f'gen-braille.py: the dot geometry below is 7x14 only, not {SIZE}')

COLS = {0: 0b0110000, 1: 0b0000110}      # left dots -> cols 1,2; right -> 4,5
BANDS = [(2, 3), (5, 6), (8, 9), (11, 12)]
# bit index -> (column, row band).  Dots 1-3 and 7 are the left column.
DOT = {0: (0, 0), 1: (0, 1), 2: (0, 2), 6: (0, 3),
       3: (1, 0), 4: (1, 1), 5: (1, 2), 7: (1, 3)}

out = gs.gen_dir(SIZE, 'regular')
for n in range(256):
    rows = [0] * 14
    for bit, (col, band) in DOT.items():
        if n & (1 << bit):
            for r in range(*BANDS[band]):
                rows[r] |= COLS[col]
            rows[BANDS[band][1]] |= COLS[col]
    art = [''.join('#' if v & (1 << (6 - c)) else '.' for c in range(7))
           for v in rows]
    cp = 0x2800 + n
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp, art)
print(f'{out}: 256 braille patterns')
