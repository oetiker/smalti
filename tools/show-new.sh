#!/bin/sh
# Print every glyph this repo adds, in the terminal's own font.
# Anything that looks wrong here is a glyph to fix in glyphs/*.txt.
cd "$(dirname "$0")/.." || exit 1
python3 - <<'PY'
import glob, re
cps = sorted({int(x, 16) for f in glob.glob('glyphs/*.txt')
              for x in re.findall(r'^CHAR U\+([0-9A-Fa-f]+)', open(f).read(), re.M)})
groups = [
    ('latin-1  ', lambda c: c < 0x100),
    ('lat-ext-A', lambda c: 0x100 <= c < 0x180),
    ('greek    ', lambda c: 0x370 <= c < 0x400),
    ('typo     ', lambda c: 0x2010 <= c < 0x2100),
    ('arrows   ', lambda c: 0x2190 <= c < 0x2200),
    ('maths    ', lambda c: 0x2200 <= c < 0x2300),
    ('shapes   ', lambda c: c >= 0x2500),
]
for label, pred in groups:
    sel = [chr(c) for c in cps if pred(c)]
    for i in range(0, len(sel), 48):
        print(f"{label if i == 0 else ' ' * len(label)} {' '.join(sel[i:i+48])}")
print()
print('words   Kapitel ¶ 7 § 3 — »zwei« „drei“ … 5 ≤ x ≤ 9 → ok ✓')
print('maths   ∑(αᵢ ± β²) ≈ ∫ Δx → ∞, φ = ½(1+√5), ω ∈ Ω')
print('czech   Příšerně žluťoučký kůň úpěl ďábelské ódy')
print('polish  Zażółć gęślą jaźń')
print('legal   ® ™ ‰ ¼ ½ ¾ ☆ ★')
PY
