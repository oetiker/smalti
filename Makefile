# Tamzen 7x14 with extra glyphs.
#
#   make           build build/Tamzen7x14r.otb
#   make install   copy it over the font wezterm actually loads
#   make preview   show every added glyph as ASCII art
#   make restore   put the untouched baseline back
#
# Requires: fonttosfnt (Debian/Ubuntu package xfonts-utils).

BASE  := upstream/Tamzen7x14r.bdf
EXTRA := $(wildcard glyphs/*.txt)
OUT   := build/Tamzen7x14r
DEST  := $(HOME)/.local/share/fonts/tamzen-patched
WEZCFG := $(HOME)/.config/wezterm/wezterm.lua

.PHONY: all install preview show restore clean watch

all: $(OUT).otb

$(OUT).bdf: $(BASE) $(EXTRA) tools/merge-glyphs.py
	@mkdir -p build
	tools/merge-glyphs.py $(BASE) $(EXTRA) > $@

# fonttosfnt writes a bitmap-only OTB whose scalable metrics do not describe
# the strike; repair-tamzen.py fixes the four fields wezterm depends on.
$(OUT).otb: $(OUT).bdf tools/repair-tamzen.py
	fonttosfnt -o $@ -- $<
	tools/repair-tamzen.py $@

install: $(OUT).otb
	cp $(OUT).otb $(DEST)/Tamzen7x14r.otb
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
		if $(MAKE) --no-print-directory install; then \
			[ -f $(WEZCFG) ] && touch $(WEZCFG) && echo "wezterm reloaded"; \
		else \
			echo "BUILD FAILED -- font left untouched, still watching"; \
		fi; \
	done

show: ; @tools/show-new.sh

preview: $(OUT).bdf
	tools/show-glyphs.py $(OUT).bdf $(EXTRA)

restore:
	cp baseline/Tamzen7x14r.otb $(DEST)/Tamzen7x14r.otb
	@echo "baseline restored -- reload wezterm with Ctrl+Shift+R"

clean:
	rm -f $(OUT).bdf $(OUT).otb
