#!/usr/bin/env python3
"""Eval runner for eos-vision.

Two tiers, reported separately and never conflated (Build Standards Rule 3):

  structural      real PASS/FAIL assertions that run here
  conversational  realistic trigger prompts with the behaviour a good answer must
                  show. Reported PENDING until graded against a live run. A
                  fixture that has never been run is not evidence.

The structural checks all guard one thing: this skill documents field paths and
values inside the dashboard's board JSON, and `app/index.html` is the only place
those actually exist. If the app is edited and the skill is not, the skill breaks
silently -- it will read a key that is gone and report nothing wrong. These checks
turn that into a failing build.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", "..", ".."))
APP = os.path.join(REPO, "app", "index.html")


def _skill_text():
    with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def _flat(text):
    """Collapse whitespace. These files are hard-wrapped at ~92 columns, so a
    required phrase can straddle a line break ("higher is\nworse"). Matching raw
    text would fail on formatting rather than on substance."""
    return re.sub(r"\s+", " ", text)


def _app_text():
    if not os.path.isfile(APP):
        return None
    with open(APP, encoding="utf-8") as f:
        return f.read()


def check_app_contains(assertion):
    """Every token the skill relies on must exist in the dashboard app."""
    app = _app_text()
    if app is None:
        return False, f"app/index.html not found at {APP} -- cannot verify"
    missing = [t for t in assertion["tokens"] if t not in app]
    return not missing, (f"missing from app/index.html: {missing}" if missing
                         else f"all {len(assertion['tokens'])} token(s) present in the app")


def check_skill_mentions(assertion):
    """The skill body must state a rule we consider load-bearing."""
    text = _flat(_skill_text())
    missing = [t for t in assertion["phrases"] if _flat(t) not in text]
    return not missing, (f"SKILL.md never states: {missing}" if missing
                         else f"all {len(assertion['phrases'])} required statement(s) present")


def check_skill_omits(assertion):
    """The skill must NOT stray into another skill's job."""
    text = _flat(_skill_text())
    present = [t for t in assertion["phrases"] if _flat(t) in text]
    return not present, (f"SKILL.md strays into: {present}" if present
                         else "stays in its lane")


def check_schema_version_agrees(assertion):
    """The schema number the skill writes must be the one the app reads."""
    app = _app_text()
    if app is None:
        return False, "app/index.html not found -- cannot verify"
    app_versions = set(re.findall(r"schema\s*[:=]\s*(\d+)", app))
    skill_versions = set(re.findall(r'"schema"\s*:\s*(\d+)', _skill_text()))
    if not skill_versions:
        return False, "SKILL.md declares no schema version"
    if not app_versions:
        return False, "app/index.html declares no schema version"
    bad = skill_versions - app_versions
    return not bad, (f"skill writes schema {sorted(skill_versions)} but the app reads "
                     f"{sorted(app_versions)}" if bad
                     else f"schema {sorted(skill_versions)} agrees with the app")


CHECKS = {
    "app_contains": check_app_contains,
    "skill_mentions": check_skill_mentions,
    "skill_omits": check_skill_omits,
    "schema_version_agrees": check_schema_version_agrees,
}


def main():
    fixtures_dir = os.path.join(HERE, "fixtures")
    passed = failed = pending = 0
    for fname in sorted(os.listdir(fixtures_dir)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(fixtures_dir, fname), encoding="utf-8") as f:
            fixture = json.load(f)
        if fixture.get("type") == "conversational":
            pending += 1
            print(f"PENDING  {fixture['id']}: {fixture['prompt'][:68]}...")
            continue
        for assertion in fixture.get("assertions", []):
            fn = CHECKS.get(assertion["check"])
            if fn is None:
                failed += 1
                print(f"FAIL     {fixture['id']}/{assertion['check']}: no such check")
                continue
            ok, detail = fn(assertion)
            print(f"{'PASS' if ok else 'FAIL'}     {fixture['id']}/"
                  f"{assertion['check']}: {detail}")
            passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
    print()
    print(f"structural: {passed} passed, {failed} failed | "
          f"conversational: {pending} pending (not yet graded)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
