#!/usr/bin/env python3
"""Resolve the glyph store for one (size, face) and emit a BDF.

Usage: build-face.py SIZE FACE [--donor BDF] [--out FILE]

This is the merge step.  It does not know where a glyph came from beyond the
three layers tools/glyphstore.py defines, and it never invents one: an absent
generator shows up as a missing glyph, not as a silently smaller font.

    build-face.py 7x14 regular --out build/Smalti7x14-Regular.bdf
    build-face.py 7x14 italic --donor build/Smalti7x14-Regular.bdf --out ...

THE DONOR, AND WHY A SLANTED FACE NEEDS ONE
    A .txt file carries pixels and nothing else, but a BDF glyph also carries a
    name, an advance and a bounding box.  For regular and bold those come from
    upstream, whose blocks are copied through verbatim.  Italic and bold-italic
    have no upstream of their own, so they take that metadata from the upright
    face they lean -- regular and bold respectively -- which is what --donor
    points at.  The donor also fixes the glyph inventory: the two faces of a
    pair always carry exactly the same codepoints.

THE FONT IS RENAMED HERE, ONCE
    The result is no longer Tamzen -- five times the glyphs, and faces upstream
    never drew -- so it is rebranded at the point the merged font comes into
    being, and every derived face inherits that.  The size goes IN the family
    name because each strike is a separate file with its own metrics and its
    own design; if every size said "Smalti" a font matcher would see seven
    designs claiming the same four styles and pick among them arbitrarily,
    which is exactly the bug upstream has.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

FAMILY = gs.FAMILY          # one definition; the checker names files with it
COPYRIGHT_ADDED = '(c) 2026 Tobias Oetiker'


def rebrand(head, w, h):
    """Rename the font, keeping upstream's copyright and adding ours.

    fonttosfnt takes the OpenType family name from FAMILY_NAME and ignores the
    XLFD FONT line; both are rewritten anyway so the BDF is coherent read on
    its own.  The licence permits modification and the attribution is not
    conditional on the name, so upstream's notice stays.

    FONT_VERSION IS PART OF THE RENAME
        It is inherited, not written, and upstream's says 1.11 -- so until it
        is rewritten here, every face claims to be Tamzen 1.11 and the .ttf
        name table says so out loud (tools/trace-outline.py reads this
        property for nameID 5 and head.fontRevision).  A fork that ships
        someone else's version number is telling a font manager it is that
        font at that revision, which is exactly the collision the rename
        exists to end.
    """
    tag = f'{FAMILY}{w}x{h}'
    head = re.sub(r'^(FONT -[^-]*)-[^-]*-', rf'\1-{tag}-', head, flags=re.M)
    head = re.sub(r'^FAMILY_NAME ".*"$',
                  f'FAMILY_NAME "{FAMILY} {w}x{h}"', head, flags=re.M)
    head = re.sub(r'^COPYRIGHT "([^"]*)"$',
                  lambda m: f'COPYRIGHT "{m.group(1)}; {COPYRIGHT_ADDED}"',
                  head, flags=re.M)
    head, n = re.subn(r'^FONT_VERSION ".*"$',
                      f'FONT_VERSION "{gs.version()}"', head, flags=re.M)
    if n != 1:
        sys.exit(f'build-face.py: expected exactly one FONT_VERSION line in '
                 f'the upstream header, found {n} -- refusing to ship a face '
                 f'carrying an inherited version number')
    return head


def slant(head):
    """fonttosfnt reads the style from these two, and they must agree."""
    head = re.sub(r'^(FONT -[^-]*-[^-]*-[^-]*)-R-', r'\1-I-', head, flags=re.M)
    head = re.sub(r'^SLANT "R"$', 'SLANT "I"', head, flags=re.M)
    if 'SLANT "I"' not in head:
        sys.exit('build-face.py: could not set SLANT in the header')
    return head


def render(cp, bm, w, h, swidth):
    """A glyph block for art that has no upstream block to inherit from."""
    return (f'STARTCHAR U+{cp:04X}\n'
            f'ENCODING {cp}\n'
            f'SWIDTH {swidth}\n'
            f'DWIDTH {w} 0\n'
            f'BBX {w} {h} 0 -3\n'
            f'BITMAP\n' + '\n'.join(gs.hexrows(bm, w)) + '\nENDCHAR\n')


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('size')
    ap.add_argument('face', choices=gs.FACES)
    ap.add_argument('--donor')
    ap.add_argument('--out')
    args = ap.parse_args()
    size, face = args.size, args.face
    w, h = gs.cell(size)

    upright = gs.UPRIGHT_OF.get(face)
    if upright and not args.donor:
        sys.exit(f'build-face.py: the {face} face needs --donor '
                 f'(the built {upright} BDF)')

    if upright:
        donor = gs.Bdf(args.donor)
        head = slant(donor.head)
        meta, swidth = donor.pre, donor.swidth
        expect = set(donor.blocks)
    else:
        base = gs.Bdf(gs.upstream_bdf(size, face))
        head = rebrand(base.head, w, h)
        meta, swidth = {}, base.swidth
        expect = None

    resolved = gs.resolve(size, face)
    if not resolved:
        sys.exit(f'build-face.py: no glyphs resolved for {size}/{face}')
    if expect is not None and set(resolved) != expect:
        missing = sorted(expect - set(resolved))
        extra = sorted(set(resolved) - expect)
        sys.exit(f'build-face.py: {size}/{face} does not match its donor '
                 f'{args.donor}: {len(missing)} missing '
                 f'{["U+%04X" % c for c in missing[:8]]}, {len(extra)} extra '
                 f'{["U+%04X" % c for c in extra[:8]]}')

    counts = {'hand': 0, 'upstream': 0, 'gen': 0}
    blocks = {}
    for cp, (layer, bm) in resolved.items():
        counts[layer] += 1
        if layer == 'upstream':
            blocks[cp] = base.blocks[cp]
        elif cp in meta:
            blocks[cp] = ('STARTCHAR ' + meta[cp] + 'BITMAP\n'
                          + '\n'.join(gs.hexrows(bm, w)) + '\nENDCHAR\n')
        else:
            blocks[cp] = render(cp, bm, w, h, swidth)

    head = re.sub(r'^CHARS \d+$', f'CHARS {len(blocks)}', head, flags=re.M)
    out = [head + '\n']
    for cp in sorted(blocks):
        out.append(blocks[cp] + '\n')
    out.append('ENDFONT\n')
    text = ''.join(out)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
        open(args.out, 'w', encoding='latin1').write(text)
    else:
        sys.stdout.write(text)
    print(f'{size}/{face}: {len(blocks)} glyphs -- {counts["hand"]} drawn here, '
          f'{counts["upstream"]} upstream, {counts["gen"]} generated',
          file=sys.stderr)


main()
