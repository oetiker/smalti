#!/usr/bin/env python3
"""Render glyphs of a BDF font as ASCII art, side by side.

Usage: show-glyphs.py FONT.bdf [EXTRA.txt | U+XXXX ...]

With no selection the whole font is shown.  An EXTRA.txt argument selects
exactly the codepoints that file defines, which is what `make preview` wants.
"""
import re
import sys

font = sys.argv[1]
text = open(font, encoding='latin1').read()
m = re.search(r'^FONTBOUNDINGBOX (\d+) (\d+) ', text, re.M)
W, H = int(m.group(1)), int(m.group(2))
asc = int(re.search(r'^FONT_ASCENT (\d+)', text, re.M).group(1))

glyphs = {}
for chunk in text.split('STARTCHAR ')[1:]:
    body = chunk.partition('ENDCHAR')[0]
    cp = int(re.search(r'^ENCODING (\d+)', body, re.M).group(1))
    rows = body.partition('BITMAP\n')[2].strip().split('\n')
    glyphs[cp] = [r.strip() for r in rows]

want = []
for arg in sys.argv[2:]:
    if arg.startswith('U+'):
        want.append(int(arg[2:], 16))
    else:
        want += [int(x, 16) for x in re.findall(r'^CHAR U\+([0-9A-Fa-f]+)',
                                                open(arg).read(), re.M)]
want = want or sorted(glyphs)

def art(cp):
    out = []
    for row in glyphs[cp]:
        v = int(row, 16)
        out.append(''.join('#' if v & (1 << (7 - b)) else '.' for b in range(W)))
    return out

for i in range(0, len(want), 8):
    batch = [cp for cp in want[i:i + 8] if cp in glyphs]
    if not batch:
        continue
    arts = [art(cp) for cp in batch]
    pad = ' ' * (W - 6)
    print('   ' + '  '.join(f'{cp:04X}{pad}' for cp in batch))
    print('   ' + '  '.join(f'{chr(cp):<{W}}' for cp in batch))
    for r in range(H):
        mark = '  <- baseline' if r == asc - 1 else ''
        print(f'{r:2d} ' + '  '.join(a[r] for a in arts) + mark)
    print()
