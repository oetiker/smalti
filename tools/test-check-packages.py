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
SIZES = ["7x14", "8x16"]
# Cases name a font by its FILENAME, not by a face, so a case can drop or
# corrupt an 8x16 font.  A suite that could only ever injure a 7x14 face
# would stay green while the whole 8x16 half of the package went
# unchecked -- which is the fault this dimension exists to make reachable.
FONTS = [f"Smalti{size}-{face}.ttf" for size in SIZES for face in FACES]


def need(tool):
    if shutil.which(tool) is None:
        sys.exit(f"{tool} is required to run this suite -- install it "
                 f"(Debian/Ubuntu: sudo apt install rpm dpkg cpio)")


def build(workdir, *, yaml_extra="", drop_font=None, version="0.1.0",
          fontdir="/usr/share/fonts/truetype/smalti", name="fonts-smalti",
          packager="deb", corrupt_font=None):
    """Build one package into workdir and return its path.

    Everything a case wants to break is a parameter, so no case edits a
    finished package.
    """
    stage = workdir / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "build").mkdir(exist_ok=True)
    for font in FONTS:
        if font == drop_font:
            continue
        data = (ROOT / "build" / font).read_bytes()
        if font == corrupt_font:
            data = data + b"\x00"      # a byte the built face does not have
        (stage / "build" / font).write_bytes(data)
    for doc in ("README.md", "LICENSE.tamzen"):
        shutil.copy2(ROOT / doc, stage / doc)

    contents = []
    for font in FONTS:
        if font == drop_font:
            continue
        contents.append(f"  - src: build/{font}\n"
                        f"    dst: {fontdir}/{font}\n")
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
    missing = [f for f in FONTS if not (ROOT / "build" / f).exists()]
    if missing:
        sys.exit(f"missing built faces: {' '.join(missing)} -- run `make` first")

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
                    deb=build(tmp / "c1", packager="deb",
                              corrupt_font="Smalti7x14-Bold.ttf"))

        # 3 -- seven fonts instead of eight
        expect_fail("missing face", f"expected {len(FONTS)} .ttf",
                    deb=build(tmp / "c2", packager="deb",
                              drop_font="Smalti7x14-Italic.ttf"))

        # 4 -- right files, wrong directory
        expect_fail("wrong font directory", "unexpected path",
                    deb=build(tmp / "c3", packager="deb",
                              fontdir="/usr/share/fonts/smalti"))

        # 5 -- a version that is not VERSION
        expect_fail("wrong version", "version is not",
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
                              corrupt_font="Smalti7x14-Regular.ttf"))

        # 8 -- an 8x16 font is absent.  Without this the suite would only
        # ever injure the 7x14 half and would stay green on a package that
        # shipped no 8x16 font at all.
        expect_fail("missing 8x16 font", "Smalti8x16-Regular.ttf is not in the package",
                    deb=build(tmp / "c7", packager="deb",
                              drop_font="Smalti8x16-Regular.ttf"))

        # 9 -- an 8x16 font whose bytes are not the built face's bytes.  The
        # count in case 8 can be satisfied by any eight files; only this case
        # proves the 8x16 half is actually BYTE-compared against build/.
        expect_fail("corrupt 8x16 font", "Smalti8x16-Italic.ttf does not match build/",
                    deb=build(tmp / "c8", packager="deb",
                              corrupt_font="Smalti8x16-Italic.ttf"))

    print("\nall cases red for their own reason")


if __name__ == "__main__":
    main()
