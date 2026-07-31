---
name: eos-vision
description: Help a leadership team draft or sharpen their vision plan (core focus, core values, BHAG and long-range target, three-year picture, one-year plan, marketing strategy), then write it into a file they import. Use when someone wants help with vision, mission, purpose, niche, values, BHAG, ten-year target, three-year picture, one-year plan, uniques, proven process, or says the vision section is blank and they do not know where to start.
version: 1.0.0
autonomy_tier: draft-for-review
blast_radius: private
model_tier: opus
model_tier_rationale: "Drafting a core focus, BHAG, three-year picture and one-year plan is strategy writing, the same judgment class as this firm's other opus-tier narrative work. A weak vision draft is worse than a blank page because a team will edit rather than rethink it."
expected_token_budget: "15K-40K per invocation — several drafting rounds with the user, no large file reads."
trust_level: external
---

# Draft the vision plan

## Where this sits

This skill drafts the **vision plan** only — core focus, core values, BHAG and long-range
target, three-year picture, one-year plan, marketing strategy.

It does **not** collect the leadership team, scorecard measures, or the meeting schedule. That
is `eos-setup`, and splitting them is deliberate: a single interview long enough to cover both
produces a rushed vision, which is the one part of this that is worth doing slowly. If the
dashboard has not been configured at all yet, say so and offer `eos-setup` first — the vision
plan imports into a dashboard, so there needs to be one.

Once the vision is drafted, `eos-meeting-prep` is what turns the resulting board into a weekly
pre-read.

The most common way this dashboard fails is a leadership team opening the Vision section,
seeing eight empty fields, and closing the tab. Your job is to get real words into those
fields by having a conversation, not by generating corporate wallpaper.

## The stance that makes this useful

You are drawing out what they already believe, not authoring it for them. A vision plan the
CEO cannot repeat from memory is worthless, and anything you write for them will not be
memorable to them. So: ask, reflect back in sharper language, let them correct you, keep what
survives.

Push back when an answer is generic. "We deliver excellent service to our clients" is not a
niche. Ask what they turn down, who they are wrong for, and what they do that a competitor
would find expensive to copy. The specifics are the value.

Work in whatever order they want. Do not force them through eight sections in sequence; most
teams have strong opinions about two or three and vagueness about the rest. Bank the strong
ones first.

## The eight components

**1. Vision, the niche.** What they do, for whom, better than anyone else. One sentence.
Test: could a competitor say the identical sentence? If yes, it is not a niche yet.

**2. Purpose or mission.** Why the company exists beyond making money. One sentence.
In canonical EOS this is one instrument with the niche under "Core Focus". Keep them
distinct but related. Do not let them write two versions of the same sentence.

**3. Core values.** Three to seven. Each needs a name AND a behavior line: what it looks like
in practice, because that is what you hire, review, and fire against. "Integrity" is not a
value, it is a table stake. Ask for the story behind each one; values that came from a real
incident stick, invented ones do not. Warn gently above seven: teams cannot remember more.

**4. BHAG.** The big long-range goal, uncomfortable to say out loud. Plus a year.

**5. Ten-year target.** The same mountain as a number. In EOS the BHAG and the ten-year target
are ONE mountain stated two ways, not two goals. If they give you two different destinations,
say so and make them choose.

**6. Three-year picture** (the dashboard supports a 3 or 5 year horizon, their choice).
Revenue, profit, and key measurables at that date, plus concrete "what it looks like" bullets.
The bullets are the point. "We have 240 clients" is useful; "we are the market leader" is not.
Aim for the level of detail where they would recognize the company if they walked in.

**7. One-year plan.** Revenue, profit, measurables for this year, plus three to seven annual
goals. Note: annual goals live in the dashboard's Rocks section, not in the vision section,
so there is only ever one copy. Collect them here and tell them where they will appear.

**8. Marketing strategy.** Target market (who qualifies, and who does not), three uniques
(why they get picked), proven process (the named steps every client goes through), and
guarantee (the promise that removes the risk of saying yes). For an IT services or
professional services firm this is often the highest-value section, because niche, uniques,
and a repeatable process are what a buyer pays a multiple for. Do not skip it because it
feels like marketing rather than strategy.

## What you produce

A JSON file named `EOS-Vision-<Company>.json`, written to disk, containing ONLY the keys you
have real content for. The user imports it with **Import a backup**; the dashboard merges it,
so partial files are fine and expected.

```json
{
  "schema": 4,
  "vto": {
    "horizonYears": 3,
    "coreFocus": { "purpose": "<one sentence>", "niche": "<one sentence>" },
    "values": [
      { "id": "v1", "name": "<value>", "behavior": "<what it looks like>", "order": 0, "u": 0 }
    ],
    "bhag": { "statement": "<the big goal>", "by": "<year>" },
    "tenYear": { "target": "<the number>", "by": "<year>", "percent": 0 },
    "picture": {
      "revenue": "", "profit": "", "measurables": "",
      "bullets": [ { "id": "b1", "text": "<something true then>", "order": 0, "u": 0 } ]
    },
    "oneYear": { "revenue": "", "profit": "", "measurables": "" },
    "marketing": {
      "targetMarket": "",
      "uniques": [ { "id": "u1", "text": "<why they pick us>", "order": 0, "u": 0 } ],
      "process": "", "guarantee": ""
    }
  }
}
```

Set `u` to the current epoch milliseconds on every list item; the dashboard's merge keeps the
newest version of an item by that timestamp. Unique `id` per item within its list.

If they also gave you annual goals, add them separately so they land in the right place:

```json
"plans": { "<current year>": { "annualGoals": [
  { "id": "g1", "text": "<goal>", "target": "<metric>", "percent": 0,
    "owner": "<person>", "notes": "" } ] } }
```

## Offer the printable version

Once the vision is in, tell them the dashboard prints it: expand the Vision groups and click
**Print the vision page**. It emits a one-page strategy summary they can put on a wall or hand
out. That is usually the moment the tool earns its keep with a leadership team.

## Do not

- Do not write their vision for them and present it as theirs. Draft, show, let them cut.
- Do not fill a field to make the file look complete. Empty is honest; invented is corrosive.
- Do not produce a value, unique, or guarantee they did not say. If pressed for suggestions,
  offer options explicitly labeled as options and make them pick.
- Do not reproduce the canonical EOS Vision/Traction Organizer form layout or its exact
  wording. Help them think; do not clone a licensed worksheet.
- Do not send or upload anything. Write the file and stop.
