# Security Policy

## Scope

`cfoforit-openmarketplace` is public: the public CFOforIT Claude plugin marketplace. See `CLAUDE.md` or the README for
detail. Assume any commit here could reach a public mirror if one exists for this repo,
and treat it accordingly.

> If this repo contains client references, in fixtures, examples, vectorstores,
> dashboards, or archived scripts, name them and their location in `CLAUDE.md`. Client
> names in file or directory names are acceptable only while the repo stays private, and
> are themselves a reason to keep it private.

## Hard rules

- No credentials, tokens, or connection strings in any commit. Read them from the
  environment or a credential store at runtime.
- No client PII or client financial records in commits, fixtures, examples, or eval
  cases.
- No cross-client contamination. One client's data must never appear in another
  client's artifact, fixture, response, or example.
- No client or personal payloads committed as fixtures. Runtime snapshots are state,
  not code, and belong in SharePoint, not git.
- Destructive tooling, meaning anything that deletes, moves, or overwrites, must be
  dry-runnable and must print what it would remove before removing it. A tool that
  reports success after reverting real work is indistinguishable from one that worked.
- Anything that widens what an automated or unattended process can touch, such as a new
  write path to a client system, a newly scheduled task, or a looser access policy, is a
  charter Rule 18 change and needs review before it ships, not after.
- Do not add a sync path from a private repo to a public mirror without deciding so
  deliberately. Most repos have none and should stay that way.

## Reporting

Report privately to **steve.torres@cfoforit.com**. Do not open an issue and do not
discuss in a shared channel.

### If this repo is private

Acknowledgement within 1 business day for anything involving client data.

### If this repo is public

Please do not disclose publicly before a fix ships. Include the affected file or
component, reproduction steps, and impact. Acknowledgement within 2 business days,
triage within 5. We confirm the fix with you before public disclosure and credit you
unless you would rather we did not.

In scope: anything that could cause a user's session to exfiltrate data, execute
unintended commands, or write outside the intended directory; prompt-injection vectors
in bundled content; any credential or client-identifying data found committed here.

Out of scope: vulnerabilities in the underlying platform or vendor infrastructure,
which should go to the vendor; issues that require a modified fork of this repo.

## If client data or a secret is committed

1. Do not force-push before reporting. Preserve the history for assessment and notify
   steve.torres@cfoforit.com before rewriting history.
2. Rotate the exposed credential first. Removal from git does not undo exposure.
3. Establish whether the commit reached a public mirror, a deployed site, or anywhere
   else client-visible. If it did, treat it as a disclosure.
4. Record the incident and the remediation.

## Deployment

If this repo auto-deploys on push to `main`, every commit to `main` is a publish, not
just a merge. If a deploy gate, such as access control or a preview stage, is the only
thing between the content and the open internet, treat it as a security control, not a
convenience. Do not disable, bypass, or widen it to make something easier to test. A
decision to make a page or path more shareable is made deliberately, per page, not as a
side effect of another change.

## Supported versions

Only `main` is supported. Where this repo has no tagged releases, `main` is what any
downstream consumer resolves to at any moment.
