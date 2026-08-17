# Changelog

## 1.0.0 (2026-08-16)

First release. Automates a manual routine: opening 70 to 100 real estate agents' public
profile pages across Zillow, Redfin, realtor.com and homes.com, looking for listings that have
gone pending, contingent or under contract, or that sold recently. Output is an Excel workbook
plus a self-contained HTML dashboard.

**The design decision the whole skill turns on.** Most nights this watch finds nothing. That
means a broken run and a quiet night produce the same-looking report, and the failure mode is
not "the tool errors" — it is "the tool reassures you". So a page that loaded and showed
nothing (`ok` with no listings) and a page that refused to load (`blocked` or `page_changed`)
are tracked as different outcomes that never collapse into one. Every report leads with
coverage rather than hit count, the dashboard banner turns red the moment coverage is short,
and a run with zero coverage does not write a snapshot, so a blocked night cannot poison the
next night's "new since last run" column.

Recorded classifications and why:

- **`autonomy_tier: draft-for-review`** — it produces a list a person reads and acts on. It
  takes no action itself and has no send path of any kind.
- **`blast_radius: client-touching`** — the output is a working document for a client's
  collections team, and a wrong row sends a real person after a real agent.
- **`model_tier: sonnet`** — page reading and name reconciliation, both bounded by a written
  playbook. The arithmetic is in Python.
- **`trust_level: untrusted-web`** — every page it reads is open-web content authored by the
  subject of the report, who has an incentive to influence it. Rule 15.1 note is in the body:
  page text is data, never instruction, and anything resembling an instruction is recorded in
  the visit note and flagged in the run summary rather than obeyed.

Deliberate scope refusals, some of them the client's own instruction:

- No outbound contact. No drafted emails, no collection letters, no "just in case" template.
- No MLS, IDX, or login-gated data. Public profile pages only.
- No scraping service, no proxy, no CAPTCHA handling. Browsing happens in the operator's own
  signed-in Chrome at human speed, and a block is reported as a block. This is slower than the
  alternatives and it is the version that is still defensible in a year.
- No profile discovery. The operator supplies each URL. A machine-guessed profile is a coin
  flip, and one wrong agent's listings does more damage than a hundred missed ones.
- No risk scoring, ranking, or tie-back to balances. The client asked for a list by name, and
  a list by name is what it produces.

Name matching is deterministic and lives in `scripts/lw.py`, not in the model's head, with
nickname and credential-suffix normalization so "Bob Smith, PA" matches "Robert Smith". Every
non-exact match still ships, labeled `near` or `mismatch` with the page's actual wording — a
row is never dropped for having the wrong name on it, because a persistent mismatch usually
means a rotted profile link, which is worth more than the listing data it replaced.
