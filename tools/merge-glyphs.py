#!/usr/bin/env python3
"""Merge ASCII-art glyph definitions into a BDF font.

Usage: merge-glyphs.py BASE.bdf EXTRA.txt [EXTRA.txt ...] > MERGED.bdf

The BDF bitmap format packs each row into whole bytes, most significant bit
leftmost.  A 7-pixel-wide cell therefore occupies bits 7..1 of one byte and
bit 0 is always padding.  Glyphs are emitted sorted by encoding, and the
CHARS count is rewritten, because fonttosfnt trusts both.
"""
import re
import sys

CELL_W = 7
CELL_H = 14
SWIDTH = None   # copied from the base font's own glyphs, never computed


def parse_base(path):
    """Return (header_text, {encoding: block_text}, footer_text)."""
    global CELL_W, CELL_H, SWIDTH
    text = open(path, encoding='latin1').read()
    m = re.search(r'^FONTBOUNDINGBOX (\d+) (\d+) ', text, re.M)
    CELL_W, CELL_H = int(m.group(1)), int(m.group(2))
    SWIDTH = re.search(r'^SWIDTH (\S+ \S+)$', text, re.M).group(1)
    head, _, rest = text.partition('\nSTARTCHAR ')
    blocks = {}
    for chunk in ('STARTCHAR ' + rest).split('STARTCHAR ')[1:]:
        body, _, _tail = chunk.partition('ENDCHAR')
        enc = int(re.search(r'^ENCODING (\d+)', body, re.M).group(1))
        blocks[enc] = 'STARTCHAR ' + body + 'ENDCHAR\n'
    return head, blocks


def parse_extra(path):
    """Return {encoding: (name, [14 row strings])} from one ASCII-art file."""
    out = {}
    cp = name = None
    rows = []
    for lineno, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        # A pixel row is recognised BEFORE a comment, because '#' is both the
        # ink character and the comment marker: the em dash row '#######'
        # would otherwise be swallowed as a comment.
        if len(line) == CELL_W and not set(line) - {'#', '.'}:
            if cp is None:
                sys.exit(f'{path}:{lineno}: pixel row before any CHAR line')
            rows.append(line)
            continue
        if not line.strip() or line.lstrip()[0] in '#;':
            continue
        if line.startswith('CHAR '):
            if cp is not None:
                _flush(out, path, cp, name, rows, lineno)
            m = re.match(r'CHAR U\+([0-9A-Fa-f]{4,6})\s+(.*)', line)
            if not m:
                sys.exit(f'{path}:{lineno}: bad CHAR line: {line!r}')
            cp, name, rows = int(m.group(1), 16), m.group(2).strip(), []
            continue
        sys.exit(f'{path}:{lineno}: expected a CHAR line, a comment, or a row '
                 f"of exactly {CELL_W} '#'/'.' characters, got {line!r}")
    if cp is not None:
        _flush(out, path, cp, name, rows, lineno)
    return out


def _flush(out, path, cp, name, rows, lineno):
    if len(rows) != CELL_H:
        sys.exit(f'{path}: U+{cp:04X} has {len(rows)} rows, need {CELL_H} '
                 f'(near line {lineno})')
    if cp in out:
        sys.exit(f'{path}: U+{cp:04X} defined twice')
    out[cp] = (name, rows)


def render(cp, name, rows):
    bits = []
    for row in rows:
        v = 0
        for i, ch in enumerate(row):
            if ch == '#':
                v |= 1 << (7 - i)
        bits.append(f'{v:02X}')
    return (f'STARTCHAR U+{cp:04X}\n'
            f'ENCODING {cp}\n'
            f'SWIDTH {SWIDTH}\n'
            f'DWIDTH {CELL_W} 0\n'
            f'BBX {CELL_W} {CELL_H} 0 -3\n'
            f'BITMAP\n' + '\n'.join(bits) + '\nENDCHAR\n')


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    head, blocks = parse_base(sys.argv[1])
    added = replaced = 0
    for path in sys.argv[2:]:
        for cp, (name, rows) in parse_extra(path).items():
            if cp in blocks:
                replaced += 1
            else:
                added += 1
            blocks[cp] = render(cp, name, rows)
    head = re.sub(r'^CHARS \d+$', f'CHARS {len(blocks)}', head, flags=re.M)
    sys.stdout.write(head + '\n')
    for cp in sorted(blocks):
        sys.stdout.write(blocks[cp] + '\n')
    sys.stdout.write('ENDFONT\n')
    print(f'{sys.argv[1]}: {added} added, {replaced} replaced, '
          f'{len(blocks)} total', file=sys.stderr)


main()
