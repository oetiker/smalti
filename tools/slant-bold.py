#!/usr/bin/env python3
"""Build the bold oblique face.

Usage: slant-bold.py BOLD.bdf OBLIQUE.bdf UPRIGHT.bdf > BOLD-OBLIQUE.bdf

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
    Where the two disagree -- Latin Extended-A, which glyphs-bold/ composes
    against the bold base font rather than emboldening -- the bold oblique
    follows the emboldening rule instead.

    Only the glyphs the oblique actually sheared are rebuilt this way.  Every
    other glyph, from box drawing to the Powerline separators, is copied
    straight from the bold face so that the two bold faces stay identical
    wherever slant is meaningless.
"""
import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import accents
from weight import widen


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    bold_path, oblique_path, upright_path = sys.argv[1:4]
    oblique = accents.load(oblique_path)
    upright = accents.load(upright_path)

    text = open(bold_path, encoding='latin1').read()
    head, _, rest = text.partition('\nSTARTCHAR ')
    head = re.sub(r'^(FONT -[^-]*-[^-]*-[^-]*)-R-', r'\1-I-', head, flags=re.M)
    head = re.sub(r'^SLANT "R"$', 'SLANT "I"', head, flags=re.M)
    if 'SLANT "I"' not in head:
        sys.exit('slant-bold.py: could not set SLANT in the header')

    n, out = 0, []
    for chunk in ('STARTCHAR ' + rest).split('STARTCHAR ')[1:]:
        body, _, _tail = chunk.partition('ENDCHAR')
        cp = int(re.search(r'^ENCODING (-?\d+)', body, re.M).group(1))
        # A glyph the oblique left alone is not a text glyph, or had no room
        # to lean; either way the upright bold form is the right one.
        if cp in oblique and oblique[cp] != upright.get(cp):
            pre = body.partition('BITMAP\n')[0]
            rows = widen(oblique[cp])
            n += 1
            out.append('STARTCHAR ' + pre + 'BITMAP\n'
                       + '\n'.join(f'{v:02X}' for v in rows) + '\nENDCHAR\n')
        else:
            out.append('STARTCHAR ' + body + 'ENDCHAR\n')

    sys.stdout.write(head + '\n' + '\n'.join(out) + '\nENDFONT\n')
    print(f'{bold_path}: {n} glyphs sheared and emboldened', file=sys.stderr)


main()
