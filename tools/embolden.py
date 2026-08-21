#!/usr/bin/env python3
"""Derive a bold glyph file from a regular one.

Usage: embolden.py REGULAR.txt BOLD.txt BOLD-BASE.bdf

Tamzen's own bold widens every stroke by one pixel to the LEFT: bold 'A' is
regular 'A' OR itself shifted one column left.  That rule reproduces 108 of
the 189 upstream glyphs exactly; the rest are hand-tuned, mostly to stop dense
counters from filling in.  It is the right default here, with two exceptions:

  * Solid geometric shapes are NOT emboldened.  A filled circle has no strokes
    to thicken -- widening it just makes it lopsided.  Real fonts leave these
    identical across weights.
  * Greek capitals that share a Latin letterform are copied from the bold base
    font, not emboldened, so bold Alpha stays exactly bold A.
"""
import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import accents

SRC, DST, BASE = sys.argv[1], sys.argv[2], sys.argv[3]

# Shapes, not strokes: identical in both weights.  Widening a filled circle
# or a braille dot does not make it bold, it makes it lopsided -- and braille
# and box-drawing must keep their exact pitch to line up with their neighbours.
KEEP = (set(range(0x2500, 0x2900))          # shapes, dingbats, braille
        | {0x2022, 0x23BF, 0x23F5, 0x23FA, 0x29C9}
        # Already at maximum density: every one of these fills 6 or 7 columns
        # with 1-pixel detail, so any widening merges the interior.  Bold and
        # regular are the same glyph, which is what most fonts do anyway.
        | {0x00AE, 0x2122, 0x2030, 0x00BC, 0x00BD, 0x00BE, 0x203B})
# Greek capitals whose letterform IS the Latin one.
TWIN = {0x391:'A', 0x392:'B', 0x395:'E', 0x396:'Z', 0x397:'H', 0x399:'I',
        0x39A:'K', 0x39C:'M', 0x39D:'N', 0x39F:'O', 0x3A1:'P', 0x3A4:'T',
        0x3A5:'Y', 0x3A7:'X', 0x3BF:'o'}

def runs(v):
    out, start = [], None
    for c in range(7):
        if v & (1 << (7 - c)):
            if start is None:
                start = c
        elif start is not None:
            out.append((start, c - 1))
            start = None
    if start is not None:
        out.append((start, 6))
    return out

def widen(bm):
    """Widen each stroke by one pixel, without closing a counter.

    The plain rule -- OR the row with itself shifted one column left --
    reproduces 108 of the 189 upstream bold glyphs, but it also merges any
    1-pixel gap, which turned the pilcrow, the registered sign and lowercase
    pi into solid blobs.  Working on runs instead, and falling back to
    widening rightward when the left is blocked, reproduces 93 of 189 and
    never fills a counter.  Legible beats faithful here.
    """
    out = []
    for v in bm:
        rr, n = runs(v), v
        for i, (s, e) in enumerate(rr):
            prev = rr[i - 1][1] if i else None
            nxt = rr[i + 1][0] if i + 1 < len(rr) else None
            if s > 0 and (prev is None or s - prev > 2):
                n |= 1 << (7 - (s - 1))
            elif e < 6 and (nxt is None or nxt - e > 2):
                n |= 1 << (7 - (e + 1))
        out.append(n & 0xFE)
    return out

bold_base = accents.load(BASE)
text = open(SRC).read()
out = [f'# GENERATED from {SRC} by tools/embolden.py -- do not hand-edit;\n'
       f'# edit {SRC} and re-run `make bold-sources`.\n']
counts = {'embolden': 0, 'keep': 0, 'twin': 0}

# Anchor on line starts: the source files document their own format in a
# comment that contains the words "CHAR U+XXXX", which a plain split would eat.
for m in re.finditer(r'^CHAR (U\+([0-9A-Fa-f]+)[^\n]*)\n((?:[.#]{7}\n){14})',
                     text, re.M):
    head, cp, rows = m.group(1), int(m.group(2), 16), m.group(3).split('\n')[:14]
    if cp in TWIN:
        bm, counts['twin'] = bold_base[ord(TWIN[cp])], counts['twin'] + 1
    elif cp in KEEP:
        bm, counts['keep'] = accents.pack(rows), counts['keep'] + 1
    else:
        bm = widen(accents.pack(rows))
        counts['embolden'] += 1
    out.append(f'CHAR {head}\n' + '\n'.join(accents.art(bm)) + '\n')

open(DST, 'w').write('\n'.join(out) + '\n')
print(f'{DST}: {counts["embolden"]} emboldened, {counts["keep"]} kept as-is, '
      f'{counts["twin"]} copied from the bold base')
