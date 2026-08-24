# Smalti 7x14 -- Tamzen 7x14 with 813 extra glyphs, in four faces.
#
#   make            build all four faces into build/, .bdf and .ttf
#   make outlines   the .ttf faces only
#   make woff2      the compressed web copies
#   make preview    show the added glyphs as ASCII art
#   make show       print every added glyph in the terminal
#   make install    copy all four .ttf where fontconfig will find them
#   make watch      rebuild, install and reload on every save
#   make check      everything below: the glyph store, the built faces, and
#                   the proof that each .ttf is the same shape as its bitmap
#   make check-sources   the glyph store and the built faces only
#   make check-outlines  the .ttf-against-.bdf proof only
#   make check-version   the version in VERSION, read back out of every face
#   make headers    rewrite every drawing into its normal form
#   make index      regenerate docs/coverage.md
#   make site       build the specimen site into build/site/
#   make check-site prove the site ships this repository's drawings
#   make restore    put the untouched baselines back
#
# Requires: python3-venv.  `make venv` does the rest -- nothing else, no
# system font tooling.  Smalti used to ship a bitmap-only .otb built by
# fonttosfnt (Debian/Ubuntu package xfonts-utils); it does not any more, and
# dropping it took the last non-pip dependency out of the build.  See
# README.md, "Why there is no .otb".

SIZE  := 7x14
FONT  := Smalti$(SIZE)

# Anywhere fontconfig scans works.  The `-ttf` suffix is history -- it dates
# from when a second directory held the bitmap .otb -- but it is kept because
# it is what wezterm's font_dirs points at, and because it says what the
# directory holds.  KEEP IT .ttf ONLY: wezterm scans font_dirs itself and a
# build that reads bitmap strikes would find two candidates per face.
DEST  := $(HOME)/.local/share/fonts/smalti-ttf
# `restore` still targets the ORIGINAL Tamzen directory: its job is to give
# you a working terminal back, and after the rename that means pointing
# wezterm at upstream Tamzen, not at a Smalti-named file holding 189 glyphs.
TAMZEN_DEST := $(HOME)/.local/share/fonts/tamzen-patched
WEZCFG := $(HOME)/.config/wezterm/wezterm.lua

UPSTREAM_R := upstream/$(SIZE)/Tamzen$(SIZE)r.bdf
UPSTREAM_B := upstream/$(SIZE)/Tamzen$(SIZE)b.bdf

# The drawings: one file per glyph, hand-owned, always winning.  Listed as a
# prerequisite rather than discovered inside a recipe so that adding a drawing
# rebuilds the derived faces too.
HAND  := $(wildcard glyphs/$(SIZE)/*/*.txt)

# The derived layer must be GENERATED, never discovered: if it were found with
# a wildcard, an empty directory would silently build a bold face out of
# upstream's 190 glyphs instead of failing.
GEN     := build/gen/$(SIZE)/.stamp
GENTOOL := tools/glyphstore.py tools/accents.py tools/weight.py \
           tools/gen-braille.py tools/gen-arrows.py tools/gen-circled-digits.py \
           tools/gen-latin-ext-a.py tools/embolden.py tools/slant-bdf.py \
           tools/slant-bold.py

FACES := Regular Bold Italic BoldItalic
TTF   := $(FACES:%=build/$(FONT)-%.ttf)
WOFF2 := $(FACES:%=build/$(FONT)-%.woff2)
BDF   := $(FACES:%=build/$(FONT)-%.bdf)

.PHONY: all install preview show restore clean watch headers index \
        check check-sources check-outlines check-version venv outlines woff2 \
        print-dest \
        site check-site serve-site

# The .bdf strikes are the intermediate; the .ttf is the deliverable.  There
# is no bitmap-format output any more: an .otb is invisible to fontconfig and
# to every browser, so it reached nothing but a patched wezterm, while the
# .ttf renders the identical pixels everywhere.  `make check-outlines` is the
# proof of that "identical", glyph by glyph.
all: $(BDF) outlines

# STEPS are the rows where the lean drops a column: above the first the glyph
# moves right, below the last it moves left.  More steps means more lean.
#   make STEPS=4,7,10 install
STEPS := 5,8

# One ordered recipe, because the generators feed each other: the bold face is
# emboldened from the RESOLVED regular face, the italic is sheared from it, and
# the bold-italic from the resolved italic and bold.  The order also settles
# the one place two generators write the same file: gen-latin-ext-a runs after
# embolden and wins for U+0100..U+017F, because composing against upstream's
# own bold letters and bold accents beats widening the regular ones.
$(GEN): $(GENTOOL) $(HAND) $(UPSTREAM_R) $(UPSTREAM_B)
	@rm -rf build/gen/$(SIZE)      # generated output only; nothing here is committed
	@mkdir -p $(dir $@)
	python3 tools/gen-braille.py $(SIZE)
	python3 tools/gen-arrows.py $(SIZE)
	python3 tools/gen-circled-digits.py $(SIZE)
	python3 tools/gen-latin-ext-a.py $(UPSTREAM_R) build/gen/$(SIZE)/regular
	python3 tools/embolden.py $(SIZE)
	python3 tools/gen-latin-ext-a.py $(UPSTREAM_B) build/gen/$(SIZE)/bold
	python3 tools/slant-bdf.py --steps $(STEPS) $(SIZE)
	python3 tools/slant-bold.py $(SIZE)
	@touch $@

# VERSION is a prerequisite because build-face.py stamps it into the BDF's
# FONT_VERSION, which is where the outline path reads it from.
BUILDFACE := tools/build-face.py tools/glyphstore.py VERSION

build/$(FONT)-Regular.bdf: $(GEN) $(HAND) $(UPSTREAM_R) $(BUILDFACE)
	python3 tools/build-face.py $(SIZE) regular --out $@

build/$(FONT)-Bold.bdf: $(GEN) $(HAND) $(UPSTREAM_B) $(BUILDFACE)
	python3 tools/build-face.py $(SIZE) bold --out $@

# The slanted faces have no upstream layer of their own, so they take their
# per-glyph BDF metadata -- and their glyph inventory -- from the upright face
# they lean.  See tools/build-face.py.
build/$(FONT)-Italic.bdf: build/$(FONT)-Regular.bdf $(GEN) $(HAND) $(BUILDFACE)
	python3 tools/build-face.py $(SIZE) italic --donor $< --out $@

build/$(FONT)-BoldItalic.bdf: build/$(FONT)-Bold.bdf $(GEN) $(HAND) $(BUILDFACE)
	python3 tools/build-face.py $(SIZE) bold-italic --donor $< --out $@

# Three parts, and `check` is all of them.  Never let one answer to the name
# `check` on its own: a check target that runs part of the checks and reports
# success is worse than no check at all, because CI goes green on it.
check: check-sources check-outlines check-version

# The version in VERSION, read back out of the finished files.  It is part of
# `check` because the number has two hops to make -- into the BDF's
# FONT_VERSION, then into the .ttf name table -- and either can go quiet
# independently.  A font claiming a version it is not looks exactly like a
# font that is fine.
check-version: all
	$(PY) tools/check-version.py $(SIZE)

# The drawings and the built faces (design spec section 9).
# The self-test runs FIRST and is not optional: it breaks the tree seven ways
# and insists check-glyphs.py notices each one.  A green check below only means
# something if the checker underneath it can go red, and twice now it could
# not -- once for a drawing that had drifted out of normal form, once for a run
# with nothing built to check.
# $(PY), not python3: both of these now read the built .ttf with fontTools,
# which lives in the venv.  Nothing else about them changed.
check-sources: all
	$(PY) tools/test-check-glyphs.py $(SIZE)
	$(PY) tools/check-glyphs.py $(SIZE)

headers:
	python3 tools/glyph-headers.py

index:
	python3 tools/glyph-index.py

# One install target, not two.  While the bitmap .otb existed there had to be
# two, because both formats claim the same family name and fontconfig serving
# one while wezterm's font_dirs found the other gave every face two
# candidates.  With one format that problem is gone.
install: all
	@mkdir -p $(DEST)
	cp $(TTF) $(DEST)/
	@fc-cache -f $(DEST) >/dev/null 2>&1 || true
	@echo "installed to $(DEST) -- family 'Smalti $(SIZE)', all four faces"
	@if ls $(DEST)/*.otb >/dev/null 2>&1; then \
		echo "WARNING: $(DEST) also holds .otb files.  Remove them -- a wezterm"; \
		echo "         that reads bitmap strikes sees two candidates per face."; \
	fi
	@echo "A RUNNING wezterm that still cannot load the font is showing its"
	@echo "per-process fontconfig cache, not a failed install -- see README.md,"
	@echo "'Making it look right', for why font_dirs is the answer."

# Rebuild and reload on every save.  Directories are watched, not files,
# because editors replace a file rather than writing into it, which would
# leave a file watch pointing at the old inode.
# Touching the wezterm config triggers wezterm's own automatic config reload,
# which is the same action as pressing Ctrl+Shift+R.
watch:
	@echo "watching glyphs/ and tools/ -- Ctrl-C to stop"
	@while true; do \
		inotifywait -qq -r -e close_write,moved_to,create,delete glyphs tools; \
		echo "--- $$(date +%H:%M:%S)"; \
		if $(MAKE) --no-print-directory install; then \
			[ -f $(WEZCFG) ] && touch $(WEZCFG) && echo "wezterm reloaded"; \
		else \
			echo "BUILD FAILED -- fonts left untouched, still watching"; \
		fi; \
	done

# CI asks where `install` puts things rather than hardcoding the path in a
# workflow.  A second copy of DEST is a second thing to forget when it moves,
# and it has moved once already.
print-dest: ; @echo $(DEST)

show: ; @tools/show-new.sh

preview: build/$(FONT)-Regular.bdf $(GEN)
	tools/show-glyphs.py $< glyphs/$(SIZE)/regular build/gen/$(SIZE)/regular

restore:
	cp baseline/Tamzen7x14r.otb $(TAMZEN_DEST)/Tamzen7x14r.otb
	cp baseline/Tamzen7x14b.otb $(TAMZEN_DEST)/Tamzen7x14b.otb
	@echo "upstream Tamzen restored to $(TAMZEN_DEST) -- point wezterm there"

clean:
	rm -f $(BDF) $(TTF) $(WOFF2)
	rm -f build/*.otb              # stale output of a format this no longer builds
	rm -f build/nfpm build/nfpm_*.tar.gz
	rm -rf build/gen build/site
	rm -rf build/selftest-*        # only if a self-test died mid-case

# ------------------------------------------------------------------ outlines
#
# Each .bdf strike is traced into an outline .ttf -- one file per strike,
# because outlines cannot vary with cell size.  tools/trace-outline.py has the
# reasoning; `make check-outlines` proves the trace is exact, glyph by glyph
# and then pixel by pixel.
#
# This is the ONLY delivered format.  The bitmap .otb it replaced was
# invisible to most of the system -- fontconfig's
# 70-no-bitmaps-except-emoji.conf rejects anything with outline=false, and no
# browser renders an embedded strike -- so it reached nothing but a wezterm
# patched to read strikes.  The trace loses nothing: upem is the cell height
# times 64, so at the drawn size and every integer multiple of it the
# rasteriser reproduces the source bitmap exactly.
#
# Nothing here runs fonttosfnt, so nothing inherits its broken metrics or its
# incomplete name table, and repair-tamzen.py has no part in the build.  That
# tool now belongs to `make restore` alone.

VENV := .venv
PY   := $(VENV)/bin/python

# One command from a clean clone: everything the outline build needs.
venv: $(VENV)/.stamp
$(VENV)/.stamp: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet -r requirements.txt
	@touch $@

outlines: $(TTF)
woff2:    $(WOFF2)

build/%.ttf: build/%.bdf tools/trace-outline.py tools/glyphstore.py | $(VENV)/.stamp
	$(PY) tools/trace-outline.py $< $@

build/%.woff2: build/%.ttf | $(VENV)/.stamp
	$(VENV)/bin/fonttools ttLib.woff2 compress -o $@ $<

# Every glyph of every face: filled area against lit pixel count, then the
# rendered raster against the bitmap at 1x, 2x and 3x.
check-outlines: outlines
	$(PY) tools/check-outlines.py \
	    $(foreach f,$(FACES),build/$(FONT)-$(f).bdf build/$(FONT)-$(f).ttf)
	@for f in $(FACES); do \
		$(PY) tools/render-check.py build/$(FONT)-$$f.bdf \
		      build/$(FONT)-$$f.ttf || exit 1; \
	done

# ---------------------------------------------------------------- the site
#
# A specimen page that renders every glyph as real text, says honestly what is
# and is not covered, and lets a visitor edit any glyph's pixels and open the
# pull request from the browser.
#
# IT LOADS THE .woff2 FILES.  The outlines are exact at 14, 28 and 42 px and
# the page offers no size in between, because a size in between is where the
# pixels stop being pixels.
#
# Nothing under build/site/ is committed, for the same reason nothing else
# under build/ is: generated output is generated, never discovered.

SITE   := build/site
# owner/name for the "edit this glyph on GitHub" links.  Taken from the git
# remote so a fork's links point at the fork; GitHub Actions passes
# github.repository instead, because a checkout there has no useful remote.
SITE_REPO   ?=
SITE_BRANCH ?= main
SITE_ARGS   := --branch $(SITE_BRANCH) $(if $(SITE_REPO),--repo $(SITE_REPO),)

SITESRC := site/index.html site/smalti.css site/smalti.js

site: $(SITE)/index.html
$(SITE)/index.html: $(WOFF2) $(TTF) $(SITESRC) tools/build-site.py \
                    tools/glyphstore.py | $(VENV)/.stamp
	$(PY) tools/build-site.py $(SITE_ARGS) --out $(SITE) $(SIZE)

# The site ships a copy of every drawing.  A stale copy would hand a
# contributor a wrong file and turn their first pull request into a spurious
# diff, so every glyph, in every face, is compared back against the store --
# including the exact bytes the in-page editor would emit.
check-site: site
	$(PY) tools/check-site.py --site $(SITE) $(SIZE)

# fetch() refuses file:// URLs, so the site has to be served to be looked at.
serve-site: site
	@echo "http://localhost:8014/ -- Ctrl-C to stop"
	@cd $(SITE) && python3 -m http.server 8014

# ------------------------------------------------------------------ packages
#
# Two OS packages, built by nfpm from one description.  See
# docs/superpowers/specs/2026-08-24-os-packages-design.md.
#
# NOTHING HERE IS REACHABLE FROM `all` OR `check`.  The font build needs
# python3-venv and nothing else, and packaging must not quietly change that:
# a contributor who never builds a package downloads nothing and installs
# nothing.

NFPM_VERSION := 2.47.0
# Pinned here, beside the version, and NOT taken from the checksums.txt that
# ships next to the tarball -- a checksum fetched from the same place as the
# file it checks proves only that the download did not corrupt.
NFPM_SHA256  := 0660ca602b2d2d2ae4781a06c692b3eeb9d437ffea05b831d76e41f4a3188783
NFPM_TAR     := nfpm_$(NFPM_VERSION)_Linux_x86_64.tar.gz
NFPM_URL     := https://github.com/goreleaser/nfpm/releases/download/v$(NFPM_VERSION)/$(NFPM_TAR)
NFPM         := build/nfpm

# `sha256sum --check` exits non-zero on a mismatch, which stops the recipe
# before anything is extracted.  The tarball is removed either way so a failed
# download cannot be mistaken for a good one on the next run.
$(NFPM):
	@mkdir -p build
	curl -fsSL -o build/$(NFPM_TAR) $(NFPM_URL)
	@echo "$(NFPM_SHA256)  build/$(NFPM_TAR)" | sha256sum --check -
	tar -xzf build/$(NFPM_TAR) -C build nfpm
	@rm -f build/$(NFPM_TAR)
	@touch $@
