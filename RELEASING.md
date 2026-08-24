# Releasing Smalti

A release is **two clicks in the GitHub Actions UI**, with a pull request in
between that you review.

1. **Actions → Create release PR → Run workflow.** Pick `bugfix`, `feature`
   or `major`. The workflow refuses unless every check on the current `main`
   commit is green, works out the next version, rolls `CHANGES.md`, writes
   `VERSION`, and opens a `release/vX.Y.Z` pull request. Nothing is tagged
   yet; closing that pull request cancels the release.

2. **Review the changelog and merge the pull request.** The merge tags
   `vX.Y.Z`, builds and checks the fonts and the `.deb`/`.rpm` packages,
   attaches all of them to the release, and publishes it.

Everything that decides the version comes from the repository, not from the
run: `CHANGES.md` is the source of truth for what is being released, and
`VERSION` is the copy every artefact carries.

## Before you dispatch

Write the entries as you go, under `## [Unreleased]` in `CHANGES.md`. The
release refuses to roll an empty `[Unreleased]` block, which is the backstop
against a version with no notes.

## What you will see, that looks wrong but is not

**"Approve workflows to run" on the release pull request.** A pull request
opened by `GITHUB_TOKEN` does not skip its checks — it parks them, waiting for
someone with write access to click that button once. The alternative is a
stored personal token or a GitHub App to create, store and rotate, to save one
click on a pull request somebody is reviewing anyway. Seeing the banner is the
system working.

**The release is a draft for a minute or two.** The fonts and the packages
are built and checked *after* the tag exists and attached to a draft, so
nobody can see a Smalti release without them. The last job flips it to
published, and it waits on both add-on jobs to do so. If either the font job
or the packages job fails, the release stays a draft — which is the right
outcome, not a bug.

## Why it is two steps and not a push from a workflow

`main` is protected by a ruleset whose bypass list is empty, and that list only
accepts users, teams, apps, org admins, repository roles and deploy keys.
`GITHUB_TOKEN` is none of those, so it cannot be added and cannot push to
`main`. A pull request needs no bypass. Do not try to route around it with an
`on: push` trigger either: a push made with `GITHUB_TOKEN` does not fire
workflow triggers.

## Recovery

**Re-run, never re-dispatch.** Actions → the failed run → **Re-run failed
jobs**. The version comes from `CHANGES.md` in the repository, not from run
inputs, so a re-run does exactly what the first attempt would have.

There is deliberately no `workflow_dispatch` on the publish workflow: a whole-
workflow re-run would find the tag already present, stop, and leave the release
a draft forever. **Re-run failed jobs** keeps the successful job's outputs,
which is what the later jobs need.

If a run died *between* creating the tag and creating the release, the tag has
to be removed by hand before a re-run can finish — `git push origin --delete
vX.Y.Z`, after checking with whoever is releasing.

## Where this came from

The flow is **borrowed** from the `repo-infra` standard
(`~/checkouts/repo-infra`): `.github/workflows/release-pr.yml`,
`.github/workflows/release-publish.yml`, the five files in
`.github/workflows/lib/`, and `.github/repo-infra.json`. Smalti keeps its own
CI — `validate.yml`, `build.yml` and `pages.yml` are this project's — because
the standard does not recognise a font built from ASCII-art text files, and
teaching it a new ecosystem is a change to that project rather than this one.

**Do not hand-edit the borrowed files.** Take a newer version of the whole set,
or the next update silently reverts you. Smalti-specific behaviour lives in the
`publish-fonts` and `publish-packages` jobs in `release-publish.yml`, which are
this project's own. The standard's `apply` would normally append an add-on
job's name to `finalize`'s `needs:` list when it installs the job; Smalti does
not run `apply`, so that list — currently
`[publish, publish-fonts, publish-packages]` — is maintained by hand. Add a
third add-on job and add its name there too, or the release publishes before
that job has attached anything.

### The one place that rule is broken, on purpose

`release-pr.yml` and `lib/checks.js` carry a local patch, marked in their
version lines as `+ LOCAL PATCH`. It is reported upstream; until a repo-infra
release carries the fix, **check before taking a newer set, or taking it
reintroduces the bug.**

The guard that waits for green checks before releasing excluded only the
*current* run's jobs. So a release attempt that failed for any reason left a
failed check run on the commit, and every later attempt read that corpse as
"this commit has a failing check" and refused. Check runs cannot be deleted,
so **the commit became permanently un-releasable** — and deleting the release
branch does not help, because the block is attached to the commit.

That is not theoretical: it cost Smalti its first release. `0.1.0` was
prepared correctly, failed to open its pull request because *Allow GitHub
Actions to create and approve pull requests* was off, and then could not be
retried at all. Two separate faults, and the second one hid behind the first.

The id-gathering now lives in `lib/checks.js` as `guardIgnoreIds`, where
`lib/checks.test.js` tests it — including that a genuinely failing check still
blocks a release, which is the half a careless fix would drop. It was inline
YAML before, where nothing could test it, which is why the bug shipped.

    node --test .github/workflows/lib/checks.test.js

That is deliberately **not** in `make check` or CI: this repository's only
build dependency is `python3-venv`, and adding node to the gates to test a
borrowed file would be a poor trade. Upstream runs these tests.

### If a release ever does get stuck on a poisoned commit

Land any further commit on `main` and dispatch again. The guard reads the
checks of the commit it is releasing, so a commit with a clean history
releases normally. The prepared branch from the failed attempt can be reused
as-is: nothing downstream reads the pull request, which is only a review
surface — `release-publish.yml` fires on `CHANGES.md` landing on `main` and
reads the version out of the repository.
