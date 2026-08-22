# Smalti 7x14 -- Tamzen 7x14 with 813 extra glyphs, in four faces.
#
#   make            build all four faces into build/, bitmap and outline
#   make outlines   build only the outline .ttf faces
#   make check      prove each .ttf is the same shape as its .bdf strike
#   make preview    show the added glyphs as ASCII art
#   make show       print every added glyph in the terminal
#   make install    copy all four over the fonts wezterm actually loads
#   make watch      rebuild, install and reload on every save
#   make sources    regenerate the derived glyph sources (see below)
#   make restore    put the untouched baselines back
#
# Requires: fonttosfnt (Debian/Ubuntu package xfonts-utils) for the .otb path,
# and python3-venv for the .ttf path -- `make venv` does the rest.

DEST  := $(HOME)/.local/share/fonts/smalti
# `restore` still targets the ORIGINAL Tamzen directory: its job is to give
# you a working terminal back, and after the rename that means pointing
# wezterm at upstream Tamzen, not at a Smalti-named file holding 189 glyphs.
TAMZEN_DEST := $(HOME)/.local/share/fonts/tamzen-patched
WEZCFG := $(HOME)/.config/wezterm/wezterm.lua

REG_SRC  := $(wildcard glyphs/*.txt)
BOLD_SRC := $(wildcard glyphs-bold/*.txt)

FACES := Regular Bold Italic BoldItalic

.PHONY: all install preview show sources restore clean watch \
        venv outlines woff2 check install-outlines

all: $(FACES:%=build/Smalti7x14-%.otb) outlines

build/Smalti7x14-Regular.bdf: upstream/Tamzen7x14r.bdf $(REG_SRC) tools/merge-glyphs.py
	@mkdir -p build
	tools/merge-glyphs.py upstream/Tamzen7x14r.bdf $(REG_SRC) > $@

build/Smalti7x14-Bold.bdf: upstream/Tamzen7x14b.bdf $(BOLD_SRC) tools/merge-glyphs.py
	@mkdir -p build
	tools/merge-glyphs.py upstream/Tamzen7x14b.bdf $(BOLD_SRC) > $@

# The oblique face is sheared from the finished regular BDF, not from the
# glyph sources, so it inherits every glyph automatically and there is no
# glyphs-italic/ to keep in sync.  See tools/slant-bdf.py for the geometry.
# STEPS are the rows where the lean drops a column: above the first the glyph
# moves right, below the last it moves left.  More steps means more lean.
#   make STEPS=4,7,10 install
STEPS := 5,8
build/Smalti7x14-Italic.bdf: build/Smalti7x14-Regular.bdf tools/slant-bdf.py
	tools/slant-bdf.py --steps $(STEPS) $< > $@

# The bold oblique is sheared FIRST and emboldened second: the bold face has
# no side bearing left to lean into.  See tools/slant-bold.py.
build/Smalti7x14-BoldItalic.bdf: build/Smalti7x14-Bold.bdf build/Smalti7x14-Italic.bdf \
                        build/Smalti7x14-Regular.bdf tools/slant-bold.py tools/weight.py
	tools/slant-bold.py build/Smalti7x14-Bold.bdf build/Smalti7x14-Italic.bdf \
	                    build/Smalti7x14-Regular.bdf > $@

# fonttosfnt writes a bitmap-only OTB whose scalable metrics do not describe
# the strike; repair-tamzen.py fixes the four fields wezterm depends on.
build/%.otb: build/%.bdf tools/repair-tamzen.py
	fonttosfnt -o $@ -- $<
	tools/repair-tamzen.py $@

# glyphs/ is hand-written and is the source of truth.  glyphs-bold/ is derived
# from it -- run this after editing a regular glyph, then rebuild.
# latin-ext-a is composed against the BOLD base font, which beats emboldening
# because Tamzen's own bold letters and bold accents already exist.  Every
# other file is derived from its regular counterpart.
sources: glyphs/braille.txt
	@mkdir -p glyphs-bold
	python3 tools/gen-latin-ext-a.py upstream/Tamzen7x14b.bdf glyphs-bold/latin-ext-a.txt
	@for f in $(filter-out glyphs/latin-ext-a.txt,$(REG_SRC)); do \
		python3 tools/embolden.py $$f glyphs-bold/$$(basename $$f) \
		        upstream/Tamzen7x14b.bdf || exit 1; \
	done

glyphs/braille.txt: tools/gen-braille.py
	python3 tools/gen-braille.py

install: all
	@mkdir -p $(DEST)
	cp build/Smalti7x14-Regular.otb $(DEST)/Smalti7x14-Regular.otb
	cp build/Smalti7x14-Bold.otb $(DEST)/Smalti7x14-Bold.otb
	cp build/Smalti7x14-Italic.otb $(DEST)/Smalti7x14-Italic.otb
	cp build/Smalti7x14-BoldItalic.otb $(DEST)/Smalti7x14-BoldItalic.otb
	@echo "installed to $(DEST) -- wezterm needs font_dirs and family 'Smalti 7x14'"

# Rebuild and reload on every save.  Directories are watched, not files,
# because editors replace a file rather than writing into it, which would
# leave a file watch pointing at the old inode.
# Touching the wezterm config triggers wezterm's own automatic config reload,
# which is the same action as pressing Ctrl+Shift+R.
watch:
	@echo "watching glyphs/ and tools/ -- Ctrl-C to stop"
	@while true; do \
		inotifywait -qq -e close_write,moved_to glyphs tools; \
		echo "--- $$(date +%H:%M:%S)"; \
		if $(MAKE) --no-print-directory sources install; then \
			[ -f $(WEZCFG) ] && touch $(WEZCFG) && echo "wezterm reloaded"; \
		else \
			echo "BUILD FAILED -- fonts left untouched, still watching"; \
		fi; \
	done

show: ; @tools/show-new.sh

preview: build/Smalti7x14-Regular.bdf
	tools/show-glyphs.py $< glyphs/extra.txt

restore:
	cp baseline/Tamzen7x14r.otb $(TAMZEN_DEST)/Tamzen7x14r.otb
	cp baseline/Tamzen7x14b.otb $(TAMZEN_DEST)/Tamzen7x14b.otb
	@echo "upstream Tamzen restored to $(TAMZEN_DEST) -- point wezterm there"

clean:
	rm -f $(FACES:%=build/Smalti7x14-%.bdf) $(FACES:%=build/Smalti7x14-%.otb) \
	      $(FACES:%=build/Smalti7x14-%.ttf) $(FACES:%=build/Smalti7x14-%.woff2)

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

outlines: $(FACES:%=build/Smalti7x14-%.ttf)
woff2:    $(FACES:%=build/Smalti7x14-%.woff2)

build/%.ttf: build/%.bdf tools/trace-outline.py | $(VENV)/.stamp
	$(PY) tools/trace-outline.py $< $@

build/%.woff2: build/%.ttf | $(VENV)/.stamp
	$(VENV)/bin/fonttools ttLib.woff2 compress -o $@ $<

# Every glyph of every face: filled area against lit pixel count, then the
# rendered raster against the bitmap at 1x, 2x and 3x.
check: outlines
	$(PY) tools/check-outlines.py \
	    $(foreach f,$(FACES),build/Smalti7x14-$(f).bdf build/Smalti7x14-$(f).ttf)
	@for f in $(FACES); do \
		$(PY) tools/render-check.py build/Smalti7x14-$$f.bdf \
		      build/Smalti7x14-$$f.ttf || exit 1; \
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
