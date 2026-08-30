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
  7. the editor's ghost fonts: that every codepoint the page offers a
     reference glyph for is really in a shipped hint font, AND that every one
     it refuses is really absent from all of them

The decode here is written out again rather than imported from build-site.py
on purpose: a check that shares its arithmetic with the thing it checks can
only ever prove that the code is self-consistent.
"""
import argparse
import json
import os
import re
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


def parse_ranges(css):
    """Every codepoint a `unicode-range:` declaration covers, per @font-face.

    Parsed out of the served CSS rather than recomputed from the fonts,
    because the CSS is what the browser obeys.  A range the fonts justify but
    the CSS does not declare is still a glyph the visitor never sees.
    """
    out = []
    for block in css.split('@font-face')[1:]:
        m = re.search(r'url\("hint/([^"]+)"\)', block)
        r = re.search(r'unicode-range:\s*([^;]+);', block)
        if not m or not r:
            continue
        cps = set()
        for part in r.group(1).split(','):
            part = part.strip()
            lo, _, hi = part[2:].partition('-')
            cps.update(range(int(lo, 16), int(hi or lo, 16) + 1))
        out.append((m.group(1), cps))
    return out


def check_hint(site, d):
    """Leg 7: the ghost fonts say what the data claims they say."""
    from fontTools.ttLib import TTFont

    css_path = os.path.join(site, 'hint.css')
    if not os.path.exists(css_path):
        bad('hint.css is missing, so the editor has no ghost font at all')
        return 0
    declared = parse_ranges(open(css_path, encoding='utf-8').read())
    if not declared:
        bad('hint.css declares no @font-face with a unicode-range, so nothing '
            'the data marks as hintable could actually be drawn')
        return 0

    have = set()
    for fn, css_cps in declared:
        path = os.path.join(site, 'hint', fn)
        if not os.path.exists(path):
            bad(f'hint.css names hint/{fn}, which is not in the site')
            continue
        f = TTFont(path, lazy=True)
        real = set(f.getBestCmap())
        f.close()
        if css_cps - real:
            miss = sorted(css_cps - real)[:3]
            bad(f'hint/{fn} is declared for {len(css_cps - real)} codepoints '
                f'it does not contain, e.g. ' +
                ', '.join(f'U+{c:04X}' for c in miss))
        if css_cps & have:
            bad(f'hint/{fn} overlaps an earlier font on '
                f'{len(css_cps & have)} codepoints, so which one draws the '
                f'ghost depends on CSS rule order')
        have |= css_cps

    flags = d.get('hint', '')
    if len(flags) != len(d['cps']):
        bad(f'the hint flags cover {len(flags)} codepoints, the site lists '
            f'{len(d["cps"])}')
        return 0
    # BOTH directions.  Checking only that a "1" is real would pass a file of
    # nothing but zeroes, which is exactly the shape of a check that has
    # quietly stopped checking.
    claimed = {cp for cp, b in zip(d['cps'], flags) if b == '1'}
    denied = {cp for cp, b in zip(d['cps'], flags) if b == '0'}
    for cp in sorted(claimed - have)[:3]:
        bad(f'the site says U+{cp:04X} has a ghost, but no shipped hint font '
            f'declares it')
    for cp in sorted(denied & have)[:3]:
        bad(f'the site says U+{cp:04X} has no ghost, but hint.css declares it '
            f'-- the editor would refuse to show a reference it has')
    if not claimed:
        bad('not one listed codepoint is marked as hintable, so the ghost is '
            'dead for the whole font')
    return len(claimed)


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

    # 6b -- THE CELL THE STYLESHEET BELIEVES IN.
    #
    # site/smalti.css is copied into every size's page unchanged, so every
    # number in it that knows the cell has to come from size.css instead.  When
    # it did not, the 8x16 page laid an eight-column editor into a seven-column
    # grid and set every specimen line at 14px on a 16px cell -- both silent,
    # both visible only to someone who opened the page and looked.  A page that
    # renders wrong while every other check is green is exactly what this
    # section exists to stop.
    scss = os.path.join(site, 'size.css')
    css2 = open(scss, encoding='utf-8').read() if os.path.exists(scss) else ''
    if not css2:
        bad('size.css is missing, so the page has no cell geometry at all and '
            'falls back to whatever smalti.css happens to hardcode')
    else:
        for prop, want in (('--cell-cols', w), ('--cell-rows', h)):
            if f'{prop}: {want};' not in css2:
                bad(f'size.css does not declare {prop}: {want} for {size}')
        if f'--u2: {h}px;' not in css2:
            bad(f'size.css does not set --u2 to the cell height {h}px, so '
                f'every pixel-font size on the page is not a whole multiple '
                f'of the cell and the text renders blurred')

    page_css = open(os.path.join(site, 'smalti.css'), encoding='utf-8').read()
    if 'repeat(var(--cell-cols)' not in page_css:
        bad('smalti.css does not take the editor grid column count from '
            '--cell-cols, so the paint grid is only correct at one cell width')

    # Every specimen line asks for a class by its zoom index; smalti.js builds
    # it as 's' + z.  A class that does not exist is not an error in any
    # browser -- the line just silently renders at the body size, which is how
    # this shipped.
    for spec in d['specimen']:
        if f'.s{spec["z"]} ' not in page_css:
            bad(f'the {spec["px"]}px specimen line uses class .s{spec["z"]}, '
                f'which smalti.css does not define -- it would render at the '
                f'body size instead')
        if spec['px'] != spec['z'] * h:
            bad(f'specimen line claims {spec["px"]}px at zoom {spec["z"]} on a '
                f'{h}-row cell')

    # The guide rows the editor draws.  The baseline is the one that moves
    # between sizes, so an unchecked constant here is invisible until someone
    # looks at the 8x16 editor.
    g = d.get('guides') or {}
    if not g:
        bad('the data carries no guide rows, so the editor would draw its '
            'baseline from a constant')
    else:
        if not 0 < g['cap'] < g['xheight'] < g['baseline'] < h:
            bad(f'guide rows out of order or off the cell: {g} on {h} rows')
        # Re-derived independently of build-site.py, from the strike this
        # build actually produced: the baseline is the last row of the ascent.
        bdf = os.path.join('build', f'Smalti{size}-Regular.bdf')
        m = re.search(r'^FONT_ASCENT (\d+)', open(bdf, encoding='latin-1').read(),
                      re.M) if os.path.exists(bdf) else None
        if m is None:
            bad(f'{bdf} has no FONT_ASCENT, so the baseline cannot be checked')
        elif g['baseline'] != int(m.group(1)) - 1:
            bad(f'the page draws its baseline on row {g["baseline"]}, but '
                f'{bdf} says FONT_ASCENT {m.group(1)}, so it is row '
                f'{int(m.group(1)) - 1}')

    # 7 -- the editor's ghost fonts.  The page tells a contributor either
    # "here is what this character looks like" or "there is no reference for
    # this one", and both claims have to be true of the files it ships: the
    # first would otherwise draw an empty box that reads as a design decision,
    # and the second would hide a hint that is right there.
    n_hint = check_hint(site, d)

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
    print(f'check-site: {n_hint} of {len(listed)} listed codepoints have a '
          f'ghost in the vendored hint fonts')
    if fails:
        if len(fails) > 20:
            print(f'  ... and {len(fails) - 20} more')
        print(f'check-site: {len(fails)} FAILURES')
        sys.exit(1)
    print('check-site: ok')


main()
