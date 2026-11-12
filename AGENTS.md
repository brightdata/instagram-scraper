# For coding agents working in this repository

Read this before changing anything. Every line below was verified against the
live API or the installed SDK on 2026-09-08, and most of it contradicts the
SDK's own docstrings.

## Auth

- The SDK reads `BRIGHTDATA_API_TOKEN` from the environment, from a `.env` file
  found by searching upward from its own install folder (so the project root,
  when the virtualenv is inside the project), or from the Bright Data CLI login.
  Setting it, or running `bdata login` once, is the one step a human must do;
  never paste a key into code.
- Always construct the client as `SyncBrightDataClient(auto_create_zones=False)`.
  Left on, the SDK tries to create Web Unlocker and SERP zones on startup. This
  repository never uses a zone, and zone creation fails on accounts without a
  payment method.

## How the API behaves

- Every SDK call is an asynchronous job: trigger, poll, return. Expect one to
  three minutes per account. There is no synchronous path in the SDK.
- Many URLs in one call is one job. Prefer that over a loop. For large runs use
  `posts_trigger`, `posts_status`, `posts_fetch` and keep the snapshot id.
- One credit per record. Comments cost one per comment; `reels_all` costs one
  per reel the account has ever posted. 5,000 credits are free each month.
- Reels discovery needs `timeout=420`; the 180-second default expires.
- `post_type` takes `"Post"` or `"Reels"`. The SDK docstring's `"Reel"` returns an
  error row and no reels.
- An empty date window comes back as an error row whose message contains
  "There are no public posts in the profile for the specified period". That is
  a success with zero records. Match the message, not `error_code`; a dead
  account uses the same code.
- The schema changes without notice. Never hardcode a field list.
- The full documentation index, one `.md` page per entry:
  https://docs.brightdata.com/llms.txt

## Working here

- `pytest` runs offline and needs no token. `ruff check .` must pass.
- CI installs from the README's own commands on an empty machine. A weekly
  workflow executes every fenced block in the README against the real API, and
  the same run also does a smaller live check.
  A snippet must be complete and paste-able on its own, and its shown output
  must be real.
- The field table in the README sits between `<!-- fields:start -->` and
  `<!-- fields:end -->` and is regenerated weekly. Do not edit it by hand.
- The "last verified" badge line at the top of the README is rewritten by the
  weekly run. Do not edit it by hand.
- Keep it small: 15 files and 450 lines of Python. Do not add retries,
  deduplication, scheduling, databases, async examples or concurrency.
