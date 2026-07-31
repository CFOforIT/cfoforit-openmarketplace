# M&A Command Center — engine

The machinery behind a deal command center, with no methodology attached.

Two things worth having:

**A financial tie-out gate that fails honestly.** Before you rely on a target's numbers,
`ma_engine.validate` checks that the balance sheet balances at every date, that cash agrees to
the cash-flow statement, that net income agrees to the movement in retained earnings *and* to
the P&L, that detail foots to every total, and that add-backs sum into the normalized EBITDA
you're quoting. Tolerance is **one dollar**, not a percentage — in diligence a small
unexplained difference usually means a whole schedule is wrong.

The property that makes it worth using: **a check that cannot run counts as failed.** Feed it a
file with no balance sheet and it reports the balance-sheet check as failed with "could not
run", never as passed. A gate that returns PASS when it cannot see is worse than no gate,
because you trust it.

**A self-contained command-center renderer.** `ma_engine.render` turns deal JSON into one HTML
file — tabs, collapsible groups, an open-items-only filter, status pills. No build step, no
server, no external requests. Opens in any browser and survives being emailed.

## What this is not

This is the engine, not a playbook. It ships **no** diligence checklist, no integration task
library, and no scoring rubric — those are CFOforIT's own work product and stay in-house. You
supply your own JSON; the engine renders and validates whatever you give it.

## Install

```
/plugin marketplace add cfoforit/cfoforit-openmarketplace
/plugin install ma-command-center@cfoforit-openmarketplace
```

Or just copy `engine/ma_engine/` into your own project:

```python
import sys; sys.path.insert(0, "engine")
from ma_engine import validate as V, render

report = V.validate(my_statements, hard_stop=False)
print(report.status, [c.name for c in report.blocking_failures])

html = render.render_command_center("Acme Holdings", "Target Co", docs,
                                   audience="client", prepared_by="Acme Holdings")
```

`engine/README.md` documents the JSON shapes.

## Generated, not hand-edited

**Everything under `engine/` is generated from CFOforIT's internal repository and will be
overwritten.** Edits made here are lost on the next sync. Open an issue instead — happy to take
fixes upstream.

A drift check in the internal repository fails the build whenever this copy stops matching its
source, so what you see here is what we run.

## Licence

See `LICENSE` at the repository root.
