---
name: eos-meeting-prep
description: Prepare a weekly leadership meeting from an exported dashboard board file. Reads the board, flags what is off track, overdue, or unowned, and drafts the issues list and headlines for discussion. Use when someone asks to prep the weekly meeting, get ready for the leadership meeting, review the board before the meeting, or asks what needs attention this week.
---

# Prepare the weekly meeting

Turn an exported board file into a pre-read the leadership team can absorb in two minutes, so
the meeting is spent deciding rather than reading.

## Input

The user's exported board JSON. They produce it with the **Back up** button in the dashboard,
which writes `EOSDashboard_<Company>_<date>.json`. Ask them for the path if they have not given
it. If they have never exported, tell them to click **Back up** once; it takes a second and
also protects their data.

Read it. Do not ask them to paste its contents; it is large.

## What to look at

Work from the data, not from assumptions.

- **Priorities (`plans[<year>].quarters[<Q>].rocks`).** Current quarter only, determined by
  `view.quarter` and `view.year`. Flag anything with `status` of `offtrack` or `atrisk`.
  Also flag a Rock whose `percent` has not moved since the previous export if they give you
  two files, because a Rock frozen at 40 percent for three weeks is the real signal.
  Flag Rocks with no `owner`; unowned work does not happen.
- **Annual goals (`plans[<year>].annualGoals`).** Note any below the pace implied by how far
  through the year they are. Say the arithmetic out loud rather than just asserting it.
- **To-dos (`todos`).** Anything not `Complete` with a `due` in the past is overdue; count the
  days. In this cadence to-dos are seven-day commitments, so more than a couple carrying over
  is itself the issue worth raising.
- **Issues (`ids`).** Anything not `Resolved`, ordered by `priority`. Note issues that have
  been open across multiple exports if you have them.
- **Scorecard (`scorecard.rows`, `revenue`, `pipeline`, `sla`).** Call out measures off their
  `goal`, and respect `direction`: for a `lower` measure like churn or AR over 60, higher is
  worse. Do not congratulate them on a number going the wrong way.
- **Vision (`vto`).** If large parts are empty, mention it once, quietly, as a quarterly item.
  Do not make it this week's headline.

## What you produce

A short pre-read, in chat by default. Offer to save it as a file if they want to circulate it.

Structure it like this, and keep the whole thing under a page:

1. **Where we stand.** Two or three sentences. The honest state of the quarter, not a summary
   of the data. Lead with what changed or what is at risk, not with what is fine.
2. **Off track and needs a decision.** Each item: what it is, who owns it, what is actually
   blocking it if the data says, and the decision the meeting needs to make. If the data does
   not say what is blocking it, say that, and make "find out" the item.
3. **Overdue commitments.** Owner, item, days late. A flat list, no commentary needed.
4. **Suggested issues to work.** Drawn from the above, ordered by what would hurt most if it
   slid another week. Say why each one is on the list.
5. **Suggested headlines.** Genuine wins or callouts you can point to in the data. If there are
   none, say so rather than manufacturing one. A fabricated win teaches the team to discount
   the whole pre-read.

## Getting it back into the dashboard

If they want the suggested issues and to-dos added, write a merge file rather than making them
retype. Name it `EOS-Prep-<Company>-<date>.json` and include only what is new:

```json
{
  "schema": 4,
  "ids": [
    { "id": "i<epoch>a", "title": "<issue>", "owner": "<person>", "status": "Open",
      "priority": "High", "auto": false, "u": <epoch ms> }
  ],
  "todos": [
    { "id": "t<epoch>a", "owner": "<person>", "desc": "<commitment>", "due": "<YYYY-MM-DD>",
      "status": "Not Started", "u": <epoch ms> }
  ],
  "headlines": [ { "id": "h<epoch>a", "text": "<headline>", "u": <epoch ms> } ]
}
```

They import it with **Import a backup**. The dashboard merges by item id and keeps the newest
version by `u`, so this adds without overwriting anything they have edited. Every `id` must be
unique; suffix with a letter if you generate several in the same millisecond.

## Judgment

- **Draft, never decide.** You surface what the data says and propose the agenda. Owners,
  priorities, and commitments are the team's call in the room.
- **Do not invent an owner.** If a Rock has no owner, that is the finding.
- **Do not soften a number.** If revenue is short, say the figure and the gap.
- **Do not add items to the board without being asked.** Write the merge file only on request.
- **Do not send, email, or post the pre-read.** Produce it and stop; the user circulates it.
