#!/usr/bin/env python3
"""Build the specimen site into build/site/ -- see site/ for its sources.

Usage: build-site.py [--out DIR] [--repo OWNER/NAME] [--branch NAME] [SIZE]

Three jobs, and every one of them reads the glyph store rather than a list
somebody has to keep up to date:

  * the four .woff2 faces, copied from build/ -- a BROWSER CANNOT RENDER THE
    .otb FILES AT ALL.  They are bitmap-only and no browser draws an embedded
    strike, so the site loads the traced outlines.  Those are pixel-exact at
    integer multiples of the cell height (14, 28, 42 px) and blurry between.
  * data/glyphs.json -- every glyph's art, its provenance layer and the exact
    header line its .txt file carries, so the in-page editor can emit a file
    that is byte-identical to the committed one.
  * the coverage model, computed from glyphstore.resolve() -- the same call
    `make index` makes for docs/coverage.md, so the site and the table can
    never disagree.

RAGGED COVERAGE IS THE POINT (design spec section 7).  The site therefore
lists the codepoints the font does NOT have, next to the ones it does, in
every block it touches -- and separates the ones left undrawn BY RULE from the
ones nobody has got to yet.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

from fontTools.unicodedata import Blocks

# The site's own sources, listed rather than globbed: a file that is not named
# here does not reach the site, which is the same rule the rest of the build
# follows for generated output.
ASSETS = ('smalti.css', 'smalti.js')

FACE_FILE = {'regular': 'Regular', 'bold': 'Bold',
             'italic': 'Italic', 'bold-italic': 'BoldItalic'}

FACE_LABEL = {'regular': 'Regular', 'bold': 'Bold',
              'italic': 'Oblique', 'bold-italic': 'Bold Oblique'}

LAYER_CHAR = {'hand': 'h', 'upstream': 'u', 'gen': 'g'}

# The wordmark in the hero is laid out of the font's own pixels, so it changes
# when the drawings change.  Set from Basic Latin, which upstream drew.
WORDMARK = 'smalti'

# The specimen copy.  Every codepoint in it is checked against the resolved
# face before the page is written, because a specimen that falls back to
# another font is a specimen of that font.  Only 14, 28 and 42 px: the outline
# reproduces the strike exactly at integer multiples of the cell height and
# nowhere else.
SPECIMEN = (
    (42, 'Smalti — glass tesserae'),
    (28, 'Ĳsselmeer · ΔΣΩ αβγπφψ · ¾ ≈ 0.75 · «wort» · ¶ §'),
    (14, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789'),
    (14, '→ ↔ ⇒ ↵ ∑ ∏ √ ∞ ≠ ≤ ≥ ± × ÷ ● ○ ◆ ★ ✓ ✗ ⠿ ⑂ ❯ ⏺ ‰ ™ ®'),
    (14, 'oetiker@sol  ~/src/smalti  main  make check ✓'),
)


def ui_chars():
    """Every non-ASCII character the page itself can put on screen.

    The chrome -- nav, labels, buttons, tooltips -- is set in Smalti too, so a
    character the font lacks would quietly pull in a fallback and the page
    would stop being a specimen of this font.  Read out of the sources rather
    than kept as a list, because a list is a second thing to remember.
    """
    import html
    out = set()
    for name in ('index.html',) + ASSETS:
        text = open(os.path.join('site', name), encoding='utf-8').read()
        if name.endswith('.html'):
            text = html.unescape(text)
        out |= {c for c in text if ord(c) > 127}
    return sorted(out)


# --------------------------------------------------------------- unicode --

def bmp_blocks():
    """(start, end, name) for every Unicode block that reaches into the BMP.

    fontTools carries the block table; unicodedata does not expose one.  Only
    the BMP, because nothing this font could plausibly cover lives above it and
    a list of 397 blocks is noise, not honesty.
    """
    out = []
    for i, start in enumerate(Blocks.RANGES):
        end = Blocks.RANGES[i + 1] - 1 if i + 1 < len(Blocks.RANGES) else 0x10FFFF
        if start <= 0xFFFF:
            out.append((start, min(end, 0xFFFF), Blocks.VALUES[i]))
    return out


def undrawn_by_rule(cp):
    """True when a terminal would never ask this font for this codepoint.

    east_asian_width 'W' means the terminal gives the character two cells and
    takes it from the emoji font, so a 7x14 bitmap for it would be both unused
    and the wrong width.  That is why fifteen Dingbats are missing, and it is a
    decision, not a gap.
    """
    return unicodedata.east_asian_width(chr(cp)) == 'W'


def in_target(cp):
    """True when a missing glyph here would be a real hole.

    Excluded: unassigned and surrogate codepoints, because there is nothing to
    draw; controls and private use, because what belongs there is a judgement
    this font makes one codepoint at a time (upstream parks VT100 line drawing
    in fifteen control slots, and glyphs/7x14 draws seven Powerline symbols and
    deliberately no more).  Those show up as `extra` instead, counted but never
    counted against.
    """
    if unicodedata.category(chr(cp)) in ('Cn', 'Cs', 'Co', 'Cc'):
        return False
    return not undrawn_by_rule(cp)


# ------------------------------------------------------------------ data --

def build_data(size, repo, branch):
    w, h = gs.cell(size)
    faces = list(gs.FACES)
    resolved = {f: gs.resolve(size, f) for f in faces}

    covered = sorted(resolved[faces[0]])
    for f in faces[1:]:
        if sorted(resolved[f]) != covered:
            raise SystemExit(f'{f} covers a different set of codepoints than '
                             f'{faces[0]} -- the site assumes one inventory '
                             f'per size, and `make check` assumes it too')
    cov = set(covered)

    # Which blocks the font touches at all.  A block with no coverage is still
    # reported (that is the recruiting poster), but only the touched ones get a
    # per-codepoint strip and a place in the glyph browser.
    blocks, listed = [], []
    for start, end, name in bmp_blocks():
        rng = range(start, end + 1)
        n_cov = n_target = n_rule = 0
        cps_here = []
        for cp in rng:
            hit, tgt, rule = cp in cov, in_target(cp), undrawn_by_rule(cp)
            n_cov += hit
            n_target += tgt
            n_rule += rule and unicodedata.category(chr(cp)) != 'Cn'
            if hit or tgt or (rule and unicodedata.category(chr(cp)) != 'Cn'):
                cps_here.append(cp)
        if not n_cov and not n_target:
            continue
        b = {'name': name, 'start': start, 'end': end,
             'covered': sum(1 for cp in cps_here if cp in cov and in_target(cp)),
             'target': n_target,
             'extra': sum(1 for cp in cps_here if cp in cov and not in_target(cp)),
             'byRule': n_rule, 'from': len(listed), 'to': len(listed)}
        if n_cov:
            b['to'] = len(listed) + len(cps_here)
            listed.extend(cps_here)
        blocks.append(b)

    # `state` is one character per listed codepoint and says only what the
    # coverage view is about: is it there, is it missing, or was it left out on
    # purpose.  Provenance is a separate variable and gets its own colours.
    state = ''.join('#' if cp in cov else ('w' if undrawn_by_rule(cp) else '.')
                    for cp in listed)

    # A browser will not draw a control code, a format character or a surrogate
    # as text however good the font is, so those tiles fall back to a picture
    # of the drawing.  Upstream parks fifteen VT100 line-drawing glyphs in
    # control slots, so this is not a hypothetical case.
    textok = ''.join('0' if unicodedata.category(chr(cp))
                     in ('Cc', 'Cf', 'Cs', 'Zl', 'Zp') else '1'
                     for cp in listed)

    for px, text in SPECIMEN:
        for ch in text:
            if ord(ch) not in cov:
                raise SystemExit(
                    f'the {px}px specimen line uses U+{ord(ch):04X} '
                    f'{gs.unicode_name(ord(ch))}, which this font does not '
                    f'have -- the browser would substitute another font and '
                    f'the specimen would be a specimen of that one')
    for ch in ui_chars():
        if ord(ch) not in cov:
            raise SystemExit(
                f'the page sets U+{ord(ch):04X} {ch!r} '
                f'{gs.unicode_name(ord(ch))} in its own chrome and this font '
                f'does not have it -- use a character it does have')

    bits, layers = {}, {}
    for f in faces:
        r = resolved[f]
        bits[f] = ''.join(
            ''.join(f'{sum(1 << (w - 1 - i) for i, c in enumerate(row) if c == "#"):02X}'
                    for row in gs.art(r[cp][1], w))
            for cp in covered)
        layers[f] = ''.join(LAYER_CHAR[r[cp][0]] for cp in covered)

    totals = []
    for f in faces:
        c = {'hand': 0, 'upstream': 0, 'gen': 0}
        for layer, _bm in resolved[f].values():
            c[layer] += 1
        totals.append({'face': f, 'label': FACE_LABEL[f], 'total': len(resolved[f]),
                       'hand': c['hand'], 'upstream': c['upstream'],
                       'gen': c['gen']})

    return {
        'size': size, 'cell': {'w': w, 'h': h},
        'repo': repo, 'branch': branch,
        'faces': faces,
        'faceLabel': {f: FACE_LABEL[f] for f in faces},
        'faceFile': {f: f'Smalti{size}-{FACE_FILE[f]}.woff2' for f in faces},
        'cps': listed,
        'headers': [gs.header(cp) for cp in listed],
        'state': state,
        'textok': textok,
        'specimen': [{'px': px, 'text': text} for px, text in SPECIMEN],
        'bits': bits, 'layers': layers,
        'blocks': blocks, 'totals': totals,
    }, resolved, covered


# --------------------------------------------------------------- wordmark --

def wordmark_svg(resolved, w, h, text=WORDMARK):
    """The hero, laid out of the font's own pixels, one tessera per pixel.

    Smalti are the glass tiles a mosaic is made from and a pixel is one, so the
    wordmark is set as tiles with grout between them rather than as type.  The
    facet highlight and the per-tile lightness are deterministic in (x, y):
    the page must look the same on every load, and identical tiles would look
    like a screen rather than like glass.
    """
    art = {cp: gs.art(bm, w) for cp, (_l, bm) in resolved['regular'].items()}
    cols = len(text) * w
    parts = [f'<svg class="wordmark" viewBox="0 0 {cols} {h}" '
             f'role="img" aria-label="{text}" shape-rendering="crispEdges" '
             f'preserveAspectRatio="xMinYMid meet">']
    for i, ch in enumerate(text):
        rows = art[ord(ch)]
        for y, row in enumerate(rows):
            for x, px in enumerate(row):
                if px != '#':
                    continue
                gx = i * w + x
                # A stable hash of the tile's position, so the mosaic is the
                # same mosaic every time it is drawn.
                n = (gx * 37 + y * 101) % 7
                parts.append(
                    f'<rect class="t t{n}" x="{gx}.06" y="{y}.06" '
                    f'width="0.88" height="0.88"/>')
                parts.append(
                    f'<rect class="f" x="{gx}.06" y="{y}.06" '
                    f'width="0.88" height="0.30"/>')
    parts.append('</svg>')
    return ''.join(parts)


# ------------------------------------------------------------------ main --

def default_repo():
    """owner/name from the git remote, so a fork's links point at the fork."""
    try:
        url = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
                             capture_output=True, text=True, check=True,
                             cwd=gs.ROOT).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ''
    url = url.removesuffix('.git')
    for sep in ('github.com:', 'github.com/'):
        if sep in url:
            return url.split(sep, 1)[1]
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('size', nargs='?', default='7x14')
    ap.add_argument('--out', default=os.path.join('build', 'site'))
    ap.add_argument('--repo', default=None)
    ap.add_argument('--branch', default='main')
    a = ap.parse_args()

    repo = a.repo if a.repo is not None else default_repo()
    if not repo:
        print('build-site: no GitHub repository known, so the "open a pull '
              'request" links are disabled.  Pass --repo owner/name.',
              file=sys.stderr)

    data, resolved, covered = build_data(a.size, repo, a.branch)
    w, h = data['cell']['w'], data['cell']['h']

    out = a.out
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, 'fonts'), exist_ok=True)
    os.makedirs(os.path.join(out, 'data'), exist_ok=True)

    for face, name in data['faceFile'].items():
        src = os.path.join('build', name)
        if not os.path.exists(src):
            raise SystemExit(f'{src} is missing -- run `make woff2` first')
        shutil.copyfile(src, os.path.join(out, 'fonts', name))

    # sort_keys and a fixed separator so two builds of the same sources give
    # the same bytes; C's release path cares and so does a Pages diff.
    with open(os.path.join(out, 'data', 'glyphs.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(data, fh, separators=(',', ':'), sort_keys=True)

    for name in ASSETS:
        shutil.copyfile(os.path.join('site', name), os.path.join(out, name))

    # The @font-face rules are generated rather than written by hand, because
    # the filenames carry the cell size and site/smalti.css must not have to
    # know it.  `font-display: block` so the page never flashes a fallback
    # font: a fallback here would misrepresent the thing being specimened.
    css = ['/* generated by tools/build-site.py -- do not edit */']
    for face in data['faces']:
        css.append('@font-face {\n'
                   '  font-family: SmaltiSite;\n'
                   f'  src: url("fonts/{data["faceFile"][face]}") '
                   'format("woff2");\n'
                   f'  font-weight: {700 if face.startswith("bold") else 400};'
                   f' font-style: {"oblique" if "italic" in face else "normal"};'
                   ' font-display: block;\n}')
    with open(os.path.join(out, 'fonts.css'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(css) + '\n')

    # Read the cmap out of the font that was actually built rather than
    # asserting a number: the page tells a visitor that .notdef is glyph 0 and
    # deliberately unmapped, and that claim has to be true of this build.
    from fontTools.ttLib import TTFont
    ttf = TTFont(os.path.join('build', f'Smalti{a.size}-Regular.ttf'),
                 lazy=True)
    cmap = len(ttf.getBestCmap())
    ttf.close()

    hand = data['totals'][0]['hand']
    tmpl = open(os.path.join('site', 'index.html'), encoding='utf-8').read()
    page = (tmpl
            .replace('{{WORDMARK}}', wordmark_svg(resolved, w, h))
            .replace('{{SIZE}}', a.size)
            .replace('{{GLYPHS}}', str(len(covered)))
            .replace('{{CMAP}}', str(cmap))
            .replace('{{FACES}}', str(len(data['faces'])))
            .replace('{{HAND}}', str(hand))
            .replace('{{CELL_W}}', str(w))
            .replace('{{CELL_H}}', str(h))
            .replace('{{REPO}}', repo or ''))
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)

    # Pages serves this as a plain directory; without it Jekyll would eat any
    # path starting with an underscore and add a build step nobody asked for.
    open(os.path.join(out, '.nojekyll'), 'w', encoding='utf-8').close()

    listed = len(data['cps'])
    print(f'{out}: {len(covered)} glyphs x {len(data["faces"])} faces, '
          f'{listed} codepoints listed across {len(data["blocks"])} blocks, '
          f'{hand} drawn here')


main()
