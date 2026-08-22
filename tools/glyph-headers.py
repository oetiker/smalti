#!/usr/bin/env python3
"""Normalise the header line of every hand-drawn glyph file.

Usage: glyph-headers.py [SIZE ...]        (default: every size in glyphs/)

`0041.txt` on its own tells a reviewer nothing, so each file carries one
comment line naming the codepoint, the character and its Unicode name.  It is
written by this tool and checked by tools/check-glyphs.py, so a contributor may
leave it off entirely, or get it wrong, and have it filled in.

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
            want = gs.header(cp) + '\n' + '\n'.join(rows) + '\n'
            total += 1
            if open(path, encoding='utf-8').read() != want:
                open(path, 'w', encoding='utf-8').write(want)
                print(f'  rewrote {path}')
                changed += 1
print(f'{total} glyph files, {changed} rewritten')
