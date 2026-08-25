#!/usr/bin/env python3
"""The stroke-widening rule shared by the bold and the bold-oblique faces.

Tamzen's own bold widens every stroke by one pixel to the LEFT: bold 'A' is
regular 'A' OR itself shifted one column left.  That plain rule reproduces 108
of the 189 upstream glyphs exactly -- the best score of anything tried -- but
it also merges every 1-pixel gap, which turned the pilcrow, the registered
sign and lowercase pi into solid blobs.

Working on RUNS instead, and falling back to widening rightward when the left
is blocked, reproduces 93 of 189 and never fills a counter.  Fidelity to
upstream was deliberately traded for legibility here; do not "fix" it back.
An earlier counter-aware attempt scored 22/189 because it extended the
rightmost pixel of a solid run rightward -- work on runs, not pixels.

The rightward fallback is also what lets the BOLD OBLIQUE exist at all.  A
sheared glyph puts ink in column 0 on its lower rows, where there is nothing
to the left to widen into; the run rule quietly widens those rows rightward
instead, so shearing first and emboldening second loses no ink.

The low-bit mask is derived from the width, not the constant 0xFE it used to
be.  At 7 wide bit 0 is BDF row padding; at 8 wide it is column 7, and clearing
it deletes a real column with no visible error.  tools/slant-bdf.py already
derives its own pad mask this way (PAD_MASK = 0xFF << (8 - CELL_W) & 0xFF) --
this module was the one straggler still using the 7-wide-only constant.
"""
CELL_W = 7


def set_width(w):
    """Set the cell width the rule works at.

    Kept as module state rather than a parameter because embolden.py and
    slant-bold.py both call widen() in loops and there is exactly one width in
    play per run.
    """
    global CELL_W
    CELL_W = w


def _mask():
    """The packed-row bits that are real columns at this width.

    A BDF row is padded to a whole byte, MSB first, so column c is bit 7-c and
    the low 8-CELL_W bits are padding.  At 7 wide that mask is 0xFE; at 8 wide
    it is 0xFF, and using 0xFE there would delete column 7.
    """
    return (0xFF << (8 - CELL_W)) & 0xFF


def runs(v):
    """The (first, last) column of each solid stroke in one packed row."""
    out, start = [], None
    for c in range(CELL_W):
        if v & (1 << (7 - c)):
            if start is None:
                start = c
        elif start is not None:
            out.append((start, c - 1))
            start = None
    if start is not None:
        out.append((start, CELL_W - 1))
    return out


def widen(bm):
    """Widen each stroke by one pixel, without closing a counter."""
    out = []
    for v in bm:
        rr, n = runs(v), v
        for i, (s, e) in enumerate(rr):
            prev = rr[i - 1][1] if i else None
            nxt = rr[i + 1][0] if i + 1 < len(rr) else None
            if s > 0 and (prev is None or s - prev > 2):
                n |= 1 << (7 - (s - 1))
            elif e < CELL_W - 1 and (nxt is None or nxt - e > 2):
                n |= 1 << (7 - (e + 1))
        out.append(n & _mask())
    return out
