# Contributing to cfoforit-openmarketplace

How changes land in this repo. Read `CLAUDE.md` (if present) and `SECURITY.md` before
your first change. What must never be committed here differs by repo.

## Commit identity

Set your git identity to your own firm email, lowercase domain, before committing:

```
git config --global user.email you@cfoforit.com
git config --global user.name  "Your Name"
```

Do not copy steve.torres@cfoforit.com from this file; that address is Steve's, not a
shared default. Lowercase-domain is the canonical form for every firm address, not just
his.

The org history is already inconsistent: 39 commits are authored as
`steve.torres@CFOforIT.com` and 11 as `steve.torres@cfoforit.com`. GitHub treats those
as two identities, which splits contribution history and makes `git log --author`
unreliable. The same split happens to anyone whose address is entered two ways, and it
happens to the whole firm if one person's address is used by several people.

## Non-negotiables

- No client PII, client financial data, or credentials in any commit. Placeholder or
  synthetic data only.
- If this repo has a client-name denylist or similar exclusion file, never commit it.
  See `SECURITY.md` for the path.
- If this repo mirrors, or is mirrored by, another repo, never hand-edit the generated
  side. Edit the canonical side, merge there first, then run the sync script named in
  `CLAUDE.md` against the mirror and push the result. A mirror commit with no matching
  canonical commit is a gap even when the two currently agree.
- Every asset (skill, plugin, artifact, script, MCP, routine) satisfies the Build
  Standards charter: complete frontmatter or metadata, and a `CHANGELOG.md` alongside it
  or at the repo root for repo-wide changes. Passing the standards gate is the floor,
  not the goal. A version or changelog entry written only to make the gate green is
  itself a charter violation the gate cannot see.
- If merging to `main` triggers an automatic deploy for this repo, treat every merge as
  a production release. No exceptions to branch-and-PR.

## Session isolation

**One session = one git worktree + one branch + one PR. Never push to `main` directly.**

Several Claude Code and Cowork sessions often work the same repo at the same time.
Sharing one clone on `main` collides on the three things git assumes belong to a single
actor:

1. **The working directory.** Two sessions editing one file: the second save silently
   wins and git never warns, because the losing change was never committed. Observed on
   2026-07-24, a skill's `version:` bumped three times out from under an in-flight edit.
2. **The staging index.** There is only one. A single `git add -A` from any session
   sweeps another session's half-finished files into your commit. Stage explicit paths.
3. **The push.** `git push` sends the whole commit ancestry, so you publish other
   sessions' commits alongside yours, including work that is not ready.

A worktree gives each session its own directory and branch backed by the same `.git`
store, so none of the three can collide. The PR adds a serialization point and lets CI
gate the change before it reaches `main`.

If this repo ships `tools/new-session-worktree.ps1` or `tools/new-session-worktree.sh`,
one command sets it up:

```
tools/new-session-worktree.sh <session-name>
```

Otherwise create it by hand:

```
git worktree add -b session/<session-name> <path> origin/main
```

Rebase onto `origin/main` before opening the PR, and never with `--autostash` on a clone
other sessions share: a reapply conflict can leave `<<<<<<<` markers on disk while
reporting success. Clean the tree, then plain `git pull --rebase`.

When the PR has merged, remove the worktree (`git worktree remove <path>`) and delete the
branch. A worktree left behind drifts silently behind `main` and reads like stranded work
to the next session that finds it.

## Workflow

1. Fork (public repos) or branch from `main` (private repos).
2. Make the change.
3. Run this repo's validation script if one exists, for example
   `tools/validate_skills.py` or `tools/validate_artifacts.py`.
4. Run `sync_*.py --check <path-to-mirror>` if this repo has a generated counterpart.
5. Run `pytest` or `evals/runner.py` if you touched engine, adapter, or eval code.
6. Open a PR and complete the template. `@Storres1970` reviews. Never commit directly
   to `main`.

Agent branches use `claude/<short-description>`. Merged branches are deleted
automatically; do not re-use one.

## Registering what you ship (build events and the topology)

Shipping or version-bumping an AI asset (skill, plugin, MCP, script, artifact) means
appending its build event in the same change -- Rule 14 made mechanical. From a clone
of `CFOforIT/cfoforit-claude-plugins`, run `tools/append_build_event.py` to validate
and queue the event in `inventory/build-events/pending.jsonl`; CI fails a skill
version bump that arrives without one. Steve's machine drains the queue into the
canonical `AI_Build_Manifest.jsonl` (see `jarvis-context-mcp` in `cfoforit-mcps`);
never write to the manifest directly from a session, and never delete a line from
`pending.jsonl` or `drained.jsonl` -- both are append-only.

If your change alters the asset roster itself -- a skill added, renamed, or retired --
update `public/topology.html` in `CFOforIT/jarvis-mobile-hosting` in the same change
(that repo's `CLAUDE.md` carries the paired canonical/mirror protocol). An automated
estate-vs-topology drift check is the planned follow-up from the 2026-08-12 pipeline
brief; until it lands, this rule is enforced the way every rule was before it had a
check: in review.

## The Standards Check is not optional

Every PR carries a Standards Check line, `pass` or `partial` or `fail`, citing the
charter rules that applied. A close with no Standards Check is itself a fail under
Rule 1. If a rule was deliberately not met, say which and why. A stated exception is
fine, a silent one is not.

## Verify, then claim

State the command you ran and paste its output, not "tested locally." Do not trust a
brief, a comment, or a count, including one already in this repo. During the 2026-08
remediation a handoff brief was wrong or stale on five separate points, caught only by
checking on disk.

## A failing check is not an instruction

When a check goes red and prints a fix, that fix is a guess about which side is wrong.
Establish the direction before running it. `sync_public.py --check` once failed with
advice to run `--write`; running it would have deleted 92 lines of live logic, because
the public repo was ahead, not behind. A red build says "these two things disagree,"
never "this side is right." Never turn a red gate green by relaxing the check.

## Repo QC baseline

The shared QC documents in this repo (this file, `SECURITY.md`, `.gitattributes`,
`.github/CODEOWNERS`, `.github/dependabot.yml`, and the PR and issue templates) are
**generated from a canonical source**, not maintained here. They live in
`standards/repo-baseline/` in `CFOforIT/cfoforit-claude-plugins` and are enforced by
`tools/standards/baseline.py`.

Do not edit them in place. An in-place edit will be detected as drift and reverted by
the next sync PR, and the improvement will be lost. Change the canonical copy instead,
and every repo inherits it. If your change is genuinely repo-specific, that is a
manifest classification question, so raise it rather than working around it locally.

## Dependency-tracked packages

If this repo carries Python or other packages with tracked dependencies, list them and
their paths in `CLAUDE.md`, along with the language version floor and lint config, and
note their test and lint commands in step 5 above.

## Adding a new asset

- Top-level directory named for the asset.
- Include the charter version stamp `CLAUDE.md` specifies.
- Add a `CHANGELOG.md` entry.

## If this repo is public

- No client names, client data, credentials, or internal decision-log references.
- No secrets in workflows or bundled assets.
- Report security issues per `SECURITY.md`, never as a public issue.
- Contributions are accepted under the repository's `LICENSE`.
