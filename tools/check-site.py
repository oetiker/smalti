#!/usr/bin/env python3
"""Prove the built site tells the truth about the repository.

Usage: check-site.py [--site DIR] [SIZE]

The site ships a copy of every drawing so that a visitor can edit one without
cloning anything.  A copy can go stale, and a stale copy here is worse than no
site at all: it would put a wrong file on a contributor's clipboard and turn
their first pull request into a spurious diff.  So every claim the site makes
is re-derived from the glyph store and compared:

  1. the codepoints it lists, and which of them it says are covered
  2. every glyph's bitmap, in every face, against glyphstore.resolve()
  3. every glyph's provenance layer, against the same
  4. THE EDITOR'S OUTPUT.  The exact bytes the page puts on the clipboard,
     for every glyph in every face -- against the committed .txt file where
     one exists, and against what glyphstore.write_glyph would produce where
     one does not.  Both are then read back with the real parser, so a file
     made on the site is known to survive `make check`.
  5. the four .woff2 faces, byte for byte against build/
  6. that no template placeholder survived into index.html

The decode here is written out again rather than imported from build-site.py
on purpose: a check that shares its arithmetic with the thing it checks can
only ever prove that the code is self-consistent.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

LAYER_CHAR = {'hand': 'h', 'upstream': 'u', 'gen': 'g'}

fails = []


def bad(msg):
    fails.append(msg)
    if len(fails) <= 20:
        print('  FAIL ' + msg)


def decode(bits, k, w, h):
    """Two hex digits per row, most significant bit in column 0."""
    out = []
    for y in range(h):
        v = int(bits[(k * h + y) * 2:(k * h + y) * 2 + 2], 16)
        out.append(''.join('#' if v >> (w - 1 - x) & 1 else '.'
                           for x in range(w)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('size', nargs='?', default='7x14')
    ap.add_argument('--site', default=os.path.join('build', 'site'))
    a = ap.parse_args()
    size, site = a.size, a.site

    with open(os.path.join(site, 'data', 'glyphs.json'), encoding='utf-8') as fh:
        d = json.load(fh)
    w, h = d['cell']['w'], d['cell']['h']
    if (w, h) != gs.cell(size):
        bad(f'cell {w}x{h} in the data, {gs.cell(size)} in the repository')

    resolved = {f: gs.resolve(size, f) for f in gs.FACES}
    covered = sorted(resolved['regular'])

    if d['faces'] != list(gs.FACES):
        bad(f'faces {d["faces"]} != {list(gs.FACES)}')

    # 1 -- the listed set, and which of it is covered
    listed = d['cps']
    if listed != sorted(listed):
        bad('the listed codepoints are not in ascending order, so the site '
            'and the bitmaps disagree about which glyph is which')
    if len(listed) != len(set(listed)):
        bad('a codepoint is listed twice')
    if len(d['state']) != len(listed) or len(d['textok']) != len(listed):
        bad('state/textok are not one character per listed codepoint')
    said = [cp for cp, s in zip(listed, d['state']) if s == '#']
    if said != covered:
        miss = set(covered) - set(said)
        extra = set(said) - set(covered)
        bad(f'the site says {len(said)} glyphs are covered, the store resolves '
            f'{len(covered)}; missing {sorted(miss)[:6]} extra {sorted(extra)[:6]}')

    # blocks must partition the listed set exactly, or the browser shows a
    # glyph under the wrong Unicode block heading.
    at = 0
    for b in d['blocks']:
        if b['to'] > b['from']:
            if b['from'] != at:
                bad(f'block {b["name"]} starts at {b["from"]}, expected {at}')
            for i in range(b['from'], b['to']):
                if not b['start'] <= listed[i] <= b['end']:
                    bad(f'U+{listed[i]:04X} filed under {b["name"]}')
                    break
            at = b['to']
    if at != len(listed):
        bad(f'the blocks cover {at} of {len(listed)} listed codepoints')

    # 2, 3, 4 -- every glyph, every face
    tmp = tempfile.mkdtemp(prefix='smalti-check-')
    scratch = os.path.join(tmp, '0041.txt')
    idx = {cp: i for i, cp in enumerate(listed)}
    n_file = n_committed = n_blank = 0

    for face in gs.FACES:
        bits, layers = d['bits'][face], d['layers'][face]
        if len(bits) != len(covered) * h * 2:
            bad(f'{face}: bits is {len(bits)} chars, expected '
                f'{len(covered) * h * 2}')
            continue
        if len(layers) != len(covered):
            bad(f'{face}: layers is {len(layers)} chars, expected {len(covered)}')
            continue
        for k, cp in enumerate(covered):
            i = idx[cp]
            layer, bm = resolved[face][cp]
            rows_repo = gs.art(bm, w)
            rows_site = decode(bits, k, w, h)
            if rows_site != rows_repo:
                bad(f'{face} U+{cp:04X}: the site ships a different drawing')
                continue
            if layers[k] != LAYER_CHAR[layer]:
                bad(f'{face} U+{cp:04X}: site says layer {layers[k]!r}, '
                    f'store says {LAYER_CHAR[layer]!r}')
            if d['headers'][i] != gs.header(cp):
                bad(f'U+{cp:04X}: header {d["headers"][i]!r} != '
                    f'{gs.header(cp)!r}')
                continue

            # What the editor puts on the clipboard, built the way smalti.js
            # builds it: the shipped header line, the rows, one newline each.
            text = (d['headers'][i] + '\n' + '\n'.join(rows_site) + '\n')
            emitted = text.encode('utf-8')
            n_file += 1

            path = os.path.join(gs.hand_dir(size, face), gs.filename(cp))
            if os.path.exists(path):
                with open(path, 'rb') as fh:
                    want = fh.read()
                n_committed += 1
                if emitted != want:
                    bad(f'{face} U+{cp:04X}: the editor would emit bytes that '
                        f'differ from the committed {path}')
                    continue
            else:
                gs.write_glyph(scratch, cp, rows_site)
                with open(scratch, 'rb') as fh:
                    want = fh.read()
                if emitted != want:
                    bad(f'{face} U+{cp:04X}: the editor would emit bytes that '
                        f'differ from what write_glyph produces')
                    continue
            # Whatever the site emits must survive the real parser, or a
            # contributor's first pull request fails CI.
            with open(scratch, 'wb') as fh:
                fh.write(emitted)
            try:
                if gs.read_glyph(scratch, w, h) != rows_repo:
                    bad(f'{face} U+{cp:04X}: emitted file parses to a '
                        f'different drawing')
            except gs.GlyphError as e:
                bad(f'{face} U+{cp:04X}: emitted file is rejected: {e}')

    # A brand-new drawing: the editor starts an uncovered codepoint from an
    # empty grid, and that file has to parse too.
    blank = ['.' * w] * h
    for i, cp in enumerate(listed):
        if d['state'][i] != '.':
            continue
        n_blank += 1
        text = (d['headers'][i] + '\n' + '\n'.join(blank) + '\n')
        gs.write_glyph(scratch, cp, blank)
        with open(scratch, 'rb') as fh:
            if fh.read() != text.encode('utf-8'):
                bad(f'U+{cp:04X}: a new empty drawing would not match '
                    f'write_glyph')
                continue
        try:
            if gs.read_glyph(scratch, w, h) != blank:
                bad(f'U+{cp:04X}: a new empty drawing does not parse back')
        except gs.GlyphError as e:
            bad(f'U+{cp:04X}: a new empty drawing is rejected: {e}')

    os.remove(scratch)
    os.rmdir(tmp)

    # 5 -- the fonts.  A browser cannot render the .otb files at all, so if
    # these are wrong or missing the page shows a fallback font and every
    # claim above becomes decoration.
    fcss = os.path.join(site, 'fonts.css')
    css = open(fcss, encoding='utf-8').read() if os.path.exists(fcss) else ''
    if not css:
        bad('fonts.css is missing, so the page has no @font-face rule at all '
            'and would render in a fallback font')
    for face, name in d['faceFile'].items():
        if css.count(f'fonts/{name}') != 1:
            bad(f'fonts.css does not reference fonts/{name} exactly once')
        here = os.path.join(site, 'fonts', name)
        there = os.path.join('build', name)
        if not os.path.exists(here):
            bad(f'{here} is missing')
        elif not os.path.exists(there):
            bad(f'{there} is missing -- run `make woff2`')
        elif open(here, 'rb').read() != open(there, 'rb').read():
            bad(f'{here} differs from {there}')

    # 6 -- nothing left unsubstituted, and the specimen really is this font
    page = open(os.path.join(site, 'index.html'), encoding='utf-8').read()
    if '{{' in page:
        bad('index.html still holds a template placeholder: ' +
            page[page.index('{{'):page.index('{{') + 40])
    for s in d['specimen']:
        for ch in s['text']:
            if ord(ch) not in resolved['regular']:
                bad(f'the {s["px"]}px specimen uses U+{ord(ch):04X}, which the '
                    f'font does not have')

    print(f'check-site: {len(listed)} codepoints listed, {len(covered)} glyphs '
          f'x {len(gs.FACES)} faces')
    print(f'check-site: {n_file} editor outputs checked, of which '
          f'{n_committed} against a committed .txt file byte for byte')
    print(f'check-site: {n_blank} not-yet-drawn codepoints start from a blank '
          f'grid that parses')
    if fails:
        if len(fails) > 20:
            print(f'  ... and {len(fails) - 20} more')
        print(f'check-site: {len(fails)} FAILURES')
        sys.exit(1)
    print('check-site: ok')


main()
