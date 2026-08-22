# Smalti 7x14 -- Tamzen 7x14 with 813 extra glyphs, in four faces.
#
#   make            build all four faces into build/, bitmap and outline
#   make outlines   build only the outline .ttf faces
#   make preview    show the added glyphs as ASCII art
#   make show       print every added glyph in the terminal
#   make install    copy all four over the fonts wezterm actually loads
#   make watch      rebuild, install and reload on every save
#   make check      everything below: the glyph store, the built faces, and
#                   the proof that each .ttf is the same shape as its strike
#   make check-sources   the glyph store and the built faces only
#   make check-outlines  the .ttf-against-.bdf proof only
#   make headers    normalise the header line of every drawing
#   make index      regenerate docs/coverage.md
#   make restore    put the untouched baselines back
#
# Requires: fonttosfnt (Debian/Ubuntu package xfonts-utils) for the .otb path,
# and python3-venv for the .ttf path -- `make venv` does the rest.

SIZE  := 7x14
FONT  := Smalti$(SIZE)

DEST  := $(HOME)/.local/share/fonts/smalti
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
OTB   := $(FACES:%=build/$(FONT)-%.otb)
TTF   := $(FACES:%=build/$(FONT)-%.ttf)
WOFF2 := $(FACES:%=build/$(FONT)-%.woff2)
BDF   := $(FACES:%=build/$(FONT)-%.bdf)

.PHONY: all install preview show restore clean watch headers index \
        check check-sources check-outlines venv outlines woff2 install-outlines

# The bitmap faces AND the outline faces: an .otb is invisible to fontconfig
# and to every browser, so the .ttf is not an extra, it is how the font
# reaches anything that is not wezterm.
all: $(OTB) outlines

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

BUILDFACE := tools/build-face.py tools/glyphstore.py

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

# fonttosfnt writes a bitmap-only OTB whose scalable metrics do not describe
# the strike; repair-tamzen.py fixes the fields wezterm depends on.
build/%.otb: build/%.bdf tools/repair-tamzen.py
	fonttosfnt -o $@ -- $<
	tools/repair-tamzen.py $@

# Two halves, and `check` is both.  Never let one of them answer to the name
# `check` on its own: a check target that runs half the checks and reports
# success is worse than no check at all, because CI goes green on it.
check: check-sources check-outlines

# The drawings and the built faces (design spec section 9).
check-sources: all
	python3 tools/check-glyphs.py $(SIZE)

headers:
	python3 tools/glyph-headers.py

index:
	python3 tools/glyph-index.py

install: all
	@mkdir -p $(DEST)
	cp build/$(FONT)-Regular.otb $(DEST)/$(FONT)-Regular.otb
	cp build/$(FONT)-Bold.otb $(DEST)/$(FONT)-Bold.otb
	cp build/$(FONT)-Italic.otb $(DEST)/$(FONT)-Italic.otb
	cp build/$(FONT)-BoldItalic.otb $(DEST)/$(FONT)-BoldItalic.otb
	@echo "installed to $(DEST) -- wezterm needs font_dirs and family 'Smalti $(SIZE)'"

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

show: ; @tools/show-new.sh

preview: build/$(FONT)-Regular.bdf $(GEN)
	tools/show-glyphs.py $< glyphs/$(SIZE)/regular build/gen/$(SIZE)/regular

restore:
	cp baseline/Tamzen7x14r.otb $(TAMZEN_DEST)/Tamzen7x14r.otb
	cp baseline/Tamzen7x14b.otb $(TAMZEN_DEST)/Tamzen7x14b.otb
	@echo "upstream Tamzen restored to $(TAMZEN_DEST) -- point wezterm there"

clean:
	rm -f $(BDF) $(OTB) $(TTF) $(WOFF2)
	rm -rf build/gen

# ------------------------------------------------------------------ outlines
#
# The .otb files above are bitmap-only, and a bitmap-only font is invisible to
# most of the system: fontconfig's 70-no-bitmaps-except-emoji.conf rejects
# anything with outline=false, and no browser renders an embedded strike.  So
# each strike is ALSO traced into an outline .ttf -- one file per strike,
# because outlines cannot vary with cell size.  tools/trace-outline.py has the
# reasoning; `make check` proves the trace is exact.
#
# This path does not use fonttosfnt and so does not inherit its broken name
# table either, which is why repair-tamzen.py has no part in it.

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

build/%.ttf: build/%.bdf tools/trace-outline.py | $(VENV)/.stamp
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

# Kept separate from `install`: the .ttf files carry the same family name as
# the .otb files, so putting both in one directory would give wezterm's
# font_dirs two candidates for every face.  Install these where fontconfig
# looks instead, and every other application gets the font too.
install-outlines: outlines
	@mkdir -p $(DEST)-ttf
	cp $(FACES:%=build/Smalti7x14-%.ttf) $(DEST)-ttf/
	@fc-cache -f $(DEST)-ttf >/dev/null 2>&1 || true
	@echo "installed to $(DEST)-ttf -- fontconfig serves family 'Smalti 7x14'"
