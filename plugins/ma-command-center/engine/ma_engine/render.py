"""render.py -- deal JSON -> self-contained HTML M&A command-center artifact.

Mirrors cfoforit-client-delivery/engine/mhr_engine/render.py's visual system
(locked palette, toptabs shell, tile component, validation table) WITHOUT
importing it -- cfoforit-ma is a fully independent plugin (Steve, 2026-07-26:
"put it under its own plugin ... I do not want to have the client plugin get
too big"). Consistency here means the same design tokens and shell pattern,
duplicated on purpose, not a runtime code dependency between the two plugins.

One scoped exception to the firm's no-red-in-client-materials convention:
the Tab 4 validation gate renders red on a failed check (original build
brief, Section 8; confirmed by Steve 2026-07-26). Nowhere else in this
command center uses red.

Every financial number rendered here is read straight from the deal JSON the
skills wrote -- nothing in the browser recomputes EBITDA, a tie-out, or a
validation check. The one calculation the artifact performs is the strategic-fit
weighted average, because that is the client's own judgment being re-weighted
live (Steve, 2026-07-26). See the "Two-engine reconciliation contract" below for
why that cannot silently disagree with the record.

This module renders whatever files exist and shows a plain empty state for
whatever doesn't (deal-stage gating means most targets only have Tab 1
populated).

Two-engine reconciliation contract
----------------------------------
Steve, 2026-07-28: in-artifact calculation is fine, but it must "never create a
conflict between the actual data and what the artifact is using to render any
calculations."

Two implementations of one formula cannot be made identical by asserting it, so
the design makes disagreement loud instead of impossible:

1. `composite_fit_score()` in this module is canonical. The JS `score()` is a
   deliberate re-implementation, and `tests/test_reconciliation.py` extracts the
   real shipped JS and runs it under node against the same cases as the Python.
   The two engines are tested to agree, not assumed to.
2. At render time Python reconciles the score SAVED in the deal record against
   the same formula re-run on that record's OWN attributes. Disagreement renders
   a red banner naming both numbers -- a deal file whose composite_score has
   drifted from its attributes is never displayed as if it were fine.
3. The page carries `data-baseline` (Python's answer). On load the JS recomputes
   the untouched inputs and compares. If it can't reproduce the number the page
   was rendered with, it reveals a red banner and DISABLES the emit button
   rather than showing a figure neither engine vouches for.
4. The of-record score is server-rendered and always visible. The browser's own
   number only ever appears in a separate amber "Working score (unsaved)" tile
   that stays hidden until the client actually edits something. The two are
   never shown in the same slot.
5. Nothing here persists. An edit leaves as JSON carrying `_provenance`
   (the baseline it started from, the render's `data-as-of`, and whether it was
   changed at all) so the write gate can refuse to land on a deal file that has
   moved on since the page was rendered.
"""

from __future__ import annotations

import datetime as _dt
import html
import json as _json

NAVY = "#002060"
STEEL = "#4682B4"
# These are the firm's brand values, matching mhr_engine and the rest of the
# repo exactly. Steve, 2026-07-29: "let's get the green and amber colors to be
# consistent in everything we create ... make these match what we have on the
# MHR engine." An earlier version of this file shipped darker variants for
# contrast; consistency won. tests/test_palette.py pins these so the two
# duplicated palettes cannot drift apart again silently.
GREEN = "#3CB371"
AMBER = "#D97706"
RED = "#A5301F"  # scoped: validation-gate fail state only (Section 8 exception)
PAPER = "#F7F5F0"
INK = "#16233A"
INK_SOFT = "#4C5A70"
BORDER = "#E4DFD3"


def _esc(v):
    return html.escape("" if v is None else str(v))


def _fmt_money(v):
    """Format a $K figure. Degrades to a flagged cell on a non-numeric value
    rather than raising: a malformed figure in one row must not take down the
    whole render, and silently dropping it would be worse than showing that
    something is wrong there."""
    if v is None:
        return _na()
    try:
        v = float(v)
    except (TypeError, ValueError):
        return _na("non-numeric")
    return f"(${abs(v):,.0f}K)" if v < 0 else f"${v:,.0f}K"


def _fmt_pct(v):
    if v is None:
        return _na()
    try:
        v = float(v)
    except (TypeError, ValueError):
        return _na("non-numeric")
    return f"({abs(v) * 100:.1f}%)" if v < 0 else f"{v * 100:.1f}%"


def _na(label="not provided"):
    return f'<span class="na">{_esc(label)}</span>'


def _tile(label, value, sub=""):
    """label and sub are ESCAPED (pass plain text); `value` is inserted as RAW
    HTML so callers can pass _fmt_money()/_na() output. Passing unescaped
    user data as `value` is an injection; passing HTML as `sub` renders the
    tags literally. Both mistakes have been made here -- check which you want."""
    sub_html = f'<div class="tile-sub">{_esc(sub)}</div>' if sub else ""
    return (f'<div class="tile"><div class="tile-label">{_esc(label)}</div>'
            f'<div class="tile-val">{value}</div>{sub_html}</div>')


def _status_pill(status):
    colors = {
        "not_started": INK_SOFT, "requested": AMBER, "received": STEEL,
        "reviewed": GREEN, "flagged": RED,
        "in_progress": AMBER, "complete": GREEN, "blocked": RED,
    }
    color = colors.get(status, INK_SOFT)
    return f'<span class="pill" style="color:{color};border-color:{color}">{_esc(status or "n/a")}</span>'


def _empty_state(tab_label, action_hint):
    return (f'<div class="empty-state"><p><strong>{_esc(tab_label)}</strong> has not been started for this target.</p>'
            f'<p class="empty-hint">{_esc(action_hint)}</p></div>')


# ---------------------------------------------------------------------------
# Strategic-fit editor
#
# Steve, 2026-07-26: "the client should be able to rank the weight of each of
# the categories ... those categories may change ... the client can change it
# and update it ... enter data and for it to recalculate and reformat."
#
# This is a deliberate, scoped departure from the build brief's "no logic in
# the artifact" rule. The reading: that rule exists so financial truth is never
# recomputed in a browser, away from the validation gate. A weighted average of
# values the user just typed is not financial truth -- it is the user's own
# judgment, arithmetic they could do on paper. So live recalculation here is
# fine; recomputing EBITDA or a tie-out here would not be.
#
# What is NOT bent: the artifact still cannot persist. Per the brief, artifacts
# may not write to SharePoint and must not use browser storage. So edits live
# only in the page until the user copies the emitted JSON back to the skill,
# which writes it under the normal confirm-before-write gate. Nothing the client
# types here can silently become the record.
#
# Attributes are read from the document, never hardcoded: the list is expected
# to change per client and per deal, and rows can be added or removed in-page.
# ---------------------------------------------------------------------------

_FIT_SCALE = {"yes": 1.0, "partial": 0.5, "no": 0.0}

# Tolerance for agreeing that two computations of the same score are the same
# number. Tighter than the 2dp we display, loose enough that float noise across
# two languages is not reported as a discrepancy.
_RECONCILE_TOL = 5e-5


def composite_fit_score(attrs, scale=None):
    """The canonical weighted-fit formula. Python owns it; the in-page JS is a
    re-implementation that gets reconciled against this on every load.

    Blank weight means "equal share" (an unweighted row still counts rather
    than scoring zero). An attribute with no fit chosen is excluded from both
    numerator and denominator -- unanswered must never read as "no".

    Returns (score|None, scored_count, attribute_count).
    """
    scale = scale or _FIT_SCALE
    attrs = attrs or []
    wsum = acc = 0.0
    scored = 0
    for a in attrs:
        fit = a.get("fit")
        if not fit or fit not in scale:
            continue
        w = a.get("weight")
        try:
            w = 1.0 if w in (None, "") else float(w)
        except (TypeError, ValueError):
            w = 1.0
        wsum += w
        acc += w * float(scale[fit])
        scored += 1
    if not scored or wsum <= 0:
        return None, scored, len(attrs)
    return acc / wsum, scored, len(attrs)


def _fmt_score(v):
    """Format a score for display without assuming it is a number. A deal file
    with junk in composite_score must render that junk visibly (escaped), not
    crash the page and not silently blank it."""
    if v is None:
        return "&mdash;"
    try:
        return _esc(f"{float(v):.2f}")
    except (TypeError, ValueError):
        return _esc(v)


def _reconcile(stored, derived):
    """Compare the score saved in the deal record against the same formula run
    fresh on that record's own attributes. Returns (ok, banner_html).

    A mismatch is never smoothed over: it means the JSON's composite_score and
    its attributes disagree, and which one is right is a question for a human.
    """
    if stored is None or derived is None:
        return True, ""
    try:
        if abs(float(stored) - float(derived)) <= _RECONCILE_TOL:
            return True, ""
    except (TypeError, ValueError):
        return False, (
            '<div class="banner banner-red"><strong>Calculation mismatch.</strong> '
            f'The deal record stores a composite fit score of {_esc(stored)}, which is not a '
            'number this engine can re-derive. Displayed figures are not reconciled &mdash; '
            'do not rely on this panel until the deal record is corrected.</div>')
    return False, (
        '<div class="banner banner-red"><strong>Calculation mismatch &mdash; do not rely on this '
        'score.</strong> The deal record stores a composite fit of '
        f'<strong>{_esc(f"{float(stored):.4f}")}</strong>, but re-running the same weighted formula '
        f'on that record&rsquo;s own attributes gives <strong>{_esc(f"{derived:.4f}")}</strong>. '
        'The stored value and the attributes behind it disagree. Re-save the screen through '
        'ma-financial-summary to resolve which is correct.</div>')


def _strategic_fit_editor(fit: dict, *, interactive: bool = True) -> str:
    attrs = fit.get("attributes", []) or []
    scale = fit.get("fit_scale") or _FIT_SCALE
    stored = fit.get("composite_score")
    rec = fit.get("recommendation") or "pending"

    # Reconcile at render time, in Python, against the record as it sits on
    # disk -- before any client interaction can muddy the question.
    derived, scored_n, attr_n = composite_fit_score(attrs, scale)
    reconciled, mismatch_banner = _reconcile(stored, derived)
    of_record = stored if stored is not None else derived

    if not interactive:
        rows = "".join(
            f'<tr><td>{_esc(a.get("name"))}</td>'
            f'<td>{_esc(a.get("fit") or "pending")}</td>'
            f'<td>{_esc(a.get("weight")) if a.get("weight") is not None else _na("unweighted")}</td></tr>'
            for a in attrs)
        return (mismatch_banner
                + _tile("Composite fit score (of record)",
                        _fmt_score(of_record) if of_record is not None else _na("pending"), rec)
                + '<table><thead><tr><th>Key attribute</th><th>Fit</th>'
                  f'<th>Weight</th></tr></thead><tbody>{rows}</tbody></table>')

    def opts(sel):
        return "".join(
            f'<option value="{_esc(k)}"{" selected" if (sel or "") == k else ""}>{_esc(k)}</option>'
            for k in ("", *scale.keys()))

    rows = "".join(
        f'<tr data-fit-row>'
        f'<td><input class="fx-name" type="text" value="{_esc(a.get("name"))}" '
        f'aria-label="Attribute name"></td>'
        f'<td><select class="fx-fit" aria-label="Fit">{opts(a.get("fit"))}</select></td>'
        f'<td><input class="fx-w" type="number" min="0" step="any" '
        f'value="{_esc(a.get("weight")) if a.get("weight") is not None else ""}" '
        f'placeholder="equal" aria-label="Weight"></td>'
        f'<td><button type="button" class="fx-del" aria-label="Remove attribute">&times;</button></td>'
        f'</tr>'
        for a in attrs)

    scale_json = _json.dumps(scale)
    # data-baseline is Python's own answer for the unmodified inputs. The JS
    # re-checks itself against it on load; if the two engines disagree the page
    # says so in red instead of quietly showing the JS number.
    baseline_attr = "" if derived is None else f"{derived:.6f}"
    of_record_txt = _fmt_score(of_record)
    return f"""
<div class="fx" data-fit-scale='{_esc(scale_json)}' data-baseline="{_esc(baseline_attr)}"
     data-reconciled="{'1' if reconciled else '0'}">
  {mismatch_banner}
  <div class="banner banner-amber fx-dirty-banner" id="fxDirty" hidden>
    <strong>Working copy &mdash; not saved.</strong> You have changed the weights or attributes.
    The deal record still says <strong>{of_record_txt}</strong>. Nothing below becomes the record
    until the emitted JSON is written back through CFOforIT.
  </div>
  <div class="banner banner-red" id="fxDrift" hidden>
    <strong>Calculation engine mismatch.</strong> The in-page calculator did not reproduce the
    score this page was rendered with. Do not rely on the figures in this panel; send the page
    back to CFOforIT.
  </div>
  <div class="summary-strip">
    <div class="tile"><div class="tile-label">Composite fit score (of record)</div>
      <div class="tile-val" id="fxOfRecord">{of_record_txt}</div>
      <div class="tile-sub">{_esc(rec)}</div></div>
    <div class="tile" id="fxWorkingTile" hidden><div class="tile-label">Working score (unsaved)</div>
      <div class="tile-val" id="fxScore">&mdash;</div>
      <div class="tile-sub" id="fxRec">&nbsp;</div></div>
    <div class="tile"><div class="tile-label">Weights total</div>
      <div class="tile-val" id="fxWsum">&mdash;</div>
      <div class="tile-sub">blank weights count as equal</div></div>
  </div>
  <p class="fx-help">Set a weight per attribute and pick the fit. A working score recalculates as
  you type, shown <em>alongside</em> the score of record so the two are never confused. Attributes
  are yours to change &mdash; rename, add or remove rows to match what matters on this deal.
  Nothing here is saved automatically: use <em>Copy updated JSON</em> and hand it back so it can be
  written to the deal record.</p>
  <table><thead><tr><th>Key attribute</th><th>Fit</th><th>Weight</th><th></th></tr></thead>
  <tbody id="fxBody">{rows}</tbody></table>
  <div class="fx-actions">
    <button type="button" id="fxAdd">+ Add attribute</button>
    <button type="button" id="fxCopy">Copy updated JSON</button>
    <button type="button" id="fxReset">Revert to record</button>
    <span id="fxMsg" class="fx-msg"></span>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Tab 1 -- One-Page Summary (go-no-go-screen.json)
# ---------------------------------------------------------------------------

def render_tab1_summary(doc: dict | None, *, interactive: bool = True) -> str:
    if not doc:
        return _empty_state("One-Page Summary",
                             "Run ma-financial-summary to screen this target and produce a Go/No-Go one-pager.")

    meta = doc.get("meta", {})
    frozen = meta.get("snapshot_frozen")
    banner = (
        f'<div class="banner banner-amber">Pre-LOI screen &middot; seller-supplied, unaudited'
        f'{" &middot; frozen at LOI" if frozen else ""}</div>'
    )

    fit_block = _strategic_fit_editor(doc.get("strategic_fit", {}), interactive=interactive)

    snap = doc.get("financial_snapshot", {})
    periods = snap.get("periods", [])
    lines = snap.get("lines", [])
    snap_rows = ""
    if periods and lines:
        head = "".join(f"<th>{_esc(p)}</th>" for p in periods)
        body = ""
        for line in lines:
            vals = line.get("values", {})
            cells = "".join(f"<td>{_fmt_money(vals.get(p))}</td>" for p in periods)
            body += f'<tr><td>{_esc(line.get("label"))}</td>{cells}</tr>'
        snap_rows = f'<table><thead><tr><th>$K</th>{head}</tr></thead><tbody>{body}</tbody></table>'
    else:
        snap_rows = _empty_state("Financial snapshot", "No historical financials supplied yet.")

    conc = doc.get("customer_concentration", {})
    conc_html = (
        f'<p>Top customer {_fmt_pct(conc.get("top1_pct_of_revenue"))} of revenue &middot; '
        f'top 5 {_fmt_pct(conc.get("top5_pct_of_revenue"))} &middot; '
        f'top 10 {_fmt_pct(conc.get("top10_pct_of_revenue"))}</p>'
    ) if conc else _empty_state("Customer concentration", "Not provided yet.")

    pricing = doc.get("estimated_pricing", {})
    pricing_html = (
        f'<p>Estimated multiple {_esc(pricing.get("estimated_multiple_low"))}&ndash;'
        f'{_esc(pricing.get("estimated_multiple_high"))}x on {_esc(pricing.get("basis") or "n/a")} &middot; '
        f'EBITDA impact {_fmt_money(pricing.get("estimated_ebitda_impact"))}</p>'
    )

    return (
        banner
        + '<h1>Strategic fit</h1>' + fit_block
        + '<h1>5-year financial snapshot</h1>' + snap_rows
        + '<h1>Customer concentration</h1>' + conc_html
        + '<h1>Estimated deal economics</h1>' + pricing_html
    )


# ---------------------------------------------------------------------------
# Tab 2 -- Diligence (diligence-requests.json + diligence-workplan.json)
# ---------------------------------------------------------------------------

def _stage_badge(stage):
    return f'<span class="stage-badge stage-{_esc(stage)}">Stage {_esc(stage)}</span>' if stage else ""


# ---------------------------------------------------------------------------
# Collapsible groups and the open-items filter
#
# Steve, 2026-07-29: "when there's a list of items that are grouped, we can
# click on the arrow to group or ungroup each one of those sections ... when
# something is considered done, the user has the ability to click a button that
# only shows the things that are still open ... quickly toggle between
# everything and just the items that are still open."
#
# Two things, built once and used by every tab so the interaction is identical
# wherever there is a grouped list.
#
# What "done" means is NOT a UI decision -- it comes from each file's own status
# lifecycle, and the two lifecycles are different (that distinction was the
# single biggest schema error in the original brief). Encoded once here rather
# than re-derived per tab:
#
#   request checklist   not_started -> requested -> received -> reviewed
#                       done = reviewed. `flagged` is OPEN and needs attention.
#   workplan / Gantt    not_started -> in_progress -> complete, plus blocked
#                       done = complete. `blocked` is OPEN -- a blocked task is
#                       the opposite of finished, and hiding it would bury the
#                       thing most likely to sink a deadline.
#
# `applicable: false` is a THIRD state, not a synonym for done. An item ruled
# not applicable is neither outstanding nor accomplished; counting it as done
# would overstate progress, and counting it as open would send someone chasing
# a request nobody wants.
#
# Two honesty rules the filter must respect, because a filtered list that looks
# like a complete list is a misleading document and these get screenshotted:
#
#   1. The summary tiles NEVER change with the filter. They describe the record.
#      Only row visibility changes.
#   2. When a filter is active the page says so, visibly, above the list.
# ---------------------------------------------------------------------------

_DONE_STATUS = frozenset({"reviewed", "complete"})

# Statuses that are open AND need attention ahead of the rest. Kept separate
# from "open" so the filter can surface them without inventing a third mode.
_ATTENTION_STATUS = frozenset({"flagged", "blocked"})


def _item_state(obj) -> str:
    """'done' | 'open' | 'na' for any request item or Gantt task.

    Reads `applicable` and `status` only, so it works across both lifecycles
    without the caller having to know which one it is holding.
    """
    if obj.get("applicable") is False:
        return "na"
    return "done" if obj.get("status") in _DONE_STATUS else "open"


def _row_attrs(obj) -> str:
    """Attributes the client-side filter switches on. Put on every <tr> in a
    filterable list."""
    state = _item_state(obj)
    attrs = f' data-item data-state="{state}"'
    if obj.get("status") in _ATTENTION_STATUS:
        attrs += ' data-attention="1"'
    return attrs


def _count_states(items) -> tuple[int, int, int]:
    """(open, done, na). One pass, so a group header cannot disagree with its
    own rows."""
    o = d = n = 0
    for it in items:
        s = _item_state(it)
        o += s == "open"
        d += s == "done"
        n += s == "na"
    return o, d, n


def _group_summary_counts(items) -> str:
    """The count badge in a group header.

    Shows open-of-actionable, not done-of-total: the question a user has in
    front of a diligence list is "how much is left", and `12/40` reads
    ambiguously in both directions. `na` is reported separately rather than
    folded into either number.
    """
    o, d, n = _count_states(items)
    actionable = o + d
    if o == 0 and actionable:
        badge = '<span class="count count-done">all done</span>'
    else:
        badge = (f'<span class="count"><strong data-open-count>{o}</strong> '
                 f'of {actionable} open</span>')
    if n:
        badge += f' <span class="count count-na">{n} n/a</span>'
    return badge


def _group(name: str, items, inner_html: str, *, cls: str = "section-group",
           open_by_default: bool = False, extra_attrs: str = "") -> str:
    """One collapsible group: click the arrow to expand or collapse.

    `items` is used for the header counts and for the filter's decision about
    whether this whole group is finished. `inner_html` is already-rendered
    content, so a group can hold a table, nested groups, or both.
    """
    o, d, n = _count_states(items)
    return (
        f'<details class="{cls}" data-group data-open-items="{o}" '
        f'data-total-items="{o + d + n}"{" open" if open_by_default else ""}'
        f'{extra_attrs}>'
        f'<summary><span class="grp-arrow" aria-hidden="true"></span>'
        f'<span class="grp-name">{_esc(name)}</span> '
        f'{_group_summary_counts(items)}'
        f'<span class="grp-done-chip">complete</span></summary>'
        f'{inner_html}</details>'
    )


def _list_toolbar(scope_id: str, *, noun: str = "items",
                  filterable: bool = True) -> str:
    """The controls above a grouped list. One per list region.

    `aria-pressed` carries the toggle state so the control is operable and
    announced correctly without a live region; the JS reads it as the source of
    truth rather than keeping a separate variable that could drift from what the
    button looks like.
    """
    filt = (
        f'<div class="lt-seg" role="group" aria-label="Filter {_esc(noun)}">'
        f'<button type="button" class="lt-btn active" data-filter="all" '
        f'aria-pressed="true">All</button>'
        f'<button type="button" class="lt-btn" data-filter="open" '
        f'aria-pressed="false">Open only</button>'
        f'</div>'
    ) if filterable else ""
    return (
        f'<div class="list-toolbar" data-listscope="{_esc(scope_id)}">'
        f'{filt}'
        f'<button type="button" class="lt-btn lt-plain" data-expand="all">'
        f'Expand all</button>'
        f'<button type="button" class="lt-btn lt-plain" data-expand="none">'
        f'Collapse all</button>'
        f'<span class="lt-state" data-filter-note hidden>'
        f'Filtered &mdash; showing open {_esc(noun)} only. '
        f'<strong>This is not the full list.</strong></span>'
        f'</div>'
    )


def render_tab2_requests(doc: dict | None, stage_filter: int = 1) -> str:
    if not doc:
        return _empty_state("Diligence request checklist",
                             "Advance this target past screening to spin up the 361-item request checklist.")
    sections = doc.get("sections", [])

    def _sec_items(sec):
        """Legal nests one level deep. Counting only sec["items"] silently
        undercounts by ~180 requests once subsections exist."""
        out = list(sec.get("items", []))
        for sub in sec.get("subsections", []):
            out.extend(sub.get("items", []))
        return out

    all_items = [it for s in sections for it in _sec_items(s)]
    total = len(all_items)
    outstanding = sum(1 for it in all_items if it["status"] not in ("reviewed",))
    flagged = sum(1 for it in all_items if it["status"] == "flagged")

    strip = (
        f'<div class="summary-strip">{_tile("Total requests", total)}'
        f'{_tile("Outstanding", outstanding)}{_tile("Flagged", flagged, "review these first")}</div>'
    )

    def _rows(items):
        # The stage badge was previously emitted OUTSIDE a <td>, which put it
        # between cells where a browser hoists it out of the row entirely.
        return "".join(
            f'<tr{_row_attrs(it)}><td>{_esc(it["reference_source"])}</td>'
            f'<td>{_esc(it["description"])}</td>'
            f'<td>{_stage_badge(it["stage"])}</td>'
            f'<td>{_status_pill(it["status"])}</td></tr>'
            for it in items)

    def _keep(items):
        return [it for it in items
                if stage_filter is None or (it["stage"] or 99) <= stage_filter]

    body = []
    for sec in sections:
        direct = _keep(sec.get("items", []))
        subs = [(sub, _keep(sub.get("items", []))) for sub in sec.get("subsections", [])]
        subs = [(sub, its) for sub, its in subs if its]
        shown = direct + [it for _, its in subs for it in its]
        if not shown:
            continue
        inner = f'<table><tbody>{_rows(direct)}</tbody></table>' if direct else ""
        for sub, its in subs:
            # Legal nests, so a subsection is a group in its own right and gets
            # its own arrow and its own counts.
            inner += _group(sub["name"], its,
                            f'<table><tbody>{_rows(its)}</tbody></table>',
                            cls="subsection-group")
        body.append(_group(sec["name"], shown, inner))

    return (strip
            + f'<div class="stage-note">Showing Stage {stage_filter} and below '
              f'&middot; {"preliminary checklist only" if stage_filter == 1 else "full list"}'
              f'</div>'
            + _list_toolbar("requests", noun="requests")
            + "".join(body))


def render_tab2_workplan(doc: dict | None) -> str:
    if not doc:
        return _empty_state("Diligence team workplan",
                             "Advance this target past screening to spin up the internal analysis workplan.")
    tasks = doc.get("tasks", [])
    by_role = {}
    for t in tasks:
        by_role.setdefault(t["role"], []).append(t)

    body = []
    for role, rtasks in by_role.items():
        rows = "".join(
            f'<tr{_row_attrs(t)}><td>{_esc(t["task"])}'
            + (f' <span class="dup-tag">dual review</span>'
               if t.get("duplicate_role_group") else "")
            + f'</td><td>{_status_pill(t["status"])}</td>'
              f'<td>{_esc(t["percent_complete"])}%</td></tr>'
            for t in rtasks
        )
        body.append(_group(role, rtasks,
                           f'<table><tbody>{rows}</tbody></table>'))
    return _list_toolbar("workplan", noun="tasks") + "".join(body)


# ---------------------------------------------------------------------------
# Tab 3 -- Integration Gantt (integration.json)
# ---------------------------------------------------------------------------

def render_tab3_integration(doc: dict | None) -> str:
    if not doc:
        return _empty_state("Integration Gantt",
                             "Advance this target to integration to spin up the 145-task department Gantt.")
    tasks = doc.get("tasks", [])
    synergy_tasks = [t for t in tasks if t.get("synergy")]
    projected = sum(t["synergy"]["projected_annual_value"] or 0 for t in synergy_tasks)
    realized = sum(t["synergy"]["realized_annual_value"] or 0 for t in synergy_tasks)
    # `sub` is escaped by _tile, so it must be PLAIN TEXT -- passing HTML here
    # renders the tags literally to the viewer.
    realized_txt = (f"{realized:,.0f}K realized" if realized else "none realized yet")
    synergy_strip = _tile("Synergy: projected",
                          _fmt_money(projected) if projected else _na("not yet estimated"),
                          realized_txt)

    by_dept = {}
    for t in tasks:
        by_dept.setdefault(t["department"], []).append(t)

    body = [f'<div class="summary-strip">{synergy_strip}</div>',
            _list_toolbar("integration", noun="tasks")]
    for dept, dtasks in by_dept.items():
        rows = "".join(
            f'<tr{_row_attrs(t)}><td>{_esc(t["task"])}'
            + (f' <span class="dup-tag">shared w/ linked dept</span>'
               if t.get("linked_task_key") else "")
            + f'</td><td>{_esc(t.get("milestone")) or "&mdash;"}</td>'
              f'<td>{_status_pill(t["status"])}</td>'
              f'<td>{_esc(t["percent_complete"])}%</td></tr>'
            for t in dtasks
        )
        body.append(_group(dept, dtasks,
                           f'<table><tbody>{rows}</tbody></table>'))
    return "".join(body)


# ---------------------------------------------------------------------------
# Tab 4 -- Financial Analysis (financials-detail.json)
# ---------------------------------------------------------------------------

def render_tab4_financials(doc: dict | None) -> str:
    if not doc:
        return _empty_state("Financial Analysis",
                             "Drop post-LOI financial exports into intake/ and run ma-financial-summary.")

    validation = doc.get("meta", {}).get("validation", {})
    status = validation.get("status", "unknown")
    banner_class = "banner-green" if status == "pass" else "banner-red" if status == "fail" else "banner-amber"
    checks = validation.get("checks", [])

    # Group the checks by the gate's own `group` field rather than rendering 60+
    # rows flat. A validation page you have to scroll to read is a validation
    # page nobody reads.
    _GROUP_LABELS = {
        "bs-tie": "Balance sheet balances",
        "cash-tie": "Cash ties to the cash-flow statement",
        "re-tie": "Retained earnings rollforward",
        "pl-tie": "P&L detail and internal arithmetic",
        "cf-tie": "Cash-flow statement arithmetic",
        "bridge-tie": "EBITDA bridge and add-backs",
        "customer-tie": "Customer reconciliation",
        "ar-tie": "AR aging reconciliation",
    }

    def _check_state(c):
        """A check is 'done' when it passed. A failed NON-blocking check is a
        flag, which is open work -- not a pass, and not a stop."""
        return "done" if c.get("passed") else "open"

    def _check_rows(cs):
        return "".join(
            f'<tr data-item data-state="{_check_state(c)}"'
            + ('' if c.get("passed") else ' data-attention="1"')
            + f'><td>{"PASS" if c.get("passed") else "FAIL"}</td>'
              f'<td>{_esc(c.get("name"))}</td><td>{_esc(c.get("delta"))}</td>'
              f'<td>{_esc(c.get("blocking") and "blocking" or "advisory")}</td>'
              f'<td>{_esc(c.get("detail"))}</td></tr>'
            for c in cs)

    grouped: dict[str, list] = {}
    for c in checks:
        grouped.setdefault(c.get("group") or "other", []).append(c)

    check_html = ""
    if checks:
        check_html = _list_toolbar("validation", noun="checks")
        for gid, cs in grouped.items():
            # A group containing a failure opens by default. What broke should
            # be on screen without a click; what passed can stay folded away.
            failed = [c for c in cs if not c.get("passed")]
            # _group() reads `applicable`/`status`, which a check dict does not
            # carry, so hand it shapes that map onto the same vocabulary.
            as_items = [{"status": "complete" if c.get("passed") else "blocked"}
                        for c in cs]
            check_html += _group(
                _GROUP_LABELS.get(gid, gid), as_items,
                '<table><thead><tr><th>Result</th><th>Check</th><th>Delta</th>'
                '<th>Severity</th><th>Detail</th></tr></thead>'
                f'<tbody>{_check_rows(cs)}</tbody></table>',
                open_by_default=bool(failed))

    gate = (
        f'<div class="banner {banner_class}">Gate status: {_esc(status).upper()}'
        + (f' &mdash; {_esc(validation.get("failure_reason"))}'
           if status == "fail" and validation.get("failure_reason") else "")
        + '</div>'
        + check_html
    )

    variance = doc.get("vs_go_no_go_variance", {})
    variance_html = (
        f'<p>Revenue variance vs. screen {_fmt_pct(variance.get("revenue_variance_pct"))} &middot; '
        f'EBITDA variance {_fmt_pct(variance.get("ebitda_variance_pct"))} &middot; '
        f'concentration variance {_fmt_pct(variance.get("concentration_variance_pct"))}</p>'
    ) if variance.get("go_no_go_snapshot_ref") else _empty_state(
        "Screen vs. actual variance", "No pre-LOI screen on file to compare against.")

    bridge = doc.get("ebitda_bridge", {})
    addbacks = bridge.get("addbacks", [])
    addback_rows = "".join(
        f'<tr><td>{_esc(a.get("label"))}</td><td>{_fmt_money(a.get("amount"))}</td>'
        f'<td>{_esc(a.get("category"))}</td><td>{_esc(a.get("confidence") or "unconfirmed")}</td></tr>'
        for a in addbacks
    )
    bridge_html = (
        f'{_tile("Reported EBITDA", _fmt_money(bridge.get("reported_ebitda", {}).get("value") if isinstance(bridge.get("reported_ebitda"), dict) else bridge.get("reported_ebitda")))}'
        f'{_tile("Normalized EBITDA", _fmt_money(bridge.get("normalized_ebitda", {}).get("value") if isinstance(bridge.get("normalized_ebitda"), dict) else bridge.get("normalized_ebitda")))}'
    )
    if addback_rows:
        bridge_html += f'<table><thead><tr><th>Add-back</th><th>Amount</th><th>Category</th><th>Confidence</th></tr></thead><tbody>{addback_rows}</tbody></table>'

    rrm = doc.get("recurring_revenue_metrics", {})
    rrm_html = (
        f'<p>NRR {_fmt_pct(rrm.get("nrr_pct"))} &middot; GRR {_fmt_pct(rrm.get("grr_pct"))} &middot; '
        f'logo churn {_fmt_pct(rrm.get("logo_churn_pct"))} &middot; basis: {_esc(rrm.get("classification_basis") or "unclassified")}</p>'
    )

    return (
        gate
        + '<h1>Screen vs. actual variance</h1>' + variance_html
        + '<h1>EBITDA bridge</h1>' + f'<div class="summary-strip">{bridge_html}</div>'
        + '<h1>Recurring revenue metrics</h1>' + rrm_html
    )


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

_CSS = f"""
*{{box-sizing:border-box}}
body{{margin:0;background:{PAPER};color:{INK};font-family:-apple-system,'Segoe UI',Arial,sans-serif;font-size:15px;line-height:1.55}}
.masthead{{background:{NAVY};color:#F4F6FB;padding:20px 28px}}
.masthead .brand{{font-weight:800;font-size:12px;letter-spacing:.12em;opacity:.85}}
.masthead .ttl{{font-size:22px;font-weight:700;margin-top:4px}}
.toptabs{{background:#13294b;display:flex;gap:2px;padding:0 20px;position:sticky;top:0;z-index:5}}
.toptab-btn{{background:transparent;border:none;color:#b7c4d6;font-weight:700;font-size:13px;padding:12px 16px;cursor:pointer;border-bottom:3px solid transparent}}
.toptab-btn.active{{color:#fff;border-bottom-color:{AMBER}}}
.toptab-panel{{display:none;padding:24px 28px 60px;max-width:1000px;margin:0 auto}}
.toptab-panel.active{{display:block}}
h1{{font-size:18px;color:{NAVY};margin:28px 0 12px;border-top:1px solid {BORDER};padding-top:16px}}
h1:first-of-type{{border-top:none;margin-top:0}}
table{{border-collapse:collapse;width:100%;margin:0 0 16px;font-size:13.5px}}
th,td{{padding:7px 10px;border-bottom:1px solid {BORDER};text-align:left}}
thead th{{background:{NAVY};color:#fff}}
.tile{{background:#fff;border:1px solid {BORDER};border-radius:8px;padding:12px 16px;min-width:160px}}
.tile-label{{font-size:11px;color:{INK_SOFT};text-transform:uppercase;letter-spacing:.05em}}
.tile-val{{font-size:22px;font-weight:700;color:{NAVY}}}
.tile-sub{{font-size:12px;color:{INK_SOFT}}}
.summary-strip{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}}
.banner{{padding:10px 16px;border-radius:6px;font-weight:700;margin-bottom:16px}}
.banner-green{{background:#E8F5EC;color:{GREEN}}}
.banner-amber{{background:#FCF1DE;color:{AMBER}}}
.banner-red{{background:#FBE7E4;color:{RED}}}
.pill{{border:1px solid;border-radius:999px;padding:2px 8px;font-size:11.5px;font-weight:600}}
.na{{color:#98a2b3;font-style:italic}}
.empty-state{{padding:40px 20px;text-align:center;color:{INK_SOFT};border:1px dashed {BORDER};border-radius:10px}}
.empty-hint{{font-size:13px}}
.section-group{{border:1px solid {BORDER};border-radius:8px;margin-bottom:8px;background:#fff}}
.section-group summary{{padding:10px 14px;cursor:pointer;font-weight:600}}
.section-group table{{margin:0}}
.subsection-group{{border-top:1px solid {BORDER};background:{PAPER}}}
.subsection-group summary{{padding:8px 14px 8px 26px;cursor:pointer;font-weight:600;font-size:13px;color:{NAVY}}}
.count{{color:{INK_SOFT};font-weight:400;font-size:12.5px}}
.count-done{{color:{GREEN};font-weight:600}}
.count-na{{color:{INK_SOFT};font-style:italic}}

/* --- Collapsible groups -------------------------------------------------
   The default browser marker is replaced with an explicit chevron: it is the
   affordance Steve asked to click, and the native triangle is inconsistent
   between browsers and nearly invisible on some. `list-style:none` plus the
   ::-webkit-details-marker rule covers both engines. */
summary{{list-style:none}}
summary::-webkit-details-marker{{display:none}}
[data-group] > summary{{display:flex;align-items:center;gap:8px;
  user-select:none;-webkit-user-select:none}}
[data-group] > summary:hover{{background:rgba(70,130,180,.06)}}
[data-group] > summary:focus-visible{{outline:2px solid {AMBER};outline-offset:-2px}}
.grp-arrow{{flex:0 0 auto;width:0;height:0;border-left:6px solid {STEEL};
  border-top:4.5px solid transparent;border-bottom:4.5px solid transparent;
  transition:transform .12s ease}}
[data-group][open] > summary .grp-arrow{{transform:rotate(90deg)}}
.grp-name{{flex:1 1 auto;min-width:0}}
/* Shown only when the open-only filter has emptied this group, so a finished
   section still appears in the outline instead of vanishing -- a section that
   disappears is indistinguishable from one that was never there. */
/* Green text on a light green field, not white on green: the firm green is
   2.45:1 against white (HANDOFF §5e records why the brand value was kept over a
   darker variant), so white knocked out of it is not legible at 10.5px. This is
   the same treatment .banner-green already uses. */
.grp-done-chip{{display:none;flex:0 0 auto;font-size:10.5px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;color:{GREEN};
  background:#E8F5EC;border:1px solid {GREEN};border-radius:3px;padding:1px 6px}}

/* --- List toolbar ------------------------------------------------------- */
.list-toolbar{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  margin:0 0 12px}}
.lt-seg{{display:inline-flex;border:1px solid {NAVY};border-radius:6px;
  overflow:hidden}}
.lt-btn{{font:inherit;font-size:12.5px;font-weight:600;padding:6px 12px;
  border:none;background:#fff;color:{NAVY};cursor:pointer}}
.lt-seg .lt-btn + .lt-btn{{border-left:1px solid {NAVY}}}
.lt-seg .lt-btn.active{{background:{NAVY};color:#fff}}
.lt-plain{{border:1px solid {BORDER};border-radius:6px;color:{INK_SOFT};
  font-weight:600}}
.lt-plain:hover{{color:{NAVY};border-color:{STEEL}}}
.lt-btn:focus-visible{{outline:2px solid {AMBER};outline-offset:1px}}
/* The filter notice is not decoration. A filtered list that reads as a complete
   list is a misleading document, and these pages get screenshotted. */
.lt-state{{font-size:12px;color:{AMBER};background:#FCF1DE;
  border:1px solid {AMBER};border-radius:4px;padding:4px 9px}}

/* --- Open-only filter --------------------------------------------------- */
/* Row hiding is cosmetic and always was: every figure is inlined, so this is a
   reading aid, never an access control. Audience separation is byte-level and
   happens before render. */
/* The flag lives on each GROUP, not on a shared ancestor. Tab 2 holds two
   independent lists (the request checklist and the team workplan) whose
   toolbars share one parent panel, so flagging the parent made one list's
   filter silently reach into the other's rows. */
[data-group][data-filtered="open"] [data-item][data-state="done"]{{display:none}}
[data-group][data-filtered="open"] [data-item][data-state="na"]{{display:none}}
[data-group][data-filtered="open"][data-empty="1"] > summary{{opacity:.55}}
[data-group][data-filtered="open"][data-empty="1"] .grp-done-chip{{display:inline-block}}
[data-group][data-filtered="open"][data-empty="1"] > summary .count{{display:none}}
[data-attention="1"] td:first-child{{box-shadow:inset 3px 0 0 {AMBER}}}
.stage-badge{{display:none}}
.stage-note{{font-size:12.5px;color:{INK_SOFT};margin-bottom:10px}}
.dup-tag{{font-size:10.5px;color:{STEEL};border:1px solid {STEEL};border-radius:4px;padding:1px 5px}}
.internal-flag{{background:{AMBER};color:#fff;border-radius:3px;padding:1px 6px;font-size:10.5px;letter-spacing:.08em}}
.fx-help{{font-size:12.5px;color:{INK_SOFT};max-width:70ch}}
.fx input,.fx select{{font:inherit;font-size:13px;padding:4px 6px;border:1px solid {BORDER};border-radius:4px;background:#fff;color:{INK};max-width:100%}}
.fx .fx-name{{min-width:180px;width:100%}}
.fx .fx-w{{width:90px}}
.fx-del{{background:none;border:1px solid {BORDER};color:{INK_SOFT};border-radius:4px;cursor:pointer;font-size:14px;line-height:1;padding:3px 8px}}
.fx-del:hover{{color:{RED};border-color:{RED}}}
.fx-actions{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0 4px}}
.fx-actions button{{font:inherit;font-size:13px;font-weight:600;padding:7px 14px;border-radius:6px;border:1px solid {NAVY};background:#fff;color:{NAVY};cursor:pointer}}
#fxCopy{{background:{NAVY};color:#fff}}
.fx-actions button:disabled{{opacity:.45;cursor:not-allowed}}
/* The working score sits next to the score of record, never in place of it, so
   an unsaved edit can't be mistaken for what the deal file says. */
#fxWorkingTile{{border-color:{AMBER};background:#FFFBEB}}
#fxWorkingTile .tile-label{{color:{AMBER}}}
.fx-msg{{font-size:12.5px;color:{GREEN}}}
.fx-dump{{background:#fff;border:1px solid {BORDER};border-radius:6px;padding:12px;overflow-x:auto;font-size:11.5px;max-height:320px}}
.fx :focus-visible{{outline:2px solid {AMBER};outline-offset:1px}}
.artifact-foot{{max-width:1000px;margin:0 auto;padding:18px 28px 40px;font-size:11.5px;color:{INK_SOFT};border-top:1px solid {BORDER}}}
/* Wide tables scroll inside their own container so the page body never scrolls
   sideways: a client CFO will open this on a phone mid-negotiation. */
.toptab-panel table{{display:block;overflow-x:auto;white-space:nowrap}}
@media (max-width:700px){{
  .toptab-panel{{padding:16px 14px 48px}}
  .masthead{{padding:16px 14px}}
  .masthead .ttl{{font-size:18px}}
  .toptabs{{overflow-x:auto;padding:0 8px}}
  .toptab-btn{{white-space:nowrap;padding:12px 12px;font-size:12.5px}}
  .summary-strip{{flex-direction:column}}
  .tile{{min-width:0;width:100%}}
  .artifact-foot{{padding:16px 14px 40px}}
}}
"""

_JS = """

// --- Strategic-fit editor: live recalculation, explicit emit, no persistence ---
(function(){
  var root = document.querySelector('.fx');
  if(!root) return;
  var scale = {};
  try { scale = JSON.parse(root.dataset.fitScale || '{}'); } catch(e) { scale = {}; }
  var body = document.getElementById('fxBody');
  var TOL = 5e-5;

  function rows(){ return Array.prototype.slice.call(body.querySelectorAll('[data-fit-row]')); }

  function read(){
    return rows().map(function(tr){
      var w = tr.querySelector('.fx-w').value.trim();
      return {
        name: tr.querySelector('.fx-name').value,
        fit: tr.querySelector('.fx-fit').value || null,
        weight: w === '' ? null : Number(w)
      };
    });
  }

  // Same formula as ma_engine.render.composite_fit_score. These two are
  // deliberately duplicated -- one in each language -- and reconciled on load
  // rather than trusted. See score() / the drift check below.
  function score(data){
    // A blank weight means "equal share", so unweighted rows still count rather
    // than silently scoring zero. Rows with no fit chosen are excluded from the
    // score entirely and from the denominator -- an unanswered attribute must
    // not read as a "no".
    var scored = data.filter(function(a){ return a.fit && scale[a.fit] !== undefined; });
    var wsum = 0, acc = 0;
    scored.forEach(function(a){
      var w = (a.weight === null || isNaN(a.weight)) ? 1 : a.weight;
      wsum += w; acc += w * scale[a.fit];
    });
    return { value: (scored.length && wsum > 0) ? acc/wsum : null,
             scored: scored.length, total: data.length };
  }

  // Snapshot of the record as rendered. Any deviation from this is a working
  // copy, and the page has to say so.
  var pristine = JSON.stringify(read());
  var trusted = root.dataset.reconciled === '1';
  var stamp = document.querySelector('[data-as-of]');

  function serialize(){ return JSON.stringify(read()); }

  function recalc(){
    var data = read();
    var s = score(data);
    var dirty = serialize() !== pristine;
    var el = document.getElementById('fxScore');
    var rec = document.getElementById('fxRec');

    document.getElementById('fxDirty').hidden = !dirty;
    document.getElementById('fxWorkingTile').hidden = !dirty;

    if(s.value === null){
      el.textContent = '—';
      rec.textContent = 'no attributes scored yet';
    } else {
      el.textContent = s.value.toFixed(2);
      rec.textContent = s.scored + ' of ' + s.total + ' attributes scored';
    }
    var totals = data.map(function(a){ return (a.weight === null || isNaN(a.weight)) ? 1 : a.weight; })
                     .reduce(function(x,y){ return x+y; }, 0);
    document.getElementById('fxWsum').textContent = totals ? totals.toFixed(2) : '—';
    document.getElementById('fxMsg').textContent = '';
  }

  // Two-engine reconciliation. The page was rendered with a score Python
  // computed; the JS recomputes the untouched inputs and must land on the same
  // number. If it does not, the formulas have drifted apart and the honest
  // move is to say so, not to display whichever one happens to be in the DOM.
  function driftCheck(){
    var baseRaw = root.dataset.baseline;
    var mine = score(read()).value;
    var bad;
    if(baseRaw === '' || baseRaw === undefined){
      bad = (mine !== null);
    } else {
      bad = (mine === null) || Math.abs(mine - Number(baseRaw)) > TOL;
    }
    if(bad || !trusted){
      if(bad) document.getElementById('fxDrift').hidden = false;
      document.getElementById('fxCopy').disabled = true;
      document.getElementById('fxCopy').title =
        'Disabled: this panel is not reconciled with the deal record.';
    }
  }

  function addRow(){
    var tr = document.createElement('tr');
    tr.setAttribute('data-fit-row','');
    var opts = ['<option value=""></option>'].concat(Object.keys(scale).map(function(k){
      return '<option value="'+k+'">'+k+'</option>'; })).join('');
    tr.innerHTML = '<td><input class="fx-name" type="text" value="" aria-label="Attribute name"></td>'
      + '<td><select class="fx-fit" aria-label="Fit">'+opts+'</select></td>'
      + '<td><input class="fx-w" type="number" min="0" step="any" placeholder="equal" aria-label="Weight"></td>'
      + '<td><button type="button" class="fx-del" aria-label="Remove attribute">×</button></td>';
    body.appendChild(tr);
    recalc();
  }

  root.addEventListener('input', recalc);
  root.addEventListener('change', recalc);
  root.addEventListener('click', function(e){
    if(e.target.classList.contains('fx-del')){
      var tr = e.target.closest('[data-fit-row]');
      if(tr){ tr.remove(); recalc(); }
    }
  });
  document.getElementById('fxAdd').addEventListener('click', addRow);

  document.getElementById('fxReset').addEventListener('click', function(){
    location.reload();
  });

  document.getElementById('fxCopy').addEventListener('click', function(){
    var data = read();
    var s = score(data);
    var payload = {
      strategic_fit: {
        attributes: data,
        composite_score: s.value === null ? null : Number(s.value.toFixed(4)),
        fit_scale: scale,
        scored_count: s.scored,
        attribute_count: s.total,
        edited_in_artifact_at: new Date().toISOString()
      },
      // Carried so the skill can prove this edit started from the record it
      // thinks it did. If the deal file has moved on since this page was
      // rendered, the write must stop and ask rather than clobber.
      _provenance: {
        baseline_composite_score: root.dataset.baseline === '' ? null : Number(root.dataset.baseline),
        rendered_data_as_of: stamp ? (stamp.dataset.asOf || null) : null,
        unchanged_from_render: JSON.stringify(data) === pristine
      },
      _note: 'Edited in the command center. NOT saved -- hand this to ma-financial-summary to write it to the deal record under the normal confirm-before-write gate. The skill must re-derive composite_score from attributes and refuse the write if it disagrees with the value above.'
    };
    var txt = JSON.stringify(payload, null, 2);
    var msg = document.getElementById('fxMsg');
    function ok(){ msg.textContent = 'Copied. Paste this back to save it.'; }
    function fail(){
      msg.textContent = 'Could not copy automatically — JSON shown below, copy it manually.';
      var pre = document.createElement('pre');
      pre.className = 'fx-dump'; pre.textContent = txt;
      root.appendChild(pre);
    }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(txt).then(ok).catch(fail);
    } else { fail(); }
  });

  driftCheck();
  recalc();
})();
document.querySelectorAll('.toptab-btn').forEach(function(btn){
  btn.addEventListener('click', function(){
    document.querySelectorAll('.toptab-btn').forEach(function(b){b.classList.remove('active')});
    document.querySelectorAll('.toptab-panel').forEach(function(p){p.classList.remove('active')});
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
  });
});

// --- Grouped lists: collapse/expand, and the open-items filter -------------
//
// One controller for every grouped list on every tab, so the interaction is
// identical wherever a list appears. Each toolbar owns the groups that follow it
// up to the next toolbar, which means a tab can hold several independent lists
// (Tab 2 holds the request checklist and the team workplan) without them
// fighting over one another's state.
//
// Deliberately absent: any persistence. The artifact may not use browser
// storage, so filter and expansion state live for the life of the page only.
// Nothing a viewer clicks here can become part of the record.
(function(){
  var toolbars = Array.prototype.slice.call(
    document.querySelectorAll('.list-toolbar[data-listscope]'));
  if(!toolbars.length) return;

  // Groups belonging to a toolbar: following siblings up to the next toolbar.
  // Using sibling walk rather than a wrapper element keeps the renderer free to
  // emit a toolbar followed by groups without an extra nesting level.
  function groupsFor(tb){
    var out = [], el = tb.nextElementSibling;
    while(el && !el.classList.contains('list-toolbar')){
      if(el.hasAttribute && el.hasAttribute('data-group')) out.push(el);
      // Nested groups (Legal subsections) are collected too.
      if(el.querySelectorAll){
        Array.prototype.push.apply(out, Array.prototype.slice.call(
          el.querySelectorAll('[data-group]')));
      }
      el = el.nextElementSibling;
    }
    return out;
  }

  function mode(tb){
    var on = tb.querySelector('[data-filter="open"]');
    return (on && on.getAttribute('aria-pressed') === 'true') ? 'open' : 'all';
  }

  // Recount from the DOM rather than trusting the server-rendered attribute.
  // The two should always agree; if they ever don't, the number next to the
  // rows a viewer can actually see is the one that must be right.
  function refresh(tb){
    var m = mode(tb);
    var groups = groupsFor(tb);
    groups.forEach(function(g){
      // Every open row anywhere under this group, in one query: a section's own
      // rows plus any nested subsection's (Legal). One query rather than two is
      // not just tidier -- summing a "direct" and a "nested" pass double-counted
      // direct rows, because in `g.querySelectorAll('[data-group] [data-item]')`
      // the ancestor the descendant combinator matches is allowed to be `g`
      // itself. Corporate then reported 4 open out of 3 actionable.
      var open = g.querySelectorAll('[data-item][data-state="open"]').length;
      var badge = g.querySelector(':scope > summary [data-open-count]');
      if(badge) badge.textContent = String(open);
      g.setAttribute('data-empty', open === 0 ? '1' : '0');
      // In open-only mode a finished group folds itself shut. Its header stays,
      // so the outline is still complete and you can see the section is done
      // rather than wondering whether it exists.
      if(m === 'open' && open === 0) g.removeAttribute('open');
    });
    var note = tb.querySelector('[data-filter-note]');
    if(note) note.hidden = (m !== 'open');
  }

  function applyFilter(tb, next){
    tb.querySelectorAll('[data-filter]').forEach(function(b){
      var on = b.getAttribute('data-filter') === next;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    groupsFor(tb).forEach(function(g){
      g.setAttribute('data-filtered', next);
    });
    refresh(tb);
    // Switching INTO open-only expands what still has work in it. Otherwise the
    // button lands you on a wall of collapsed headers and you have to click
    // "Expand all" to see the thing you just asked to see. Switching back to All
    // deliberately leaves expansion alone -- collapsing there would throw away
    // whatever the viewer had opened.
    if(next === 'open'){
      groupsFor(tb).forEach(function(g){
        if(g.getAttribute('data-empty') === '0') g.setAttribute('open', '');
      });
    }
  }

  toolbars.forEach(function(tb){
    tb.addEventListener('click', function(ev){
      var btn = ev.target.closest ? ev.target.closest('button') : null;
      if(!btn || !tb.contains(btn)) return;

      if(btn.hasAttribute('data-filter')){
        applyFilter(tb, btn.getAttribute('data-filter'));
        return;
      }
      if(btn.hasAttribute('data-expand')){
        var wantOpen = btn.getAttribute('data-expand') === 'all';
        groupsFor(tb).forEach(function(g){
          // Expand-all must not re-open a group the filter just emptied --
          // that would show a header with no rows under it and read as a bug.
          if(wantOpen && mode(tb) === 'open'
             && g.getAttribute('data-empty') === '1') return;
          if(wantOpen) g.setAttribute('open', '');
          else g.removeAttribute('open');
        });
        return;
      }
    });
    // Recount when a group is expanded, so a nested subsection opened for the
    // first time reports the same number as its parent header.
    groupsFor(tb).forEach(function(g){
      g.addEventListener('toggle', function(){ refresh(tb); });
    });
    refresh(tb);
  });
})();
"""


# ---------------------------------------------------------------------------
# Audience model
#
# A client build is DIFFERENT BYTES, never the firm build with tabs hidden.
# Every figure in this artifact is inlined into the HTML, so a CSS-hidden or
# display:none section is fully readable in View Source -- hiding is not a
# control. Content a given audience must not have is never constructed.
#
#   firm    CFOforIT staff. Everything.
#   client  the ACQUIRER (our client, the buyer). Their own deal, including
#           their own pricing and EBITDA addback analysis -- that is their
#           work product. Excludes CFOforIT's internal deal-team workplan
#           (analyst assignments, per-analyst percent complete), which is our
#           unfinished homework and not theirs to see mid-negotiation.
#   target  the company being acquired. Integration-phase content only. Never
#           pricing, never addbacks, never diligence findings -- those are the
#           buyer's private view of what the target is worth and where its
#           earnings are soft, and showing them to the seller is an unforced
#           negotiating loss. NOT YET IMPLEMENTED: blocked at the door below
#           pending explicit written sign-off, so enabling it later is a
#           config change rather than a redesign.
#
# The tab set is an ALLOWLIST per audience, deliberately not a denylist: a tab
# missing from a build is visible and gets reported, while a tab that leaks in
# is silent. Build in the direction where the failure is loud.
# ---------------------------------------------------------------------------

AUDIENCES = ("firm", "client", "target")

_TAB_ALLOWLIST = {
    "firm": ("summary", "diligence", "integration", "financials"),
    "client": ("summary", "diligence", "integration", "financials"),
    "target": ("integration",),
}

# Sub-content within an allowed tab that a given audience must not receive.
#
# Only keys listed in _ENFORCED_DENIES below are actually consumed by the
# renderer. Do not add a key here expecting it to take effect -- config that
# reads as enforcement but is never consumed is worse than no config, because
# it invites the assumption that a control exists. `test_deny_keys_are_all_enforced`
# fails if these drift apart.
_SECTION_DENY = {
    "firm": frozenset(),
    "client": frozenset({"internal_workplan"}),
    # "target" intentionally holds ONLY the deny it can currently honor. The
    # additional field-level stripping a target build needs (estimated_pricing
    # on Tab 1, ebitda_bridge.addbacks on Tab 4, diligence findings) is NOT
    # expressible as a tab/section deny -- it requires filtering the deal JSON
    # before the renderers run. That work is required before "target" is
    # enabled, and _check_audience() blocks the audience until it exists.
    "target": frozenset({"internal_workplan"}),
}

# The deny keys the renderer actually acts on. Keep in sync with the branches
# in render_command_center().
_ENFORCED_DENIES = frozenset({"internal_workplan"})


def _check_audience(audience: str) -> None:
    if audience not in AUDIENCES:
        raise ValueError(
            f"unknown audience {audience!r}; expected one of {AUDIENCES}")
    if audience == "target":
        raise NotImplementedError(
            "the 'target' audience is defined but deliberately not enabled. A "
            "target-facing build must omit the buyer's private analysis -- "
            "estimated_pricing (Tab 1), ebitda_bridge.addbacks (Tab 4) and "
            "diligence findings -- which is FIELD-level filtering of the deal "
            "JSON, not something the tab/section allowlist can express. "
            "Enabling it requires (a) that filtering, (b) tests proving those "
            "fields are absent from target bytes, and (c) explicit written "
            "sign-off, since showing a seller your own valuation of them is an "
            "unforced negotiating loss. Do not work around this by passing "
            "'client' -- the client IS the acquirer and legitimately sees all "
            "of the above.")


def render_command_center(client: str, target: str, docs: dict,
                          *, audience: str = "firm",
                          data_as_of: str | None = None,
                          expires_on: str | None = None,
                          prepared_by: str = "CFOforIT") -> str:
    """Render the tabbed command center for one deal.

    docs keys (any may be absent): go_no_go, diligence_requests,
    diligence_workplan, integration, financials_detail

    audience defaults to "firm" on purpose: an un-updated caller that does not
    know about this parameter gets the internal build, which is safe to leave
    inside the firm. The unsafe direction (external content) is never the
    default.

    prepared_by names whoever produced the artifact, and it drives both the
    masthead and the footer. It defaults to "CFOforIT" because that is the firm
    install, but a client running this plugin on their own machine is NOT
    preparing a CFOforIT deliverable -- on a single_org install this is their
    `organization_name` from ma-config.json. Getting it wrong puts a false
    attribution on a document about an acquisition, which is worse than a
    cosmetic bug.
    """
    _check_audience(audience)
    allowed = _TAB_ALLOWLIST[audience]
    denied = _SECTION_DENY[audience]

    diligence_body = ('<div class="subtabs"><em>Request Checklist</em></div>'
                      + render_tab2_requests(docs.get("diligence_requests")))
    if "internal_workplan" not in denied:
        diligence_body += ('<h1>Team Workplan</h1>'
                           + render_tab2_workplan(docs.get("diligence_workplan")))

    all_tabs = {
        "summary": ("One-Page Summary", lambda: render_tab1_summary(docs.get("go_no_go"))),
        "diligence": ("Diligence", lambda: diligence_body),
        "integration": ("Integration Gantt", lambda: render_tab3_integration(docs.get("integration"))),
        "financials": ("Financial Analysis", lambda: render_tab4_financials(docs.get("financials_detail"))),
    }
    tabs = [(tid, all_tabs[tid][0], all_tabs[tid][1]()) for tid in allowed]
    btns = "".join(
        f'<button class="toptab-btn{" active" if i == 0 else ""}" data-tab="{tid}">{_esc(label)}</button>'
        for i, (tid, label, _) in enumerate(tabs)
    )
    panels = "".join(
        f'<div id="panel-{tid}" class="toptab-panel{" active" if i == 0 else ""}">{body}</div>'
        for i, (tid, label, body) in enumerate(tabs)
    )
    # A firm build must be self-evidently internal, so a copy that escapes by
    # email or screenshot is identifiable as not-for-client on sight.
    internal_stamp = (' &middot; <span class="internal-flag">INTERNAL</span>'
                      if audience == "firm" else "")

    # Footer provenance. When this file is SENT rather than served, none of the
    # usual server-side controls exist -- no revocation, no access log, no
    # session expiry. What the artifact can still carry is an honest account of
    # what it is and when it stops being current. A recipient who opens a
    # forwarded copy in six months should be able to see that from the page.
    _rendered = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # "Prepared by CFOforIT for <client>" is right on the firm install and
    # simply false on the client's own -- there, the acquirer IS the preparer.
    # Comparing the two names is what lets one footer serve both installs.
    _by = (prepared_by or "").strip()
    if _by and _by.casefold() == (client or "").strip().casefold():
        foot = [f'Prepared by {_esc(client)}']
    elif _by:
        foot = [f'Prepared by {_esc(_by)} for {_esc(client)}']
    else:
        foot = [f'Prepared for {_esc(client)}']
    foot.append(f'Rendered {_rendered}')
    if data_as_of:
        foot.append(f'Data as of {_esc(data_as_of)}')
    if expires_on:
        foot.append(f'<strong>Treat as stale after {_esc(expires_on)}</strong>')
    foot.append('Confidential' + (' &mdash; INTERNAL, not for distribution'
                                  if audience == "firm" else ''))
    # data-as-of is machine-readable on purpose: an edit emitted from this page
    # carries it back, so a write can refuse to land on a deal file that has
    # moved on since the page was rendered.
    _asof_attr = f' data-as-of="{_esc(data_as_of)}"' if data_as_of else ''
    footer = (f'<div class="artifact-foot"{_asof_attr}>'
              + ' &middot; '.join(foot) + '</div>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(target)} &mdash; M&amp;A Command Center</title>
<style>{_CSS}</style></head>
<body>
<div class="masthead"><div class="brand">{_esc((_by or "CFOforIT").upper())} &middot; M&amp;A COMMAND CENTER{internal_stamp}</div>
<div class="ttl">{_esc(client)} &mdash; {_esc(target)}</div></div>
<div class="toptabs">{btns}</div>
{panels}
{footer}
<script>{_JS}</script>
</body></html>"""
