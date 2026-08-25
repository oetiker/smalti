#!/usr/bin/env python3
"""Derive the italic face from the resolved regular face by shearing it.

Usage: slant-bdf.py [--steps R,R,...] [SIZE]        (default 7x14)

IT CONSUMES THE RESOLVED FACE, NOT A BUILT BDF
    Every layer of the regular face is in place by the time this runs, so
    hand-drawing a regular glyph improves its italic automatically.  The output
    is only a candidate: a drawing in glyphs/<size>/italic/ outranks it, which
    is how the nine letters this leaves upright can be corrected by hand.

WHY A SHEAR AND NOT REDRAWN LETTERFORMS
    At 7x14 there is no room for cursive letterforms.  A shear keeps every
    stroke Tamzen drew and changes only where it sits.

THE GEOMETRY: A CONSTANT SLOPE, NOT A SINGLE STEP
    Tamzen draws in columns 1..5 and keeps column 0 and column 6 as side
    bearing -- one free column on each side.  The lean spends both of them:
    rows above the first step move one column RIGHT, rows below the last step
    move one column LEFT, and the rows between stay put.  Two pixels of lean
    in total, with the glyph still centred in its cell.

    The displacement depends on the ROW, not on the character, which is what
    makes it a slope rather than a kink.  A tall letter therefore leans
    further than a short one, exactly as in a real oblique, and the top of a
    long stem keeps leaning instead of stopping.  An earlier version stepped
    once at a fixed row: every letter then leaned the same one pixel whatever
    its height, so ascenders and capitals went flat above the step.

    --steps 5,8 is the default and puts the steps either side of the
    x-height.  An x-height letter (rows 5..10) is split three and three; a
    capital (rows 3..10) gets its extra lean in the two rows above the
    x-height; a descender (rows 11..13) trails to the left of the baseline.

WHY THE SHEAR IS UNIFORM ACROSS GLYPHS
    Every slanted glyph uses the same displacement at the same row, so the
    two columns of gap between two slanted neighbours are preserved at every
    row.  Between a slanted glyph and an upright one -- a bracket, or one of
    the crowded letters below -- the gap narrows to one column at the top and
    bottom rows.  That is unavoidable when the two lean differently, and it
    is what upright brackets around italic text look like anyway.

WHAT IS SLANTED
    Letters, digits, and the punctuation that is TEXT rather than drawing:
    '#', ':', ';', '!' and '?'.  Everything else keeps its upright form.  Box
    drawing, block elements, braille, arrows, dingbats, geometric shapes and
    the Powerline separators all have to tile with their neighbours or line
    up in a column, and a shear breaks that.  Brackets, pipes and slashes
    stay upright too, so ASCII tables and diagrams keep their verticals.

    A few letters are drawn edge to edge -- Tamzen widens 'AE', 'IJ', 'OE'
    and the raised-comma letters into the side bearing to get their width --
    so there is nothing to lean them into.  Shearing only their other rows
    would put a kink in the middle of a stroke, so they stay upright and the
    tool names them.
"""
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

CELL_W = 7
STEPS = (5, 8)       # rows where the displacement drops by one column


def pad_mask():
    """The packed-row bits that are real columns at the current CELL_W.

    A BDF row is padded to a whole byte, MSB first, so column c is bit 7-c
    and the low 8-CELL_W bits are padding.  This must be a FUNCTION of
    CELL_W, not a constant computed once at import: CELL_W is still the
    default 7 at that point, and main() only reassigns CELL_W itself, so a
    module-level `PAD_MASK = 0xFF << (8 - CELL_W) & 0xFF` evaluated here
    would freeze at 0xFE and silently clear column 7 at every width above 7
    (tools/weight.py's _mask() and tools/slant-bold.py document the same
    trap).  Calling this after CELL_W is set keeps it live.
    """
    return 0xFF << (8 - CELL_W) & 0xFF


# Punctuation that reads as text and should lean with the letters around it.
PUNCT = {0x23, 0x3A, 0x3B, 0x21, 0x3F}       # # : ; ! ?
LETTERS = {'Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd', 'Nl'}


def offset(row):
    """Columns to move this row, positive right."""
    return 1 - sum(1 for s in STEPS if row >= s)


def is_slanted(cp):
    if cp in PUNCT:
        return True
    try:
        return unicodedata.category(chr(cp)) in LETTERS
    except ValueError:
        return False


def move(v, k):
    mask = pad_mask()
    return (v >> k) & mask if k >= 0 else (v << -k) & mask


def has_room(rows):
    """False if any row would push ink out of the cell in either direction."""
    mask = pad_mask()
    for r, v in enumerate(rows):
        k = offset(r)
        if k > 0:
            # Shifting right by k loses ink from the rightmost k columns.
            # Column c is bit 7-c, so the rightmost k columns of a CELL_W
            # wide row are bits (8-CELL_W)..(8-CELL_W+k-1).  At CELL_W=7
            # that is bits 1..k, and testing bits 0..k (as this used to)
            # gave the same answer only because bit 0 is always-clear
            # padding there; at CELL_W=8 there is no padding bit to absorb
            # the extra bit and the wider test wrongly rejected glyphs that
            # actually had room.
            overflow = ((1 << k) - 1) << (8 - CELL_W)
            if v & overflow:
                return False
        if k < 0 and v & (mask ^ (mask >> -k)):
            return False
    return True


def shear(rows):
    return [move(v, offset(r)) for r, v in enumerate(rows)]


def main():
    global STEPS, CELL_W
    argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] == '--steps':
        STEPS = tuple(int(x) for x in argv[1].split(','))
        argv = argv[2:]
    size = argv[0] if argv else '7x14'
    CELL_W, _h = gs.cell(size)

    regular = gs.bitmaps(size, 'regular')
    if not regular:
        sys.exit(f'slant-bdf.py: the {size} regular face resolved to nothing')
    outdir = gs.gen_dir(size, 'italic')

    crowded, n = [], 0
    for cp, rows in sorted(regular.items()):
        out = rows
        if is_slanted(cp):
            if has_room(rows):
                out = shear(rows)
                n += 1
            else:
                crowded.append(cp)
        gs.write_glyph(os.path.join(outdir, gs.filename(cp)), cp,
                       gs.art(out, CELL_W))

    steps = ','.join(str(s) for s in STEPS)
    print(f'{outdir}: {n} of {len(regular)} glyphs sheared, steps at {steps}')
    if crowded:
        print('  left upright, no room to lean: '
              + ' '.join(f'U+{c:04X} {chr(c)}' for c in sorted(crowded)))


main()
