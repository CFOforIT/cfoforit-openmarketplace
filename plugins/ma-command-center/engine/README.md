# ma_engine

Generated from CFOforIT's internal repository. Do not edit here; see `GENERATED`.

Three modules:

- **`validate.py`** — the financial tie-out gate. `validate(detail, hard_stop=False)`
  returns a `CheckReport` with `.status` (`"pass"`/`"fail"`), `.blocking_failures`,
  `.flags`, and `.as_snapshot_block()` for the renderer.
- **`render.py`** — `render_command_center(client, target, docs, audience=…,
  prepared_by=…)` returns one self-contained HTML document. No external requests.
- **`config.py`** — portable deal-path resolution. Refuses to guess: a path that
  escapes the configured root, or an unknown machine, raises rather than falling
  back to a default that may be wrong.

## The `statements` shape the gate reads

```
detail["statements"] = {
  "pnl": {
    "periods": ["FY2024", "FY2025", "TTM"],
    "revenue_lines": [ {"label": …, "values": {period: amount}} ],
    "cogs_lines":    [ {"label": …, "values": {period: amount}} ],
    "sga_lines":     [ {"label": …, "values": {period: amount}} ],
    "totals": {period: {"total_revenue", "total_cogs", "gross_profit",
                        "total_sga", "ebitda", "depreciation_amortization",
                        "ebit", "interest_expense", "other_income",
                        "pretax_income", "income_tax_provision", "net_income"}}
  },
  "balance_sheet": {
    "dates": ["2024-12-31", "2025-12-31"],
    "lines": [ {"label": …,
                "section": "asset" | "liability" | "equity",
                "role": "cash" | "retained_earnings" | …,   # optional but see below
                "values": {date: amount}} ]
  },
  "cash_flow": {
    "periods": ["FY2025"],
    "periods_detail": {period: {"opening_date", "closing_date", "net_income",
                                "noncash": {}, "working_capital": {},
                                "net_operating", "net_investing", "net_financing",
                                "net_change_in_cash", "beginning_cash",
                                "ending_cash"}}
  },
  "equity_rollforward": [
    {"period", "opening_retained_earnings", "net_income", "distributions",
     "closing_retained_earnings", "closing_date"}
  ]
}
```

**`role` is load-bearing.** The gate cannot find cash by matching a label — targets
call it "Cash", "Cash & Cash Equivalents", "Cash and equivalents". Tag the two lines
it must locate with `role: "cash"` and `role: "retained_earnings"`. Omit them and the
corresponding checks **fail** with "could not run" rather than silently not running.

**`closing_date` on each cash-flow period** is what ties ending cash to the right
balance-sheet column. Without it the cash check cannot run, and that is a failure.

`ebitda_bridge` (optional) takes `period`, `reported_ebitda`, `addbacks[]` with
`amount`, and `normalized_ebitda`. Both figures accept either a bare number or
`{"value": n, "source": "…"}`.
