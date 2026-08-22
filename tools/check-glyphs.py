#!/usr/bin/env python3
"""Validate the glyph store and the faces built from it.

Usage: check-glyphs.py [--built DIR] [SIZE ...]

Checks, in the order the design spec lists them:

  * a filename is uppercase hex, at least four digits, and parses to a
    codepoint;
  * the header line matches what `make headers` would write, including the two
    special cases (the character is shown only when printable, and the fifteen
    codepoints with no Unicode name take <control> or <unnamed>);
  * every file is exactly H rows of exactly W characters drawn from '.' and
    '#';
  * every built face passes repair-tamzen.py with no remaining defect;
  * glyph counts per face are equal across the faces of a size.

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
            want = gs.header(cp)
            first = open(path, encoding='utf-8').readline().rstrip('\n')
            if first != want:
                fail(f'{path}: header is {first!r}, `make headers` would write '
                     f'{want!r}')
            if any(len(r) != w or set(r) - {'.', '#'} for r in rows):
                fail(f'{path}: rows must be {w} characters of . and #')
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


def check_built(built):
    """Every built .otb must already be repaired: re-running fixes nothing."""
    otbs = sorted(f for f in os.listdir(built) if f.endswith('.otb')) \
        if os.path.isdir(built) else []
    if not otbs:
        print(f'  (no built .otb in {built}; skipping the repair check)')
        return
    scratch = os.path.join(built, '.check')
    os.makedirs(scratch, exist_ok=True)
    for f in otbs:
        copy = os.path.join(scratch, f)
        shutil.copyfile(os.path.join(built, f), copy)
        out = subprocess.run([sys.executable, os.path.join(HERE, 'repair-tamzen.py'),
                              copy], capture_output=True, text=True)
        if out.returncode != 0:
            fail(f'{f}: repair-tamzen.py failed: {out.stderr.strip()}')
        elif 'already repaired' not in out.stdout:
            fail(f'{f}: still has defects after the build:\n'
                 + '\n'.join(out.stdout.strip().split('\n')[1:]))
    shutil.rmtree(scratch)


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
    check_built(built)
    for p in problems:
        print('FAIL ' + p, file=sys.stderr)
    if problems:
        sys.exit(f'{len(problems)} problem(s)')
    print('check: ok')


main()
