# Tamzen 7x14 with extra glyphs, regular and bold.
#
#   make            build both faces into build/
#   make preview    show the added glyphs as ASCII art
#   make show       print every added glyph in the terminal
#   make install    copy both over the fonts wezterm actually loads
#   make watch      rebuild, install and reload on every save
#   make sources    regenerate the derived glyph sources (see below)
#   make restore    put the untouched baselines back
#
# Requires: fonttosfnt (Debian/Ubuntu package xfonts-utils).

DEST  := $(HOME)/.local/share/fonts/tamzen-patched
WEZCFG := $(HOME)/.config/wezterm/wezterm.lua

REG_SRC  := $(wildcard glyphs/*.txt)
BOLD_SRC := $(wildcard glyphs-bold/*.txt)

.PHONY: all install preview show sources restore clean watch

all: build/Tamzen7x14r.otb build/Tamzen7x14b.otb

build/Tamzen7x14r.bdf: upstream/Tamzen7x14r.bdf $(REG_SRC) tools/merge-glyphs.py
	@mkdir -p build
	tools/merge-glyphs.py upstream/Tamzen7x14r.bdf $(REG_SRC) > $@

build/Tamzen7x14b.bdf: upstream/Tamzen7x14b.bdf $(BOLD_SRC) tools/merge-glyphs.py
	@mkdir -p build
	tools/merge-glyphs.py upstream/Tamzen7x14b.bdf $(BOLD_SRC) > $@

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
	cp build/Tamzen7x14r.otb $(DEST)/Tamzen7x14r.otb
	cp build/Tamzen7x14b.otb $(DEST)/Tamzen7x14b.otb
	@echo "installed -- reload wezterm with Ctrl+Shift+R"

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

preview: build/Tamzen7x14r.bdf
	tools/show-glyphs.py $< glyphs/extra.txt

restore:
	cp baseline/Tamzen7x14r.otb $(DEST)/Tamzen7x14r.otb
	cp baseline/Tamzen7x14b.otb $(DEST)/Tamzen7x14b.otb
	@echo "baselines restored -- reload wezterm with Ctrl+Shift+R"

clean:
	rm -f build/Tamzen7x14r.bdf build/Tamzen7x14r.otb \
	      build/Tamzen7x14b.bdf build/Tamzen7x14b.otb
