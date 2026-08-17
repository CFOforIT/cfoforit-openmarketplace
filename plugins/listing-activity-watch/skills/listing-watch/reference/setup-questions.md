# First-run setup questions

Ask all ten in one message, numbered, so the person answers in a single pass. Every answer
maps to a field in `config.json`; nothing here is asked twice.

Defaults in brackets are safe. If someone says "just use the defaults", accept that, write the
config, and only insist on questions 1 and 2 — without those the skill has nothing to read and
nowhere to write.

---

**1. Where is your agent roster file?**
Full path to the Excel workbook holding agent names and profile links.
*Why:* it is the only input. If it does not exist yet, the skill writes a template to fill in.
→ `roster_path`

**2. Where should the outputs go?**
Folder for the Excel workbook and the dashboard. A OneDrive or SharePoint-synced folder is a
good choice; the run's working files go in a `_listing_watch` subfolder there.
*Why:* the deliverable has to land somewhere the person who reads it can reach.
→ `output_folder`

**3. Which sites are in scope?** [zillow, redfin, realtor, homes]
*Why:* fewer sites means a faster run. Any agent can still have blanks on individual sites;
this sets the ceiling, the roster sets the per-agent reality.
→ `sites`

**4. How recent does a SOLD have to be to still matter?** [14 days]
*Why:* a sale from four months ago is history. A sale from last week is a live collections
lead. This is the line between the two.
→ `sold_window_days`

**5. Which statuses should count as a hit?** [PENDING, CONTINGENT, UNDER CONTRACT, plus SOLD
inside the window]
*Why:* some teams also want ACTIVE or COMING SOON. Most do not, because those do not indicate
money moving.
→ `qualifying_statuses`

**6. How close does a name have to be before we call it a match?** [0.80]
A number between 0 and 1. Lower catches more spelling variants and returns more noise to
review; higher is stricter. Non-matches are never dropped either way, only labeled.
*Why:* profiles show "Bob Smith, PA" where the roster says "Robert Smith". Someone has to
decide how much of that to auto-accept.
→ `near_match_threshold`

**7. What short label should go in the output file names?** [Listing-Watch]
Appears as `<label>_ListingWatch_2026-08-01_to_2026-08-16.xlsx`.
*Why:* teams running this for more than one book of business need the files to be tellable
apart at a glance.
→ `label`

**8. When should this run, and does it need to be scheduled?** [manual for the first week]
*Why:* the honest answer for week one is manual, so the person can see what it produces before
trusting it overnight. Scheduling is a separate step, and worth doing only once the output has
been believed for a few days.
→ `run_note`

**9. Who reads the output each morning, and what do they do when a site is blocked?**
*Why:* this is the question that keeps the tool honest. A blocked site is reported loudly, and
someone has to know that the answer is "check those agents by hand today", not "assume it was
a quiet night".
→ `owner`

**10. Is there anything the watch must never do?** [no outbound contact, no logged-in or
MLS-gated data]
*Why:* the defaults already refuse both, but saying it out loud once means the boundary is the
client's, not an assumption of ours.
→ `constraints_note`

---

## Two things worth saying out loud during setup

**The roster links are the whole game.** The skill visits exactly the URLs given and never
goes looking. That is deliberate: a link chosen by a person is the right agent in the right
market, and a link found by a machine is a coin flip. The cost is that a rotted link stays
rotted until someone fixes it, which is why name mismatches are reported rather than hidden.

**Browsing happens in the person's own Chrome, signed in as them, at human speed.** There is
no scraping service, no proxy, and no bot-evasion in this skill. If a site pushes back, the
run says so and moves on. That is slower than the alternatives and it is the version that is
defensible six months from now.
