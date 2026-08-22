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
  * every built face passes repair-tamzen.py with no remaining defect;
  * glyph counts per face are equal across the faces of a size.

THE WHOLE FILE, NOT ONE LINE OF IT
    Checking only the header line let a drawing drift without anyone noticing:
    a trailing blank line, or CRLF endings, still parses to the same pixels, so
    the font was unaffected and the check stayed green -- while `make headers`
    would rewrite the file, which means the tree was not in the normal form CI
    is supposed to be enforcing.  The rule is now the one glyphstore.normalised
    states, applied to every byte.

A CHECK THAT CANNOT FAIL MUST NOT PASS
    If the built faces this needs are absent, that is a failure, not a skip.
    Announcing "skipping the repair check" and then exiting 0 reads to CI and
    to a contributor as full coverage of a run that verified four rules out of
    five.  tools/test-check-glyphs.py breaks the tree six ways and insists this
    notices each one.

A duplicate codepoint is not checked for, because one file per glyph makes it
impossible: the filesystem enforces uniqueness.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphstore as gs

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
    """Every built .otb must already be repaired: re-running fixes nothing.

    The faces are named, not discovered.  A glob would let a half-finished
    build -- three faces where there should be four -- satisfy this check, and
    an empty directory would satisfy it completely.  Absence is a failure with
    a way out of it, never a skip.
    """
    want = [f'{gs.font_stem(size, face)}.otb'
            for size in sizes for face in gs.FACES]
    missing = [f for f in want if not os.path.isfile(os.path.join(built, f))]
    if missing:
        fail(f'{len(missing)} of {len(want)} built faces are missing from '
             f'{built}/ ({", ".join(missing[:4])}'
             f'{", ..." if len(missing) > 4 else ""}), so the repair check '
             f'could not run -- run `make` first, or point --built at the '
             f'directory that holds them')
        return
    scratch = os.path.join(built, '.check')
    os.makedirs(scratch, exist_ok=True)
    try:
        for f in want:
            copy = os.path.join(scratch, f)
            shutil.copyfile(os.path.join(built, f), copy)
            out = subprocess.run(
                [sys.executable, os.path.join(HERE, 'repair-tamzen.py'), copy],
                capture_output=True, text=True)
            if out.returncode != 0:
                fail(f'{f}: repair-tamzen.py failed: {out.stderr.strip()}')
            elif 'already repaired' not in out.stdout:
                fail(f'{f}: still has defects after the build:\n'
                     + '\n'.join(out.stdout.strip().split('\n')[1:]))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print(f'  {len(want)} built faces re-checked with repair-tamzen.py')


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
