#!/usr/bin/env python3
"""skill-standards-gate: validate every SKILL.md against the CFOforIT Build Standards
charter (v1.8, 2026-05-21). Runs identically in CI (GitHub Action) and locally.

This is the authoritative enforcement layer for skill governance. The in-session
skill-author-guard hook is a speed bump that can be routed around by tooling choice;
this gate fires on every push to main no matter how a file was written.

HARD FAILURES (exit 1):
  - frontmatter missing or unparseable
  - required fields absent: name, description, version, autonomy_tier,
    blast_radius, model_tier, trust_level
  - version not semver (X.Y.Z, optional -suffix like -beta)
  - autonomy_tier outside {read-only, draft-for-review, send-with-confirm, fully-autonomous}
  - blast_radius outside {private, internal, client-touching, external, financial-impact}
  - trust_level outside {internal, client, external, untrusted-web}   (Rule 15)
  - model_tier outside {haiku, sonnet, opus}                          (Rule 16)
  - Rule 18 forbidden combo: fully-autonomous + external/financial-impact
  - CHANGELOG.md absent, or lacking an entry for the current version  (Rule 17)

WARNINGS (exit 0, annotated): missing model_tier_rationale / expected_token_budget
(Rule 16 detail), missing or thin evals/ (<5 fixtures) or no runner.py (Rule 1 --
warn-only per-plugin until that plugin's runnable coverage lands, then add it to
EVAL_BLOCKING_PLUGINS to enforce as hard errors), status: active on a 0.x version (Rule 1 beta).

MAINTENANCE DUTY: the enums below encode charter v1.8. Any charter revision that
touches Rules 2/15/16/17/18 must update this file in the same session (same rule as
charter-derived artifacts staying in sync with the charter).
"""
import os
import re
import sys

CHARTER_VERSION = "1.8"
# Eval enforcement is per-plugin: a plugin listed here has demonstrated runnable eval
# coverage (fixtures + real runner on every skill) and is held to Rule 1 as a HARD error.
# Plugins not yet listed get warnings until their coverage lands. First flip 2026-07-24:
# cfoforit-client-delivery (13/13 skills, 67 real fixtures, runners green).
EVAL_BLOCKING_PLUGINS = {"cfoforit-client-delivery"}

AUTONOMY_TIERS = {"read-only", "draft-for-review", "send-with-confirm", "fully-autonomous"}
BLAST_RADII = {"private", "internal", "client-touching", "external", "financial-impact"}
TRUST_LEVELS = {"internal", "client", "external", "untrusted-web"}
MODEL_TIERS = {"haiku", "sonnet", "opus"}
FORBIDDEN_COMBOS = {("fully-autonomous", "external"), ("fully-autonomous", "financial-impact")}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?$")
REQUIRED = ["name", "description", "version", "autonomy_tier", "blast_radius", "model_tier", "trust_level"]

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
errors, warnings = [], []


def report(kind, path, msg):
    rel = os.path.relpath(path).replace("\\", "/")
    if IN_CI:
        print(f"::{kind} file={rel}::{msg}")
    else:
        print(f"{kind.upper():7s} {rel}: {msg}")
    (errors if kind == "error" else warnings).append((rel, msg))


def parse_frontmatter(text):
    """Line-based YAML-lite: top-level `key: value` pairs between the first --- pair."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            val = m.group(2).strip().strip('"').strip("'")
            fm[m.group(1)] = val
    return None  # closing --- never found


def check_skill(skill_dir):
    skill_md = os.path.join(skill_dir, "SKILL.md")
    text = open(skill_md, encoding="utf-8", errors="replace").read()
    fm = parse_frontmatter(text)
    if fm is None:
        report("error", skill_md, "frontmatter missing or unterminated (no closing ---)")
        return

    for field in REQUIRED:
        if field not in fm or not fm[field]:
            report("error", skill_md, f"required frontmatter field missing: {field}")

    ver = fm.get("version", "")
    if ver and not SEMVER_RE.match(ver):
        report("error", skill_md, f"version '{ver}' is not semver (Rule 17)")

    for field, enum, rule in (
        ("autonomy_tier", AUTONOMY_TIERS, "Rule 2"),
        ("blast_radius", BLAST_RADII, "Rule 18"),
        ("trust_level", TRUST_LEVELS, "Rule 15"),
        ("model_tier", MODEL_TIERS, "Rule 16"),
    ):
        val = fm.get(field, "")
        if val and val not in enum:
            report("error", skill_md,
                   f"{field} '{val}' not in charter v{CHARTER_VERSION} enum {sorted(enum)} ({rule})")

    combo = (fm.get("autonomy_tier", ""), fm.get("blast_radius", ""))
    if combo in FORBIDDEN_COMBOS:
        report("error", skill_md,
               f"forbidden Rule 18 combination: autonomy_tier={combo[0]} with blast_radius={combo[1]}")

    changelog = os.path.join(skill_dir, "CHANGELOG.md")
    if not os.path.isfile(changelog):
        report("error", skill_md, "CHANGELOG.md missing from skill folder (Rule 17)")
    elif ver and ver not in open(changelog, encoding="utf-8", errors="replace").read():
        report("error", changelog, f"no CHANGELOG entry mentions current version {ver} (Rule 17)")

    # ---- warnings ----
    if "model_tier_rationale" not in fm:
        report("warning", skill_md, "model_tier_rationale missing (Rule 16; backfill on next real edit)")
    if "expected_token_budget" not in fm:
        report("warning", skill_md, "expected_token_budget missing (Rule 16; backfill on next real edit)")
    if ver.startswith("0.") and fm.get("status", "") == "active":
        report("warning", skill_md, "status: active on a 0.x version (Rule 1 wants beta labeling)")

    evals_dir = os.path.join(skill_dir, "evals")
    plugin = os.path.basename(os.path.dirname(os.path.dirname(skill_dir)))
    kind = "error" if plugin in EVAL_BLOCKING_PLUGINS else "warning"
    if not os.path.isdir(evals_dir):
        report(kind, skill_md, "no evals/ directory (Rule 1; eval gate is warn-only until runners exist)")
    else:
        fixtures_dir = os.path.join(evals_dir, "fixtures")
        n = len([f for f in os.listdir(fixtures_dir)]) if os.path.isdir(fixtures_dir) else 0
        if n < 5:
            report(kind, skill_md, f"evals/fixtures/ has {n} fixtures, charter minimum is 5 (Rule 1)")
        if not os.path.isfile(os.path.join(evals_dir, "runner.py")):
            report(kind, skill_md, "evals/runner.py missing; fixtures cannot be executed/graded (Rule 1)")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plugins_root = os.path.join(root, "plugins")
    if not os.path.isdir(plugins_root):
        print(f"::error::no plugins/ directory found under {root}")
        return 1
    count = 0
    for plugin in sorted(os.listdir(plugins_root)):
        skills_root = os.path.join(plugins_root, plugin, "skills")
        if not os.path.isdir(skills_root):
            continue
        for skill in sorted(os.listdir(skills_root)):
            sd = os.path.join(skills_root, skill)
            if os.path.isfile(os.path.join(sd, "SKILL.md")):
                count += 1
                check_skill(sd)
    print(f"\nskill-standards-gate: {count} skills checked, "
          f"{len(errors)} errors, {len(warnings)} warnings (charter v{CHARTER_VERSION})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
