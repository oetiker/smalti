#!/usr/bin/env python3
"""Prove the widening rule respects the cell width it was given.

The 8-wide cases exist because the rule was written for 7 wide, where bit 0 of
each packed row is BDF padding.  At 8 wide bit 0 is column 7, and a mask that
clears it deletes a real column silently.
"""
import sys
import weight

FAIL = 0


def check(name, got, want):
    global FAIL
    if got != want:
        print(f'FAIL {name}: got {got:#04x}, want {want:#04x}')
        FAIL += 1
    else:
        print(f'ok   {name}')


# ---- 7 wide: the existing behaviour must not change ----------------------
weight.set_width(7)
# columns 0..6 -> bits 7..1.  A stem at column 3 is bit 4 = 0x10.
check('7-wide stem widens left', weight.widen([0x10])[0], 0x30)
# Ink in column 0 (bit 7) has nothing to its left, so it widens right.
check('7-wide col0 widens right', weight.widen([0x80])[0], 0xC0)

# ---- 8 wide: column 7 is real ink and must survive -----------------------
weight.set_width(8)
# A stem at column 7 is bit 0 = 0x01.  It must widen LEFT into column 6,
# giving 0x03 -- and crucially must not be masked away.
check('8-wide col7 survives', weight.widen([0x01])[0], 0x03)
# A full 8-wide row must come back unchanged, not with column 7 cleared.
check('8-wide solid row intact', weight.widen([0xFF])[0], 0xFF)

sys.exit(1 if FAIL else 0)
