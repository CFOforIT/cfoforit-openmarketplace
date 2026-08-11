"""validate.py -- the financial tie-out gate for a post-LOI financials-detail.

A deliberate MIRROR of `mhr_engine.validate`, not a call into it (Decision #16).
Same `Check` / `CheckReport` / `_tie` shapes, same tolerance constants, same
`as_snapshot_block()` output, same hard-stop behaviour. The duplication is the
chosen cost of keeping the two plugins independent; `tests/test_validate_mirrors_mhr.py`
asserts the shapes have not drifted apart.

What is deliberately NOT mirrored: MHR's chart-of-accounts completeness checks.
This plugin has no COA mapping by ruling -- a target's native accounts are
rendered as given -- so there is no mapping to be complete. Checking it would be
theatre.

The checks, from `skills/ma-financial-summary/SKILL.md`:

  1. Current-period net earnings agrees to the movement in retained earnings.
  2. Cash on the balance sheet agrees to ending cash on the cash-flow statement.
  3. The balance sheet balances (Assets = Liabilities + Equity).
  4. Detailed revenue ties to total revenue.
  5. Period totals foot and cross-statement totals reconcile.
  6. Every add-back sums correctly into its stated normalized EBITDA.

Plus M&A-specific reconciliations that are surfaced but non-blocking, because a
seller legitimately may not have produced the supporting schedule yet: customer
detail coverage, AR aging to gross AR, unresolved customer name variants, and
add-backs with no evidence behind them.

And one non-blocking check whose rationale is different, because it is the only
one here that reads the counterparty's own arithmetic rather than ours: the
target's STATED balance-sheet totals against the line items they claim to total
(section A0). Every other tie-out derives all three sides from `lines`, so it
compares our reconstruction against itself and cannot see a printed total that
does not foot. Non-blocking is a ruling, not an oversight -- see A0.

Fail-loud rule: a blocking failure raises MAError. It does NOT return a report
the caller might render as a pass. The caller that wants the report anyway
(to show the client exactly what broke) passes hard_stop=False and reads
`report.status`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import MAError

SUBTOTAL_TOLERANCE = 1.00   # dollars, on subtotals only
ZERO_TOLERANCE = 0.005      # effectively exact (sub-cent)

# Which `stated_totals` key answers to which `lines[].section` value. Keyed by
# section rather than by the seller's label text on purpose: one target prints
# "TOTAL ASSETS", the next "Total assets", the next "Assets, total". Matching
# label strings would make the check a spelling lottery.
_STATED_SECTIONS = (
    ("asset", "assets"),
    ("liability", "liabilities"),
    ("equity", "equity"),
)


@dataclass
class Check:
    name: str
    group: str
    passed: bool
    expected: object = None
    actual: object = None
    delta: object = None
    tolerance: float = 0.0
    blocking: bool = True
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name, "group": self.group, "passed": self.passed,
            "expected": self.expected, "actual": self.actual,
            "delta": self.delta, "tolerance": self.tolerance,
            "blocking": self.blocking, "detail": self.detail,
        }


@dataclass
class CheckReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, **kw) -> None:
        self.checks.append(Check(**kw))

    @property
    def status(self) -> str:
        return "fail" if any((not c.passed and c.blocking)
                             for c in self.checks) else "pass"

    @property
    def blocking_failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed and c.blocking]

    @property
    def flags(self) -> list[Check]:
        """Non-blocking failures. These do not stop the build but must be
        visible -- a silent 'advisory' is the same as no check at all."""
        return [c for c in self.checks if not c.passed and not c.blocking]

    def as_snapshot_block(self) -> dict:
        """Matches what render_tab4_financials() reads: status, checks, and on
        failure a human-readable reason it can put in the red banner."""
        block = {
            "status": self.status,
            "checks": [c.as_dict() for c in self.checks],
            "flags": [c.as_dict() for c in self.flags],
        }
        if self.status == "fail":
            block["failure_reason"] = "; ".join(
                f"{c.name} (delta {c.delta:+,.2f})" if isinstance(c.delta, (int, float))
                else c.name for c in self.blocking_failures)
        return block


def _tie(rep: CheckReport, name, group, expected, actual, *, tol,
         blocking=True, detail=""):
    delta = round((actual or 0) - (expected or 0), 2)
    rep.add(name=name, group=group, passed=abs(delta) <= tol,
            expected=round(expected or 0, 2), actual=round(actual or 0, 2),
            delta=delta, tolerance=tol, blocking=blocking, detail=detail)


def _missing(rep: CheckReport, name, group, what, *, blocking=True):
    """A check that could not run is a FAILURE, not a pass.

    This is the single most important line in the file. The tempting
    alternative -- skip the check when the data is absent -- produces a report
    that says 'pass' on a file with no balance sheet in it. A gate that passes
    when it cannot see is worse than no gate, because it is trusted.
    """
    rep.add(name=name, group=group, passed=False, blocking=blocking,
            detail=f"could not run: {what}")


def _sum_lines(lines, period) -> float:
    return float(sum((ln.get("values") or {}).get(period, 0) or 0
                     for ln in (lines or [])))


def validate(detail: dict, *, hard_stop: bool = True) -> CheckReport:
    """Run the gate over a `financials-detail.json` dict.

    `detail["statements"]` carries the three statements in a checkable shape;
    see skills/ma-financial-summary/reference/schema.md. A file with no
    `statements` block fails every tie-out rather than passing vacuously.
    """
    rep = CheckReport()
    st = detail.get("statements") or {}
    pnl = st.get("pnl") or {}
    bs = st.get("balance_sheet") or {}
    cf = st.get("cash_flow") or {}
    roll = st.get("equity_rollforward") or []

    pnl_totals = pnl.get("totals") or {}
    pnl_periods = pnl.get("periods") or []
    bs_lines = bs.get("lines") or []
    bs_dates = bs.get("dates") or []
    cf_detail = cf.get("periods_detail") or {}

    # --- A0. The target's stated totals foot to their own line items ---------
    #
    # Runs BEFORE the A = L + E check below, and it is the only check in this
    # file that reads a number the TARGET printed rather than one we computed.
    #
    # Every other tie-out here derives all three sides from `lines` and compares
    # our arithmetic against itself. That is the right shape for MHR, which
    # reads our own client's ledger tied to a trial balance at Gate 1 -- there
    # the ledger IS the source, so no adversarial printed figure exists. This
    # gate reads a document supplied by the counterparty in a purchase
    # negotiation, and a stated total that does not foot to its own line items
    # is exactly where a misstatement lives. Without this check, a target
    # printing 5,000,000 over asset lines summing to 4,700,000 passes every
    # tie-out: we substitute our 4,700,000 for their 5,000,000 and then verify
    # ours against ours. The gap arrived with the mirroring (Decision #16), not
    # from anything done wrong -- a check built for trusted, self-produced data
    # was carried into a context where the document is untrusted.
    #
    # NON-BLOCKING by ruling (Steve, 2026-08-11). A mismatch is surfaced on the
    # validation page; it does not stop the write to financials-detail.json.
    # Early-stage screening runs on scrappy documents and a rounding artifact in
    # a seller's PDF should not halt a deal review. It lands in `report.flags`,
    # so it is visible -- a silent advisory is the same as no check at all.
    #
    # Absence is a non-blocking FAILURE, never a pass. `stated_totals` is a new
    # capture, so files built before it do not carry one; blocking on absence
    # would convert the ruling above into a hard stop on every historical file.
    # It is recorded as "could not run" and appears in flags.
    stated = bs.get("stated_totals") or {}
    if not bs_lines or not bs_dates:
        _missing(rep, "Stated totals foot to their own line items",
                 "stated-tie",
                 "no balance-sheet lines or dates in statements.balance_sheet",
                 blocking=False)
    elif not stated:
        _missing(rep, "Stated totals foot to their own line items",
                 "stated-tie",
                 "no statements.balance_sheet.stated_totals: the target's "
                 "printed totals were not captured at ingest, so they cannot "
                 "be compared against the line items they claim to total",
                 blocking=False)
    else:
        for d in bs_dates:
            per_date = stated.get(d) or {}
            if not per_date:
                _missing(rep,
                         f"Stated totals foot to their own line items ({d})",
                         "stated-tie",
                         f"no stated totals captured for {d}", blocking=False)
                continue
            for section, key in _STATED_SECTIONS:
                s = _scalar(per_date.get(key))
                derived = _sum_lines([l for l in bs_lines
                                      if l.get("section") == section], d)
                if s is None:
                    _missing(rep, f"Stated {key} foots to its own lines ({d})",
                             "stated-tie",
                             f"stated_totals[{d!r}] carries no {key!r}",
                             blocking=False)
                    continue
                _tie(rep, f"Stated {key} foots to its own lines ({d})",
                     "stated-tie", s, derived, tol=SUBTOTAL_TOLERANCE,
                     blocking=False,
                     detail=f"target printed {s:,.0f}; its own {section} lines "
                            f"sum to {derived:,.0f}")
            # The printed "TOTAL LIABILITIES & EQUITY" is a figure the target
            # struck itself, not the sum of the two checked above, so it earns
            # its own comparison. Deliberately OPTIONAL rather than
            # flagged-when-absent: plenty of balance sheets print no combined
            # line, and demanding one would fire on legitimate documents. The
            # three section totals above are the required set.
            sle = _scalar(per_date.get("liabilities_and_equity"))
            if sle is not None:
                dle = (_sum_lines([l for l in bs_lines
                                   if l.get("section") == "liability"], d)
                       + _sum_lines([l for l in bs_lines
                                     if l.get("section") == "equity"], d))
                _tie(rep,
                     f"Stated liabilities & equity foots to its own lines ({d})",
                     "stated-tie", sle, dle, tol=SUBTOTAL_TOLERANCE,
                     blocking=False,
                     detail=f"target printed {sle:,.0f}; its own liability and "
                            f"equity lines sum to {dle:,.0f}")

    # --- A. Balance sheet balances: Assets = Liabilities + Equity ------------
    if not bs_lines or not bs_dates:
        _missing(rep, "BS balances: Assets = Liabilities + Equity", "bs-tie",
                 "no balance-sheet lines or dates in statements.balance_sheet")
    else:
        for d in bs_dates:
            assets = _sum_lines([l for l in bs_lines
                                 if l.get("section") == "asset"], d)
            liabs = _sum_lines([l for l in bs_lines
                                if l.get("section") == "liability"], d)
            equity = _sum_lines([l for l in bs_lines
                                 if l.get("section") == "equity"], d)
            _tie(rep, f"BS balances: Assets = Liabilities + Equity ({d})",
                 "bs-tie", assets, liabs + equity, tol=SUBTOTAL_TOLERANCE,
                 detail=f"assets {assets:,.0f} vs L+E {liabs + equity:,.0f}")

    # --- B. Cash on the BS agrees to ending cash on the CF -------------------
    cash_line = next((l for l in bs_lines
                      if l.get("role") == "cash"), None)
    if not cf_detail:
        _missing(rep, "Cash: balance sheet agrees to cash-flow statement",
                 "cash-tie", "no statements.cash_flow.periods_detail")
    elif cash_line is None:
        _missing(rep, "Cash: balance sheet agrees to cash-flow statement",
                 "cash-tie",
                 'no balance-sheet line tagged role="cash"')
    else:
        for period, c in cf_detail.items():
            close_date = c.get("closing_date")
            if close_date is None:
                _missing(rep,
                         f"Cash: balance sheet agrees to cash flow ({period})",
                         "cash-tie",
                         f"cash_flow.{period} has no closing_date to tie to")
                continue
            bs_cash = (cash_line.get("values") or {}).get(close_date)
            if bs_cash is None:
                _missing(rep,
                         f"Cash: balance sheet agrees to cash flow ({period})",
                         "cash-tie",
                         f"no balance-sheet cash at {close_date}")
                continue
            _tie(rep, f"Cash: balance sheet agrees to cash flow ({period})",
                 "cash-tie", bs_cash, c.get("ending_cash"),
                 tol=SUBTOTAL_TOLERANCE,
                 detail=f"balance sheet at {close_date}")
            # Internal continuity: opening + change = close.
            _tie(rep, f"Cash flow: beginning + net change = ending ({period})",
                 "cash-tie", c.get("ending_cash"),
                 (c.get("beginning_cash") or 0) + (c.get("net_change_in_cash") or 0),
                 tol=SUBTOTAL_TOLERANCE)

    # --- C. Net earnings agrees to the movement in retained earnings ---------
    re_line = next((l for l in bs_lines
                    if l.get("role") == "retained_earnings"), None)
    if not roll:
        _missing(rep, "Net earnings agrees to movement in retained earnings",
                 "re-tie", "no statements.equity_rollforward")
    else:
        for row in roll:
            period = row.get("period", "?")
            opening = row.get("opening_retained_earnings")
            ni = row.get("net_income")
            dist = row.get("distributions") or 0
            closing = row.get("closing_retained_earnings")
            if opening is None or ni is None or closing is None:
                _missing(rep,
                         f"Retained earnings rollforward complete ({period})",
                         "re-tie", "opening, net_income or closing is absent")
                continue
            _tie(rep, f"Retained earnings rollforward foots ({period})",
                 "re-tie", closing, opening + ni + dist,
                 tol=SUBTOTAL_TOLERANCE,
                 detail=f"opening {opening:,.0f} + NI {ni:,.0f} "
                        f"+ distributions {dist:,.0f}")
            # The rollforward's net income must be the P&L's net income -- a
            # rollforward that foots against its own made-up NI proves nothing.
            pt = pnl_totals.get(period)
            if pt is None:
                _missing(rep,
                         f"Rollforward net income = P&L net income ({period})",
                         "re-tie", f"no P&L totals for period {period}")
            else:
                _tie(rep, f"Rollforward net income = P&L net income ({period})",
                     "re-tie", pt.get("net_income"), ni,
                     tol=SUBTOTAL_TOLERANCE)
            # And the closing balance must be what the balance sheet says.
            close_date = row.get("closing_date")
            if re_line is not None and close_date:
                bs_re = (re_line.get("values") or {}).get(close_date)
                if bs_re is not None:
                    _tie(rep,
                         f"Rollforward closing RE = balance sheet RE ({period})",
                         "re-tie", bs_re, closing, tol=SUBTOTAL_TOLERANCE,
                         detail=f"balance sheet at {close_date}")

    # --- D. Detail foots to totals, per period ------------------------------
    if not pnl_periods or not pnl_totals:
        _missing(rep, "Detailed revenue ties to total revenue", "pl-tie",
                 "no statements.pnl periods or totals")
    else:
        for period in pnl_periods:
            t = pnl_totals.get(period)
            if t is None:
                _missing(rep, f"P&L totals present ({period})", "pl-tie",
                         f"period listed in pnl.periods but absent from totals")
                continue
            _tie(rep, f"Detailed revenue ties to total revenue ({period})",
                 "pl-tie", t.get("total_revenue"),
                 _sum_lines(pnl.get("revenue_lines"), period),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"Detailed cost of sales ties to total ({period})",
                 "pl-tie", t.get("total_cogs"),
                 _sum_lines(pnl.get("cogs_lines"), period),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"Detailed SG&A ties to total ({period})", "pl-tie",
                 t.get("total_sga"), _sum_lines(pnl.get("sga_lines"), period),
                 tol=SUBTOTAL_TOLERANCE)

            # --- E. Cross-statement / within-statement arithmetic ----------
            _tie(rep, f"Revenue - cost of sales = gross profit ({period})",
                 "pl-tie", t.get("gross_profit"),
                 (t.get("total_revenue") or 0) - (t.get("total_cogs") or 0),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"Gross profit - SG&A = EBITDA ({period})", "pl-tie",
                 t.get("ebitda"),
                 (t.get("gross_profit") or 0) - (t.get("total_sga") or 0),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"EBITDA - D&A = EBIT ({period})", "pl-tie",
                 t.get("ebit"),
                 (t.get("ebitda") or 0) - (t.get("depreciation_amortization") or 0),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"Pre-tax income foots ({period})", "pl-tie",
                 t.get("pretax_income"),
                 (t.get("ebit") or 0) - (t.get("interest_expense") or 0)
                 + (t.get("other_income") or 0),
                 tol=SUBTOTAL_TOLERANCE)
            _tie(rep, f"Net income foots ({period})", "pl-tie",
                 t.get("net_income"),
                 (t.get("pretax_income") or 0)
                 - (t.get("income_tax_provision") or 0),
                 tol=SUBTOTAL_TOLERANCE)

    # --- F. Cash-flow statement internal arithmetic -------------------------
    for period, c in cf_detail.items():
        derived_op = ((c.get("net_income") or 0)
                      + sum((c.get("noncash") or {}).values())
                      + sum((c.get("working_capital") or {}).values()))
        _tie(rep, f"Cash flow: operating section foots ({period})", "cf-tie",
             c.get("net_operating"), derived_op, tol=SUBTOTAL_TOLERANCE)
        _tie(rep, f"Cash flow: net change = op + inv + fin ({period})", "cf-tie",
             c.get("net_change_in_cash"),
             (c.get("net_operating") or 0) + (c.get("net_investing") or 0)
             + (c.get("net_financing") or 0), tol=SUBTOTAL_TOLERANCE)
        # The CF's net income must be the P&L's, for the same reason as the
        # rollforward's.
        pt = pnl_totals.get(period)
        if pt is not None:
            _tie(rep, f"Cash flow net income = P&L net income ({period})",
                 "cf-tie", pt.get("net_income"), c.get("net_income"),
                 tol=SUBTOTAL_TOLERANCE)

    # --- G. EBITDA bridge ---------------------------------------------------
    bridge = detail.get("ebitda_bridge") or {}
    addbacks = bridge.get("addbacks") or []
    reported = _scalar(bridge.get("reported_ebitda"))
    normalized = _scalar(bridge.get("normalized_ebitda"))
    if reported is None or normalized is None:
        _missing(rep, "Add-backs sum into normalized EBITDA", "bridge-tie",
                 "ebitda_bridge is missing reported_ebitda or normalized_ebitda")
    else:
        _tie(rep, "Add-backs sum into normalized EBITDA", "bridge-tie",
             normalized, reported + sum(float(a.get("amount") or 0)
                                        for a in addbacks),
             tol=SUBTOTAL_TOLERANCE,
             detail=f"{len(addbacks)} add-back(s) on the schedule")
        # And reported EBITDA must be the P&L's EBITDA for the bridge's period.
        bp = bridge.get("period")
        if bp and bp in pnl_totals:
            _tie(rep, f"Bridge reported EBITDA = P&L EBITDA ({bp})",
                 "bridge-tie", (pnl_totals[bp] or {}).get("ebitda"), reported,
                 tol=SUBTOTAL_TOLERANCE)
        elif bp:
            _missing(rep, "Bridge reported EBITDA = P&L EBITDA", "bridge-tie",
                     f"bridge period {bp!r} not present in pnl.totals")
        else:
            _missing(rep, "Bridge reported EBITDA = P&L EBITDA", "bridge-tie",
                     "ebitda_bridge has no period, so it cannot be tied to "
                     "the P&L")

    # --- H. Non-blocking reconciliations, surfaced not hidden ---------------
    conc = detail.get("customer_concentration") or {}
    master = conc.get("customer_master") or []
    ttm = (detail.get("meta") or {}).get("primary_period")
    if master and ttm and ttm in pnl_totals:
        total_rev = (pnl_totals[ttm] or {}).get("total_revenue") or 0
        covered = float(sum(c.get("revenue") or 0 for c in master))
        pct = (covered / total_rev * 100) if total_rev else 0
        rep.add(name="Customer detail reconciles to total revenue",
                group="customer-tie",
                passed=abs(covered - total_rev) <= SUBTOTAL_TOLERANCE,
                expected=round(total_rev, 2), actual=round(covered, 2),
                delta=round(covered - total_rev, 2),
                tolerance=SUBTOTAL_TOLERANCE, blocking=False,
                detail=f"customer schedule covers {pct:.1f}% of {ttm} revenue")

    unresolved = conc.get("unresolved_name_matches") or []
    rep.add(name="Customer names resolved across source documents",
            group="customer-tie", passed=(len(unresolved) == 0),
            expected=0, actual=len(unresolved), blocking=False,
            detail=("unresolved: " + "; ".join(
                str(u.get("variant", u)) for u in unresolved[:6]))
            if unresolved else "all names matched")

    ar = detail.get("ar_aging") or {}
    if ar.get("buckets"):
        aged = float(sum(b.get("amount") or 0 for b in ar["buckets"]))
        gross = ar.get("gross_ar")
        if gross is None:
            _missing(rep, "AR aging foots to gross AR", "ar-tie",
                     "ar_aging has buckets but no gross_ar", blocking=False)
        else:
            _tie(rep, "AR aging foots to gross AR", "ar-tie", gross, aged,
                 tol=SUBTOTAL_TOLERANCE, blocking=False,
                 detail=f"{len(ar['buckets'])} aging buckets")

    unconfirmed = [a for a in addbacks
                   if not a.get("confidence")
                   or a.get("confidence") == "unconfirmed"]
    rep.add(name="Every add-back carries a confidence and a basis",
            group="bridge-tie", passed=(len(unconfirmed) == 0),
            expected=0, actual=len(unconfirmed), blocking=False,
            detail=("unconfirmed: " + ", ".join(
                str(a.get("label")) for a in unconfirmed[:6]))
            if unconfirmed else "all add-backs evidenced")

    if hard_stop and rep.blocking_failures:
        names = "; ".join(f"{c.name} (delta={c.delta}, {c.detail})"
                          for c in rep.blocking_failures)
        raise MAError("validation gate failed; no one-pager on untied numbers",
                      stage="validate", schedule="gate", detail=names)
    return rep


def _scalar(v):
    """Accept either a bare number or a {"value": n, "source": ...} object.

    The schema uses both shapes in different places and the renderer already
    tolerates both; the gate must not be the one place that only handles one.
    """
    if isinstance(v, dict):
        v = v.get("value")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
