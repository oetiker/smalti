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
SIZES = ["7x14", "8x16"]
# The exact set of .ttf a package must hold, in one place: the count
# assert below and the byte comparison must not be able to disagree
# about how many faces there are, which is how the 8x16 half could
# otherwise ship unchecked while the count still passed.
FONTS = [f"Smalti{size}-{face}.ttf" for size in SIZES for face in FACES]
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

    if len(fonts) != len(FONTS):
        fail(f"{label}: expected {len(FONTS)} .ttf under {fontdir}, "
             f"found {len(fonts)}")

    for name in FONTS:
        built = ROOT / "build" / name
        inside = root / fontdir.lstrip("/") / name
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

    # Read the control tarball, NOT `dpkg-deb --info`.  --info prints control
    # file names with no leading path, so a substring test against it can never
    # fire -- a check that would have passed every package forever.
    #
    # Keep the whole pipeline in bytes.  --ctrl-tarfile emits a binary tar
    # stream; text=True would decode it as UTF-8 and apply universal-newline
    # translation, turning any 0x0D byte (a CRLF in a control file, or a
    # non-ASCII maintainer name) into 0x0A before it gets re-encoded -- which
    # corrupts the stream and makes `tar -t` fail on a well-formed package.
    # Only the member names, not the stream, need to become text.
    ctrl = subprocess.run(["dpkg-deb", "--ctrl-tarfile", str(path)],
                          check=True, capture_output=True)
    names_raw = subprocess.run(["tar", "-t"], input=ctrl.stdout,
                               check=True, capture_output=True).stdout
    names = names_raw.decode().split()
    for script in ("preinst", "postinst", "prerm", "postrm"):
        if f"./{script}" in names:
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
        # Do NOT use check=True here.  rpm2cpio validates the cpio archive it
        # writes by comparing bytes copied against the package's declared
        # RPMSIGTAG_PAYLOADSIZE header.  nfpm 2.47.0 declares that field as
        # the sum of the six payload files' *content* bytes, but the real
        # cpio archive it writes is larger by the cpio headers and trailer,
        # so the comparison always fails and rpm2cpio exits 1 -- while having
        # written a complete, correct payload.  Measured twice independently
        # on build/smalti-fonts-0.1.0-1.noarch.rpm: exit 1, stderr completely
        # empty, 373240 bytes of valid cpio payload on stdout; extracting it
        # and diffing against build/ shows all four .ttf byte-identical.
        # Patching just that one header field to the true archive size makes
        # the same rpm2cpio binary exit 0 on the same file, confirming the
        # cause.  So: don't trust the exit status, but don't trust empty
        # output either -- an empty payload still FAILS below.  There is
        # nothing on stderr to log; rpm2cpio never wrote anything there.
        cpio = subprocess.run(["rpm2cpio", str(path)], capture_output=True)
        if not cpio.stdout:
            fail("rpm: rpm2cpio produced no payload")
            return
        # rpm payload members carry ABSOLUTE names.  Without
        # --no-absolute-filenames, cpio ignores cwd and tries to write to the
        # real /usr/share/... -- it dies with a permission error here, and on
        # a privileged runner it would silently write outside the repository.
        subprocess.run(["cpio", "-idm", "--quiet", "--no-absolute-filenames"],
                       input=cpio.stdout, cwd=tmp, check=True)
        compare_tree(Path(tmp), RPM_FONTDIR, RPM_NAME, "rpm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deb")
    ap.add_argument("--rpm")
    args = ap.parse_args()

    if not args.deb and not args.rpm:
        sys.exit("nothing to check: pass --deb and/or --rpm")

    for name in FONTS:
        built = ROOT / "build" / name
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
