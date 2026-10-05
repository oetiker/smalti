# Releasing Smalti

A release is two steps in the GitHub Actions UI, with a pull request in
between that you review.

1. **Actions → Create release PR → Run workflow.** Pick `bugfix`, `feature`
   or `major`. The workflow works out the next version, rolls `CHANGES.md`,
   writes `VERSION` and commits that to a `release/vX.Y.Z` branch. On that
   branch it builds and checks the fonts and the `.deb`/`.rpm` packages, runs
   the full CI, attaches every file to a draft release and opens the pull
   request. Nothing is tagged yet; closing the pull request cancels the
   release.

2. **Review the changelog and merge the pull request.** The merge tags the
   commit that was built as `vX.Y.Z`, uploads the `.deb` and `.rpm` to the
   oposs package repository on `gitea.oetiker.ch`, checks that the draft
   carries every file listed in `release_assets` in `.github/repo-infra.json`,
   and publishes it. If the upload fails, the release stays a draft.

`CHANGES.md` is the source of truth for what is being released, and `VERSION`
is the copy every font and package carries.

## Before you dispatch

Write the entries as you go, under `## [Unreleased]` in `CHANGES.md`. The
release refuses to roll an empty `[Unreleased]` block.

Create release PR refuses to start when a check on the current `main` commit
has already failed, when a release pull request is still open, or when the
latest release in `CHANGES.md` has no tag. The message names the cause.

## What you will see

**"Approve workflows to run" on the release pull request.** A pull request
opened by `GITHUB_TOKEN` parks its own checks until someone approves them.
Nobody needs to: Create release PR already ran the build and the CI on exactly
this commit and reported `ci-passed` and `changelog-updated` for it. Publish
deletes the parked runs after the release.

**A draft release while the pull request is open.** The fonts, the zip and the
packages are attached to it when the pull request opens. The merge makes it
public.

## When main moves under a release

A release is built from one `main` commit. If another pull request merges
first, the release pull request turns red with `main moved after vX.Y.Z was
built; close this pull request and dispatch Create release PR again`. Do that.
Pressing **Update branch** on a release pull request has the same effect: the
new head was never built, and the checks say so.

## Recovery

**Re-run, never re-dispatch.** If the publish run fails, open it under Actions
and choose **Re-run failed jobs**. The version comes from `CHANGES.md` in the
repository, not from run inputs, so a re-run does what the first attempt would
have done. There is deliberately no `workflow_dispatch` on the publish
workflow.

If publish fails with `main at <sha> does not match the release built from
<head>`, it tagged nothing and every re-run fails the same way. Abandon the
release with a pull request that moves its entries back under `[Unreleased]`,
then dispatch again.

## Where this comes from

The release flow and the changelog gate are the `repo-infra` standard. Its
files under `.github/workflows/` carry a `repo-infra: <piece> vN` marker in
their first comment line and are never edited here; `repo_infra check` reports
an edited one, and `repo_infra apply` installs newer versions.

Smalti's own work lives in two files the standard calls:

- `.github/workflows/ci-local.yml`: the glyph store and outline proof
  (`make check`), the coverage index, the font build and install, and the OS
  packages (`make check-packages`). `ci.yml` calls it on every push to `main`
  and every pull request, and Create release PR calls it on the release
  branch.
- `.github/workflows/release-build-local.yml`: builds the fonts and the
  packages for a release with `SOURCE_DATE_EPOCH` set to the release commit's
  timestamp, checks them, and uploads them for the draft release.

The upload uses the repository secret `GITEA_PACKAGE_TOKEN` (a Gitea token
with the `write:package` scope only) and the repository variable
`GITEA_PACKAGE_USER`. Gitea tokens do not expire; rotate the secret by hand.
A re-run of a failed upload skips the packages Gitea already holds.

`pages.yml`, the specimen site, is Smalti's own and not part of the standard.
