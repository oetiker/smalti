#!/usr/bin/env python3
"""Prove accents.marks() hands back a mark and not a piece of a letter.

A mark lifted by subtraction is only as good as the agreement between its two
donors.  Upstream's 8x16 'a' carries a spur on its last row that its own
'a-acute' does not, so 'a-acute minus a' kept that pixel -- a mark eleven rows
tall, holding ink level with the letter it was meant to sit above.  compose()
then saw a collision against every base and fell back to its raised comma, so
33 glyphs per face shipped in v0.2.0's 8x16 family with the mark stranded in
the last column ('c-acute' drawn as c with a bar beside it).  Nothing caught
it: `make check` counts glyphs and never looks at their shape.

7x14's donors agree, so subtraction alone was right there and the clip must
change nothing -- case `7x14 unchanged` is that regression, and it is what
lets the fix be read as a repair of 8x16 rather than a redraw of the font.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accents
import glyphstore as gs

FAIL = 0


def check(name, got, want):
    global FAIL
    if got != want:
        print(f'FAIL {name}: got {got!r}, want {want!r}')
        FAIL += 1
    else:
        print(f'ok   {name}')


def rows(bm):
    return [i for i, v in enumerate(bm) if v]


# The marks that sit ABOVE the letter, and the donor whose ink they must clear.
ABOVE = {0x300: 'grave', 0x301: 'acute', 0x302: 'circumflex',
         0x303: 'tilde', 0x308: 'diaeresis', 0x30A: 'ring'}

# Every mark above a letter, at the sizes this font ships, fits in the rows
# over the x-height.  Four is the widest any of them is (8x16's ring); a lift
# that comes back taller has letter in it.
MAX_MARK_ROWS = 4

for size in ('7x14', '8x16'):
    w, h = gs.cell(size)
    for face, base_lo, base_up in (('regular', 0x61, 0x41), ('bold', 0x61, 0x41)):
        g = accents.load(gs.upstream_bdf(size, face))
        m = accents.marks(g, h)
        lo_top, up_top = rows(g[base_lo])[0], rows(g[base_up])[0]
        for cc, label in ABOVE.items():
            for upper, top in ((False, lo_top), (True, up_top)):
                got = rows(m[cc, upper])
                case = f'{size}/{face} {label}{" (capital)" if upper else ""}'
                if not got:
                    check(f'{case} is not empty', False, True)
                    continue
                check(f'{case} clears the letter at row {top}',
                      got[-1] < top, True)
                check(f'{case} is at most {MAX_MARK_ROWS} rows',
                      got[-1] - got[0] + 1 <= MAX_MARK_ROWS, True)
        # The cedilla hangs below the letter; the clip must not touch it.
        check(f'{size}/{face} cedilla still hangs below the letter',
              rows(m[0x327, False])[0] > lo_top, True)

# 7x14 is the regression guard: its donors agree, so every mark there must be
# exactly what plain subtraction produced before the clip existed.
g = accents.load(gs.upstream_bdf('7x14', 'regular'))
m = accents.marks(g, 14)
for cc, label in ABOVE.items():
    check(f'7x14 unchanged: {label} == a-{label} minus a',
          m[cc, False], accents.sub(g[{0x300: 0xE0, 0x301: 0xE1, 0x302: 0xE2,
                                       0x303: 0xE3, 0x308: 0xE4,
                                       0x30A: 0xE5}[cc]], g[0x61]))

print('FAILED' if FAIL else 'all accent-mark cases pass')
sys.exit(1 if FAIL else 0)
