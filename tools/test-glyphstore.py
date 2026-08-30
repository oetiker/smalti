#!/usr/bin/env python3
"""Prove Bdf.cell_bitmaps() trims upstream's cap overshoot and nothing else.

Sixteen upstream letters (O Q a b d g h l m n p q r u w y) declare BBX height
17 in the 8x16 faces -- one row taller than the cell, always on top.  Every
consumer that works in the uniform h-row grid must read them through
cell_bitmaps(); the raw `.bitmaps` attribute hands back all 17 rows.

The two names are one character apart -- `gs.bitmaps(size, face)` is trimmed,
`gs.Bdf(path).bitmaps` is not -- and embolden.py read the wrong one.  The bug
was invisible until a Greek TWIN of an overshoot letter existed: TWIN maps
U+039F to `O` and U+03BF to `o`, so drawing Greek made embolden write a
17-row file that read_glyph() rejected.  Case `twin` below is that regression.
"""
import ast
import os
import pathlib
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

FAIL = 0


def check(name, got, want):
    global FAIL
    if got != want:
        print(f'FAIL {name}: got {got!r}, want {want!r}')
        FAIL += 1
    else:
        print(f'ok   {name}')


SIZES = ['7x14', '8x16']
FACES = ['regular', 'bold']

# embolden.py's TWIN map, read from its source rather than copied: a second
# copy would drift, and the point of the regression below is to track the
# real map.  embolden.py runs its whole job at import time, so it cannot be
# imported -- parse the literal instead.
def _twin():
    tree = ast.parse(pathlib.Path(__file__).with_name('embolden.py').read_text())
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(getattr(t, 'id', None) == 'TWIN' for t in node.targets)):
            return ast.literal_eval(node.value)
    raise SystemExit('test-glyphstore.py: no TWIN map found in embolden.py')


TWIN = _twin()

# ---- the upstream fact this all rests on --------------------------------
b8 = gs.Bdf(gs.upstream_bdf('8x16', 'bold'))
check('raw .bitmaps keeps the overshoot row',
      len(b8.bitmaps[ord('O')]), 17)
check('raw .bitmaps disagrees with the cell height',
      b8.h, 16)

# ---- every glyph lands in the uniform grid -------------------------------
for size in SIZES:
    _w, h = gs.cell(size)
    for face in FACES:
        bdf = gs.Bdf(gs.upstream_bdf(size, face))
        bad = [cp for cp, bm in bdf.cell_bitmaps(h).items() if len(bm) != h]
        check(f'{size}/{face}: every cell_bitmaps glyph is {h} rows', bad, [])

# ---- the trim loses no ink ----------------------------------------------
for face in FACES:
    bdf = gs.Bdf(gs.upstream_bdf('8x16', face))
    over = [cp for cp, d in bdf.heights.items() if d != bdf.h]
    check(f'8x16/{face}: exactly 16 glyphs overshoot', len(over), 16)
    inky = [f'U+{cp:04X}' for cp in over
            if any(bdf.bitmaps[cp][:bdf.heights[cp] - bdf.h])]
    check(f'8x16/{face}: every dropped row is blank', inky, [])

# ---- 7x14 is untouched: no overshoot there, so the trim is the identity --
for face in FACES:
    bdf = gs.Bdf(gs.upstream_bdf('7x14', face))
    check(f'7x14/{face}: cell_bitmaps is the identity',
          bdf.cell_bitmaps(bdf.h), bdf.bitmaps)

# ---- the regression: embolden's overshooting TWIN sources ----------------
# Derived, not asserted by name.  Only ONE of TWIN's fifteen Latin sources
# overshoots -- `O` for U+039F.  Lowercase `o` does NOT, so a case written
# for it would pass whether or not the trim exists: a check that cannot go
# red.  Pinning the derived set is what makes this case able to fail, and
# also flags the day upstream gives another TWIN letter an overshoot.
for face in FACES:
    bdf = gs.Bdf(gs.upstream_bdf('8x16', face))
    over = {cp for cp, latin in TWIN.items()
            if bdf.heights[ord(latin)] != bdf.h}
    check(f'8x16/{face}: TWIN sources that overshoot', over, {0x039F})
    got = bdf.cell_bitmaps(16)
    for cp in sorted(over):
        check(f'twin U+{cp:04X} <- 8x16/{face} {TWIN[cp]!r} is 16 rows',
              len(got[ord(TWIN[cp])]), 16)

# ---- a corrupt BITMAP is still told apart from a deliberate overshoot ----
tmp = 'build/selftest-glyphstore'
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(tmp)
try:
    src = gs.upstream_bdf('8x16', 'regular')
    text = open(src, encoding='latin1').read()
    # Delete one BITMAP row from U+0041, leaving its BBX claiming 16.
    head, _, rest = text.partition('STARTCHAR U+0041\n')
    body, _, tail = rest.partition('ENDCHAR')
    pre, _, bits = body.partition('BITMAP\n')
    rows = bits.strip().split('\n')
    hurt = os.path.join(tmp, 'hurt.bdf')
    open(hurt, 'w', encoding='latin1').write(
        head + 'STARTCHAR U+0041\n' + pre + 'BITMAP\n'
        + '\n'.join(rows[:-1]) + '\n' + 'ENDCHAR' + tail)
    try:
        gs.Bdf(hurt).cell_bitmaps(16)
        check('a truncated BITMAP raises GlyphError', 'no error', 'GlyphError')
    except gs.GlyphError as e:
        check('a truncated BITMAP raises GlyphError',
              'declares BBX height' in str(e), True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(1 if FAIL else 0)
