#!/usr/bin/env python3
"""Build the specimen site into build/site/ -- see site/ for its sources.

Usage: build-site.py [--out DIR] [--repo OWNER/NAME] [--branch NAME] [SIZE ...]

Three jobs, and every one of them reads the glyph store rather than a list
somebody has to keep up to date:

  * the four .woff2 faces, copied from build/ -- a BROWSER CANNOT RENDER THE
    .otb FILES AT ALL.  They are bitmap-only and no browser draws an embedded
    strike, so the site loads the traced outlines.  Those are pixel-exact at
    integer multiples of the cell height (1x, 2x, 3x) and blurry between.
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

ONE PAGE PER SIZE, each under its own name -- build/site/7x14/, build/site/8x16/
-- with a redirect at the root.  The page is templated per size all the way
down to its title, its cell dimensions and its wordmark, so a single page
carrying every size would have to rewrite all of that on a click and hold two
glyph sets in memory to do it.  A sibling page carries it for free, and the
in-page editor stays honest because a page only ever knows one size.  The
masthead links the siblings.
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

# The editor's ghost fonts, vendored by tools/make-hint-fonts.py.  This build
# never downloads them and never subsets them; all it does is read their cmaps
# so it can hand each codepoint to exactly one of them.
HINT_DIR = os.path.join('site', 'hint')
HINT_MANIFEST = 'SOURCES.json'

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
# another font is a specimen of that font.
#
# THE NUMBER IS A MULTIPLE OF THE CELL HEIGHT, NOT A PIXEL SIZE.  The outline
# reproduces the strike exactly at integer multiples and nowhere else, so the
# ladder is 14/28/42 at 7x14 and 16/32/48 at 8x16.  It was written as literal
# pixels once, and that one hardcoded ladder is what blocked the second size.
ZOOMS = (1, 2, 3)

# The editor's guide lines.  These three are rows of the DRAWING, not of the
# font metrics, so they cannot be derived -- but they were measured across
# upstream's own faces at both cell sizes and are the same row at each: the cap
# line is the top row of A B E H, the x-height line the top row of
# a c e m n o r s u v w x z, and the maths axis the row `-`, `+`, `<` and `>`
# sit on.  The BASELINE is the one that moves (row 10 at 7x14, row 11 at 8x16),
# so it is read out of the built font below instead of being written here --
# it was `var BASE = 10` in site/smalti.js, and the 8x16 editor drew its
# baseline through the middle of the letters.
GUIDE_CAP, GUIDE_XHEIGHT, GUIDE_AXIS = 3, 5, 7
SPECIMEN = (
    (3, 'Smalti — glass tesserae'),
    (2, 'Ĳsselmeer · ΔΣΩ αβγπφψ · ¾ ≈ 0.75 · «wort» · ¶ §'),
    (1, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789'),
    (1, '→ ↔ ⇒ ↵ ∑ ∏ √ ∞ ≠ ≤ ≥ ± × ÷ ● ○ ◆ ★ ✓ ✗ ⠿ ⑂ ❯ ⏺ ‰ ™ ®'),
    (1, 'oetiker@sol  ~/src/smalti  main  make check ✓'),
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

def hint_plan(hint_dir=HINT_DIR):
    """Which vendored ghost font owns which codepoint.

    Returns [(filename, sorted codepoints)] in manifest order, with the sets
    DISJOINT: a codepoint goes to the first font that has it.  Overlapping
    unicode-ranges would leave the browser two candidates for one character
    and the ghost would then depend on rule order rather than on a decision
    made here.

    The cmaps are read out of the .woff2 files that are actually shipped, not
    out of the manifest, so a file swapped without re-running make-hint-fonts
    cannot lie about what it contains.
    """
    from fontTools.ttLib import TTFont

    path = os.path.join(hint_dir, HINT_MANIFEST)
    if not os.path.exists(path):
        raise SystemExit(f'{path} is missing -- run tools/make-hint-fonts.py '
                         f'to vendor the editor\'s ghost fonts')
    manifest = json.load(open(path, encoding='utf-8'))
    plan, taken = [], set()
    for entry in manifest['fonts']:
        fn = entry['file']
        src = os.path.join(hint_dir, fn)
        if not os.path.exists(src):
            raise SystemExit(f'{src} is named in {HINT_MANIFEST} but is not '
                             f'here -- re-run tools/make-hint-fonts.py')
        f = TTFont(src, lazy=True)
        cps = set(f.getBestCmap())
        f.close()
        mine = sorted(cps - taken)
        taken |= cps
        plan.append((fn, mine))
    if not taken:
        raise SystemExit(f'{hint_dir} holds no codepoints at all -- the ghost '
                         f'would be blank for every glyph')
    return plan


def css_ranges(cps):
    """Merge a sorted codepoint list into CSS `unicode-range` syntax."""
    out, i, n = [], 0, len(cps)
    while i < n:
        j = i
        while j + 1 < n and cps[j + 1] == cps[j] + 1:
            j += 1
        out.append(f'U+{cps[i]:X}' if i == j else f'U+{cps[i]:X}-{cps[j]:X}')
        i = j + 1
    return ', '.join(out)


def build_data(size, repo, branch, hinted):
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

    # Which codepoints the editor can show a ghost for.  Recorded rather than
    # guessed at in the browser: the page must be able to SAY that it has no
    # hint for a codepoint instead of drawing the empty box a missing glyph
    # produces, which a contributor would reasonably read as a design.
    hint = ''.join('1' if cp in hinted else '0' for cp in listed)

    for mult, text in SPECIMEN:
        px = mult * h
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
        'hint': hint,
        # `z` is the MULTIPLE and `px` only the label.  site/smalti.js used
        # to build the CSS class as 's' + px, which asked for .s16/.s32/.s48
        # on the 8x16 page while smalti.css only ever defined .s14/.s28/.s42 --
        # so every specimen line silently fell back to the body size.
        'specimen': [{'z': mult, 'px': mult * h, 'text': text}
                     for mult, text in SPECIMEN],
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


def write_root(root, sizes):
    """The site root: a redirect to the first size, and the Pages opt-out.

    The root is not a page of its own.  It forwards to the first size and
    carries the fragment across, so a bookmark of `/#browse` still lands on
    the glyph browser now that the page has moved to `/7x14/#browse`.  The
    no-script body is the real list rather than an apology, because it is also
    what a reader gets if the redirect is ever wrong.
    """
    links = '\n'.join(f'<li><a href="{s}/">Smalti {s}</a></li>' for s in sizes)
    open(os.path.join(root, 'index.html'), 'w', encoding='utf-8').write(
        '<!doctype html>\n'
        '<html lang="en">\n<meta charset="utf-8">\n'
        '<title>Smalti</title>\n'
        f'<link rel="canonical" href="{sizes[0]}/">\n'
        f'<meta http-equiv="refresh" content="0; url={sizes[0]}/">\n'
        f'<script>location.replace("{sizes[0]}/" + location.hash);</script>\n'
        '<h1>Smalti</h1>\n<ul>\n' + links + '\n</ul>\n')

    # Pages serves the upload as a plain directory; without this Jekyll would
    # eat any path starting with an underscore and add a build step nobody
    # asked for.  At the ROOT, because Jekyll is applied to the whole upload.
    open(os.path.join(root, '.nojekyll'), 'w', encoding='utf-8').close()


def build_one(size, out, repo, branch, plan, sizes):
    """Write one size's page into `out`.

    `sizes` is every size this run covers, so the masthead can link to the
    siblings; a run of one size gets no size links, which is what a repository
    with one size should show.
    """
    data, resolved, covered = build_data(
        size, repo, branch, {cp for _fn, cps in plan for cp in cps})
    w, h = data['cell']['w'], data['cell']['h']

    # Read the cmap out of the font that was actually built rather than
    # asserting a number: the page tells a visitor that .notdef is glyph 0 and
    # deliberately unmapped, and that claim has to be true of this build.
    from fontTools.ttLib import TTFont
    ttf = TTFont(os.path.join('build', f'Smalti{size}-Regular.ttf'), lazy=True)
    cmap = len(ttf.getBestCmap())
    # And the BASELINE, in rows, from the same font.  One pixel is upem/cell_h
    # units by construction and check-glyphs.py proves it, so the ascent is a
    # whole number of pixels and the baseline is the row above it.  This was
    # `var BASE = 10` in site/smalti.js -- a 7x14 row -- so the 8x16 editor
    # drew its baseline through the middle of every letter.
    upem = ttf['head'].unitsPerEm
    px_units, rem = divmod(upem, h)
    if rem:
        raise SystemExit(f'{size}: upem {upem} is not a whole number of pixels '
                         f'over {h} rows, so the baseline is not a row')
    ascent_px, rem = divmod(ttf['hhea'].ascent, px_units)
    if rem:
        raise SystemExit(f'{size}: ascent {ttf["hhea"].ascent} is not a whole '
                         f'number of {px_units}-unit pixels')
    ttf.close()

    data['guides'] = {'baseline': ascent_px - 1, 'cap': GUIDE_CAP,
                      'xheight': GUIDE_XHEIGHT, 'axis': GUIDE_AXIS}

    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, 'fonts'), exist_ok=True)
    os.makedirs(os.path.join(out, 'data'), exist_ok=True)
    os.makedirs(os.path.join(out, 'hint'), exist_ok=True)

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

    # ------------------------------------------------------------ size.css --
    #
    # THE SIZE-DEPENDENT HALF OF THE STYLESHEET.  site/smalti.css is copied
    # into every size's page UNCHANGED, so anything in it that knows the cell
    # is right for one size and wrong for every other.  That is not
    # hypothetical: it laid an 8-column editor grid into `repeat(7, ...)`, so
    # the drawing wrapped and no glyph was legible, and it sized every scrap of
    # pixel-font text at a literal 14px on a 16px cell, which is not a whole
    # multiple and therefore blurs -- the one thing this whole site exists to
    # avoid.  Generated for the same reason fonts.css is: what carries the size
    # is generated, and smalti.css does not have to know it.
    #
    # THE LAYOUT MODULE IS THE CELL, which is what smalti.css's own opening
    # comment always claimed.  One unit is the cell WIDTH.  Both drawn sizes
    # are exactly 1:2, so --u2 is the cell HEIGHT, --u4 twice it and --u6 three
    # times it at either size -- which is exactly the 1x/2x/3x ladder the
    # outline is pixel-exact at.  A size that is not 1:2 breaks that identity
    # silently, so it is refused here rather than shipped blurry.
    if h != 2 * w:
        raise SystemExit(
            f'{size}: this stylesheet assumes a 1:2 cell, and {w}x{h} is not '
            f'one.  --u2 would no longer be the cell height, so every pixel '
            f'font size on the page would stop being a whole multiple of it. '
            f'Give size.css its own --u2..--u6 derived from the height before '
            f'adding this size.')
    unit = [1, 2, 3, 4, 6, 8]
    size_css = ['/* generated by tools/build-site.py -- do not edit */',
                ':root {',
                f'  --cell-cols: {w};',
                f'  --cell-rows: {h};'] + \
               [f'  --u{"" if n == 1 else n}: {n * w}px;' for n in unit] + \
               ['  --pix: var(--u4);', '}',
                '@media (max-width: 720px) {',
                '  :root { --pix: var(--u3); }', '}']
    with open(os.path.join(out, 'size.css'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(size_css) + '\n')

    # The ghost fonts.  One family name over several files, each with a
    # unicode-range covering exactly what it owns, so a browser fetches ONE of
    # them -- the Nerd Font alone is a megabyte and must not be pulled down to
    # draw a letter.  `font-display: block` because a ghost that arrives as a
    # different font mid-draw would be worse than one that arrives late, and
    # `swap` is what produces that.
    hint_css = ['/* generated by tools/build-site.py -- do not edit */']
    for fn, cps in plan:
        shutil.copyfile(os.path.join(HINT_DIR, fn),
                        os.path.join(out, 'hint', fn))
        if not cps:
            # Every codepoint it has is already owned by an earlier font.  Ship
            # the file (the licence names it) but do not declare a face with an
            # empty unicode-range, which no browser has a defined behaviour for.
            continue
        hint_css.append('@font-face {\n'
                        '  font-family: SmaltiHint;\n'
                        f'  src: url("hint/{fn}") format("woff2");\n'
                        '  font-weight: 400; font-style: normal;'
                        ' font-display: block;\n'
                        f'  unicode-range: {css_ranges(cps)};\n}}')
    with open(os.path.join(out, 'hint.css'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(hint_css) + '\n')
    for fn in sorted(os.listdir(HINT_DIR)):
        if fn.endswith('.txt') or fn == HINT_MANIFEST:
            shutil.copyfile(os.path.join(HINT_DIR, fn),
                            os.path.join(out, 'hint', fn))

    hand = data['totals'][0]['hand']

    # Links to the other sizes.  Plain size names, never a prettified
    # multiplication sign: ui_chars() checks the TEMPLATE, so a character
    # injected here would never be proved to be in the font.
    nav = '\n    '.join(f'<a class="size" href="../{s}/">{s}</a>'
                        for s in sizes if s != size)

    tmpl = open(os.path.join('site', 'index.html'), encoding='utf-8').read()
    page = (tmpl
            .replace('{{WORDMARK}}', wordmark_svg(resolved, w, h))
            .replace('{{SIZE}}', size)
            .replace('{{GLYPHS}}', str(len(covered)))
            .replace('{{CMAP}}', str(cmap))
            .replace('{{FACES}}', str(len(data['faces'])))
            .replace('{{HAND}}', str(hand))
            .replace('{{CELL_W}}', str(w))
            .replace('{{CELL_H}}', str(h))
            .replace('{{SIZENAV}}', nav)
            # The page names its own ppem ladder in three places.  Derived,
            # never typed: at 8x16 the prose said 14/28/42 while the font
            # rendered 16/32/48, and prose that contradicts the specimen
            # beside it is worse than no prose.
            .replace('{{PX1}}', str(h))
            .replace('{{PX2}}', str(2 * h))
            .replace('{{PX3}}', str(3 * h))
            # A deliberately BAD size, to show what falls between the rungs,
            # and what one rung lands on at a 150% scale factor.
            .replace('{{PX_BLUR}}', str(h + 3))
            .replace('{{PX_DEV}}', str(h * 3 // 2))
            .replace('{{REPO}}', repo or ''))
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)

    listed = len(data['cps'])
    print(f'{out}: {len(covered)} glyphs x {len(data["faces"])} faces, '
          f'{listed} codepoints listed across {len(data["blocks"])} blocks, '
          f'{hand} drawn here')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('size', nargs='*', default=['7x14'])
    ap.add_argument('--out', default=os.path.join('build', 'site'))
    ap.add_argument('--repo', default=None)
    ap.add_argument('--branch', default='main')
    a = ap.parse_args()

    repo = a.repo if a.repo is not None else default_repo()
    if not repo:
        print('build-site: no GitHub repository known, so the "open a pull '
              'request" links are disabled.  Pass --repo owner/name.',
              file=sys.stderr)

    sizes = a.size or ['7x14']
    if len(set(sizes)) != len(sizes):
        raise SystemExit(f'a size is named twice: {sizes}')

    # Read once and handed to every size: the ghost fonts are vendored per
    # repository, not per size, and re-reading their cmaps per size would be
    # the same work done twice.
    plan = hint_plan()

    root = a.out
    shutil.rmtree(root, ignore_errors=True)
    for size in sizes:
        build_one(size, os.path.join(root, size), repo, a.branch, plan, sizes)
    write_root(root, sizes)
    print(f'{root}: {len(sizes)} size(s) -- {", ".join(sizes)}; '
          f'the root redirects to {sizes[0]}')


main()
