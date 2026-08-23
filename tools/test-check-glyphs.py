#!/usr/bin/env python3
"""Fault injection for tools/check-glyphs.py: prove it can still go red.

Usage: test-check-glyphs.py [SIZE]        (default 7x14)

A green check means nothing unless the check can fail.  Two defects got past
this checker while it reported success, and both had the same shape -- a rule
that quietly verified less than it claimed:

  * a drawing that parses to the right pixels but is not what `make headers`
    writes (a trailing blank line, CRLF endings) passed, because only the
    header LINE was compared;
  * a run with no built faces to check announced that it was skipping the
    built-face check and then exited 0, so four rules out of five read as five.

Each case below breaks one thing and insists check-glyphs.py notices.  Case 1
is the control: without a clean tree that passes, a checker that failed on
everything would score full marks here.

The five metric cases are not invented failures.  Every one of them is a
defect this font actually shipped with, back when the built face came out of
fonttosfnt: the advance width and the average width disagreed, a phantom
lineGap appeared, and fsSelection said REGULAR on all four faces so none of
them ever paired.  The build no longer goes anywhere near that tool, which is
exactly when a check stops being exercised and starts being decorative.

Each case runs against a sandbox under build/, never against the working tree,
so an interrupted run cannot leave a broken drawing behind.  glyphs/ is copied
because the cases edit it; upstream/ and build/gen/ are symlinked because they
are only read.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
CHECKER = os.path.join(HERE, 'check-glyphs.py')
ROOT = os.path.dirname(HERE)


def sandbox():
    """A throwaway copy of the tree, just complete enough to check."""
    if not os.path.isdir(os.path.join(ROOT, 'build', 'gen', SIZE)):
        sys.exit(f'test-check-glyphs.py: nothing built for {SIZE}; '
                 f'run `make` first')
    d = tempfile.mkdtemp(prefix='selftest-', dir=os.path.join(ROOT, 'build'))
    shutil.copytree(os.path.join(ROOT, gs.HAND_ROOT), os.path.join(d, 'glyphs'))
    os.symlink(os.path.join(ROOT, gs.UPSTREAM_ROOT), os.path.join(d, 'upstream'))
    os.mkdir(os.path.join(d, 'build'))
    os.symlink(os.path.join(ROOT, gs.GEN_ROOT), os.path.join(d, 'build', 'gen'))
    for face in gs.FACES:
        name = gs.font_stem(SIZE, face) + '.ttf'
        src = os.path.join(ROOT, 'build', name)
        if not os.path.isfile(src):
            shutil.rmtree(d, ignore_errors=True)
            sys.exit(f'test-check-glyphs.py: build/{name} is missing; '
                     f'run `make` first')
        shutil.copyfile(src, os.path.join(d, 'build', name))
    return d


def run(d):
    r = subprocess.run([sys.executable, CHECKER, SIZE], cwd=d,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def drawing(d, cp=0x00A7):
    return os.path.join(d, 'glyphs', SIZE, 'regular', gs.filename(cp))


def built(d, face='regular'):
    return os.path.join(d, 'build', gs.font_stem(SIZE, face) + '.ttf')


def edit_font(path, mutate):
    """Load a face, break it, write it back.

    lazy=False and a write to a SEPARATE path, then a rename.  TTFont reads
    tables on demand, so saving over the file it is still reading produces a
    font that is neither the original nor the edit -- which reads here as a
    checker that failed for the wrong reason.
    """
    from fontTools.ttLib import TTFont
    font = TTFont(path, lazy=False)
    mutate(font)
    font.save(path + '.tmp')
    font.close()
    os.replace(path + '.tmp', path)


# ---- the cases.  Each takes the sandbox and breaks one thing. --------------

def clean(_d):
    """the control: an untouched tree must pass"""


def trailing_blank_line(d):
    """a trailing blank line, which still parses to the same pixels"""
    with open(drawing(d), 'a') as fh:
        fh.write('\n')


def trailing_space(d):
    """a trailing space on the header line"""
    p = drawing(d)
    text = gs.read_raw(p).split('\n')
    text[0] += ' '
    open(p, 'w', newline='').write('\n'.join(text))


def crlf(d):
    """CRLF line endings, which universal-newline reads hide"""
    p = drawing(d)
    raw = gs.read_raw(p)
    open(p, 'w', newline='').write(raw.replace('\n', '\r\n'))


def missing_header(d):
    """no header line at all"""
    p = drawing(d)
    raw = gs.read_raw(p)
    open(p, 'w', newline='').write(raw.split('\n', 1)[1])


def no_built_faces(d):
    """nothing built to check -- must fail, not skip"""
    for face in gs.FACES:
        os.remove(built(d, face))


def half_built(d):
    """three faces where there should be four"""
    os.remove(built(d, 'bold-italic'))


# ---- the render contract.  Each is a defect this font has really had. ------

def wrong_upem(d):
    """upem no longer a whole number of pixels -- nothing lands on the grid"""
    def m(f):
        f['head'].unitsPerEm = 1000
    edit_font(built(d), m)


def xavg_lie(d):
    """xAvgCharWidth understates the advance, as fonttosfnt's did by 46%"""
    def m(f):
        f['OS/2'].xAvgCharWidth = int(f['OS/2'].xAvgCharWidth * 0.54)
    edit_font(built(d), m)


def phantom_linegap(d):
    """invented leading, which pushes the row height off the cell"""
    def m(f):
        f['hhea'].lineGap = 64
    edit_font(built(d), m)


def style_bits_disagree(d):
    """fsSelection says REGULAR on the bold face, so the faces never pair"""
    def m(f):
        f['OS/2'].fsSelection = 0x40
    edit_font(built(d, 'bold'), m)


def one_wide_glyph(d):
    """a single glyph with a different advance tears the grid from there on"""
    def m(f):
        name = f.getGlyphOrder()[5]
        w, lsb = f['hmtx'][name]
        f['hmtx'][name] = (w + 64, lsb)
    edit_font(built(d), m)


CASES = [(clean, True), (trailing_blank_line, False), (trailing_space, False),
         (crlf, False), (missing_header, False), (no_built_faces, False),
         (half_built, False), (wrong_upem, False), (xavg_lie, False),
         (phantom_linegap, False), (style_bits_disagree, False),
         (one_wide_glyph, False)]


def main():
    bad = 0
    for case, want_pass in CASES:
        d = sandbox()
        try:
            case(d)
            code, out = run(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        passed = code == 0
        ok = passed == want_pass
        bad += not ok
        verdict = 'ok  ' if ok else 'BAD '
        expect = 'pass' if want_pass else 'fail'
        print(f'  {verdict} {case.__name__:20s} expected to {expect}, '
              f'exit {code} -- {case.__doc__}')
        if not ok:
            print('\n'.join('       | ' + l for l in out.strip().split('\n')))
            if case is clean:
                # The sandbox is a copy of the real glyphs/, so the control
                # case also fails when the WORKING TREE is the thing at fault.
                # Say which, or this reads as "the checker is broken".
                print('       ^ the control failed, so the working tree itself '
                      'is not clean -- fix what it names (often `make headers`) '
                      'and run again')
    if bad:
        sys.exit(f'test-check-glyphs.py: {bad} of {len(CASES)} cases wrong -- '
                 f'check-glyphs.py is not checking what it claims to')
    print(f'test-check-glyphs.py: {len(CASES)} cases, all as expected')


main()
