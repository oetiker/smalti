#!/usr/bin/env python3
"""Generate the U+2190..U+21FF arrow block into build/gen/.

Usage: gen-arrows.py [SIZE]           (default 7x14)

The block is mostly one arrow seen from four sides, so it is composed rather
than hand-drawn: a handful of parts (shaft, head, tail, overlay) are drawn
once facing right or up, and the other directions come from mirroring.  That
is the only way 112 arrows stay consistent with each other.

Mirroring is done inside the glyph's own ink window, so an arrow keeps its
vertical position instead of sliding down the cell.

Honest limit: at 7x14 some distinctions Unicode makes are finer than the cell.
A wave arrow and a squiggle arrow differ by one pixel of amplitude; a triple
arrow is three lines because four would touch.  They are drawn distinct where
distinct is possible and directionally correct always -- which still beats
falling through to a font of a different weight.

This writes only into build/gen/, so it is freely re-runnable and cannot
overwrite anyone's work.  To change one arrow, draw it: a file in
glyphs/<size>/regular/ outranks anything here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
if SIZE != '7x14':
    sys.exit(f'gen-arrows.py: the parts below are drawn at 7x14, not {SIZE}')

def F(**rows):
    bm = [0] * 14
    for k, pat in rows.items():
        r = int(k[1:])
        bm[r] |= sum(1 << (7 - i) for i, ch in enumerate(pat) if ch == '#')
    return bm

def merge(*bms):
    out = [0] * 14
    for bm in bms:
        for i, v in enumerate(bm):
            out[i] |= v
    return out

def hflip(bm):
    out = []
    for v in bm:
        n = 0
        for c in range(7):
            if v & (1 << (7 - c)):
                n |= 1 << (7 - (6 - c))
        out.append(n)
    return out

def vflip(bm):
    """Mirror inside the glyph's own ink window, so it stays put vertically."""
    used = [i for i, v in enumerate(bm) if v]
    if not used:
        return list(bm)
    lo, hi = used[0], used[-1]
    out = list(bm)
    for r in range(lo, hi + 1):
        out[r] = bm[hi - (r - lo)]
    return out

# ---- horizontal parts, facing right ---------------------------------------
SHAFT   = F(r7='######.')
LONG    = F(r7='#######')
HEAD    = F(r4='..#....', r5='..##...', r6='..###..', r7='..####.',
            r8='..###..', r9='..##...', r10='..#....')
HEADOPN = F(r4='..#....', r5='...#...', r6='....#..', r7='.....#.',
            r8='....#..', r9='...#...', r10='..#....')
HEADTWO = F(r5='.#.#...', r6='..#.#..', r7='...#.#.',
            r8='..#.#..', r9='.#.#...')
BARBUP  = F(r4='..#....', r5='..##...', r6='..###..')
BARBDN  = F(r8='..###..', r9='..##...', r10='..#....')
TAILBAR = F(r4='#......', r5='#......', r6='#......', r7='#......',
            r8='#......', r9='#......', r10='#......')
TAILCHV = F(r5='#......', r6='.#.....', r8='.#.....', r9='#......')
HOOK    = F(r8='#......', r9='#......', r10='##.....')
LOOP    = F(r8='.#.....', r9='#.#....', r10='.#.....')
CIRCLE  = F(r6='##.....', r7='#.#....', r8='##.....')
STROKE  = F(r4='...#...', r5='..#....', r6='..#....', r8='.#.....',
            r9='.#.....', r10='#......')
VSTROKE = F(r4='..#....', r5='..#....', r6='..#....',
            r8='..#....', r9='..#....', r10='..#....')
DVSTROK = F(r4='.#.#...', r5='.#.#...', r6='.#.#...',
            r8='.#.#...', r9='.#.#...', r10='.#.#...')
DOUBLE  = F(r4='....#..', r5='.....#.', r6='######.', r7='......#',
            r8='######.', r9='.....#.', r10='....#..')
TRIPLE  = F(r4='.....#.', r5='#####..', r6='......#', r7='#####..',
            r8='......#', r9='#####..', r10='.....#.')
WHITE   = F(r4='...#...', r5='...##..', r6='####.#.', r7='#.....#',
            r8='####.#.', r9='...##..', r10='...#...')
MINI_HI = F(r4='....#..', r5='######.', r6='....#..')
MINI_LO = F(r8='....#..', r9='######.', r10='....#..')
HARP_HI = F(r4='....#..', r5='######.')
HARP_LO = F(r9='######.', r10='....#..')
WAVE    = F(r5='....#..', r6='#.#..#.', r7='.#.####', r8='.....#.',
            r9='....#..')
SQUIG   = F(r5='....#..', r6='.#...#.', r7='#.#.###', r8='...#.#.',
            r9='....#..')

# ---- vertical parts, facing up --------------------------------------------
VSHAFT  = F(**{f'r{r}': '...#...' for r in range(5, 13)})
VHEAD   = F(r2='...#...', r3='..###..', r4='.#####.')
VHEADOP = F(r2='...#...', r3='..#.#..', r4='.#...#.')
VHEADTW = F(r2='...#...', r3='..###..', r5='...#...', r6='..###..')
VBAR    = F(r12='.#####.')
VDSTROK = F(r8='..###..', r10='..###..')
VDOUBLE = F(r2='...#...', r3='..###..', r4='.##.##.',
            **{f'r{r}': '..#.#..' for r in range(5, 13)})
VWHITE  = F(r3='...#...', r4='..#.#..', r5='.#...#.', r6='##...##',
            r7='.##.##.', r8='..#.#..', r9='..#.#..', r10='..###..')
VPED    = F(r12='#######')
VHARP_R = F(r2='...#...', r3='...##..', r4='...###.')
VHARP_L = F(r2='...#...', r3='..##...', r4='.###...')
VMINI_L = F(**{f'r{r}': '.#.....' for r in range(4, 12)},
            r3='###....', r2='.#.....')
VMINI_R = F(**{f'r{r}': '.....#.' for r in range(4, 12)},
            r3='....###', r2='.....#.')

# ---- diagonals, facing north-east -----------------------------------------
NE = F(r3='....###', r4='.....##', r5='....#.#', r6='...#...',
       r7='..#....', r8='.#.....', r9='#......')
NE2 = F(r3='...####', r4='...#..#', r5='..#.#.#', r6='.#.#...',
        r7='#.#....', r8='.#.....', r9='#......')

# ---- rotational, hand-drawn ------------------------------------------------
TIPL = F(r5='.#.....', r6='#####..', r7='.#..#..',
         r8='....#..', r9='....#..', r10='....#..')
CORNER_D = F(r4='#####..', r5='....#..', r6='....#..', r7='....#..',
             r8='...###.', r9='....#..')
RETURN = F(r4='.....#.', r5='.....#.', r6='.....#.', r7='.....#.',
           r8='..#..#.', r9='.#####.', r10='..#....')
# Drawn broken at the top rather than as a full ring plus an overlay: adding
# ink cannot make a gap, and the first attempt produced a solid arc.
CIRC_CW = F(r3='....#..', r4='..#.###', r5='.#...#.', r6='#.....#',
            r7='#.....#', r8='#.....#', r9='.#...#.', r10='..###..')
SEMI_CW = F(r4='..###..', r5='.#...#.', r6='#.....#', r7='.....##', r8='....#..')
ZIGZAG = F(r3='.####..', r4='...#...', r5='..#....', r6='.####..',
           r7='...#...', r8='..#....', r9='.###...', r10='..#....')
UPDOWN = F(r2='...#...', r3='..###..', r4='.#####.',
           **{f'r{r}': '...#...' for r in range(5, 10)})

G = {}
def put(cp, bm):
    G[cp] = bm

RIGHT = merge(SHAFT, HEAD)
UP = merge(VSHAFT, VHEAD)

put(0x2196, hflip(NE));            put(0x2197, NE)
put(0x2198, vflip(NE));            put(0x2199, hflip(vflip(NE)))
put(0x219A, hflip(merge(RIGHT, hflip(STROKE))))
put(0x219B, merge(RIGHT, STROKE))
put(0x219C, hflip(WAVE));          put(0x219D, WAVE)
put(0x219E, hflip(merge(SHAFT, HEADTWO)))
put(0x21A0, merge(SHAFT, HEADTWO))
put(0x219F, merge(VSHAFT, VHEADTW))
put(0x21A1, vflip(merge(VSHAFT, VHEADTW)))
put(0x21A2, hflip(merge(RIGHT, TAILCHV)))
put(0x21A3, merge(RIGHT, TAILCHV))
put(0x21A4, hflip(merge(RIGHT, TAILBAR)))
put(0x21A6, merge(RIGHT, TAILBAR))
put(0x21A5, merge(UP, VBAR));      put(0x21A7, vflip(merge(UP, VBAR)))
put(0x21A8, merge(UPDOWN, vflip(VHEAD), F(r11='.#####.')))
put(0x21A9, hflip(merge(RIGHT, HOOK)))
put(0x21AA, merge(RIGHT, HOOK))
put(0x21AB, hflip(merge(RIGHT, LOOP)))
put(0x21AC, merge(RIGHT, LOOP))
put(0x21AD, merge(WAVE, F(r5='.#.....', r10='.#.....')))
put(0x21AE, merge(LONG, HEAD, hflip(HEAD), STROKE))
put(0x21AF, ZIGZAG)
put(0x21B0, TIPL);                 put(0x21B1, hflip(TIPL))
put(0x21B2, vflip(TIPL));          put(0x21B3, hflip(vflip(TIPL)))
put(0x21B4, CORNER_D)
put(0x21B6, hflip(SEMI_CW));       put(0x21B7, SEMI_CW)
put(0x21B8, merge(hflip(NE), F(r1='#######')))
put(0x21B9, merge(hflip(merge(MINI_HI, F(r4='#......', r5='#......', r6='#......'))),
                  merge(MINI_LO, F(r8='......#', r9='......#', r10='......#'))))
put(0x21BA, hflip(CIRC_CW))
put(0x21BB, CIRC_CW)
put(0x21BC, hflip(merge(SHAFT, BARBUP)))
put(0x21BD, hflip(merge(SHAFT, BARBDN)))
put(0x21C0, merge(SHAFT, BARBUP)); put(0x21C1, merge(SHAFT, BARBDN))
put(0x21BE, merge(VSHAFT, VHARP_R)); put(0x21BF, merge(VSHAFT, VHARP_L))
put(0x21C2, vflip(merge(VSHAFT, VHARP_R)))
put(0x21C3, vflip(merge(VSHAFT, VHARP_L)))
put(0x21C4, merge(MINI_HI, hflip(MINI_LO)))
put(0x21C6, merge(hflip(MINI_HI), MINI_LO))
put(0x21C7, hflip(merge(MINI_HI, MINI_LO)))
put(0x21C9, merge(MINI_HI, MINI_LO))
put(0x21C5, merge(VMINI_L, vflip(VMINI_R)))
put(0x21F5, merge(vflip(VMINI_L), VMINI_R))
put(0x21C8, merge(VMINI_L, VMINI_R))
put(0x21CA, vflip(merge(VMINI_L, VMINI_R)))
put(0x21CB, merge(hflip(HARP_HI), HARP_LO))
put(0x21CC, merge(HARP_HI, hflip(HARP_LO)))
put(0x21CD, hflip(merge(DOUBLE, hflip(STROKE))))
put(0x21CF, merge(DOUBLE, STROKE))
put(0x21CE, merge(DOUBLE, hflip(DOUBLE), STROKE))
put(0x21D1, VDOUBLE);              put(0x21D3, vflip(VDOUBLE))
put(0x21D5, merge(VDOUBLE, vflip(VDOUBLE)))
put(0x21D6, hflip(NE2));           put(0x21D7, NE2)
put(0x21D8, vflip(NE2));           put(0x21D9, hflip(vflip(NE2)))
put(0x21DA, hflip(TRIPLE));        put(0x21DB, TRIPLE)
put(0x21DC, hflip(SQUIG));         put(0x21DD, SQUIG)
put(0x21DE, merge(UP, VSHAFT, VDSTROK))
put(0x21DF, vflip(merge(UP, VSHAFT, VDSTROK)))
put(0x21EA, merge(VWHITE, VBAR))
put(0x21EB, merge(VWHITE, VPED))
put(0x21EC, merge(VWHITE, VPED, F(r11='..###..')))
put(0x21ED, merge(VWHITE, VPED, F(r11='...#...')))
put(0x21EE, merge(VWHITE, F(r11='..#.#..', r12='..#.#..')))
put(0x21EF, merge(VWHITE, F(r11='..#.#..'), VPED))
put(0x21F0, merge(WHITE, TAILBAR))
CORNER_NW = F(r3='#####..', r4='#......', r5='..###..', r6='..##...',
              r7='..#.#..', r8='.....#.', r9='......#')
put(0x21F1, CORNER_NW)
put(0x21F2, hflip(vflip(CORNER_NW)))
put(0x21F3, merge(VWHITE, vflip(VWHITE)))
put(0x21F4, merge(RIGHT, CIRCLE))
put(0x21F6, merge(F(r3='....#..', r4='######.', r5='....#..'),
                  F(r6='....#..', r7='######.', r8='....#..'),
                  F(r9='....#..', r10='######.', r11='....#..')))
put(0x21F7, hflip(merge(RIGHT, hflip(VSTROKE))))
put(0x21F8, merge(RIGHT, VSTROKE))
put(0x21F9, merge(LONG, HEAD, hflip(HEAD), VSTROKE))
put(0x21FA, hflip(merge(RIGHT, hflip(DVSTROK))))
put(0x21FB, merge(RIGHT, DVSTROK))
put(0x21FC, merge(LONG, HEAD, hflip(HEAD), DVSTROK))
put(0x21FD, hflip(merge(SHAFT, HEADOPN)))
put(0x21FE, merge(SHAFT, HEADOPN))
put(0x21FF, merge(LONG, HEADOPN, hflip(HEADOPN)))

out = gs.gen_dir(SIZE, 'regular')
for cp in sorted(G):
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp, gs.art(G[cp], 7))
print(f'{out}: {len(G)} arrows')
