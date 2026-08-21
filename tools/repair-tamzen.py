#!/usr/bin/env python3
"""Repair the four defects in upstream Tamzen .otb files.

Usage: repair-tamzen.py FILE.otb [FILE.otb ...]   (edits in place)

Upstream: https://github.com/sunaku/tamzen-font, tag Tamzen-1.11.6, otb/.
Every file is bitmap-only (zero-length glyf) with one strike, and its
scalable metrics do not describe that strike.  Each fix is one fixed-width
field; the bitmap data itself is never touched.

  1. EBLC indexTablesSize covers only the index-subtable records, not the
     subtables they point at.  FreeType ignores the bound; read-fonts (used
     by wezterm's skrifa rasterizer) enforces it, so every bitmap lookup
     fails and the font renders BLANK.
  2. hmtx advance disagrees with the strike's own advance, so the shaper
     lays glyphs out on a slightly wrong pitch.
  3. OS/2 xAvgCharWidth claims ~54% of the real advance.  wezterm derives
     the cell width from it AND normalises every fallback font against it,
     so fallback glyphs render at about half size.
  4. hhea ascender/descender/lineGap sum to more than the strike's height,
     adding phantom leading.
  5. OS/2 fsSelection says REGULAR on every face, contradicting head.macStyle
     and the name table, which do carry the style.  The spec requires the two
     to agree.  Bold happens to pair anyway, but a matcher that trusts
     fsSelection sees three Regulars in one family and picks one arbitrarily.
"""
import struct, sys

def tables(d):
    n = struct.unpack('>H', d[4:6])[0]
    return {d[12+16*i:12+16*i+4].decode('latin1'): struct.unpack('>II', d[12+16*i+8:12+16*i+16])
            for i in range(n)}

def repair(path):
    d = bytearray(open(path, 'rb').read())
    T = tables(bytes(d))
    upm = struct.unpack('>H', d[T['head'][0]+18:T['head'][0]+20])[0]
    eo, el = T['EBLC']
    if struct.unpack('>I', d[eo+4:eo+8])[0] != 1:
        raise SystemExit(f"{path}: expected exactly one strike")
    b = eo + 8
    ppem = d[b+45]
    sasc, sdesc = struct.unpack('>bb', d[b+16:b+18])
    rows = sasc + abs(sdesc)
    upx = upm / ppem                      # font units per pixel
    changes = []

    # 1. EBLC indexTablesSize
    ist_off, ist_size = struct.unpack('>II', d[b:b+8])
    need = el - ist_off
    if ist_size < need:
        struct.pack_into('>I', d, b+4, need)
        changes.append(f"EBLC indexTablesSize {ist_size} -> {need}")

    # 2. hmtx advance (numberOfHMetrics is 1 for these monospace faces)
    hh = T['hhea'][0]
    if struct.unpack('>H', d[hh+34:hh+36])[0] != 1:
        raise SystemExit(f"{path}: expected numberOfHMetrics == 1")
    hm = T['hmtx'][0]
    adv_units = round(_strike_advance(d, T, b, ppem) * upx)
    old_adv = struct.unpack('>H', d[hm:hm+2])[0]
    if old_adv != adv_units:
        struct.pack_into('>H', d, hm, adv_units)
        changes.append(f"hmtx advance {old_adv} -> {adv_units}")

    # 3. OS/2 xAvgCharWidth
    oo = T['OS/2'][0]
    old_avg = struct.unpack('>h', d[oo+2:oo+4])[0]
    if old_avg != adv_units:
        struct.pack_into('>h', d, oo+2, adv_units)
        changes.append(f"OS/2 xAvgCharWidth {old_avg} -> {adv_units}")

    # 4. vertical metrics: make asc+desc equal the strike height exactly
    asc_u, desc_u = round(sasc*upx), round(abs(sdesc)*upx)
    if asc_u + desc_u != round(rows*upx):
        desc_u = round(rows*upx) - asc_u
    old = struct.unpack('>hhh', d[hh+4:hh+10])
    if old != (asc_u, -desc_u, 0):
        struct.pack_into('>hhh', d, hh+4, asc_u, -desc_u, 0)
        changes.append(f"hhea asc/desc/gap {old} -> ({asc_u}, {-desc_u}, 0)")
    struct.pack_into('>hhh', d, oo+68, asc_u, -desc_u, 0)      # sTypo*
    struct.pack_into('>HH',  d, oo+74, asc_u, desc_u)          # usWin*

    # 5. fsSelection must agree with head.macStyle.  ITALIC is bit 0, BOLD is
    # bit 5 and REGULAR is bit 6; REGULAR is mutually exclusive with both.
    mac = struct.unpack('>H', d[T['head'][0]+44:T['head'][0]+46])[0]
    old_sel = struct.unpack('>H', d[oo+62:oo+64])[0]
    sel = old_sel & ~0x0061
    sel |= (0x01 if mac & 0x02 else 0) | (0x20 if mac & 0x01 else 0)
    if not sel & 0x21:
        sel |= 0x40
    if sel != old_sel:
        struct.pack_into('>H', d, oo+62, sel)
        changes.append(f"OS/2 fsSelection 0x{old_sel:04X} -> 0x{sel:04X}")

    open(path, 'wb').write(bytes(d))
    print(f"{path}  (strike {int(_strike_advance(d,T,b,ppem))}x{rows} @ {ppem}ppem)")
    for c in changes:
        print(f"    {c}")
    if not changes:
        print("    already repaired")

def _strike_advance(d, T, b, ppem):
    """Advance in pixels, from the strike's own per-glyph metrics."""
    eo = T['EBLC'][0]; do = T['EBDT'][0]
    ist_off, _, n_ist = struct.unpack('>III', d[b:b+12])
    base = eo + ist_off
    first, last, add = struct.unpack('>HHI', d[base:base+8])
    h = base + add
    fmt, imgfmt, img_off = struct.unpack('>HHI', d[h:h+8])
    if fmt == 3:
        off = struct.unpack('>H', d[h+8:h+10])[0]
    elif fmt == 1:
        off = struct.unpack('>I', d[h+8:h+12])[0]
    else:
        raise SystemExit(f"unhandled indexFormat {fmt}")
    st = do + img_off + off
    return struct.unpack('>BBbbB', d[st:st+5])[4]

for path in sys.argv[1:]:
    repair(path)
