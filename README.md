# CFOforIT Open Marketplace

Free tools we build to run our own firm, shared with our clients and anyone else who wants
them. No signup, no telemetry, nothing phoning home.

Currently one tool, below. More may follow; if you install the marketplace once you will get
them without doing anything else.

---

# EOS Dashboard

A free, self-contained dashboard for running a leadership operating cadence: your vision plan,
your scorecard, quarterly priorities, and the weekly meeting that connects them.

**Your data never leaves your machine.** There is no account, no server, and no telemetry. The
dashboard is a single HTML file that stores everything in your own browser, or in a folder you
choose. Nobody else can see it, including us.

---

## Two ways to use this

### 1. Just open it (no Claude needed)

Download this repository, then open **`app/index.html`** in Chrome or Edge. That is the whole
install. Answer five setup questions and you are running.

Prefer a link you can bookmark? Host `app/` on any static host you already have. It needs no
backend.

### 2. Add the Claude plugin (recommended if you use Claude Code or Cowork)

The dashboard works fine on its own. The plugin adds three skills that do the tedious parts for
you: configuring it, drafting your vision plan, and prepping each weekly meeting.

```
/plugin marketplace add CFOforIT/cfoforit-openmarketplace
```

Then install the `eos-dashboard` plugin and say something like *"help me set up the EOS
dashboard"*.

**Pinning to a release.** The command above tracks `main`, which moves. Releases are tagged,
so if you would rather pin to a fixed version — and be able to roll back to it — use the tag:

```
/plugin marketplace add CFOforIT/cfoforit-openmarketplace@v1.0.0
```

The current release is [`v1.0.0`](https://github.com/CFOforIT/cfoforit-openmarketplace/releases/tag/v1.0.0).
See [CHANGELOG.md](CHANGELOG.md) for what changed in each one.

| Skill | What it does |
|---|---|
| `eos-setup` | Interviews you about your company, leadership team, seats, scorecard measures, and meeting cadence, then writes a starter file you import. Saves about twenty minutes of typing. |
| `eos-vision` | Talks you through the vision plan: core focus, core values with behaviors, BHAG and long-range target, the multi-year picture, this year's plan, and marketing strategy. Fixes the blank-page problem. |
| `eos-meeting-prep` | Reads your exported board and drafts a one-page pre-read: what is off track, what is overdue, which issues to work, and real headlines. |

The skills only ever read files you point them at and write files to your disk. They send
nothing anywhere.

---

## What is in the dashboard

- **Vision plan.** Vision and purpose, core values, BHAG and long-range target, a three or
  five year picture, this year's plan, and marketing strategy. Prints to a one-page summary you
  can put on a wall.
- **Scorecard.** Pick from twelve pre-written measures common to professional services and IT
  services firms, or write your own. Enter the numbers weekly.
- **Priorities.** Annual goals down to quarterly priorities, by owner, with status and percent
  complete. Group them by function or by person. One click carries the unfinished ones into the
  next quarter and archives the rest.
- **The weekly meeting.** Headlines, an issues list, to-dos with owners and due dates, a meeting
  rating, and a segment timer so ninety minutes actually holds.

---

## Sharing it with your leadership team

There is no live multi-user editing, and we would rather say that plainly than pretend. Live
shared editing needs a server, and a server means somebody holds your strategic and financial
data. Instead:

- **One person owns the board** and drives it on screen during the meeting. That is how most
  teams already run it.
- **`Publish board`** writes a self-contained read-only snapshot you can drop in Teams, Slack,
  or email. It opens on any phone with no setup.
- Inside that snapshot, each person picks their own name, updates their own priorities and
  to-dos, and clicks **`Copy my updates`** to get a short code.
- The board owner pastes it into **`Absorb updates`**. It merges by item, keeps the newest
  edit, and will not resurrect anything you deleted.

One copy-paste hop per person per week, and it works on every browser and every phone.

---

## Where your data lives, and how not to lose it

Read this part before you put real work in.

By default everything is stored in **your browser on that one device**. That is durable enough
for normal use and fragile in three specific ways: clearing browser data wipes it, a different
device does not have it, and Safari can clear stored data on its own if you go several weeks
without opening the page.

So, in order of preference:

1. **Pick a data folder** (Setup, step 6). The dashboard writes
   `EOS-Dashboard-<Company>.json` into a folder you choose, on every change. Point it at a
   folder OneDrive, SharePoint, Dropbox, or Google Drive already syncs and your own cloud keeps
   the offsite copy. **Chrome and Edge only.**
2. **Or set your download folder once.** The backup filename is always the same, so pointing
   your browser's download location at your synced folder achieves the same thing. Works in
   every browser, including Safari.
3. **Either way, the `Back up` button** downloads a full copy any time, and the dashboard backs
   itself up when you close out a meeting. The pill in the top bar tells you how old your last
   backup is.

We cannot recover your data, because we never have it.

---

## Requirements

- A current browser. Chrome or Edge for the data-folder feature; everything else works in
  Safari and Firefox too.
- Nothing else. No install, no account, no server, no subscription.

## Privacy

The dashboard makes no network requests once the page has loaded. No analytics, no telemetry,
no phone-home. You can verify this yourself: open your browser's Network tab and use it.

## Support

Provided as-is, with no support commitment. It is deliberately simple and self-contained so
there is very little to go wrong. Issues and pull requests are welcome but may not get a fast
reply.

## License

MIT. See [LICENSE](LICENSE). Use it, change it, ship it inside your own company.

## A note on EOS

EOS, Entrepreneurial Operating System, Level 10 Meeting, and Vision/Traction Organizer are
trademarks of EOS Worldwide, LLC. **This tool is independent and is not affiliated with,
endorsed by, or licensed by EOS Worldwide.** If you work with an EOS Implementer, use the tools
they recommend; this is not a substitute for the work they do with you.

---

Built by [CFOforIT](https://cfoforit.com), fractional CFO services for IT services companies.
We built it to run our own leadership meeting and figured you might want it too.
