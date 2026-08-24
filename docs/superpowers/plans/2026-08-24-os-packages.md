# OS Packages (.deb and .rpm) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **This repository's owner does not permit subagents unless they ask for them.** Default to `superpowers:executing-plans` here.

**Goal:** Ship a `.deb` and an `.rpm` as GitHub release assets, so Smalti can be installed and removed by a package manager instead of by hand.

**Architecture:** One pinned `nfpm` binary, downloaded and hash-checked into `build/`, reads one `packaging/nfpm.yaml` twice with different environment variables and emits both formats. A new `tools/check-packages.py` opens the results with `dpkg-deb` and `rpm` — the package managers' own tools, never a reader of ours — and proves the `.ttf` files inside are byte-identical to the ones `make check` already validated. Packaging is reachable only from its own targets, so the font build keeps its `python3-venv`-only dependency list.

**Tech Stack:** GNU make, nfpm 2.47.0, Python 3.12 (stdlib only for the checker), `dpkg-deb`, `rpm`, `rpm2cpio`, `cpio`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-os-packages-design.md`

## Global Constraints

- **Nothing in this plan may be reachable from `make all`, `make check`, `make outlines` or `make woff2`.** The font build's entire dependency list stays `python3-venv`.
- **A check must fail when there is nothing to check.** Never skip, never pass quietly. If `dpkg-deb` or `rpm` is missing, the target fails and names the package to install.
- **Every fault-injection case must be confirmed to trip its own rule**, not merely to make the suite red. A case that fails for an unrelated reason reads as coverage and is not.
- **Fault-inject with a fresh artefact every time.** Never edit a package in place and reuse it.
- **The build is byte-reproducible and that is load-bearing.** Nothing may put a clock or a hash seed into an artefact.
- Pinned values, copied verbatim:
  - `NFPM_VERSION := 2.47.0`
  - `NFPM_SHA256 := 0660ca602b2d2d2ae4781a06c692b3eeb9d437ffea05b831d76e41f4a3188783`
  - deb package name `fonts-smalti`, arch `all`, fonts at `/usr/share/fonts/truetype/smalti`
  - rpm package name `smalti-fonts`, arch `noarch`, fonts at `/usr/share/fonts/smalti`
  - rpm `License:` tag is `LicenseRef-Tamsyn`
  - maintainer `Tobias Oetiker <tobi@oetiker.ch>`
  - no maintainer scripts in either package; `fontconfig` is **recommended**, never depended on
- **Refinement of spec §5:** both packages carry a package release of `1`, so the file names are `fonts-smalti_<version>-1_all.deb` and `smalti-fonts-<version>-1.noarch.rpm`. The spec wrote the deb without `-1`; `rpm` requires a release field and matching them keeps one config.
- **Resolution of spec risk §14.2:** the differing font directory is supplied through the `PKG_FONTDIR` environment variable, not through nfpm's `overrides:` block. Env-var expansion is a documented nfpm feature and covers every field, so the fallback to a shared `/usr/share/fonts/smalti/` is not needed.

## File Structure

| File | Responsibility |
|---|---|
| `Makefile` (new section) | pin and fetch nfpm; `deb`, `rpm`, `packages`, `check-packages` targets |
| `packaging/nfpm.yaml` (create) | the single package description, parameterised by environment |
| `tools/check-packages.py` (create) | open both packages with the distributions' tools and prove their contents |
| `tools/test-check-packages.py` (create) | fault-injection suite: break each rule, insist the checker notices |
| `.github/workflows/build.yml` (modify) | a `packages` job on every pull request |
| `.github/workflows/release-publish.yml` (modify) | a `publish-packages` job, and `publish-packages` added to `finalize`'s `needs:` |
| `README.md` (modify) | how to install from a package |
| `RELEASING.md` (modify) | the hand-maintained `needs:` list now has a second entry |
| `CHANGES.md` (modify) | one `### New` entry |

---

### Task 1: Pin and fetch nfpm

**Files:**
- Modify: `Makefile` (new section at the end)

**Interfaces:**
- Consumes: nothing
- Produces: `$(NFPM)` — the make variable holding the path `build/nfpm`, an executable binary. Tasks 2 and 3 use it as an order-only prerequisite.

- [ ] **Step 1: Write the failing test**

There is no test file for this; the test is a fault injection run from the shell, which works because the hash is a make variable and make lets you override one on the command line.

```bash
# The test: a wrong hash must stop the build, loudly.
rm -f build/nfpm
make build/nfpm NFPM_SHA256=0000000000000000000000000000000000000000000000000000000000000000
```

- [ ] **Step 2: Run it to verify it fails for the right reason**

Run the command above.
Expected before Task 1 exists: `make: *** No rule to make target 'build/nfpm'.  Stop.`
That is the failing state. It must later fail with a checksum error instead, which is a different failure — read the message, do not just check the exit code.

- [ ] **Step 3: Write the minimal implementation**

Append to `Makefile`:

```make
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
```

Add `nfpm` to the `.PHONY` line? **No** — `build/nfpm` is a real file, not a phony target.

- [ ] **Step 4: Run the test to verify it now fails correctly**

```bash
rm -f build/nfpm
make build/nfpm NFPM_SHA256=0000000000000000000000000000000000000000000000000000000000000000
```
Expected: `build/nfpm_2.47.0_Linux_x86_64.tar.gz: FAILED` followed by `sha256sum: WARNING: 1 computed checksum did NOT match`, and make exits non-zero. `build/nfpm` must not exist afterwards.

- [ ] **Step 5: Verify the real hash works**

```bash
make build/nfpm && build/nfpm --version
```
Expected: nfpm prints version `2.47.0`.

- [ ] **Step 6: Add build/nfpm to clean and to .gitignore**

In the `clean` recipe, add:
```make
	rm -f build/nfpm build/nfpm_*.tar.gz
```
Check `.gitignore` already ignores `build/`; if it does, nothing to add.

- [ ] **Step 7: Commit**

```bash
git add Makefile .gitignore
git commit -m "Pin nfpm, and refuse the download that is not it"
```

---

### Task 2: One description, two packages

**Files:**
- Create: `packaging/nfpm.yaml`
- Modify: `Makefile` (packages section)

**Interfaces:**
- Consumes: `$(NFPM)` from Task 1; `$(TTF)` — the four built `.ttf` paths, already defined near the top of the Makefile as `build/Smalti7x14-<Face>.ttf`.
- Produces: make variables `$(DEB)` and `$(RPM)` holding the two output paths, and phony targets `deb`, `rpm`, `packages`. Task 3 checks these two files; Tasks 5 and 6 build them in CI.

- [ ] **Step 1: Write the failing test**

The test is that both files build and are the format they claim:

```bash
make packages
dpkg-deb --info build/fonts-smalti_0.1.0-1_all.deb | head -20
rpm -qp --info build/smalti-fonts-0.1.0-1.noarch.rpm
```

- [ ] **Step 2: Run it to verify it fails**

Run `make packages`.
Expected: `make: *** No rule to make target 'packages'.  Stop.`

- [ ] **Step 3: Create the package description**

Create `packaging/nfpm.yaml`:

```yaml
# One description, two packages.  The Makefile invokes nfpm twice with
# different environment variables, because the two ecosystems disagree about
# the package name, the architecture word and the font directory, and nfpm has
# a single global `name:` field.  Environment expansion covers every field;
# nfpm's `overrides:` block does not, which is why it is not used.
#
# NO SCRIPTLETS.  Both distributions' fontconfig packages carry triggers that
# rebuild the font cache when files appear under /usr/share/fonts.  A
# hand-written fc-cache postinst runs at the wrong moment relative to that
# trigger and is one more thing that can fail on a machine that is not ours.
#
# fontconfig is RECOMMENDED, not depended on: a font is usable by consumers
# that never touch fontconfig, and where fontconfig is absent there is no
# cache to refresh.  Debian's own font packages depend on nothing for this.

name: "${PKG_NAME}"
arch: "${PKG_ARCH}"
platform: "linux"
version: "${PKG_VERSION}"
release: "1"
section: "fonts"
priority: "optional"
maintainer: "Tobias Oetiker <tobi@oetiker.ch>"
homepage: "https://github.com/oetiker/smalti"
# Tamsyn's licence is a custom permissive text, not a standard SPDX
# identifier, so this names it rather than approximating it.  The full text
# ships in the package.
license: "LicenseRef-Tamsyn"
description: |
  pixel terminal font with wide Unicode coverage
  Smalti is a bitmap terminal font delivered as outlines: the em is a whole
  number of pixels, so a rasteriser reproduces the drawing exactly at the
  drawn size and every whole multiple of it.
  .
  It is a fork of Tamzen 7x14, which has 189 glyphs and nothing above U+00FF.
  Smalti adds 815 more and draws two faces upstream never had, so each of its
  four faces carries 1004 glyphs.

recommends:
  - fontconfig

contents:
  - src: build/Smalti7x14-Regular.ttf
    dst: ${PKG_FONTDIR}/Smalti7x14-Regular.ttf
  - src: build/Smalti7x14-Bold.ttf
    dst: ${PKG_FONTDIR}/Smalti7x14-Bold.ttf
  - src: build/Smalti7x14-Italic.ttf
    dst: ${PKG_FONTDIR}/Smalti7x14-Italic.ttf
  - src: build/Smalti7x14-BoldItalic.ttf
    dst: ${PKG_FONTDIR}/Smalti7x14-BoldItalic.ttf
  - src: README.md
    dst: /usr/share/doc/${PKG_NAME}/README.md
  - src: LICENSE.tamzen
    dst: /usr/share/doc/${PKG_NAME}/LICENSE.tamzen
```

- [ ] **Step 4: Add the Makefile targets**

Append to the packages section of `Makefile`:

```make
# Read once, here, so the two recipes and the file names cannot disagree.
PKG_VERSION := $(shell cat VERSION)
DEB := build/fonts-smalti_$(PKG_VERSION)-1_all.deb
RPM := build/smalti-fonts-$(PKG_VERSION)-1.noarch.rpm

packages: $(DEB) $(RPM)
deb: $(DEB)
rpm: $(RPM)

# The .ttf files are prerequisites, so a package can never be built from a
# stale face.  nfpm is order-only: re-downloading it must not rebuild a
# package that is otherwise current.
$(DEB): $(TTF) packaging/nfpm.yaml README.md LICENSE.tamzen VERSION | $(NFPM)
	PKG_NAME=fonts-smalti PKG_ARCH=all PKG_VERSION=$(PKG_VERSION) \
	PKG_FONTDIR=/usr/share/fonts/truetype/smalti \
	$(NFPM) package -f packaging/nfpm.yaml -p deb -t $@

$(RPM): $(TTF) packaging/nfpm.yaml README.md LICENSE.tamzen VERSION | $(NFPM)
	PKG_NAME=smalti-fonts PKG_ARCH=noarch PKG_VERSION=$(PKG_VERSION) \
	PKG_FONTDIR=/usr/share/fonts/smalti \
	$(NFPM) package -f packaging/nfpm.yaml -p rpm -t $@
```

Add `deb rpm packages` to the existing `.PHONY:` list. Add to `clean`:
```make
	rm -f build/*.deb build/*.rpm
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
make packages
dpkg-deb --info build/fonts-smalti_0.1.0-1_all.deb
rpm -qp --info build/smalti-fonts-0.1.0-1.noarch.rpm
```
Expected: the deb reports `Package: fonts-smalti`, `Architecture: all`, `Recommends: fontconfig`. The rpm reports `Name: smalti-fonts`, `Architecture: noarch`, `License: LicenseRef-Tamsyn`.

If `rpm` is not installed, `sudo apt install rpm` first. Note the second half of Task 3 Step 8 — the checker must fail rather than skip when it is missing.

- [ ] **Step 6: Update the Makefile's header comment**

Add to the target list at the top of `Makefile`:
```make
#   make packages   build the .deb and the .rpm into build/
#   make check-packages  open both and prove what is inside them
```

- [ ] **Step 7: Commit**

```bash
git add Makefile packaging/nfpm.yaml
git commit -m "Two packages from one description"
```

---

### Task 3: Prove what is inside the packages

**Files:**
- Create: `tools/check-packages.py`
- Create: `tools/test-check-packages.py`
- Modify: `Makefile` (add `check-packages`)

**Interfaces:**
- Consumes: `$(DEB)`, `$(RPM)` from Task 2; the built `.ttf` files in `build/`.
- Produces: `tools/check-packages.py <deb> <rpm>` — exits 0 when both packages are correct, non-zero with a named reason otherwise. Task 5 and Task 6 run it through `make check-packages`.

- [ ] **Step 1: Write the failing test**

Create `tools/test-check-packages.py`. It builds a fresh package for every case, breaks exactly one thing, and insists the checker notices *that* thing.

```python
#!/usr/bin/env python3
"""Fault injection for check-packages.py.

A green check means nothing unless the checker underneath it can go red.  Each
case below breaks one rule and asserts the checker fails FOR THAT RULE -- the
expected substring is part of the test, not decoration.  A case that fails for
an unrelated reason reads as coverage and is not.

Every case builds its own package from scratch.  Editing a package in place and
reusing it is how a previous fault-injection harness in this repository ended up
copying files onto themselves and reporting nothing.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "check-packages.py"
FACES = ["Regular", "Bold", "Italic", "BoldItalic"]


def need(tool):
    if shutil.which(tool) is None:
        sys.exit(f"{tool} is required to run this suite -- install it "
                 f"(Debian/Ubuntu: sudo apt install rpm dpkg cpio)")


def build(workdir, *, yaml_extra="", drop_face=None, version="0.1.0",
          fontdir="/usr/share/fonts/truetype/smalti", name="fonts-smalti",
          packager="deb", corrupt_face=None):
    """Build one package into workdir and return its path.

    Everything a case wants to break is a parameter, so no case edits a
    finished package.
    """
    stage = workdir / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "build").mkdir(exist_ok=True)
    for face in FACES:
        if face == drop_face:
            continue
        src = ROOT / "build" / f"Smalti7x14-{face}.ttf"
        dst = stage / "build" / f"Smalti7x14-{face}.ttf"
        data = src.read_bytes()
        if face == corrupt_face:
            data = data + b"\x00"      # a byte the built face does not have
        dst.write_bytes(data)
    for doc in ("README.md", "LICENSE.tamzen"):
        shutil.copy2(ROOT / doc, stage / doc)

    contents = []
    for face in FACES:
        if face == drop_face:
            continue
        contents.append(
            f"  - src: build/Smalti7x14-{face}.ttf\n"
            f"    dst: {fontdir}/Smalti7x14-{face}.ttf\n")
    for doc in ("README.md", "LICENSE.tamzen"):
        contents.append(f"  - src: {doc}\n    dst: /usr/share/doc/{name}/{doc}\n")

    yaml = (
        f"name: {name}\n"
        f"arch: {'all' if packager == 'deb' else 'noarch'}\n"
        f"platform: linux\n"
        f"version: {version}\n"
        f"release: '1'\n"
        f"section: fonts\n"
        f"priority: optional\n"
        f"maintainer: Tobias Oetiker <tobi@oetiker.ch>\n"
        f"license: LicenseRef-Tamsyn\n"
        f"description: test build\n"
        f"recommends:\n  - fontconfig\n"
        f"{yaml_extra}"
        f"contents:\n" + "".join(contents))
    (stage / "nfpm.yaml").write_text(yaml)

    out = workdir / ("pkg.deb" if packager == "deb" else "pkg.rpm")
    subprocess.run(
        [str(ROOT / "build" / "nfpm"), "package", "-f", "nfpm.yaml",
         "-p", packager, "-t", str(out)],
        cwd=stage, check=True, capture_output=True)
    return out


def expect_fail(label, expected, deb=None, rpm=None):
    cmd = [sys.executable, str(CHECKER)]
    cmd += ["--deb", str(deb)] if deb else []
    cmd += ["--rpm", str(rpm)] if rpm else []
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode == 0:
        sys.exit(f"FAIL {label}: checker passed a broken package")
    if expected not in out:
        sys.exit(f"FAIL {label}: checker failed, but not for its own reason.\n"
                 f"  wanted substring: {expected!r}\n  got:\n{out}")
    print(f"ok   {label}")


def main():
    for tool in ("dpkg-deb", "rpm", "rpm2cpio", "cpio"):
        need(tool)
    if not (ROOT / "build" / "nfpm").exists():
        sys.exit("build/nfpm missing -- run `make build/nfpm` first")
    if not all((ROOT / "build" / f"Smalti7x14-{f}.ttf").exists() for f in FACES):
        sys.exit("the four .ttf faces are missing -- run `make` first")

    with tempfile.TemporaryDirectory(dir=ROOT / "build") as tmp:
        tmp = Path(tmp)

        # 1 -- a good package must pass, or every case below proves nothing.
        good_deb = build(tmp / "c0", packager="deb")
        good_rpm = build(tmp / "c0r", packager="rpm", name="smalti-fonts",
                         fontdir="/usr/share/fonts/smalti")
        r = subprocess.run([sys.executable, str(CHECKER), "--deb", str(good_deb),
                            "--rpm", str(good_rpm)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"FAIL baseline: a correct pair was rejected\n{r.stdout}{r.stderr}")
        print("ok   baseline (a correct pair passes)")

        # 2 -- a face whose bytes are not the built face's bytes
        expect_fail("corrupt face", "does not match build/",
                    deb=build(tmp / "c1", packager="deb", corrupt_face="Bold"))

        # 3 -- three faces instead of four
        expect_fail("missing face", "expected 4 .ttf",
                    deb=build(tmp / "c2", packager="deb", drop_face="Italic"))

        # 4 -- right files, wrong directory
        expect_fail("wrong font directory", "unexpected path",
                    deb=build(tmp / "c3", packager="deb",
                              fontdir="/usr/share/fonts/smalti"))

        # 5 -- a version that is not VERSION
        expect_fail("wrong version", "version",
                    deb=build(tmp / "c4", packager="deb", version="9.9.9"))

        # 6 -- a maintainer script, which this package must never carry
        script = tmp / "postinst.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("#!/bin/sh\nfc-cache -f\n")
        expect_fail("maintainer script", "must carry no maintainer scripts",
                    deb=build(tmp / "c5", packager="deb",
                              yaml_extra=f"scripts:\n  postinstall: {script}\n"))

        # 7 -- the same rules on the rpm side, not just the deb
        expect_fail("rpm corrupt face", "does not match build/",
                    rpm=build(tmp / "c6", packager="rpm", name="smalti-fonts",
                              fontdir="/usr/share/fonts/smalti",
                              corrupt_face="Regular"))

    print("\nall cases red for their own reason")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
make && make build/nfpm
.venv/bin/python tools/test-check-packages.py
```
Expected: it dies because `tools/check-packages.py` does not exist yet — a `FileNotFoundError`, or every case reporting the checker "failed" for the wrong reason. Either is the correct failing state.

- [ ] **Step 3: Write the checker**

Create `tools/check-packages.py`:

```python
#!/usr/bin/env python3
"""Open the built packages with the package managers' own tools and prove
what is inside them.

Read with dpkg-deb and rpm, never with a reader of ours: our own writer
checked by our own reader is the self-confirming check this project has
already been bitten by five times.

The .ttf files are compared byte for byte against build/, which `make check`
has already proved carry the right version, metrics and outlines.  This
inherits that guarantee rather than restating it.

If a tool is missing this FAILS and names the package to install.  It does not
skip.  A check that skips its job and reports success is the recurring bug
class in this repository.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACES = ["Regular", "Bold", "Italic", "BoldItalic"]
DEB_FONTDIR = "/usr/share/fonts/truetype/smalti"
RPM_FONTDIR = "/usr/share/fonts/smalti"
DEB_NAME = "fonts-smalti"
RPM_NAME = "smalti-fonts"

problems = []


def fail(msg):
    problems.append(msg)


def require(tool, apt):
    if shutil.which(tool) is None:
        sys.exit(f"{tool} is required and is not installed.  "
                 f"Debian/Ubuntu: sudo apt install {apt}")


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def version():
    return (ROOT / "VERSION").read_text().strip()


def compare_tree(root, fontdir, pkgname, label):
    """root is an extracted package.  Prove the five properties."""
    fonts = sorted((root / fontdir.lstrip("/")).glob("*.ttf")) \
        if (root / fontdir.lstrip("/")).is_dir() else []

    # every .ttf anywhere in the package, so a file in the wrong place is
    # caught rather than silently ignored
    everywhere = sorted(root.rglob("*.ttf"))
    for f in everywhere:
        if f not in fonts:
            fail(f"{label}: unexpected path for {f.name}: /{f.relative_to(root)}")

    if len(fonts) != 4:
        fail(f"{label}: expected 4 .ttf under {fontdir}, found {len(fonts)}")

    for face in FACES:
        built = ROOT / "build" / f"Smalti7x14-{face}.ttf"
        inside = root / fontdir.lstrip("/") / f"Smalti7x14-{face}.ttf"
        if not inside.exists():
            fail(f"{label}: {inside.name} is not in the package")
            continue
        if inside.read_bytes() != built.read_bytes():
            fail(f"{label}: {inside.name} does not match build/{built.name}")

    for doc in ("README.md", "LICENSE.tamzen"):
        if not (root / "usr/share/doc" / pkgname / doc).exists():
            fail(f"{label}: {doc} is missing from /usr/share/doc/{pkgname}/")


def check_deb(path):
    require("dpkg-deb", "dpkg")
    info = run(["dpkg-deb", "--info", str(path)])
    if f"Package: {DEB_NAME}" not in info:
        fail(f"deb: package name is not {DEB_NAME}")
    if f"Version: {version()}-1" not in info:
        fail(f"deb: version is not {version()}-1")
    if "Architecture: all" not in info:
        fail("deb: architecture is not all")

    # dpkg-deb --info lists the control files it found; a maintainer script
    # shows up there.
    for script in ("preinst", "postinst", "prerm", "postrm"):
        if f"/{script}" in info:
            fail(f"deb: must carry no maintainer scripts, found {script}")

    with tempfile.TemporaryDirectory() as tmp:
        run(["dpkg-deb", "-x", str(path), tmp])
        compare_tree(Path(tmp), DEB_FONTDIR, DEB_NAME, "deb")


def check_rpm(path):
    require("rpm", "rpm")
    require("rpm2cpio", "rpm")
    require("cpio", "cpio")
    info = run(["rpm", "-qp", "--queryformat",
                "%{NAME}\n%{VERSION}\n%{RELEASE}\n%{ARCH}\n%{LICENSE}\n", str(path)])
    name, ver, rel, arch, lic = info.strip().split("\n")[:5]
    if name != RPM_NAME:
        fail(f"rpm: package name is {name}, not {RPM_NAME}")
    if ver != version():
        fail(f"rpm: version is {ver}, not {version()}")
    if rel != "1":
        fail(f"rpm: release is {rel}, not 1")
    if arch != "noarch":
        fail(f"rpm: architecture is {arch}, not noarch")
    if lic != "LicenseRef-Tamsyn":
        fail(f"rpm: license is {lic}, not LicenseRef-Tamsyn")

    scripts = run(["rpm", "-qp", "--scripts", str(path)]).strip()
    if scripts:
        fail(f"rpm: must carry no maintainer scripts, found:\n{scripts}")

    with tempfile.TemporaryDirectory() as tmp:
        cpio = subprocess.run(["rpm2cpio", str(path)], check=True, capture_output=True)
        subprocess.run(["cpio", "-idm", "--quiet"], input=cpio.stdout,
                       cwd=tmp, check=True)
        compare_tree(Path(tmp), RPM_FONTDIR, RPM_NAME, "rpm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deb")
    ap.add_argument("--rpm")
    args = ap.parse_args()

    if not args.deb and not args.rpm:
        sys.exit("nothing to check: pass --deb and/or --rpm")

    for face in FACES:
        built = ROOT / "build" / f"Smalti7x14-{face}.ttf"
        if not built.exists():
            sys.exit(f"{built} is missing -- there is nothing to compare the "
                     f"package against.  Run `make` first.")

    if args.deb:
        check_deb(Path(args.deb))
    if args.rpm:
        check_rpm(Path(args.rpm))

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        sys.exit(1)
    print("packages ok")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the suite and read every line**

```bash
.venv/bin/python tools/test-check-packages.py
```
Expected: `ok baseline`, then `ok` for each of the six broken cases, then `all cases red for their own reason`.

If a case reports "failed, but not for its own reason", fix the checker or the expected substring — do not weaken the substring to make it pass. That is the whole point of the case.

- [ ] **Step 5: Confirm each case independently**

For at least the corrupt-face and the maintainer-script cases, comment out the corresponding rule in `check-packages.py`, re-run, and confirm **only that case** goes from `ok` to `FAIL`. Restore the rule. A case that stays red with its rule removed was never testing that rule.

- [ ] **Step 6: Add the make target**

Append to the packages section of `Makefile`:

```make
# Read with the package managers' own tools, and prove the .ttf files inside
# are the ones `make check` already validated.  The self-test runs FIRST and
# is not optional, for the same reason check-sources runs its own first.
check-packages: packages
	$(PY) tools/test-check-packages.py
	$(PY) tools/check-packages.py --deb $(DEB) --rpm $(RPM)
```

Add `check-packages` to `.PHONY`.

- [ ] **Step 7: Run it**

```bash
make check-packages
```
Expected: the suite's `ok` lines, then `packages ok`.

- [ ] **Step 8: Prove it fails when a tool is missing**

```bash
# Hide every tool by pointing PATH at an empty directory, then confirm the
# checker dies rather than skipping.
mkdir -p /scratch/oetiker/claude-tmp/emptybin
env PATH=/scratch/oetiker/claude-tmp/emptybin \
    .venv/bin/python tools/check-packages.py \
    --rpm build/smalti-fonts-0.1.0-1.noarch.rpm
```
Expected: `rpm is required and is not installed.  Debian/Ubuntu: sudo apt install rpm`, exit non-zero. **Not** a pass, and not a skip.

- [ ] **Step 9: Commit**

```bash
git add tools/check-packages.py tools/test-check-packages.py Makefile
git commit -m "Open the packages with the package managers' own tools"
```

---

### Task 4: Prove reproducibility, or name the gap

**Files:**
- Modify: possibly `packaging/nfpm.yaml`, `README.md`, `.github/workflows/build.yml`

**Interfaces:**
- Consumes: `make packages` from Task 2.
- Produces: either a demonstrated byte-identity guarantee, or a named gap. Task 5's job text depends on which.

- [ ] **Step 1: Run the test**

```bash
export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
make clean && make && make packages
mkdir -p /scratch/oetiker/claude-tmp/pkgrepro && cp build/*.deb build/*.rpm /scratch/oetiker/claude-tmp/pkgrepro/
make clean && make && make packages
for f in build/*.deb build/*.rpm; do cmp "$f" "/scratch/oetiker/claude-tmp/pkgrepro/$(basename $f)" && echo "IDENTICAL $(basename $f)"; done
```
Expected if nfpm behaves: two `IDENTICAL` lines.

- [ ] **Step 2: If they differ, find out where**

```bash
dpkg-deb --contents build/fonts-smalti_0.1.0-1_all.deb | head
```
Compare the timestamps in the two listings. If the mtimes move, add an explicit `mtime` to `packaging/nfpm.yaml` derived from `SOURCE_DATE_EPOCH`, and re-run Step 1.

- [ ] **Step 3: If they still differ, name the gap — do not hide it**

This is the designed fallback, not a failure of the task. Add to `README.md` under "Known gaps" the sentence: *"The `.deb` and `.rpm` are not byte-reproducible: nfpm embeds a value that moves between builds. The `.ttf` files inside them are, and `make check-packages` proves they are the checked ones."*

And in Task 5's job, after `make check-packages`, add:
```yaml
      - name: say what is not proven
        run: echo "::warning::packages are not byte-reproducible -- see README, Known gaps"
```

- [ ] **Step 4: Report the finding before continuing**

Tell the user which branch happened. This is the one thing in the design that was written down as "prove, do not assume", and the answer changes what the repository claims about itself.

- [ ] **Step 5: Commit whichever change resulted**

```bash
git add -A
git commit -m "Packages reproduce byte for byte"   # or: "Name the gap: packages do not reproduce"
```

---

### Task 5: A packages job on every pull request

**Files:**
- Modify: `.github/workflows/build.yml`

**Interfaces:**
- Consumes: `make check-packages` from Task 3.
- Produces: a `packages` job whose green state means the packages build and their contents are proved.

- [ ] **Step 1: Read the existing build job first**

```bash
sed -n '1,130p' .github/workflows/build.yml
```
Match its style: it supplies a machine and calls make. Do not duplicate build logic into YAML.

- [ ] **Step 2: Add the job**

Append to `.github/workflows/build.yml`:

```yaml
  # The OS packages.  This is the ONE place in the repository that installs an
  # apt package, and it buys an honest check rather than a decorative one: the
  # only trustworthy test of an .rpm is `rpm -qp` on the real file, and our own
  # reader checking our own writer would prove nothing.
  #
  # It is a separate job, not a step in `build`, so that the font build's green
  # state keeps meaning "the fonts are fine" with no packaging tooling involved.
  packages:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'

      # rpm brings rpm2cpio; cpio is separate and the checker needs both to
      # unpack the .rpm.  dpkg-deb is already on the runner.
      - name: rpm tooling
        run: sudo apt-get update && sudo apt-get install -y --no-install-recommends rpm cpio

      - name: python dependencies
        run: make venv

      - name: build the fonts and the packages
        run: |
          set -euo pipefail
          SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
          export SOURCE_DATE_EPOCH
          make
          make packages

      - name: prove what is inside them
        run: make check-packages

      - uses: actions/upload-artifact@v7
        with:
          name: packages
          path: |
            build/*.deb
            build/*.rpm
```

- [ ] **Step 3: Push and watch it**

```bash
git add .github/workflows/build.yml
git commit -m "Prove the packages on every pull request"
git push
gh pr checks
```
Expected: a `packages` check appears and passes. If the repository ruleset requires named checks, adding a job does not change the required list — this one is informative until someone requires it.

- [ ] **Step 4: Confirm the job can go red**

Temporarily break one thing — for example change `DEB_NAME` in `tools/check-packages.py` to `fonts-smalty` — push, confirm the job fails, then revert. A CI job that has never been red is a job nobody has tested.

- [ ] **Step 5: Commit the revert**

```bash
git add -A && git commit -m "Revert the deliberate break"
```

---

### Task 6: Attach the packages to the release

**Files:**
- Modify: `.github/workflows/release-publish.yml`
- Modify: `RELEASING.md`
- Modify: `README.md`
- Modify: `CHANGES.md`

**Interfaces:**
- Consumes: `make packages`, `make check-packages`.
- Produces: two more assets on every GitHub release.

- [ ] **Step 1: Add the publish-packages job**

In `.github/workflows/release-publish.yml`, after the `publish-fonts` job and before `finalize`, add:

```yaml
  # A publish add-on, following the seam repo-infra defines: needs `publish`,
  # consumes its version/tag/release_id, builds from the tagged commit and
  # attaches to the DRAFT release.  If this fails, finalize does not run and
  # the release stays a draft -- the correct outcome, not a bug.
  publish-packages:
    name: Attach the OS packages
    needs: [publish]
    if: needs.publish.outputs.release_id != ''
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'

      - name: rpm tooling
        run: sudo apt-get update && sudo apt-get install -y --no-install-recommends rpm cpio

      - name: python dependencies
        run: make venv

      - name: build the packages
        run: |
          set -euo pipefail
          SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
          export SOURCE_DATE_EPOCH
          echo "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH"
          make
          make packages

      # A release must not ship a package the checks have not passed.
      - name: check
        run: make check-packages

      - name: attach them to the draft release
        uses: actions/github-script@v9
        with:
          script: |
            const fs = require('fs');
            const path = require('path');
            const dir = `${process.env.GITHUB_WORKSPACE}/build`;
            const TYPES = {
              '.deb': 'application/vnd.debian.binary-package',
              '.rpm': 'application/x-rpm',
            };
            const files = fs.readdirSync(dir)
              .filter(f => f.endsWith('.deb') || f.endsWith('.rpm')).sort();
            if (files.length !== 2) {
              core.setFailed(`expected one .deb and one .rpm, found ${files.length}`);
              return;
            }
            for (const name of files) {
              const data = fs.readFileSync(path.join(dir, name));
              const { data: asset } = await github.rest.repos.uploadReleaseAsset({
                owner: context.repo.owner,
                repo: context.repo.repo,
                release_id: Number('${{ needs.publish.outputs.release_id }}'),
                name,
                data,
                headers: {
                  'content-type': TYPES[path.extname(name)] || 'application/octet-stream',
                  'content-length': data.length,
                },
              });
              core.notice(`Attached ${asset.name} (${asset.size} bytes).`);
            }
```

- [ ] **Step 2: Add it to finalize's needs list — the trap**

Change:
```yaml
    needs: [publish, publish-fonts]
```
to:
```yaml
    needs: [publish, publish-fonts, publish-packages]
```

Forget this and the release is published before the packages are attached: a silent, correct-looking failure. Verify with:
```bash
grep -n 'needs: \[publish' .github/workflows/release-publish.yml
```

- [ ] **Step 3: Update RELEASING.md**

Find the section that explains the hand-maintained `needs:` list and add `publish-packages` to whatever it enumerates, so the document and the workflow cannot disagree.

- [ ] **Step 4: Update README.md**

Add an install section near the existing install instructions:

````markdown
### From a package

Every release attaches a `.deb` and an `.rpm`.

```sh
sudo apt install ./fonts-smalti_0.1.0-1_all.deb    # Debian, Ubuntu
sudo rpm -i smalti-fonts-0.1.0-1.noarch.rpm        # Fedora, RHEL, openSUSE
```

Both install the four faces where fontconfig finds them and carry no
maintainer scripts: the distributions' own `fontconfig` triggers rebuild the
cache. There is no apt or yum repository to add — that would need a signing
key this project does not have.
````

- [ ] **Step 5: Add the changelog entry**

Under `## [Unreleased]` → `### New` in `CHANGES.md`:

```markdown
- **`.deb` and `.rpm` packages.** Every release now attaches one of each, so Smalti can be installed and removed by a package manager instead of by hand. Both are built by a pinned `nfpm` from one description, hold the four `.ttf` faces and nothing else, and carry no maintainer scripts — the distributions' own `fontconfig` triggers rebuild the cache. `make check-packages` opens them with `dpkg-deb` and `rpm` and proves the fonts inside are byte-identical to the ones `make check` validated. No apt or yum repository is hosted: that would need a signing key, which would be the first credential this project owns.
```

- [ ] **Step 6: Commit and open the pull request**

```bash
git add -A
git commit -m "Attach the OS packages to every release"
git push
gh pr create --fill
```

- [ ] **Step 7: Verify before merging**

```bash
gh pr checks
```
Expected: `validate`, `build`, `packages` all green.

The release path itself cannot be tested before a release. The next release is the test — watch that `publish-packages` runs, that `finalize` waits for it, and that the release leaves draft state with two more assets on it.

---

## Self-Review

**Spec coverage.** §1–2 need no task. §3 tool → Task 1. §4 fetch → Task 1. §5 two packages → Task 2. §6 contents → Task 2. §7 no scriptlets → Task 2 (config) and Task 3 (checked). §8 licence → Task 2 (set) and Task 3 (checked). §9 make targets → Tasks 1–3. §10 checks → Task 3. §11 CI and release → Tasks 5 and 6. §12 reproducibility → Task 4. §13 needs no task. §14 risks: risk 1 → Task 4; risk 2 → resolved in Global Constraints by the `PKG_FONTDIR` variable; risk 3 → Task 5 comment.

**Placeholders.** None: every step carries the command or the code. Task 4's branch is a real decision procedure with both outcomes written out, not a TODO.

**Type consistency.** `check-packages.py` takes `--deb` and `--rpm`; the test suite and the Makefile both call it that way. `$(DEB)`/`$(RPM)`/`$(NFPM)` are defined in Tasks 2 and 1 and used consistently afterwards. `PKG_VERSION` is a make variable and also the environment variable nfpm reads — the same name on purpose, and the recipe passes it explicitly.
