#!/usr/bin/env python3
"""Vendor the editor's hint fonts into site/hint/ -- run by hand, NOT by make.

Usage: make-hint-fonts.py [--out DIR] [--cache DIR] [--check]

The glyph editor can draw a faint ghost of the character behind the grid, so
that a contributor drawing a codepoint nobody has drawn yet can see what the
thing is supposed to look like.  That ghost has to be THE SAME FOR EVERYONE:
a hint that depends on which fonts the visitor happens to have installed is
not a hint, it is a lottery, and two contributors would be tracing different
shapes.  So the fonts are vendored.

WHY THIS IS NOT PART OF THE BUILD.  It needs the network, and the fonts it
fetches are third-party releases that change on somebody else's schedule.
Making `make site` depend on that would put a moving part inside a build whose
whole value is that it is byte-reproducible.  These files are committed
assets, like an image: generated once, reviewed, and checked in.

NOTHING IS SUBSETTED.  The point of the ghost is the glyph that is MISSING
from Smalti today, so cutting the hint fonts down to what Smalti already
covers would delete exactly the part that matters.  Every source font is
shipped whole.  (Measured: chunking the Nerd Font by codepoint range made it
BIGGER -- 2.2 MB split against 1.0 MB whole -- because woff2 compresses the
whole glyph set better than its parts.  Do not chunk it.)

The browser still downloads at most one of these files, because
tools/build-site.py gives each one a `unicode-range` covering exactly the
codepoints it owns.

REPRODUCIBILITY.  Every source is pinned to a commit or a release tag below,
and site/hint/SOURCES.json records the SHA-256 of what was downloaded and of
what was written.  `--check` re-downloads and compares without writing, which
is how you find out that an upstream tag has been moved under you.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile

from fontTools.ttLib import TTFont

# Pinned by commit, not by branch: `main` is not a version.  To take a newer
# Noto, move this SHA and re-run -- the manifest diff then shows exactly what
# changed.
NOTO_COMMIT = '3c16704cb6f6e7c02268f7bc0cf86aaee598d16f'
NOTO_RAW = ('https://raw.githubusercontent.com/notofonts/notofonts.github.io/'
            + NOTO_COMMIT)

# The Nerd Fonts icons live in the private-use area, which no Noto font covers
# and no standard ever will -- U+E0A0..U+E0B3 (the Powerline separators) are
# in Smalti's target set today, and the rest of the icon set is where this
# font will grow next.
NERD_TAG = 'v3.5.1'
NERD_ZIP = ('https://github.com/ryanoasis/nerd-fonts/releases/download/'
            + NERD_TAG + '/NerdFontsSymbolsOnly.zip')

# Order matters: build-site.py hands each codepoint to the FIRST font here
# that has it, so the unicode-ranges it writes are disjoint and the browser
# never has two candidates for one character.  Noto Sans Mono leads because a
# monospaced ghost is the honest hint for a monospaced font.
SOURCES = (
    ('NotoSansMono-Regular',
     NOTO_RAW + '/fonts/NotoSansMono/unhinted/ttf/NotoSansMono-Regular.ttf'),
    ('NotoSansSymbols2-Regular',
     NOTO_RAW + '/fonts/NotoSansSymbols2/unhinted/ttf/'
     'NotoSansSymbols2-Regular.ttf'),
    ('NotoSansSymbols-Regular',
     NOTO_RAW + '/fonts/NotoSansSymbols/unhinted/ttf/'
     'NotoSansSymbols-Regular.ttf'),
    ('NotoSansMath-Regular',
     NOTO_RAW + '/fonts/NotoSansMath/unhinted/ttf/NotoSansMath-Regular.ttf'),
    ('SymbolsNerdFont-Regular', NERD_ZIP + '!SymbolsNerdFont-Regular.ttf'),
)

# The OFL text, and where it comes from.  notofonts.github.io's own root
# LICENSE is Apache 2.0 -- that covers the BUILD SCRIPTS in that repository,
# NOT the fonts, which every Noto name table declares to be OFL 1.1.  Shipping
# the Apache text beside an OFL font would be a licence file that says the
# wrong thing, so the text is taken from the upstream font repository instead.
# Verified at the time of pinning: the licence body is byte-identical across
# notofonts/latin-greek-cyrillic, /symbols and /math -- only the copyright
# line above it differs, and those are read from the fonts themselves below.
OFL_COMMIT = '0c7e5ee3312638800f9cc2162cc621a82695d02e'
OFL_URL = ('https://raw.githubusercontent.com/notofonts/latin-greek-cyrillic/'
           + OFL_COMMIT + '/OFL.txt')

NERD_LICENCE = NERD_ZIP + '!LICENSE'

OUT = os.path.join('site', 'hint')
MANIFEST = 'SOURCES.json'


def fetch(url, cache):
    """Download `url` once into `cache`, honouring a `zip!member` suffix."""
    outer, _, member = url.partition('!')
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    blob = os.path.join(cache, key)
    if not os.path.exists(blob):
        print(f'  fetching {outer.rsplit("/", 1)[-1]}')
        try:
            with urllib.request.urlopen(outer, timeout=120) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            # Name the URL.  A bare "404" here means a pinned upstream path
            # moved, and the only useful thing to print is which one.
            raise SystemExit(f'{outer}: HTTP {e.code} {e.reason}')
        with open(blob, 'wb') as fh:
            fh.write(data)
    data = open(blob, 'rb').read()
    if member:
        data = zipfile.ZipFile(io.BytesIO(data)).read(member)
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


stale = []


def write(a, fn, data):
    """Write a vendored file, or under --check prove the committed one matches.

    Both arms go through here so that --check cannot silently cover fewer
    files than a real run writes: adding an output without a comparison is
    then impossible rather than merely discouraged.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    path = os.path.join(a.out, fn)
    if not a.check:
        with open(path, 'wb') as fh:
            fh.write(data)
        return
    if not os.path.exists(path):
        stale.append(f'{fn} is missing')
    elif open(path, 'rb').read() != data:
        stale.append(f'{fn} differs from what the pinned source produces')


def notices(data, name):
    """The copyright and licence a font declares about ITSELF.

    Read out of the shipped file rather than copied from a repository README,
    because those two can disagree and only one of them travels with the
    bytes we serve.
    """
    f = TTFont(io.BytesIO(data), recalcTimestamp=False)
    n = f['name']
    out = (n.getDebugName(0) or '', n.getDebugName(13) or '')
    f.close()
    if 'open font license' not in out[1].lower():
        raise SystemExit(f'{name}: this font does not declare the OFL '
                         f'({out[1]!r}) -- do not ship it under LICENSE-Noto')
    return out


def to_woff2(data, name):
    """Convert a whole TTF to woff2, proving on the way that it IS a font.

    A download that quietly returned an HTML error page is the failure this
    catches: it would otherwise sail through to a committed asset that renders
    nothing, and the site would show an empty ghost with no complaint.
    """
    # recalcTimestamp=False or fontTools stamps head.modified with the clock
    # on save, and two runs of this tool would then produce different bytes --
    # which would make --check useless and, worse, useless SILENTLY, since it
    # would look like a real upstream change.  recalcBBoxes=False so the
    # outlines are passed through rather than recomputed.
    f = TTFont(io.BytesIO(data), recalcTimestamp=False, recalcBBoxes=False)
    cmap = f.getBestCmap()
    if not cmap:
        raise SystemExit(f'{name}: downloaded font has an empty cmap')
    version = f['name'].getDebugName(5) or ''
    f.flavor = 'woff2'
    buf = io.BytesIO()
    f.save(buf)
    f.close()
    return buf.getvalue(), len(cmap), version.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--cache', default=os.path.join(
        os.environ.get('TMPDIR', '/tmp'), 'smalti-hint-cache'))
    ap.add_argument('--check', action='store_true',
                    help='re-derive and compare against the manifest, '
                         'writing nothing')
    a = ap.parse_args()

    os.makedirs(a.cache, exist_ok=True)
    if not a.check:
        os.makedirs(a.out, exist_ok=True)

    manifest = {'notoCommit': NOTO_COMMIT, 'nerdTag': NERD_TAG,
                'oflCommit': OFL_COMMIT, 'fonts': []}
    total = 0
    noto_notices = []
    for name, url in SOURCES:
        src = fetch(url, a.cache)
        if name.startswith('Noto'):
            noto_notices.append((name, notices(src, name)))
        woff2, cps, version = to_woff2(src, name)
        fn = name + '.woff2'
        manifest['fonts'].append({
            'file': fn, 'source': url, 'sourceSha256': sha(src),
            'sha256': sha(woff2), 'codepoints': cps, 'version': version,
            'bytes': len(woff2),
        })
        total += len(woff2)
        print(f'  {fn:32} {cps:6} codepoints  {len(woff2)/1024:7.0f} KiB  '
              f'{version}')
        write(a, fn, woff2)

    ofl = fetch(OFL_URL, a.cache).decode('utf-8')
    if 'SIL OPEN FONT LICENSE Version 1.1' not in ofl:
        raise SystemExit(f'{OFL_URL} is not the OFL 1.1 -- refusing to ship a '
                         f'licence file that does not say what it is')
    # Strip the source repository's own copyright line off the top and put
    # every shipped font's copyright there instead, so the file names exactly
    # what it covers.
    body = ofl[ofl.index('SIL OPEN FONT LICENSE'):]
    head = ['The Noto fonts in this directory are licensed as follows.', '']
    for name, (copyright_, licence) in noto_notices:
        head += [name + '.woff2', '  ' + copyright_, '  ' + licence, '']
    write(a, 'LICENSE-Noto.txt', '\n'.join(head) + '\n' + body)

    nerd = fetch(NERD_LICENCE, a.cache).decode('utf-8')
    if 'MIT License' not in nerd:
        raise SystemExit(f'{NERD_LICENCE} is not the MIT licence -- refusing '
                         f'to ship a licence file that does not say what it '
                         f'is')
    write(a, 'LICENSE-NerdFonts.txt', nerd)

    write(a, MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + '\n')

    if a.check:
        for msg in stale:
            print('  STALE ' + msg, file=sys.stderr)
        if stale:
            print(f'make-hint-fonts: {len(stale)} vendored file(s) do NOT '
                  f'match what the pinned sources produce today',
                  file=sys.stderr)
            return 1
        print(f'make-hint-fonts: all {len(SOURCES) + 3} vendored files match '
              f'the pinned sources')
        return 0
    print(f'{a.out}: {len(SOURCES)} fonts, {total/1024:.0f} KiB total')
    return 0


sys.exit(main())
