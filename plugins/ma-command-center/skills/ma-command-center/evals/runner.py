#!/usr/bin/env python3
"""Eval runner for ma-command-center.

Structural checks run the real engine that ships beside this skill. They are not
prose assertions about the engine; they call it. Two tiers per Build Standards
Rule 3 -- conversational fixtures stay PENDING until graded against a live run.

The load-bearing property under test is the counter-intuitive one: a check the
gate CANNOT run must fail, not pass. If that ever inverts, this plugin becomes a
tool that tells people their numbers are fine when it never looked.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
PLUGIN = os.path.abspath(os.path.join(SKILL_DIR, "..", ".."))
sys.path.insert(0, os.path.join(PLUGIN, "engine"))


def _engine():
    from ma_engine import validate as V  # noqa: PLC0415
    return V


def check_empty_input_fails_every_check(assertion):
    """The whole point. An empty deal file must not pass."""
    V = _engine()
    rep = V.validate({}, hard_stop=False)
    if rep.status != "fail":
        return False, f"an empty deal file reported {rep.status!r}"
    passed = [c.name for c in rep.checks if c.blocking and c.passed]
    return not passed, (f"blocking checks passed on empty input: {passed}"
                        if passed else
                        f"all {sum(1 for c in rep.checks if c.blocking)} blocking "
                        "checks failed, each saying it could not run")


def check_unrunnable_says_so(assertion):
    """A failure must explain itself, or nobody can act on it."""
    V = _engine()
    rep = V.validate({}, hard_stop=False)
    silent = [c.name for c in rep.checks
              if not c.passed and "could not run" not in (c.detail or "")]
    return not silent, (f"failed without saying why: {silent}" if silent
                        else "every unrunnable check reports 'could not run'")


def check_hard_stop_raises(assertion):
    """hard_stop=True must stop, not hand back a report a caller may ignore."""
    V = _engine()
    try:
        V.validate({}, hard_stop=True)
    except Exception as e:                                   # noqa: BLE001
        return type(e).__name__ == "MAError", (
            f"raised {type(e).__name__}, expected MAError")
    return False, "returned normally on a failing gate"


def check_tolerance_is_a_dollar(assertion):
    V = _engine()
    ok = V.SUBTOTAL_TOLERANCE == 1.00
    return ok, (f"SUBTOTAL_TOLERANCE is {V.SUBTOTAL_TOLERANCE}, expected 1.00 "
                "-- a percentage tolerance would let a wrong schedule through"
                if not ok else "subtotal tolerance is $1.00")


def check_snapshot_block_shape(assertion):
    """The renderer reads this block. If it changes shape the validation page
    silently renders an empty table."""
    V = _engine()
    block = V.validate({}, hard_stop=False).as_snapshot_block()
    missing = [k for k in ("status", "checks", "flags") if k not in block]
    if missing:
        return False, f"snapshot block missing {missing}"
    if not block["checks"]:
        return False, "snapshot block carries no checks"
    for c in block["checks"]:
        gaps = [k for k in ("name", "passed", "delta", "detail", "blocking")
                if k not in c]
        if gaps:
            return False, f"check dict missing {gaps}"
    return True, "status, checks and flags all present and well-formed"


def check_render_is_self_contained(assertion):
    """No network access from a rendered page: it has to work offline, forever,
    from an email attachment."""
    from ma_engine.render import render_command_center  # noqa: PLC0415
    html = render_command_center("Acme Holdings", "Target Co", {},
                                 audience="client", prepared_by="Acme Holdings")
    bad = [t for t in ("http://", "https://", "<script src", "<link ")
           if t in html]
    if bad:
        return False, f"rendered page reaches outside itself: {bad}"
    if not html.startswith("<!DOCTYPE html>"):
        return False, "output is not a complete HTML document"
    return True, f"self-contained, {len(html):,} bytes, no external references"


def check_prepared_by_is_honoured(assertion):
    """Left at its default the footer says CFOforIT, which is a false
    attribution on someone else's document."""
    from ma_engine.render import render_command_center  # noqa: PLC0415
    html = render_command_center("Acme Holdings", "Target Co", {},
                                 audience="client", prepared_by="Acme Holdings")
    if "CFOFORIT" in html or "Prepared by CFOforIT" in html:
        return False, "prepared_by was ignored; the page still credits CFOforIT"
    return "ACME HOLDINGS" in html, "masthead and footer credit the caller"


def check_target_audience_refused(assertion):
    """Showing a seller your own valuation of them is an unforced loss, and the
    field-level filtering to do it safely is not implemented."""
    from ma_engine.render import render_command_center  # noqa: PLC0415
    try:
        render_command_center("A", "B", {}, audience="target")
    except NotImplementedError:
        return True, "audience='target' raises rather than silently downgrading"
    except Exception as e:                                   # noqa: BLE001
        return False, f"raised {type(e).__name__}, expected NotImplementedError"
    return False, "audience='target' was allowed"


def check_no_reference_library_shipped(assertion):
    """This plugin is the engine, not a methodology. If a checklist ever appears
    here, the split that lets it be public has broken."""
    hits = []
    for root, _dirs, files in os.walk(PLUGIN):
        for f in files:
            if f in assertion["forbidden_files"]:
                hits.append(os.path.relpath(os.path.join(root, f), PLUGIN))
    return not hits, (f"proprietary library present: {hits}" if hits
                      else "no reference library ships with this plugin")


CHECKS = {
    "empty_input_fails_every_check": check_empty_input_fails_every_check,
    "unrunnable_says_so": check_unrunnable_says_so,
    "hard_stop_raises": check_hard_stop_raises,
    "tolerance_is_a_dollar": check_tolerance_is_a_dollar,
    "snapshot_block_shape": check_snapshot_block_shape,
    "render_is_self_contained": check_render_is_self_contained,
    "prepared_by_is_honoured": check_prepared_by_is_honoured,
    "target_audience_refused": check_target_audience_refused,
    "no_reference_library_shipped": check_no_reference_library_shipped,
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
            print(f"PENDING  {fixture['id']}: {fixture['prompt'][:66]}...")
            continue
        for assertion in fixture.get("assertions", []):
            fn = CHECKS.get(assertion["check"])
            if fn is None:
                failed += 1
                print(f"FAIL     {fixture['id']}/{assertion['check']}: no such check")
                continue
            try:
                ok, detail = fn(assertion)
            except Exception as e:                           # noqa: BLE001
                ok, detail = False, f"{type(e).__name__}: {e}"
            print(f"{'PASS' if ok else 'FAIL'}     {fixture['id']}/"
                  f"{assertion['check']}: {detail}")
            passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
    print()
    print(f"structural: {passed} passed, {failed} failed | "
          f"conversational: {pending} pending (not yet graded)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
