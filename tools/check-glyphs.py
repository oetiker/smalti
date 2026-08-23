#!/usr/bin/env python3
"""Validate the glyph store and the faces built from it.

Usage: check-glyphs.py [--built DIR] [SIZE ...]

Checks, in the order the design spec lists them:

  * a filename is uppercase hex, at least four digits, and parses to a
    codepoint;
  * the file is byte-for-byte what `make headers` would write -- the whole
    file, not just its header line, including the two header special cases
    (the character is shown only when printable, and the fifteen codepoints
    with no Unicode name take <control> or <unnamed>);
  * every file is exactly H rows of exactly W characters drawn from '.' and
    '#';
  * every built face carries the metrics that make it render as drawn;
  * glyph counts per face are equal across the faces of a size.

THE WHOLE FILE, NOT ONE LINE OF IT
    Checking only the header line let a drawing drift without anyone noticing:
    a trailing blank line, or CRLF endings, still parses to the same pixels, so
    the font was unaffected and the check stayed green -- while `make headers`
    would rewrite the file, which means the tree was not in the normal form CI
    is supposed to be enforcing.  The rule is now the one glyphstore.normalised
    states, applied to every byte.

THE RENDER CONTRACT
    A .ttf can be shaped perfectly and still render wrong, because a
    rasteriser is told where the pixel grid is by the METRICS, not by the
    outlines.  check-outlines.py proves the shapes; this proves the frame
    around them:

      upem == cell height * 64      one pixel is exactly 64 units, so at the
                                    drawn size every edge lands on a device
                                    pixel boundary -- this is the whole reason
                                    the outline reproduces the bitmap
      ascent - descent == upem      the line box is exactly the cell, so a
                                    terminal's row height is the drawn height
      lineGap == 0                  no invented leading
      xAvgCharWidth == advance      a terminal sizes its cell from this; when
                                    it lied, wezterm rendered every fallback
                                    glyph at about half size
      every advance equal           it is a monospace font or it is nothing
      fsSelection agrees with
        head.macStyle               they disagreed once and the four faces
                                    never paired: no bold, no italic

    Each of those has been wrong in a shipped build of this font at least
    once.  None of them is theoretical.

A CHECK THAT CANNOT FAIL MUST NOT PASS
    If the built faces this needs are absent, that is a failure, not a skip.
    Announcing "skipping the built-face check" and then exiting 0 reads to CI
    and to a contributor as full coverage of a run that verified four rules
    out of five.  tools/test-check-glyphs.py breaks the tree seven ways and
    insists this notices each one.

A duplicate codepoint is not checked for, because one file per glyph makes it
impossible: the filesystem enforces uniqueness.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphstore as gs

# Font units per pixel.  Taken from the tracer rather than re-typed here: it
# is the number the whole render contract is built on, and two copies of it
# would eventually be two different numbers.
_spec = importlib.util.spec_from_file_location(
    'trace_outline', os.path.join(HERE, 'trace-outline.py'))
_trace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trace)
PX = _trace.PX

problems = []


def fail(msg):
    problems.append(msg)


def first_difference(raw, want):
    """Where a file stops being its normal form, said in a way you can act on."""
    a, b = raw.split('\n'), want.split('\n')
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x == y:
            continue
        n = i + 1
        if y is None:
            return f'line {n}: {x!r} is past the end of the normal form'
        if x is None:
            return f'line {n}: file ends early, normal form has {y!r}'
        return f'line {n}: has {x!r}, normal form has {y!r}'
    return 'differs invisibly'          # unreachable while raw != want


def check_files(size):
    w, h = gs.cell(size)
    n = 0
    for face in gs.FACES:
        d = gs.hand_dir(size, face)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            path = os.path.join(d, name)
            if not name.endswith('.txt'):
                fail(f'{path}: not a glyph file (every file here is <CP>.txt)')
                continue
            cp = gs.cp_of(name)
            if cp is None:
                fail(f'{path}: filename must be the codepoint in uppercase '
                     f'hex, at least four digits')
                continue
            try:
                rows = gs.read_glyph(path, w, h)
            except gs.GlyphError as e:
                fail(str(e))
                continue
            if any(len(r) != w or set(r) - {'.', '#'} for r in rows):
                fail(f'{path}: rows must be {w} characters of . and #')
            # The whole file, byte for byte.  A drawing that parses to the
            # right pixels but is not what `make headers` writes is drift, and
            # drift is what this check exists to stop.
            raw = gs.read_raw(path)
            want = gs.normalised(cp, rows)
            if raw != want:
                fail(f'{path}: not what `make headers` would write -- '
                     + first_difference(raw, want))
            n += 1
    return n


def check_counts(size):
    counts = {}
    for face in gs.FACES:
        counts[face] = len(gs.resolve(size, face))
    if len(set(counts.values())) > 1:
        fail(f'{size}: faces carry different glyph counts: ' +
             ', '.join(f'{f} {n}' for f, n in counts.items()))
    return counts


def check_built(built, sizes):
    """Every built .ttf must carry the metrics that make it render as drawn.

    The faces are named, not discovered.  A glob would let a half-finished
    build -- three faces where there should be four -- satisfy this check, and
    an empty directory would satisfy it completely.  Absence is a failure with
    a way out of it, never a skip.

    See THE RENDER CONTRACT in the module docstring for why each field is
    here.  Read the compiled font, never the tracer's own numbers, so a bug
    between the two cannot hide.
    """
    from fontTools.ttLib import TTFont

    # (fsSelection, macStyle, usWeightClass) each face must carry.  Bit 6 of
    # fsSelection is REGULAR and is exclusive with BOLD and ITALIC; macStyle
    # bit 0 is bold and bit 1 italic.  These two say the same thing in two
    # places and every consumer reads a different one, so they must agree.
    EXPECT = {
        'regular':     (0x40, 0x0, 400),
        'bold':        (0x20, 0x1, 700),
        'italic':      (0x01, 0x2, 400),
        'bold-italic': (0x21, 0x3, 700),
    }

    want = [(size, face, f'{gs.font_stem(size, face)}.ttf')
            for size in sizes for face in gs.FACES]
    missing = [f for _, _, f in want
               if not os.path.isfile(os.path.join(built, f))]
    if missing:
        fail(f'{len(missing)} of {len(want)} built faces are missing from '
             f'{built}/ ({", ".join(missing[:4])}'
             f'{", ..." if len(missing) > 4 else ""}), so the metric check '
             f'could not run -- run `make` first, or point --built at the '
             f'directory that holds them')
        return

    for size, face, name in want:
        cell_w, cell_h = gs.cell(size)
        upem_want = cell_h * PX
        adv_want = cell_w * PX
        font = TTFont(os.path.join(built, name))
        head, hhea, os2 = font['head'], font['hhea'], font['OS/2']

        def bad(what):
            fail(f'{name}: {what}')

        if head.unitsPerEm != upem_want:
            bad(f'unitsPerEm is {head.unitsPerEm}, not {upem_want} '
                f'(= {cell_h} rows * {PX} units per pixel).  One pixel is no '
                f'longer a whole number of units, so nothing lands on the '
                f'pixel grid and every glyph renders blurred')
        if hhea.lineGap != 0:
            bad(f'hhea.lineGap is {hhea.lineGap}, not 0 -- leading belongs to '
                f'the terminal, not to the font')
        box = hhea.ascent - hhea.descent + hhea.lineGap
        if box != head.unitsPerEm:
            bad(f'the line box is {box} units but upem is {head.unitsPerEm}; '
                f'a row of text is then taller or shorter than the cell the '
                f'glyphs were drawn in')
        if (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) != \
                (hhea.ascent, hhea.descent, hhea.lineGap):
            bad(f'OS/2 sTypo* ({os2.sTypoAscender}, {os2.sTypoDescender}, '
                f'{os2.sTypoLineGap}) contradicts hhea ({hhea.ascent}, '
                f'{hhea.descent}, {hhea.lineGap}); consumers read one or the '
                f'other and would disagree about the row height')
        if (os2.usWinAscent, os2.usWinDescent) != (hhea.ascent, -hhea.descent):
            bad(f'OS/2 usWin ({os2.usWinAscent}, {os2.usWinDescent}) '
                f'contradicts hhea ({hhea.ascent}, {hhea.descent}); this is '
                f'the pair that clips glyphs when it is too small')
        if os2.xAvgCharWidth != adv_want:
            bad(f'OS/2 xAvgCharWidth is {os2.xAvgCharWidth}, not {adv_want}.  '
                f'A terminal sizes its cell from this field; when it lied by '
                f'46% wezterm drew every fallback glyph at half size')

        widths = {m[0] for m in font['hmtx'].metrics.values()}
        if widths != {adv_want}:
            bad(f'advances are {sorted(widths)}, not all {adv_want} -- a '
                f'monospace font with a glyph of a different width tears the '
                f'whole grid apart from that column on')

        fs_want, mac_want, weight_want = EXPECT[face]
        if os2.fsSelection != fs_want:
            bad(f'OS/2 fsSelection is {os2.fsSelection:#0b}, not '
                f'{fs_want:#0b}')
        if head.macStyle != mac_want:
            bad(f'head.macStyle is {head.macStyle:#0b}, not {mac_want:#0b}.  '
                f'When this contradicted fsSelection the four faces never '
                f'paired: bold text stayed regular')
        if os2.usWeightClass != weight_want:
            bad(f'OS/2 usWeightClass is {os2.usWeightClass}, not '
                f'{weight_want}')

        names = {i: font['name'].getDebugName(i) for i in (1, 2, 4, 5, 6)}
        fam_want = f'{gs.FAMILY} {size}'
        if names[1] != fam_want:
            bad(f'name ID 1 is {names[1]!r}, not {fam_want!r}.  The cell size '
                f'is part of the family on purpose, so two sizes can be '
                f'installed side by side')
        for i in (2, 4, 5, 6):
            if not names[i]:
                bad(f'name ID {i} is missing; OpenType requires it and '
                    f'fontconfig pairs faces with 2')
        font.close()

    print(f'  {len(want)} built faces carry the render contract')


def main():
    argv = sys.argv[1:]
    built = 'build'
    if argv and argv[0] == '--built':
        built, argv = argv[1], argv[2:]
    sizes = argv or sorted(d for d in os.listdir(gs.HAND_ROOT)
                           if os.path.isdir(os.path.join(gs.HAND_ROOT, d)))
    for size in sizes:
        n = check_files(size)
        counts = check_counts(size)
        print(f'{size}: {n} drawings, ' +
              ', '.join(f'{f} {c}' for f, c in counts.items()))
    check_built(built, sizes)
    for p in problems:
        print('FAIL ' + p, file=sys.stderr)
    if problems:
        sys.exit(f'{len(problems)} problem(s)')
    print('check: ok')


main()
