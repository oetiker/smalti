#!/usr/bin/env python3
"""The glyph store: layout, file format and precedence.

    glyphs/<size>/<face>/<CP>.txt          committed, hand-owned, always wins
    upstream/<size>/Tamzen<size><f>.bdf    committed, hand-drawn by upstream
    build/gen/<size>/<face>/<CP>.txt       generated, never committed

<size> is upstream's own spelling (7x14), <face> is one of regular, bold,
italic, bold-italic, and <CP> is the codepoint in uppercase hex, at least four
digits.  Hex rather than the character itself because the character does not
survive contributors: 142 of this font's codepoints collide case-insensitively
on APFS and NTFS, 168 normalise to NFD on macOS, and 17 cannot be a bare
filename at all.

THE RULE

    A drawing always beats a computation.  A computation always beats nothing.

For each (size, face, codepoint) the build takes the first that exists:

    1. glyphs/<size>/<face>/<CP>.txt      this project's contributors
    2. upstream/<size>/...<face>.bdf      Scott Fial / Suraj N. Kurapati
    3. build/gen/<size>/<face>/<CP>.txt   a generator

Upstream sits ABOVE the generators, not below, because it is also hand-drawn:
tools/weight.py records that computed emboldening reproduces only 93 of
upstream's 189 bold glyphs, and a hand-drawn bold beats a computed one.  Faces
upstream never drew -- italic, bold-italic -- simply have no layer 2.

Because one file holds one glyph, a duplicate codepoint is impossible rather
than merely checked for: the filesystem enforces uniqueness.
"""
import datetime
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FACES = ('regular', 'bold', 'italic', 'bold-italic')

# The upright face a slanted face takes its glyph inventory and its per-glyph
# BDF metadata from.  A slanted face has no upstream layer of its own.
UPRIGHT_OF = {'italic': 'regular', 'bold-italic': 'bold'}

# Upstream's own filename suffix for the two faces it ships.
UPSTREAM_TAG = {'regular': 'r', 'bold': 'b'}

HAND_ROOT = 'glyphs'
GEN_ROOT = os.path.join('build', 'gen')
UPSTREAM_ROOT = 'upstream'

# The name this font is built under.  It lives here rather than in the builder
# because the checker has to name the artefacts it expects to find, and two
# spellings of the family name would let a renamed build slip past the check.
FAMILY = 'Smalti'

# The version this build claims.  It lives in a file of its own, holding
# nothing else, because the release workflow rewrites it unattended: a whole
# file written from one shell variable cannot corrupt its surroundings the way
# a mistaken sed across a source file can, and the release commit's diff is
# then one line that says only what it means.  Nothing else in the tree may
# spell a version number; every artefact takes it from here.
VERSION_FILE = os.path.join(ROOT, 'VERSION')


class GlyphError(Exception):
    """A malformed glyph file.  Always carries path and line number."""


# ----------------------------------------------------------------- version --

def version():
    """The project version as MAJOR.MINOR.PATCH, from the VERSION file."""
    try:
        with open(VERSION_FILE) as fh:
            raw = fh.read().strip()
    except OSError as e:
        raise GlyphError(f'cannot read {VERSION_FILE}: {e}')
    if not re.fullmatch(r'\d+\.\d+\.\d+', raw):
        raise GlyphError(f'{VERSION_FILE}: not a MAJOR.MINOR.PATCH version: '
                         f'{raw!r}')
    return raw


def font_revision(v=None):
    """head.fontRevision for a version string, as MAJOR.MMPP.

    head.fontRevision is a 16.16 fixed-point number: one unit is 1/65536, so
    it carries about four decimal places and no more.  Two digits each for
    minor and patch is the widest encoding that still ORDERS correctly --
    0.1.0 becomes 0.0100 and 0.1.1 becomes 0.0101, six units apart.  The
    obvious alternative of three digits each does not survive the rounding: a
    patch bump would move the number by less than one unit and two different
    releases would compare equal.

    The full version is always in nameID 5, which is the field anything
    human-facing shows.  This number exists for machines comparing builds.

    A short version is padded, so a foreign BDF carrying FONT_VERSION "1.11"
    still converts -- this tool is pointed at upstream's own files too.
    """
    parts = (v if v is not None else version()).split('.')
    if not 1 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        raise GlyphError(f'not a version number: {v!r}')
    major, minor, patch = (int(p) for p in (parts + ['0', '0'])[:3])
    if minor > 99 or patch > 99:
        raise GlyphError(
            f'version {v or version()!r}: minor and patch must each stay '
            f'below 100 to fit head.fontRevision -- widen the encoding in '
            f'glyphstore.font_revision() before releasing this')
    return float(f'{major}.{minor:02d}{patch:02d}')


# ------------------------------------------------------------- build stamp --

# The build stamp when SOURCE_DATE_EPOCH is unset.  A committed constant, not
# the clock -- see tools/trace-outline.py, "THE OUTPUT MUST BE
# BYTE-REPRODUCIBLE".  This is 2026-01-01T00:00:00Z, the year Smalti forked
# from Tamzen.
FALLBACK_EPOCH = 1767225600


def build_epoch():
    """Unix seconds to stamp into build outputs that must not carry the wall
    clock: head.created/head.modified in the .ttf faces, and mtime in the
    .deb/.rpm packages.

    Reads SOURCE_DATE_EPOCH -- the reproducible-builds convention, which also
    lets CI pin it -- and falls back to the constant above when it is unset.
    This is the ONE place that reads that variable, so the fonts and the
    packages built from them can never disagree about what "now" was.
    """
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is None or not raw.strip():
        return FALLBACK_EPOCH
    try:
        return int(raw.strip())
    except ValueError:
        raise SystemExit(f"SOURCE_DATE_EPOCH is not an integer: {raw!r}")


def build_epoch_rfc3339():
    """build_epoch(), formatted the way nfpm's `mtime:` config field wants it.

    nfpm ignores SOURCE_DATE_EPOCH entirely (as of 2.47.0): left to itself it
    stamps package contents with the wall clock, which would make every
    `make packages` run produce different bytes even with the environment
    variable exported.  Its `mtime:` field is the only override it honours,
    and it takes RFC3339, not Unix seconds.
    """
    return datetime.datetime.fromtimestamp(
        build_epoch(), tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- geometry --

def cell(size):
    """(width, height) in pixels for a size named the way upstream names it."""
    m = re.fullmatch(r'([1-9]\d*)x([1-9]\d*)', size)
    if not m:
        raise GlyphError(f'not a size: {size!r} (expected e.g. 7x14)')
    return int(m.group(1)), int(m.group(2))


def stride(w):
    """Bits per BDF row: the format pads every row to whole bytes."""
    return (w + 7) // 8 * 8


def pack(rows, w):
    """ASCII art rows -> one integer per row, most significant bit leftmost."""
    s = stride(w)
    return [sum(1 << (s - 1 - i) for i, ch in enumerate(r) if ch == '#')
            for r in rows]


def art(bm, w):
    """One integer per row -> ASCII art rows."""
    s = stride(w)
    return [''.join('#' if v & (1 << (s - 1 - c)) else '.' for c in range(w))
            for v in bm]


def hexrows(bm, w):
    n = stride(w) // 4
    return [f'{v:0{n}X}' for v in bm]


# ------------------------------------------------------------ file format --

def unicode_name(cp):
    """The Unicode name, or a stand-in for the codepoints that have none.

    Fifteen codepoints in this font have no name: U+0000 and the fourteen
    control slots upstream parks its VT100 line-drawing glyphs in.  They are
    `<control>` when their category is Cc and `<unnamed>` otherwise, which is
    what the Powerline private-use area gets.
    """
    ch = chr(cp)
    try:
        return unicodedata.name(ch)
    except ValueError:
        return '<control>' if unicodedata.category(ch) == 'Cc' else '<unnamed>'


def header(cp):
    """The one comment line at the top of a glyph file.

    Its only job is to make a diff legible, because `0041.txt` on its own tells
    a reviewer nothing.  The character is shown only when it is printable, and
    quoted, so that the space in U+0020 is visible.
    """
    ch = chr(cp)
    shown = f"'{ch}'" if ch.isprintable() else ''
    return f'# U+{cp:04X} {shown:<3}  {unicode_name(cp)}'


def filename(cp):
    return f'{cp:04X}.txt'


def cp_of(name):
    """Codepoint from a glyph filename, or None if it is not one."""
    m = re.fullmatch(r'([0-9A-F]{4,6})\.txt', name)
    if not m:
        return None
    cp = int(m.group(1), 16)
    return cp if cp <= 0x10FFFF else None


def read_glyph(path, w, h):
    """Return h art rows of w characters, or raise GlyphError.

    A PIXEL ROW IS RECOGNISED BEFORE A COMMENT.  '#' is both the ink pixel and
    the comment marker, so an em dash row '#######' would otherwise be eaten as
    a comment.  This rule is load-bearing; do not reorder these two tests.
    """
    rows = []
    with open(path, encoding='utf-8') as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip('\n')
            if len(line) == w and not set(line) - {'#', '.'}:
                rows.append(line)
                continue
            if not line.strip() or line.lstrip()[0] in '#;':
                continue
            raise GlyphError(f'{path}:{lineno}: expected a comment or a row of '
                             f"exactly {w} '#'/'.' characters, got {line!r}")
    if len(rows) != h:
        raise GlyphError(f'{path}: {len(rows)} rows, need {h}')
    return rows


def normalised(cp, rows):
    """The one canonical byte sequence a glyph file may have.

    Every tool that writes, rewrites or checks a drawing goes through here, so
    that "what `make headers` would write" has exactly one definition and a
    checker cannot drift from the writer.  Newlines are LF on every platform:
    the normal form is a property of the repository, not of the contributor's
    operating system.
    """
    return header(cp) + '\n' + '\n'.join(rows) + '\n'


def read_raw(path):
    """The file's text exactly as stored, line endings and all.

    Deliberately not universal-newline mode: a CRLF drawing must compare
    UNEQUAL to its normal form, or `make check` would bless it and
    `make headers` would never rewrite it.
    """
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write_glyph(path, cp, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(normalised(cp, rows))


def read_dir(directory, w, h):
    """{codepoint: art rows} for every glyph file in one directory."""
    out = {}
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        if not name.endswith('.txt'):
            continue
        cp = cp_of(name)
        if cp is None:
            raise GlyphError(f'{os.path.join(directory, name)}: filename must be '
                             f'the codepoint in uppercase hex, at least four '
                             f'digits, e.g. {filename(0x41)}')
        out[cp] = read_glyph(os.path.join(directory, name), w, h)
    return out


# -------------------------------------------------------------------- BDF --

class Bdf:
    """A parsed BDF: the header, and per glyph its text, metadata and bitmap.

    `blocks` keeps each glyph's original text verbatim, because upstream's
    STARTCHAR names are not derivable: fourteen glyphs live in a control-code
    slot under the name of the character they actually draw -- ENCODING 2 is
    STARTCHAR U+2592.  Re-deriving the name would lose that.
    """

    def __init__(self, path):
        text = open(path, encoding='latin1').read()
        m = re.search(r'^FONTBOUNDINGBOX (\d+) (\d+) ', text, re.M)
        self.path = path
        self.w, self.h = int(m.group(1)), int(m.group(2))
        self.swidth = re.search(r'^SWIDTH (\S+ \S+)$', text, re.M).group(1)
        self.head, _, rest = text.partition('\nSTARTCHAR ')
        self.blocks, self.pre, self.bitmaps = {}, {}, {}
        for chunk in ('STARTCHAR ' + rest).split('STARTCHAR ')[1:]:
            body, _, _tail = chunk.partition('ENDCHAR')
            cp = int(re.search(r'^ENCODING (-?\d+)', body, re.M).group(1))
            self.blocks[cp] = 'STARTCHAR ' + body + 'ENDCHAR\n'
            head, _, bits = body.partition('BITMAP\n')
            self.pre[cp] = head
            self.bitmaps[cp] = [int(x, 16) for x in bits.strip().split('\n')] \
                if bits.strip() else []


def upstream_bdf(size, face):
    """Path to upstream's own file, which keeps upstream's own name."""
    tag = UPSTREAM_TAG.get(face)
    if tag is None:
        return None
    return os.path.join(UPSTREAM_ROOT, size, f'Tamzen{size}{tag}.bdf')


def face_tag(face):
    """The face's spelling in a filename: bold-italic -> BoldItalic."""
    return ''.join(word.capitalize() for word in face.split('-'))


def font_stem(size, face):
    """The basename a built face carries, without its extension."""
    return f'{FAMILY}{size}-{face_tag(face)}'


def hand_dir(size, face):
    return os.path.join(HAND_ROOT, size, face)


def gen_dir(size, face):
    return os.path.join(GEN_ROOT, size, face)


# ------------------------------------------------------------- precedence --

def resolve(size, face):
    """{codepoint: (layer, bitmap)} for one face, layers applied in order.

    layer is 'hand', 'upstream' or 'gen'.  Assigning in reverse precedence
    order means the winner is simply whatever was written last.
    """
    w, h = cell(size)
    out = {}
    for cp, rows in read_dir(gen_dir(size, face), w, h).items():
        out[cp] = ('gen', pack(rows, w))
    path = upstream_bdf(size, face)
    if path and os.path.exists(path):
        for cp, bm in Bdf(path).bitmaps.items():
            out[cp] = ('upstream', bm)
    for cp, rows in read_dir(hand_dir(size, face), w, h).items():
        out[cp] = ('hand', pack(rows, w))
    return out


def bitmaps(size, face):
    """Just the resolved bitmaps, which is what every generator wants."""
    return {cp: bm for cp, (_layer, bm) in resolve(size, face).items()}
