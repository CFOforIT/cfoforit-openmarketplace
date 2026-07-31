---
name: eos-setup
description: Configure the EOS Dashboard for a company by interviewing the user, then writing a starter file they import. Use when someone says they want to set up the dashboard, get started, add their leadership team, pick scorecard measures, or when they have just downloaded this plugin and do not know what to do next.
version: 1.0.0
autonomy_tier: draft-for-review
blast_radius: private
model_tier: sonnet
model_tier_rationale: "A structured interview plus writing a JSON starter file. Shape is fixed and the judgment is the user's, not the model's."
expected_token_budget: "5K-15K per invocation — one interview pass and one file write; reads no large inputs."
trust_level: external
---

# Set up the EOS Dashboard

Your job is to save the user twenty minutes of typing into a blank dashboard. Interview them
in plain conversation, then hand them one file to import. You are not filling in a form; you
are helping a leadership team get their operating cadence into a tool on the first try.

## What you produce

A single JSON file the user imports with the dashboard's **Import a backup** button. Nothing
else. You never edit `app/index.html`, and you never send anything anywhere.

## Before you start

1. Confirm they can open the dashboard: `app/index.html` in this repo, double-clicked, or
   opened in Chrome or Edge. If they have not opened it yet, tell them to do that first so
   they can see what they are configuring.
2. If they have already set it up and want to change something, do NOT use this skill.
   Tell them to click **Setup** in the dashboard's top bar and edit it directly. That is
   faster than regenerating a file, and it will not overwrite work they have done.

## The interview

Ask these in order, conversationally, a couple at a time. Do not dump the whole list at once.

1. **Company name.** Required.
2. **Fiscal year start month.** Default January. One question, move on.
3. **Leadership team.** Everyone who sits in the weekly meeting: name plus the seat or title
   they hold. Push gently for the seat, because it becomes the owner label on every priority.
   If they give you a list without seats, accept it and mark seats blank rather than stalling.
   Canonical EOS seats, offer them as suggestions and never as a constraint: Visionary,
   Integrator, Sales & Marketing, Operations, Finance. Real companies have people holding
   three seats and calling themselves "VP Service Delivery". Use their words.
4. **Scorecard measures.** The handful they review weekly. Suggest from this list, which is
   tuned for professional services and IT services firms, and let them add their own:
   Revenue, Gross Margin %, MRR, New MRR, Churn %, Utilization %, Cash, AR over 60 days,
   SLA attainment %, CSAT, Pipeline created, Close rate %.
   Ask for a weekly or monthly goal per measure if they know it. Blank is fine.
5. **Meeting day, time, and length.** Default Monday 09:00, 90 minutes.

Stop there. Do NOT try to collect their vision plan in this skill; that is `eos-vision`, and
mixing the two makes both worse. Offer it as the next step at the end.

## The file you write

Write to a path the user picks, or default to their Downloads or Desktop. Name it
`EOS-Setup-<Company>.json`. Shape:

```json
{
  "schema": 4,
  "config": {
    "setupComplete": true,
    "fyStartMonth": 1,
    "meeting": { "day": "Mon", "time": "09:00", "durationMin": 90 }
  },
  "company": {
    "name": "<company>",
    "people": [
      { "id": "p1", "name": "<name>", "seat": "<seat>", "seatCanonical": null, "order": 0 }
    ]
  },
  "roster": {
    "departments": ["<distinct seat labels>"],
    "people": [ { "name": "<name>", "dept": "<seat>" } ]
  },
  "scorecard": {
    "rows": [
      { "id": "sc1", "label": "Revenue", "unit": "currency", "goal": null,
        "direction": "higher", "ownerId": "p1" }
    ]
  },
  "plans": {
    "<current year>": { "annualGoals": [], "quarters": {
      "Q1": {"rocks": []}, "Q2": {"rocks": []}, "Q3": {"rocks": []}, "Q4": {"rocks": []} } }
  },
  "headlines": [], "ids": [], "todos": [], "ratings": {}, "ratingHistory": [],
  "raters": ["<each person's name>"],
  "vto": {
    "horizonYears": 3,
    "coreFocus": { "purpose": "", "niche": "" },
    "values": [], "bhag": { "statement": "", "by": "<year + 10>" },
    "tenYear": { "target": "", "by": "<year + 10>", "percent": 0 },
    "picture": { "revenue": "", "profit": "", "measurables": "", "bullets": [] },
    "oneYear": { "revenue": "", "profit": "", "measurables": "" },
    "marketing": { "targetMarket": "", "uniques": [], "process": "", "guarantee": "" },
    "history": {}
  }
}
```

Rules that matter:

- `roster` must mirror `company.people`, with `dept` set to the person's seat. The dashboard's
  priority-grouping code reads `roster`, so a mismatch means owners do not appear in dropdowns.
- `raters` is a flat array of names, used by the meeting rating.
- `unit` is one of `currency`, `percent`, `number`. `direction` is `higher` or `lower`. Churn
  and AR over 60 are `lower`; almost everything else is `higher`.
- Use the real current year for the `plans` key.
- Leave `vto` empty. `eos-vision` fills it, and a half-guessed vision is worse than a blank one.
- Every `id` must be unique within its list. `p1`, `p2`, `sc1`, `sc2` is fine.

## Hand-off

Tell them exactly this, in your own words:

1. Open the dashboard.
2. Click **Import a backup** in the banner, or the **Absorb updates** area, and pick the file.
3. Confirm their company name shows in the top left and their people appear as owners.
4. Then offer: "Want help drafting your vision plan?" and point at `eos-vision`.

## Do not

- Do not invent people, measures, or goals they did not give you. A dashboard seeded with
  plausible-looking fiction is worse than an empty one, because they will trust it.
- Do not put a dollar figure anywhere they did not state.
- Do not send, upload, or post the file anywhere. Write it to disk and stop.
