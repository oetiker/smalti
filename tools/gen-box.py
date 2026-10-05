#!/usr/bin/env python3
"""Generate U+2500..U+259F -- box drawing and block elements -- into build/gen/.

Usage: gen-box.py [SIZE]          (default 7x14)

All the judgement is in tools/boxgeom.py: the grammar that reads an arm
specification out of the Unicode name, the per-size geometry table, and the
junction rule. This file only walks the two blocks and writes the result.

REGULAR ONLY, DELIBERATELY. embolden.py's KEEP already covers
range(0x2500, 0x2900) -- its comment says box drawing "must keep their exact
pitch to line up with their neighbours" -- and slant-bdf.py leaves category
So upright. So bold, italic and bold italic all come out right with no work
here, and adding a bold path would be the thing that broke them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxgeom
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
if SIZE not in boxgeom.GEOMETRY:
    sys.exit(f'gen-box.py: the geometry table covers '
             f'{", ".join(sorted(boxgeom.GEOMETRY))}, not {SIZE}')

out = gs.gen_dir(SIZE, 'regular')
written = 0
for cp in boxgeom.BOX:
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp,
                   boxgeom.art(boxgeom.glyph(cp, SIZE)))
    written += 1
for cp in boxgeom.BLOCKS:
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp,
                   boxgeom.art(boxgeom.block(cp, SIZE)))
    written += 1
print(f'{out}: {written} box drawing and block element glyphs')
