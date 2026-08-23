#!/usr/bin/env python3
"""Every built face must carry the version in the VERSION file.

Usage: check-version.py SIZE            (e.g. check-version.py 7x14)

A release flow that bumps a number nothing reads is worthless, and the number
has two hops to get lost on: build-face.py writes it into the BDF as
FONT_VERSION, and trace-outline.py copies it from there into the .ttf name
table and head.fontRevision.  Either going quiet would ship a font claiming a
version it is not, and nothing else in `make check` would notice.

So this reads the number back out of the finished artefacts -- the same field
a font manager shows -- and compares it with the file the release commit
edits.  It names the faces it expects rather than checking whatever it finds:
a build that produced nothing at all must fail here, not pass having compared
zero files.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

from fontTools.ttLib import TTFont

BUILD = 'build'
# .woff2 is not part of `make all` -- it is built for the site and for a
# release -- so it is checked when it exists and never demanded.
REQUIRED = ('.ttf',)
OPTIONAL = ('.woff2',)

problems = []


def fail(msg):
    problems.append(msg)
    print(f'  FAIL  {msg}')


def check_file(path, version, revision):
    font = TTFont(path, lazy=True)
    try:
        got = font['name'].getDebugName(5)
        rev = font['head'].fontRevision
    finally:
        font.close()
    want = f'Version {version}'
    if got != want:
        fail(f'{path}: nameID 5 is {got!r}, expected {want!r}')
    # 16.16 fixed point: the stored value is the nearest 1/65536.
    if abs(rev - revision) > 1.0 / 65536:
        fail(f'{path}: head.fontRevision is {rev:g}, expected {revision:g}')


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.splitlines()[2])
    size = sys.argv[1]
    version = gs.version()
    revision = gs.font_revision(version)
    print(f'version {version} (head.fontRevision {revision:g}) '
          f'from {os.path.relpath(gs.VERSION_FILE, gs.ROOT)}')

    checked = 0
    for face in gs.FACES:
        stem = os.path.join(BUILD, gs.font_stem(size, face))
        for ext in REQUIRED:
            path = stem + ext
            if not os.path.exists(path):
                fail(f'{path}: not built, so its version cannot be checked')
                continue
            check_file(path, version, revision)
            checked += 1
        for ext in OPTIONAL:
            path = stem + ext
            if os.path.exists(path):
                check_file(path, version, revision)
                checked += 1

    if not checked:
        raise SystemExit('check-version.py: no built faces were read, so this '
                         'check proved nothing -- run `make` first')
    if problems:
        raise SystemExit(f'check-version.py: {len(problems)} problem(s) in '
                         f'{checked} files')
    print(f'  {checked} built files carry version {version}')


if __name__ == '__main__':
    main()
