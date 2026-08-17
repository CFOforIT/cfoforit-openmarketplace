# Troubleshooting

---

## "Coverage says 78%. What do I do?"

Open the Coverage detail sheet and filter to anything not `ok`. Those agents were not checked
last night. Check them by hand today, or rerun the watch for just those agents.

Do not treat a low hit count as good news on a day like that. The hits sheet only means what
coverage says it means.

---

## A site is blocked every single night

In order:

1. **Slow the run down.** Blocks usually mean pace. The run has all night.
2. **Split the run.** Two sites at 2am, two at 4am.
3. **Drop the site.** Remove it from `sites` in the config. Three sites checked reliably beat
   four checked half the time, and a site that blocks every night is contributing nothing but
   a red banner.

What not to do: work around the block. This skill does not defeat bot defenses, and a fork
that does is a different thing carrying a different risk. If none of the three options above
work, the honest answer is that the site is not available to this method.

---

## An agent shows `mismatch` every run

The profile URL is almost certainly stale. Common causes: the agent changed brokerages, the
site rebuilt profile URLs, or the wrong profile was captured originally (two agents with the
same name, different market).

Fix the URL on the roster. Do not lower `near_match_threshold` to make the warning stop — that
hides real mismatches everywhere else to silence one.

---

## An agent shows `near` every run and it is genuinely them

Normal. "Bob" versus "Robert", a married name, a middle initial, a "PA" suffix. Either update
the roster to the page's spelling, or leave it — a `near` row is delivered in full and costs
one glance.

---

## The run died halfway

Rerun it. The report is written fresh each time and the diff compares against the last
*completed* run, not a partial one, so a half-finished run cannot poison tomorrow's
"new since last run" column.

If a partial report was already written and someone acted on it, the next full run reproduces
every still-live hit. Nothing is lost by rerunning.

---

## "New since last run" looks wrong

It compares against `_listing_watch/snapshots/`. Two things reset it:

- **First run ever.** Everything is new. Expected.
- **Snapshots folder emptied.** Same effect. Do not delete it.

A listing that flips PENDING → SOLD is a new row, because the status is part of the identity.
That is intended: a sale closing is exactly the event worth surfacing again.

---

## Adding or removing agents

Edit the roster. Nothing else. Adding an agent mid-week means their hits show as new on the
first run that includes them, which is correct — they are new to the watch.

---

## Excel will not open the output

`pip install openpyxl` if the run failed at the report step. If the file exists but Excel
complains, it was written while open in Excel; close it and rerun.

---

## Moving the whole thing to a new machine

Copy the roster and the `_listing_watch` folder, then update the two paths in `config.json`.
The snapshots travel with it, so the diff survives the move.
