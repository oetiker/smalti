# Releasing Smalti

A release is **two clicks in the GitHub Actions UI**, with a pull request in
between that you review.

1. **Actions → Create release PR → Run workflow.** Pick `bugfix`, `feature`
   or `major`. The workflow refuses unless every check on the current `main`
   commit is green, works out the next version, rolls `CHANGES.md`, writes
   `VERSION`, and opens a `release/vX.Y.Z` pull request. Nothing is tagged
   yet; closing that pull request cancels the release.

2. **Review the changelog and merge the pull request.** The merge tags
   `vX.Y.Z`, builds and checks the fonts, attaches them to the release, and
   publishes it.

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

**The release is a draft for a minute or two.** The fonts are built and
checked *after* the tag exists and attached to a draft, so nobody can see a
Smalti release without its fonts. The last job flips it to published. If the
font job fails, the release stays a draft — which is the right outcome, not a
bug.

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
`publish-fonts` job in `release-publish.yml`, which is this project's own.
