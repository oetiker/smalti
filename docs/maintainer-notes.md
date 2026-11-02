# Maintainer notes

Rationale the README leaves out.

## The version in every artefact

`VERSION` is the one place the version is written.  `build-face.py` writes it
into the BDF as `FONT_VERSION`, and `trace-outline.py` copies it into the
`.ttf` name table and `head.fontRevision`.  `make check-version` reads it back
out of every built face.  A release that bumps `VERSION` without the check
could ship fonts that still name the previous version, and nothing else would
notice.

The README names no version.  The release badge at its top shows the latest
one; the direct-install commands used to name a `.deb` and an `.rpm` file by
version, and were still naming 0.3.0 after 0.4.0 had shipped.

## The packages

The `.deb` and the `.rpm` install the four faces of each size where fontconfig
finds them and carry no maintainer scripts.  The distributions' own
`fontconfig` triggers rebuild the font cache.

## Several sizes from the start

The glyph store keys every drawing by size (`glyphs/<size>/<face>/`) although
upstream Tamzen ships seven sizes and Smalti draws two.  The second size,
8x16, was added into that layout without restructuring it.  Adding a size
after other people have forks and open pull requests against a single-size
layout would move every file they touch.
