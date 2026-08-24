# Design: OS packages (.deb and .rpm)

Status: proposed
Date: 2026-08-24
Scope: an addition to sub-project **C** (CI + releases). It changes nothing
about how glyphs are drawn, traced or checked; it takes the `.ttf` files the
existing build already proves correct and wraps them for two package managers.

## 1. Why

Installing Smalti today means downloading four `.ttf` files and putting them
somewhere fontconfig looks. That is fine for one machine and wrong for a fleet:
there is no way to say "this host has Smalti", no way to remove it cleanly, and
no way to roll it out with the tool that manages everything else on the box.

A `.deb` and an `.rpm` fix all three, and they cost nothing at install time
because a font package is the simplest package there is -- files in a
directory, no binaries, no architecture, no configuration.

## 2. What this is not

**No apt or yum repository is hosted.** The packages are files attached to the
GitHub release, downloaded and installed by hand:

```
sudo apt install ./fonts-smalti_0.1.0_all.deb
sudo rpm -i smalti-fonts-0.1.0-1.noarch.rpm
```

This matches repo-infra's own position, and for the same reason: a hosted
repository needs a GPG signing key that must be stored and rotated, which would
be the first credential this project owns.

## 3. The tool

**nfpm**, pinned. One static Go binary, one YAML file, emits `.deb` and `.rpm`
from a single description.

This is not a fresh choice; it is the house standard. repo-infra's design names
it under spec 2's publish add-ons:

> **OS packages** -- **nfpm** -- one static Go binary, one YAML file, emits
> deb/rpm/apk for *any* language.

Two alternatives were considered and rejected:

- **The distributions' own machinery** (`debhelper` + `dpkg-buildpackage`, and
  `rpmbuild` from a spec). Idiomatic, but it means two independent
  descriptions of the same package, and `rpmbuild` is on neither this project's
  development machine nor the GitHub runners -- so it would put an apt step
  back into a workflow, which was deliberately removed when the bitmap `.otb`
  was dropped.
- **Writing both formats by hand in Python.** The `.deb` is easy: an `ar`
  archive of two tarballs. The `.rpm` is a fiddly binary header, and -- the
  decisive objection -- **our own writer could not be honestly verified by our
  own reader**. That is the self-confirming check this project has already been
  bitten by five times.

## 4. Where nfpm comes from

`nfpm` v2.47.0, downloaded into `build/` and verified against a SHA-256 that
is **pinned in the Makefile**, beside the version. Not fetched from the release
alongside the tarball -- a checksum downloaded from the same place as the file
it checks proves only that the download did not corrupt.

This is the same shape as `make venv`, which already downloads a pinned set of
Python dependencies. A pinned, hash-checked download is not a new kind of
dependency for this project; an unpinned one would be.

The consequence that matters: **the same binary runs locally and in CI**, so
`make deb` on a contributor's machine produces what the release produces. A
rule only GitHub can run is a rule a contributor cannot check before pushing.

## 5. Two packages, one description

nfpm has a single global `name:` field, but the two ecosystems disagree about
almost every name. nfpm expands environment variables inside its config, so one
`packaging/nfpm.yaml` is invoked twice with different values:

| | deb | rpm |
|---|---|---|
| package name | `fonts-smalti` | `smalti-fonts` |
| file name | `fonts-smalti_<version>_all.deb` | `smalti-fonts-<version>-1.noarch.rpm` |
| architecture | `all` | `noarch` |
| font directory | `/usr/share/fonts/truetype/smalti/` | `/usr/share/fonts/smalti/` |
| section / group | `fonts` | `User Interface/X` |

The differing font directory is Debian's convention, not a requirement --
fontconfig scans `/usr/share/fonts` recursively on both. It is followed because
following each ecosystem's convention is the whole point of shipping two
packages instead of one tarball.

**One package holds every size.** Today that is the four faces of 7x14; when
sub-project E populates the other six cell sizes they join the same package. This
is safe only because **the cell size is part of the family name** -- `Smalti
7x14`, never `Smalti` -- so installing several sizes at once cannot make a font
matcher choose between them arbitrarily. That is upstream Tamzen's bug, and the
reason its notes say to keep only one size installed. Smalti does not have it,
so it does not need per-size packages.

## 6. Contents

- The four `.ttf` files. **No `.woff2`** -- it is a web delivery format and has
  no business in `/usr/share/fonts`.
- `README.md` and `LICENSE.tamzen` as documentation.

Nothing is generated into the package that is not already an output of `make`.

## 7. No maintainer scripts

Both distributions' `fontconfig` packages ship triggers that rebuild the font
cache when files appear under `/usr/share/fonts`. A hand-written `fc-cache`
call in a postinst is the old way, runs at the wrong moment relative to the
trigger, and is one more thing that can fail on a machine that is not ours.

The packages therefore carry **no scriptlets at all**, and **do not depend on
`fontconfig`** either -- they only *recommend* it. A hard dependency is the
tempting mistake: a font is usable by consumers that never touch fontconfig,
and where fontconfig is absent there is no cache to refresh. Debian's own font
packages depend on nothing for this reason.

## 8. Licence

Tamsyn's licence is a custom permissive text, not a standard SPDX identifier:

> "…font is free. You are hereby granted permission to use, copy, modify, and
> distribute it as you see fit."

The rpm's `License:` tag therefore reads `LicenseRef-Tamsyn` rather than
inventing an approximation, and the full text ships inside both packages.

## 9. Make targets

```
make deb              build/fonts-smalti_<version>_all.deb
make rpm              build/smalti-fonts-<version>-1.noarch.rpm
make packages         both
make check-packages   open both and prove what is inside them
```

**None of these is reachable from `make all` or `make check`.** The font build
keeps its entire dependency list -- `python3-venv` -- and a contributor who
never touches packaging installs nothing new and downloads nothing new.

## 10. The checks

`make check-packages` opens the built packages with the package managers' own
tools, never with a reader of ours:

- `dpkg-deb --contents` and `--info` for the `.deb`
- `rpm -qp --list --info` for the `.rpm`

and proves, for each:

1. exactly four `.ttf` files are present, at the paths §5 gives for that format
2. each one is **byte-identical to the corresponding file in `build/`**, which
   `make check` has already proved carries the right version, metrics and
   outlines -- this check inherits that guarantee rather than restating it
3. the declared version equals `VERSION`
4. the documentation files are present
5. no maintainer scripts are declared

**If either tool is missing, the target fails and names the package to
install.** It does not skip and it does not pass. `dpkg-deb` is present on
Debian and Ubuntu machines and on the runners; `rpm` is on neither this
project's development machine nor the runners, so the packaging CI job installs
it, and a contributor is told to. This is the project's recurring bug class --
a check that skips its job and reports success -- and the answer to "what does
this do when there is nothing to check" must be "fail".

## 11. CI and release wiring

**A new `packages` job in `build.yml`**, so every pull request proves the
packages still build and still pass `check-packages`. It installs `rpm` -- the
only apt step in the repository, confined to the one job that needs it.

**A new `publish-packages` job in `release-publish.yml`**, a sibling of
`publish-fonts`, following the seam repo-infra defines for a publish add-on:
`needs: publish`, consume `version`/`tag`/`release_id`, build from the tagged
commit, attach to the **draft** release. If it fails, the release stays a
draft, which is the designed outcome.

**`finalize`'s `needs:` list gains `publish-packages`, by hand.** repo-infra's
`apply` normally appends add-on job names there; Smalti does not run `apply`,
so the list is maintained manually. Omit the entry and the release is published
before the packages have been attached -- a silent, correct-looking failure.
`RELEASING.md` records this.

Editing `release-publish.yml` is not a violation of the borrowed-file rule.
repo-infra's `conventions.md` names "a publish job bolted onto
`release-publish.yml`" as a local edit a repository is entitled to make, because
the version marker records a *generation*, never a content hash. The marker
stays plain `v1`.

## 12. Reproducibility -- to be proved, not assumed

The build is byte-reproducible, and that is load-bearing: it is the instrument
that proved a ~1000-file restructure changed exactly one glyph. Package formats
embed timestamps by nature, so **nfpm's behaviour under `SOURCE_DATE_EPOCH` is
the one thing in this design that must be demonstrated before it is believed.**

The test is the same one the fonts get: build the packages twice from the same
tree and compare the bytes. If nfpm will not produce identical output, the
finding is reported and the gap is named in `README.md` and behind a standing
`::warning`, the way the unverified `.woff2` outlines already are. It is not
quietly shipped as if reproducible.

## 13. Relationship to repo-infra

repo-infra's spec 2 -- the publish add-ons, nfpm among them -- is an **outline
that has not shipped**. Smalti is therefore building this before the standard
does, and builds it in the standard's shape so it can be lifted upstream, or
replaced by the standard's version when that lands, without redesign.

Concretely: the job follows the documented seam, the config lives in its own
`packaging/` directory rather than being scattered, and nothing about it is
font-specific except the file list.

## 14. Risks

1. **nfpm may not be reproducible.** §12. Detected by the design's own test,
   not by a user.
2. **nfpm's per-format overrides may not reach every field this design varies.**
   The environment-variable indirection covers `name`; if a field such as the
   font directory cannot be varied per format, the fallback is a single
   `/usr/share/fonts/smalti/` for both, which fontconfig scans on either system.
   This is a small loss of convention, not of function.
3. **`rpm` on the runner is an apt step**, reintroducing something removed on
   purpose. It is confined to the packaging job, and it buys an honest check
   rather than a decorative one.
