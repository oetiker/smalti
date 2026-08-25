#!/usr/bin/env python3
"""Derive the bold face from the resolved regular face.

Usage: embolden.py [SIZE]             (default 7x14)

IT CONSUMES THE RESOLVED FACE, NOT THE RAW DRAWINGS
    Every layer of the regular face is already in place by the time this runs:
    the drawings, upstream, and the other generators.  So hand-drawing a
    regular glyph improves its bold automatically, without anyone touching the
    bold face -- which is the main reason the stack is worth building.  The
    output is only a candidate: upstream's own bold, and any drawing in
    glyphs/<size>/bold/, both outrank it.

    That is why this can emit all 1002 glyphs and not just the added ones.  For
    the 190 upstream also draws, upstream wins and this output is discarded.

THE WIDENING RULE ITSELF LIVES IN tools/weight.py
    because the bold OBLIQUE face needs exactly the same one.  It is the right
    default here, with two exceptions:

      * Solid geometric shapes are NOT emboldened.  A filled circle has no
        strokes to thicken -- widening it just makes it lopsided.  Real fonts
        leave these identical across weights.
      * Greek capitals that share a Latin letterform are copied from the bold
        base font, not emboldened, so bold Alpha stays exactly bold A.

    KEEP and TWIN below are policies about how to DERIVE, not shapes, so they
    stay in Python.  Changing a shape still needs no code change, because the
    way to change a shape is to draw it and a drawing outranks every rule.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs
import weight
from weight import widen

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
# widen() reads its width from module state, so set it before the first call.
weight.set_width(int(SIZE.split('x')[0]))

# Shapes, not strokes: identical in both weights.  Widening a filled circle
# or a braille dot does not make it bold, it makes it lopsided -- and braille
# and box-drawing must keep their exact pitch to line up with their neighbours.
KEEP = (set(range(0x2500, 0x2900))          # shapes, dingbats, braille
        | {0x2022, 0x23BF, 0x23F5, 0x23FA, 0x29C9}
        # Already at maximum density: every one of these fills 6 or 7 columns
        # with 1-pixel detail, so any widening merges the interior.  Bold and
        # regular are the same glyph, which is what most fonts do anyway.
        | {0x00AE, 0x2122, 0x2030, 0x00BC, 0x00BD, 0x00BE, 0x203B}
        # Powerline separators fill the cell edge to edge already.
        | set(range(0xE0B0, 0xE0C0)))
# Greek capitals whose letterform IS the Latin one.
TWIN = {0x391: 'A', 0x392: 'B', 0x395: 'E', 0x396: 'Z', 0x397: 'H', 0x399: 'I',
        0x39A: 'K', 0x39C: 'M', 0x39D: 'N', 0x39F: 'O', 0x3A1: 'P', 0x3A4: 'T',
        0x3A5: 'Y', 0x3A7: 'X', 0x3BF: 'o'}

w, _h = gs.cell(SIZE)
regular = gs.bitmaps(SIZE, 'regular')
if not regular:
    sys.exit(f'embolden.py: the {SIZE} regular face resolved to nothing')
bold_base = gs.Bdf(gs.upstream_bdf(SIZE, 'bold')).bitmaps
outdir = gs.gen_dir(SIZE, 'bold')

counts = {'embolden': 0, 'keep': 0, 'twin': 0}
for cp, bm in sorted(regular.items()):
    if cp in TWIN:
        out, key = bold_base[ord(TWIN[cp])], 'twin'
    elif cp in KEEP:
        out, key = bm, 'keep'
    else:
        out, key = widen(bm), 'embolden'
    counts[key] += 1
    gs.write_glyph(os.path.join(outdir, gs.filename(cp)), cp, gs.art(out, w))

print(f'{outdir}: {counts["embolden"]} emboldened, {counts["keep"]} kept '
      f'as-is, {counts["twin"]} copied from the bold base')
