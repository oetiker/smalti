#!/usr/bin/env python3
"""Build build/compare/index.html: 7x14 next to 8x16, glyph by glyph.

`make compare` is not a check -- `make check` proves things, this shows them.
It is the instrument the project owner rules 8x16's 329 hand drawings with,
one Unicode-block batch at a time (design doc section 6, section 7 for the
batch order), so it must never lie about what is drawn and never fall back to
a font Smalti does not ship.

Usage: build-compare.py [--out DIR]
"""
import argparse
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

# Hand drawings are regular-face only (design doc section 3.3): bold derives
# through embolden.py, the obliques through the shear, so there is nothing to
# judge in those faces yet.
FACE = 'regular'
SIZE_SMALL, SIZE_LARGE = '7x14', '8x16'

# The 20 Latin Extended-A letters gen-latin-ext-a.py's H() draws as literal
# 7x14 art are a no-op at 8x16, so they are silently ABSENT from that face
# (Ruling R13, .superpowers/sdd/2026-08-25-8x16/progress.md:556).  They are
# 'gen' layer at 7x14, not 'hand', so no directory listing finds them; the
# fixed list is the only place they can come from.
H_LETTERS = 'Đ đ Ħ ħ ı Ł ł Ŋ ŋ Œ œ Ŧ ŧ ſ Ŀ ŀ ĸ Ĳ ĳ ŉ'.split()
H_LABEL = 'H() letterforms -- Latin Extended-A (Ruling R13)'

# Batch order from design doc section 7, largest block first: each entry
# matches a Unicode-block byte prefix against the 309 hand-drawn 7x14
# codepoints the design doc's batch table was built from.  Task 10x added
# two more (U+26C1, U+26F6) outside that 329-tile target set -- they fall
# into the MISC_LABEL catch-all below, so the 309 total below is now 311.
# codepoints.  Labels quote the design doc's own wording so the chart and the
# plan never disagree.  Anything left over after these seven falls into the
# eighth, catch-all batch below; the ninth batch is the fixed H() list.
GROUPS = (
    ('27xx dingbats and arrows',    {0x27}),
    ('03xx Greek',                  {0x03}),
    ('21xx arrows, letterlike',     {0x21}),
    ('25xx box drawing, shapes',    {0x25}),
    ('22xx math',                   {0x22}),
    ('20xx punctuation',            {0x20}),
    ('00xx Latin-1',                {0x00}),
)
MISC_LABEL = 'Powerline, technical, misc'


def hand_codepoints(size, face):
    """Codepoints with an actual file in glyphs/<size>/<face>/.

    Deliberately a directory listing, not resolve(): resolve() also reports
    upstream and generated glyphs, and the per-block "drawn" count this chart
    shows is a promise about what has been HAND-DRAWN, nothing else.
    """
    d = gs.hand_dir(size, face)
    if not os.path.isdir(d):
        return set()
    out = set()
    for name in os.listdir(d):
        cp = gs.cp_of(name)
        if cp is not None:
            out.add(cp)
    return out


def target_groups():
    """[(label, [codepoints...])] in batch order -- the union target set.

    This is every codepoint 8x16 still needs a hand drawing for: the 311
    glyphs already hand-drawn at 7x14 (the pattern to draw against), plus the
    20 H() letters that parity requires but have no 7x14 hand file to read
    the set from.
    """
    hand7 = sorted(hand_codepoints(SIZE_SMALL, FACE))
    if len(hand7) != 311:
        raise SystemExit(
            f'glyphs/{SIZE_SMALL}/{FACE}/ holds {len(hand7)} drawings, not '
            f'the 311 the design doc\'s batch table (section 7) plus task 10x\'s '
            f'two extra glyphs is built '
            f'from -- the GROUPS table in this script has gone stale and '
            f'needs re-deriving against the new set')

    groups, assigned = [], set()
    for label, prefixes in GROUPS:
        cps = [cp for cp in hand7 if (cp >> 8) in prefixes]
        assigned.update(cps)
        groups.append((label, cps))
    groups.append((MISC_LABEL, sorted(set(hand7) - assigned)))

    h_cps = [ord(c) for c in H_LETTERS]
    if len(set(h_cps)) != 20 or set(h_cps) & set(hand7):
        raise SystemExit(
            'H_LETTERS is not 20 distinct codepoints disjoint from the 7x14 '
            'hand set -- check tools/build-compare.py against Ruling R13')
    groups.append((H_LABEL, h_cps))
    return groups


# ------------------------------------------------------------------- HTML --

def tile(cp, built7, built8):
    """One tile: codepoint label, then the 7x14 glyph beside the 8x16 one.

    A single font-family with no fallback in the CSS is necessary but NOT
    sufficient: Chromium's own font matching silently substitutes a system
    symbol/emoji font for a character the requested @font-face's cmap lacks,
    fallback list or no (confirmed by hand -- U+2701 rendered as a colour
    emoji scissors glyph before this guard was added).  The only rendering
    that cannot lie is one with no text in it at all, so a codepoint this
    face has not actually built is never placed in that span's DOM in the
    first place -- there is then nothing for any font, real or substituted,
    to draw.

    An empty span is ambiguous, though: it looks the same whether the
    codepoint was never drawn, or IS built but simply renders as nothing
    (e.g. U+0020 SPACE).  So a `missing` class -- a CSS-only dashed box, the
    familiar "no glyph here" look -- is added whenever the codepoint is
    absent from `built7`/`built8`, i.e. whenever the span is left empty.
    That is a presence check against the built cmap, never a check of what
    the glyph looks like, so a present-but-blank glyph never gets a box: it
    stays a plain empty span, exactly as before this change.  The box itself
    is a border on the still-empty span, NOT a character -- adding any
    character (a box-drawing glyph, `.notdef`, tofu, an emoji) here would
    reopen the exact substitution hole the paragraph above guards against,
    because it would put text back in the DOM for a font's own fallback
    matching to act on.
    """
    label = f'U+{cp:04X}'
    present7, present8 = cp in built7, cp in built8
    ch7 = html.escape(chr(cp), quote=False) if present7 else ''
    ch8 = html.escape(chr(cp), quote=False) if present8 else ''
    cls7 = 'glyph g7' if present7 else 'glyph g7 missing'
    cls8 = 'glyph g8' if present8 else 'glyph g8 missing'
    return (
        '<div class="tile">'
        f'<span class="cp" title="{html.escape(gs.unicode_name(cp))}">{label}</span>'
        '<div class="pair">'
        f'<span class="{cls7}">{ch7}</span>'
        f'<span class="{cls8}">{ch8}</span>'
        '</div></div>'
    )


def section(label, cps, drawn, built7, built8):
    n_drawn = len(drawn & set(cps))
    heading = f'{label} — {n_drawn} of {len(cps)} drawn'
    tiles = '\n'.join(tile(cp, built7, built8) for cp in cps)
    return (f'<section class="block">\n<h2>{html.escape(heading)}</h2>\n'
            f'<div class="tiles">\n{tiles}\n</div>\n</section>')


def build(out_dir):
    for size in (SIZE_SMALL, SIZE_LARGE):
        path = os.path.join('build', gs.font_stem(size, FACE) + '.woff2')
        if not os.path.exists(path):
            raise SystemExit(f'{path} is missing -- run `make woff2` first')

    groups = target_groups()
    drawn8 = hand_codepoints(SIZE_LARGE, FACE)
    # The actual built cmaps -- resolve() is exactly what build-face.py builds
    # the .ttf from, so "is cp in here" is the truth the woff2 will also tell
    # a browser, not a guess about it.
    built7 = set(gs.resolve(SIZE_SMALL, FACE))
    built8 = set(gs.resolve(SIZE_LARGE, FACE))
    total = sum(len(cps) for _label, cps in groups)
    total_drawn = len(drawn8 & set(cp for _label, cps in groups for cp in cps))

    w7, h7 = gs.cell(SIZE_SMALL)
    w8, h8 = gs.cell(SIZE_LARGE)
    px7, px8 = 2 * h7, 2 * h8  # the exact 2x multiple each cell is pixel-crisp at

    sections = '\n'.join(section(label, cps, drawn8, built7, built8)
                          for label, cps in groups)

    # The relative path from build/compare/index.html back to the woff2 files
    # sitting directly in build/ -- one directory up, by construction of
    # `out_dir` always being build/compare.
    up = os.path.relpath('build', out_dir)
    src7 = f'{up}/{gs.font_stem(SIZE_SMALL, FACE)}.woff2'
    src8 = f'{up}/{gs.font_stem(SIZE_LARGE, FACE)}.woff2'

    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smalti compare — {SIZE_SMALL} against {SIZE_LARGE}</title>
<style>
/* generated by tools/build-compare.py -- do not edit */

/* Two named families, each with exactly one @font-face source and NO
 * fallback anywhere a glyph tile uses them (see .g7 / .g8 below).  This is
 * the whole point of the page: an 8x16 glyph that has not been drawn yet
 * must render as nothing, not as a borrowed glyph from some other font on
 * the machine viewing this page.  A fallback here would make this chart
 * approve work that was never done. */
@font-face {{
  font-family: "SmaltiCompare7x14";
  src: url("{src7}") format("woff2");
  font-weight: 400; font-style: normal; font-display: block;
}}
@font-face {{
  font-family: "SmaltiCompare8x16";
  src: url("{src8}") format("woff2");
  font-weight: 400; font-style: normal; font-display: block;
}}

:root {{
  --bg: #16140f; --bg2: #1e1b15; --line: #3a3327;
  --ink: #efe7d3; --ink-dim: #a2977c;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 24px 32px 64px;
  background: var(--bg); color: var(--ink);
  font: 15px/1.4 ui-sans-serif, system-ui, sans-serif;
}}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
p.sub {{ color: var(--ink-dim); margin: 0 0 32px; }}
h2 {{
  font-size: 14px; font-weight: 600; color: var(--ink-dim);
  border-bottom: 1px solid var(--line); padding-bottom: 6px;
  margin: 40px 0 12px;
}}
.tiles {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.tile {{
  display: flex; flex-direction: column; align-items: center;
  gap: 4px; padding: 8px 6px; background: var(--bg2);
  border: 1px solid var(--line); border-radius: 3px; min-width: 84px;
}}
.cp {{
  font: 11px/1 ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  color: var(--ink-dim); user-select: all;
}}
.pair {{ display: flex; align-items: flex-end; gap: 10px; }}
/* No nearest-neighbour scaling hint here on purpose -- these are outline
 * glyphs rendered at an exact integer multiple of the cell height, not a
 * scaled bitmap, so they are crisp on their own and forcing that hint would
 * be wrong, possibly hiding a real rendering fault. */
.glyph {{ line-height: 1; text-align: center; }}
.g7 {{ font-family: "SmaltiCompare7x14"; font-size: {px7}px; }}
.g8 {{ font-family: "SmaltiCompare8x16"; font-size: {px8}px; }}
/* "missing" tiles a codepoint absent from that face's built cmap -- see the
 * long comment on tile() in build-compare.py for why this MUST stay a CSS
 * border and never a character.  Sized to the advance width/height a real
 * glyph would occupy at this font-size (font-size * cell_w/cell_h, cell_h),
 * so a placeholder box never shifts the tile layout relative to a drawn
 * glyph sitting next to it. */
.glyph.missing {{
  display: inline-block; box-sizing: border-box;
  border: 1px dashed var(--ink-dim);
}}
.g7.missing {{ width: {px7 * 7 // 14}px; height: {px7}px; }}
.g8.missing {{ width: {px8 * 8 // 16}px; height: {px8}px; }}
</style>
</head>
<body>
<h1>Smalti compare — {SIZE_SMALL} at {px7}px beside {SIZE_LARGE} at {px8}px</h1>
<p class="sub">{total_drawn} of {total} target glyphs drawn at {SIZE_LARGE}.
A dashed box is a glyph nobody has drawn yet at that size -- it must never be
a borrowed glyph from another font. A blank tile with no box means the
codepoint IS drawn and is legitimately empty (e.g. a space).</p>
{sections}
</body>
</html>
'''
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(page)

    print(f'{out_path}: {len(groups)} blocks, {total} target glyphs, '
          f'{total_drawn} drawn at {SIZE_LARGE}')
    for label, cps in groups:
        print(f'  {label}: {len(drawn8 & set(cps))} of {len(cps)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join('build', 'compare'))
    a = ap.parse_args()
    build(a.out)


main()
