# Data contract

Three shapes: the roster going in, the observations the model writes, the report coming out.
All three are fixed. Changing a column name breaks the diff against prior runs.

---

## 1. Roster (Excel, one row per agent)

Sheet name: `Roster` (first sheet is used if that name is absent).

| Column | Required | Notes |
|---|---|---|
| `agent_name` | yes | As you know them. This is what gets matched against the page. |
| `agent_id` | no | Your own reference. Passed through untouched to the output. |
| `zillow_url` | no | Full profile URL. Blank means skip this site for this agent. |
| `redfin_url` | no | Same. |
| `realtor_url` | no | Same. |
| `homes_url` | no | Same. |
| `notes` | no | Free text, passed through to the output. |

Extra columns are ignored, not an error. An agent with no URLs at all is reported as a roster
issue, because a row that can never produce a result is almost always a data-entry miss.

`roster_template.xlsx` written by `lw.py init` has these headers and one example row.

---

## 2. Observations (JSON, written by the model after browsing)

```json
{
  "run_started_at": "2026-08-16T02:04:00-04:00",
  "visits": [
    {
      "agent_name": "Christine Harper",
      "agent_id": "RA-1042",
      "site": "zillow",
      "profile_url": "https://www.zillow.com/profile/example",
      "outcome": "ok",
      "name_on_page": "Christy Harper",
      "listings": [
        {
          "address": "123 Oak St, Plano, TX 75024",
          "status": "PENDING",
          "status_date": "2026-08-14",
          "listing_url": "https://www.zillow.com/homedetails/example"
        }
      ],
      "note": ""
    }
  ]
}
```

**`outcome` is a closed set.**

| Value | Means | When |
|---|---|---|
| `ok` | The profile rendered and was read | Includes a genuinely empty profile |
| `blocked` | Site refused | CAPTCHA, 403, sign-in wall, rate limit, hard timeout |
| `page_changed` | Loaded, but does not look like a profile any more | Redirect to search, layout no longer matches the playbook |
| `url_missing` | No URL on the roster for this site | Not a failure; it is why coverage is not 100% |

`ok` with an empty `listings` array means *checked, nothing there*. It must never be used for
a page that could not be read. The report treats those two cases completely differently, and
that distinction is the main thing standing between this tool and a false sense of calm.

`status_date` is optional; use `null` when the page does not show one. `status` is copied as
the page words it — normalization happens in the script, so "Pending sale", "Under contract"
and "CONTINGENT" all arrive as written and are mapped once, in one place.

---

## 3. Report

Written to `output_folder` as
`<label>_ListingWatch_<period_start>_to_<period_end>.xlsx` and `..._dashboard.html`.

### Sheet: Run summary
Run timestamp, period covered, roster size, visits attempted, read, blocked, changed, skipped,
coverage percentage, and a per-site breakdown. This sheet is first because it is the sheet
that tells you whether to believe the others.

### Sheet: Hits
One row per qualifying listing.

| Column | Notes |
|---|---|
| `agent_name` | As entered on the roster |
| `agent_id` | Passed through |
| `name_on_page` | What the site actually showed |
| `match` | `exact`, `near`, or `mismatch` |
| `match_score` | 0 to 1 |
| `site` | zillow / redfin / realtor / homes |
| `status` | Normalized: PENDING, CONTINGENT, UNDER CONTRACT, SOLD |
| `status_raw` | Exactly as the page worded it |
| `address` | As shown |
| `status_date` | If shown |
| `new_since_last_run` | YES / no |
| `profile_url` | The page visited |
| `listing_url` | The listing, if linked |
| `notes` | Roster notes plus any visit note |

Sorted: new first, then mismatches and near matches, then agent name. The rows most likely to
need a human are the rows at the top.

### Sheet: Names to review
Every visit where `match` is not `exact`, including visits with no hits. A rotted link shows
up here and nowhere else.

### Sheet: Coverage detail
Every visit and its outcome, so "did we actually check Ramirez last night" has an answer.

### Sheet: Roster issues
Rows with no URLs, duplicate agent names, malformed URLs.

### Dashboard
Self-contained HTML, no network calls, opens by double-click. Same content, coverage banner at
the top. The banner is red whenever anything was blocked or changed, and the number it leads
with is coverage, not hits — because a low hit count means nothing until coverage is known.
