#!/usr/bin/env python3
"""Eval runner for listing-watch.

Two tiers, reported separately and never conflated (Build Standards Rule 3):

  structural      real PASS/FAIL assertions that run here
  conversational  realistic trigger prompts with the behaviour a good answer must
                  show. Reported PENDING until graded against a live run. A
                  fixture that has never been run is not evidence.

The structural checks guard two things. First, that the rules this skill is built
around are actually stated in SKILL.md, because a rule that lives only in the
author's head is not a rule. Second, that `scripts/lw.py` really behaves the way
the body promises -- most importantly that a blocked page and an empty page never
collapse into the same output. That is the failure this whole skill exists to
prevent, and it is cheap to assert, so it is asserted.

Run: python3 evals/runner.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))


def _skill_text():
    with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def _flat(text):
    """Collapse whitespace. These files are hard-wrapped, so a required phrase can
    straddle a line break. Matching raw text would fail on formatting, not substance."""
    return re.sub(r"\s+", " ", text)


def check_skill_mentions(assertion):
    text = _flat(_skill_text())
    missing = [t for t in assertion["phrases"] if _flat(t) not in text]
    return not missing, (f"SKILL.md never states: {missing}" if missing
                         else f"all {len(assertion['phrases'])} required statement(s) present")


def check_skill_omits(assertion):
    text = _flat(_skill_text())
    present = [t for t in assertion["phrases"] if _flat(t) in text]
    return not present, (f"SKILL.md strays into: {present}" if present
                         else "stays in its lane")


def check_status_mapping(assertion):
    """Page wording must land on the status the skill claims it does."""
    import lw
    bad = []
    for raw, expected in assertion["cases"]:
        got = lw.normalize_status(raw)
        if got != expected:
            bad.append(f"{raw!r} -> {got}, expected {expected}")
    return not bad, ("; ".join(bad) if bad
                     else f"{len(assertion['cases'])} status mapping(s) correct")


def check_name_matching(assertion):
    """Nicknames and credential suffixes must not read as different people, and a
    genuinely different person must not read as a match."""
    import lw
    bad = []
    for roster, page, expected in assertion["cases"]:
        got, score = lw.match_names(roster, page, 0.80)
        if got != expected:
            bad.append(f"{roster!r} vs {page!r} -> {got} ({score}), expected {expected}")
    return not bad, ("; ".join(bad) if bad
                     else f"{len(assertion['cases'])} name comparison(s) correct")


def check_blocked_is_not_empty(assertion):
    """The load-bearing one. A blocked visit and an empty-but-read visit must produce
    different coverage numbers, or the report can call a broken night a quiet one."""
    import lw
    config = {"sites": ["zillow"], "near_match_threshold": 0.80,
              "qualifying_statuses": lw.DEFAULT_QUALIFYING, "sold_window_days": 14}
    import datetime as dt
    end = dt.date(2026, 8, 16)
    start = end - dt.timedelta(days=14)

    def coverage(outcome):
        obs = {"visits": [{"agent_name": "A", "site": "zillow", "profile_url": "https://x",
                           "outcome": outcome, "name_on_page": "A", "listings": []}]}
        _, _, _, per_site, _ = lw.build_rows(config, obs, start, end)
        return per_site["zillow"]

    read = coverage("ok")
    blocked = coverage("blocked")
    problems = []
    if read["ok"] != 1 or read["blocked"] != 0:
        problems.append(f"a read page counted as {read}")
    if blocked["blocked"] != 1 or blocked["ok"] != 0:
        problems.append(f"a blocked page counted as {blocked}")
    if read == blocked:
        problems.append("blocked and read produce identical coverage")
    return not problems, ("; ".join(problems) if problems
                          else "blocked and read are distinct outcomes")


def check_sold_window(assertion):
    """A sale older than the window is not a lead; one inside it is. A sale with no
    date shown is kept and flagged, never silently dropped."""
    import lw
    import datetime as dt
    config = {"sites": ["zillow"], "near_match_threshold": 0.80,
              "qualifying_statuses": lw.DEFAULT_QUALIFYING, "sold_window_days": 14}
    end = dt.date(2026, 8, 16)
    start = end - dt.timedelta(days=14)
    obs = {"visits": [{"agent_name": "A", "site": "zillow", "profile_url": "https://x",
                       "outcome": "ok", "name_on_page": "A", "listings": [
                           {"address": "in window", "status": "Sold", "status_date": "2026-08-10"},
                           {"address": "too old", "status": "Sold", "status_date": "2026-01-02"},
                           {"address": "no date", "status": "Sold", "status_date": None},
                           {"address": "just active", "status": "For sale", "status_date": None}]}]}
    hits, _, _, _, _ = lw.build_rows(config, obs, start, end)
    got = sorted(h["address"] for h in hits)
    want = ["in window", "no date"]
    dated = [h for h in hits if h["address"] == "no date"]
    detail_ok = dated and "no sale date shown" in dated[0]["notes"]
    if got != want:
        return False, f"kept {got}, expected {want}"
    if not detail_ok:
        return False, "an undated sale was kept but not flagged as undated"
    return True, "window respected; undated sale kept and flagged"


CHECKS = {
    "skill_mentions": check_skill_mentions,
    "skill_omits": check_skill_omits,
    "status_mapping": check_status_mapping,
    "name_matching": check_name_matching,
    "blocked_is_not_empty": check_blocked_is_not_empty,
    "sold_window": check_sold_window,
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
