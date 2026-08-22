#!/usr/bin/env python3
"""Rewrite every hand-drawn glyph file into its normal form.

Usage: glyph-headers.py [SIZE ...]        (default: every size in glyphs/)

`0041.txt` on its own tells a reviewer nothing, so each file carries one
comment line naming the codepoint, the character and its Unicode name.  A
contributor may leave it off entirely, or get it wrong, and have it filled in
here.

The name is historical: this normalises the WHOLE file, not only its header --
trailing blank lines and CRLF endings included.  It has to, because
tools/check-glyphs.py rejects the whole file, and a normaliser that fixes less
than the checker rejects leaves a contributor with an error and no way out of
it.  Both go through glyphstore.normalised, which is the single definition.

Only glyphs/ is touched.  build/gen/ is written correctly by construction.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs


def sizes(argv):
    if argv:
        return argv
    if not os.path.isdir(gs.HAND_ROOT):
        return []
    return sorted(d for d in os.listdir(gs.HAND_ROOT)
                  if os.path.isdir(os.path.join(gs.HAND_ROOT, d)))


changed = total = 0
for size in sizes(sys.argv[1:]):
    w, h = gs.cell(size)
    for face in gs.FACES:
        d = gs.hand_dir(size, face)
        for cp, rows in gs.read_dir(d, w, h).items():
            path = os.path.join(d, gs.filename(cp))
            total += 1
            # Compared and written through glyphstore, and read with line
            # endings intact, so that this rewrites exactly the files
            # check-glyphs.py rejects -- no more and no fewer.
            if gs.read_raw(path) != gs.normalised(cp, rows):
                gs.write_glyph(path, cp, rows)
                print(f'  rewrote {path}')
                changed += 1
print(f'{total} glyph files, {changed} rewritten')
