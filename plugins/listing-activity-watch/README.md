# Listing Activity Watch

Someone on your team keeps a list of real estate agents and checks their public profile pages
every few days, looking for a listing that has gone **pending**, **contingent**, **under
contract**, or that **sold recently**. It is a real job, it takes a morning, and things get
missed simply because a hundred agents times four sites is more clicking than anyone can keep
up with.

This does that check for you and hands back two files: an Excel workbook and a dashboard.

**It reads. It never writes to anyone.** No emails, no CRM updates, no outreach. It produces a
list; a person decides what to do with it.

---

## What you get, every run

**A workbook** with five sheets:

| Sheet | What it answers |
|---|---|
| Run summary | Did last night's check actually finish? |
| Hits | Which agents have a pending, contingent, under-contract, or recent sold listing |
| Names to review | Which profile links are pointing at the wrong person, or someone who changed their name |
| Coverage detail | Was this specific agent checked last night, yes or no |
| Roster issues | Which rows in your list are missing links or duplicated |

**A dashboard**, a single HTML file that opens by double-click, with the same content and a
coverage banner across the top. It makes no network calls of any kind.

Both files are written fresh each run, named with the period they cover.

---

## Why coverage is the first number, not the hit count

Most nights there are no hits. That is normal — this is a watch, not a firehose.

Which means an empty report and a *broken* report look exactly alike. So every run leads with
how many pages were actually read, and the banner goes red the moment anything was blocked or
looked different than expected. A site refusing to load is reported as a refusal, never as
"nothing found".

If coverage is under 100%, the agents that were missed are named on the Coverage detail sheet,
and someone should check those by hand that day. That is the whole discipline of this tool.

---

## Install

You need [Claude Code](https://claude.com/product/claude-code) or Cowork, and the Claude in
Chrome extension.

```
/plugin marketplace add CFOforIT/cfoforit-openmarketplace
```

Then install the `listing-activity-watch` plugin.

One-time, in a terminal:

```
pip install openpyxl
```

---

## First run

Say **"set up the listing watch"**. You will get ten questions in one message. The two that
matter are where your agent list lives and where the output should go; sensible defaults cover
the rest.

If you do not have an agent list yet, the setup writes you a template. It has seven columns:

| Column | |
|---|---|
| `agent_name` | Required. As you know them. |
| `agent_id` | Optional. Your own reference number, passed straight through. |
| `zillow_url` | The agent's profile page. Blank means skip that site for that agent. |
| `redfin_url` | |
| `realtor_url` | |
| `homes_url` | |
| `notes` | Optional, passed through to the report. |

**You supply the profile links; the tool never goes looking for them.** That is deliberate. A
link a person picked is the right agent in the right market. A link a machine guessed is a coin
flip, and one wrong agent's listings does more damage than a hundred missed ones. Grabbing the
links is a one-time job per agent.

---

## Every run after that

Say **"run the listing watch"**, or **"did any of our agents go pending this week?"**

It asks what period you are covering — that sets how far back a sale still counts as recent —
then works through the list and writes the two files.

Expect it to take a while. It browses at human pace in your own signed-in Chrome, roughly 300
page loads for a hundred agents. Overnight is the right slot.

---

## Names that do not match

A profile might say "Bob Smith, PA" where your list says "Robert Smith". Common nicknames,
suffixes and credentials are handled, so that one comes back as an exact match.

Anything less certain is still reported, labeled `near` or `mismatch`, with what the page
actually showed next to what you expected. **A row is never dropped for having the wrong name
on it.** A persistent mismatch usually means the agent changed brokerages and the link needs
updating — which is itself worth knowing.

---

## What it will not do

Some of these are the client's own instruction; all of them are the design.

- Contact an agent, a brokerage, or anyone else, in any way.
- Read MLS, IDX, or anything behind a login. Public profile pages only.
- Defeat a CAPTCHA or work around a site's bot defenses. A block is reported as a block.
- Look for an agent whose profile URL is not already on your list.
- Store or infer anything about a person beyond the name on your list and the public listing
  information on the page.

If a site blocks you every night, the fix is to slow down, split the run across the night, or
drop that site. Three sites checked reliably beat four checked half the time.

---

## A word on the sites

Zillow, Redfin, realtor.com and homes.com each have terms of use governing automated access.
This tool reads public pages, in your own browser, signed in as you, at human speed, and it
does nothing to disguise itself. Whether that fits your agreement with each site is your call
to make, and it is worth actually making once rather than discovering it later.

We built it this way — no scraping service, no proxies, no evasion — precisely so that the
answer to "what is it doing?" is short and true.

---

## Files

Working files live in a `_listing_watch` folder inside your output folder: the config, the
current roster snapshot, and a `snapshots` folder holding one small file per completed run.
Those snapshots are what "new since last run" compares against, so leave them alone. Moving to
a new machine means copying that folder and updating two paths in `config.json`.

## License

MIT. See [LICENSE](../../LICENSE). Fork it, change it, run it inside your own company.

Provided as-is with no support commitment.
