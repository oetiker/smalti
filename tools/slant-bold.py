#!/usr/bin/env python3
"""Build the bold-italic face from the resolved regular, bold and italic faces.

Usage: slant-bold.py [SIZE]           (default 7x14)

WHY THIS IS NOT JUST slant-bdf.py RUN ON THE BOLD FACE
    The oblique spends both columns of side bearing: its top rows sit one
    column right and its bottom rows one column left.  The BOLD face has no
    side bearing left to spend -- emboldening widens strokes leftward, so 299
    of its 307 letters already start in column 0.  Shearing it can therefore
    move only one column instead of two, which is the shallow single-step
    lean whose flat stem tops the oblique was redesigned to avoid.

    So the order is reversed: shear first, embolden second.  A sheared glyph
    has ink in column 0 only on its lower rows, and tools/weight.py already
    widens rightward wherever the left is blocked, so nothing falls out of the
    cell.  Measured against the real bold face the result carries the same
    weight -- median difference zero pixels, worst case five.

    The consequence to know about: a bold-oblique letter is a widened shear of
    the REGULAR glyph, not a sheared copy of Tamzen's hand-tuned bold one.
    Where the two disagree -- Latin Extended-A, which is composed against the
    bold base font rather than emboldened -- the bold oblique follows the
    emboldening rule instead.

    Only the glyphs the oblique actually sheared are rebuilt this way.  Every
    other glyph, from box drawing to the Powerline separators, is copied
    straight from the resolved bold face so that the two bold faces stay
    identical wherever slant is meaningless.

    The output is only a candidate: a drawing in glyphs/<size>/bold-italic/
    outranks it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs
import weight
from weight import widen


def main():
    size = sys.argv[1] if len(sys.argv) > 1 else '7x14'
    # widen() reads its width from module state, so set it before the first
    # call below.
    weight.set_width(int(size.split('x')[0]))
    w, _h = gs.cell(size)
    bold = gs.bitmaps(size, 'bold')
    italic = gs.bitmaps(size, 'italic')
    upright = gs.bitmaps(size, 'regular')
    for name, face in (('bold', bold), ('italic', italic),
                       ('regular', upright)):
        if not face:
            sys.exit(f'slant-bold.py: the {size} {name} face resolved to nothing')
    outdir = gs.gen_dir(size, 'bold-italic')

    n = 0
    for cp, bm in sorted(bold.items()):
        # A glyph the oblique left alone is not a text glyph, or had no room
        # to lean; either way the upright bold form is the right one.
        if cp in italic and italic[cp] != upright.get(cp):
            bm = widen(italic[cp])
            n += 1
        gs.write_glyph(os.path.join(outdir, gs.filename(cp)), cp, gs.art(bm, w))

    print(f'{outdir}: {n} of {len(bold)} glyphs sheared and emboldened')


main()
