# Site playbook

Read this before the first visit of a run. Four sites, four ways of saying the same thing, and
four ways of refusing you.

Site layouts change. Nothing here is load-bearing except the block signatures — if a page no
longer matches what is described, that is `page_changed`, which is a real result worth
reporting, not a problem to work around.

---

## How to read any of them

1. `navigate` to the profile URL.
2. `get_page_text`. If the text is ambiguous or looks truncated, `read_page` for structure.
3. Find the agent name the page displays. Record it verbatim in `name_on_page`, including any
   suffix ("PA", "REALTOR®", team name). The script strips those; you should not.
4. Find the listing section. Record every listing with a status, whatever the status is.
5. Copy the address exactly as shown. Do not reformat, expand abbreviations, or fill in a ZIP
   the page did not give you.

Give each page a few seconds to render. These are all client-side apps and an early read
returns an empty shell that looks exactly like an agent with no listings.

---

## Status vocabulary

Copy the page's wording into `status_raw`; the script maps it. Known mappings:

| Page says | Maps to |
|---|---|
| Pending, Pending sale, Sale pending | PENDING |
| Contingent, Active contingent, Active under contract | CONTINGENT |
| Under contract, Under agreement | UNDER CONTRACT |
| Sold, Closed, Recently sold | SOLD |
| Active, For sale, Coming soon, New construction | (not a hit, still record it) |

Anything unrecognized is carried through as `OTHER` with the raw wording preserved and flagged
in the run summary. An unmapped status is how a site's new label gets noticed.

---

## Zillow

Profile URLs look like `zillow.com/profile/<handle>`.

Listings sit under headings like "For sale", "Sold", "Listings". Sold entries usually carry a
sale date; pending ones often do not.

**Block signature:** a "Press & Hold to confirm you are a human" interstitial, or a page whose
text is only a header and footer with no profile name. Both are `blocked`. Zillow is the most
aggressive of the four; expect it to be the site that fails first when a run goes too fast.

---

## Redfin

Two shapes. Some agents have a real profile at `redfin.com/real-estate-agents/<name>`; many do
not, and the roster may instead hold a search-results URL that lists that agent's deals.

Both are fine. On a search-results page, the "agent name" is the search subject rather than a
displayed profile name — set `name_on_page` to the name shown on the result rows if there is
one, otherwise `null`, and let the script flag it for review rather than guessing.

Redfin labels sold homes with a date and shows "Pending" or "Under contract" as a badge on the
card, not in the title. Read the badge.

**Block signature:** a page saying access has been denied, or an unusually fast empty response.
Redfin pushes back less than Zillow but rate-limits a burst.

---

## realtor.com

Profile URLs look like `realtor.com/realestateagents/<id>`.

Sections are usually "Active listings", "Pending", "Sold". The Sold section is often paginated
and sorted newest first — the first page is enough, since anything past it is older than any
sensible window.

Watch for team profiles: a listing on a team page may belong to a colleague. If the listing
card names a different agent than the profile, record that name in the `note`. It is not a
hit for your agent, and quietly counting it as one is worse than missing it.

**Block signature:** a Cloudflare or "checking your browser" interstitial, or a redirect to
the agent search page. Both are `blocked`.

---

## homes.com

Profile URLs look like `homes.com/real-estate-agents/<name>/<id>/`.

The smallest and most cooperative of the four. Listings are grouped by status with the status
in a heading.

**Block signature:** a sign-in modal over the content. If the modal can be dismissed without
signing in, read the page; if not, `blocked`.

---

## Pace

Roughly 300 page loads at 70-100 agents. Go at human pace. If two consecutive visits to the
same site come back blocked, stop visiting that site for the rest of the run, mark the
remaining visits for it `blocked` with a note saying the site was abandoned after repeated
blocks, and carry on with the others.

That is the correct behaviour, not a failure. A partial run reported honestly is useful. A
full run obtained by hammering a site is a liability, and one obtained by pretending blocks
were empty pages is worse than useless.
