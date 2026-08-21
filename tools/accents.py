#!/usr/bin/env python3
"""Read a BDF and derive accent masks by subtracting a base letter.

Tamzen already draws grave, acute, circumflex, tilde, diaeresis, ring and
cedilla -- on 'a', 'A', 'c' and 'C'.  Subtracting the plain letter from the
accented one recovers the mark exactly as Tamzen drew it, which is far better
than inventing one.  Marks it does NOT have (macron, breve, dot above, double
acute, caron, ogonek) are defined here by hand, in the same weight.
"""
import re

def load(path):
    text = open(path, encoding='latin1').read()
    out = {}
    for chunk in text.split('STARTCHAR ')[1:]:
        body = chunk.partition('ENDCHAR')[0]
        cp = int(re.search(r'^ENCODING (\d+)', body, re.M).group(1))
        out[cp] = [int(r.strip(), 16)
                   for r in body.partition('BITMAP\n')[2].strip().split('\n')]
    return out

def sub(acc, base):
    return [a & ~b for a, b in zip(acc, base)]

def art(rows):
    return [''.join('#' if v & (1 << (7 - b)) else '.' for b in range(7))
            for v in rows]

def pack(art_rows):
    return [sum(1 << (7 - i) for i, ch in enumerate(r) if ch == '#')
            for r in art_rows]

def marks(g):
    """{(mark_codepoint, is_upper): 14-row bitmap}"""
    m = {}
    for cc, lo, up in ((0x300, 0xE0, 0xC0), (0x301, 0xE1, 0xC1),
                       (0x302, 0xE2, 0xC2), (0x303, 0xE3, 0xC3),
                       (0x308, 0xE4, 0xC4), (0x30A, 0xE5, 0xC5)):
        m[cc, False] = sub(g[lo], g[0x61])
        m[cc, True]  = sub(g[up], g[0x41])
    m[0x327, False] = sub(g[0xE7], g[0x63])
    m[0x327, True]  = sub(g[0xC7], g[0x43])

    def hand(cc, lo_top, lo, up_top=None, up=None):
        m[cc, False] = pack(['.......'] * lo_top + lo
                            + ['.......'] * (14 - lo_top - len(lo)))
        up, up_top = up or lo, up_top if up_top is not None else lo_top - 2
        m[cc, True] = pack(['.......'] * up_top + up
                           + ['.......'] * (14 - up_top - len(up)))

    hand(0x304, 3, ['.#####.'])                       # macron
    hand(0x306, 2, ['.#...#.', '..###..'])            # breve
    hand(0x307, 3, ['...#...'])                       # dot above
    hand(0x30B, 2, ['..#.#..', '.#.#...'])            # double acute
    hand(0x30C, 2, ['.#...#.', '..#.#..'])            # caron
    m[0x328, False] = m[0x328, True] = pack(          # ogonek, below
        ['.......'] * 11 + ['...##..', '.....#.', '...##..'])
    return m
