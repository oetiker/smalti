#!/bin/sh
# Print every glyph this repo adds, in the terminal's own font.
# Anything that looks wrong here is a glyph to draw in glyphs/7x14/regular/.
cd "$(dirname "$0")/.." || exit 1
python3 - <<'PY'
import glob, os, re
cps = sorted({int(os.path.basename(f)[:-4], 16)
              for d in ('glyphs/7x14/regular', 'build/gen/7x14/regular')
              for f in glob.glob(d + '/*.txt')
              if re.fullmatch(r'[0-9A-F]{4,6}\.txt', os.path.basename(f))})
groups = [
    ('latin-1  ', lambda c: c < 0x100),
    ('lat-ext-A', lambda c: 0x100 <= c < 0x180),
    ('greek    ', lambda c: 0x370 <= c < 0x400),
    ('typo     ', lambda c: 0x2010 <= c < 0x2100),
    ('arrows   ', lambda c: 0x2190 <= c < 0x2200),
    ('maths    ', lambda c: 0x2200 <= c < 0x2300),
    ('shapes   ', lambda c: 0x2500 <= c < 0x2600),
    ('ui       ', lambda c: c in (0x23BF, 0x23F5, 0x23FA, 0x29C9)
                            or 0x2700 <= c < 0x2800),
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
print('legal   ® ™ ‰ ¼ ½ ¾ ☆ ★ ※   Ĳ ĳ ŉ')
print('spinner ✢ ∗ ✳ ✻ ✽ ✶ ✷ ✸ ✹ ✺   ◐ ◑ ◒ ◓ ◔ ◕   ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏')
print('prompt  ❯ claude  ⏺ tool  ⎿  result  ✔ ✘ ▪ ▫ ⧉')
print('braille ⣿ ⡿ ⢿ ⣻ ⣽ ⣾ ⣷ ⣯ ⣟ ⠿ ⠟ ⠯ ⠷ ⠾ ⠽ ⠻ (all 256 present)')
PY
