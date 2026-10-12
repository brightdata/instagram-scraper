[![Scrape Instagram data with the Instagram Scraper API: profiles, posts, reels, search. Collect or discover by URL and username. Start free.](.github/banner.png)](https://brightdata.com/products/web-scraper/instagram?utm_source=github)

# instagram-scraper-python

[![Live check](https://github.com/brightdata/instagram-scraper-python/actions/workflows/live.yml/badge.svg)](https://github.com/brightdata/instagram-scraper-python/actions/workflows/live.yml)
[![last verified](https://img.shields.io/badge/last%20verified-12%20Oct%202026-brightgreen)](https://github.com/brightdata/instagram-scraper-python/actions/workflows/live.yml) <!-- verified: rewritten by the daily run -->

[Quickstart](#quickstart) · [Command](#or-run-it-as-a-command) · [Endpoints](#the-rest-of-the-api) · [Data](#the-data) · [Errors](#when-it-fails) · [Coding agents](#coding-agents) · [Docs](https://docs.brightdata.com/products/scrapers/instagram/introduction) · [Support](#support)

Instagram profiles, posts, reels and comments as JSON, in Python. No Instagram
login, no browser. Built on the
[Bright Data Instagram Scraper API](https://brightdata.com/products/web-scraper/instagram?utm_source=github).

Uses the [Bright Data Python SDK](https://github.com/brightdata/sdk-python).
Full API docs:
[Instagram Scraper API](https://docs.brightdata.com/products/scrapers/instagram/introduction).

Also here: a one-command CLI for posts, and the
[Bright Data CLI](#coding-agents), which needs no Python at all.

## Quickstart

Python 3.10 or newer.

```bash
pip install brightdata-sdk
export BRIGHTDATA_API_TOKEN=YOUR_API_KEY
```

Get a token from the
[Bright Data control panel](https://brightdata.com/cp/setting/users). A `.env`
file in the project root works too, as long as the virtualenv is inside the
project.

Or skip the token. Run `npx -p @brightdata/cli bdata login` once: it opens a
browser, and from then on the SDK finds the stored credentials on its own, for
you and for any coding agent working in that terminal. Agents cannot click
through the login, so do it yourself first. The same CLI scrapes Instagram
directly; see [Coding agents](#coding-agents).

No account yet? [Create one](https://brightdata.com/cp/start); new accounts get
[5,000 free credits a month](https://docs.brightdata.com/general/account/billing-and-pricing/free-tier).

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    result = client.search.instagram.posts("https://www.instagram.com/nasa/", num_of_posts=5)
    for post in result.data:
        print(post["likes"], post["num_comments"], post["url"])
```

```
2437761 4692 https://www.instagram.com/p/Db9IVmrDvQ4/
104278 902 https://www.instagram.com/reel/DcMXl1IPNtB/
553843 4101 https://www.instagram.com/p/DcOX3hWFiey/
39490 324 https://www.instagram.com/reel/Dc4u1yKPj_s/
119582 1535 https://www.instagram.com/reel/Dc37MPNSAZq/
```

Expect one to three minutes: the API runs a job and the SDK waits for it. One
[credit](https://brightdata.com/pricing/web-scraper) per post.

Pass `auto_create_zones=False` every time. Left on, the SDK creates zones on
startup for Web Unlocker and SERP, two other Bright Data products this scraper
never touches, and zone creation fails on accounts without a payment method
([sdk-python#57](https://github.com/brightdata/sdk-python/issues/57)).

## Or run it as a command

The command in this repo does the same for several accounts and writes one
JSON file.

```bash
pip install git+https://github.com/brightdata/instagram-scraper-python
instagram-scraper nasa natgeo
```

```
Fetching up to 5 recent posts per account, for: nasa, natgeo
Usually one to three minutes each. One credit per post, 5,000 free per month.
asking  @nasa...
got     @nasa: 5 posts
asking  @natgeo...
got     @natgeo: 5 posts

Saved 10 posts as JSON to instagram.json (34 fields per post)
```

In a terminal the `asking` lines are replaced by this, updating in place, so
you can see it is working and how long it has been going:

```
⠹ @nasa 0:01:47
```

```
--limit N    posts per account, default 5, minimum 1
--out PATH   output file, default instagram.json
```

`python -m instagram_scraper` works too.

Import it instead of running it, for `ok`, `note` and `error` per account
instead of raw rows. `scrape` never raises for one bad account; check `ok`
before reading `posts`:

```python
from instagram_scraper import scrape

for outcome in scrape(["nasa", "zz_not_a_real_account_zz"], limit=1):
    if outcome.ok:
        print(f"{outcome.handle}: {len(outcome.posts)} posts")
    else:
        print(f"{outcome.handle} failed: {outcome.error}")
```

```
nasa: 1 posts
zz_not_a_real_account_zz failed: Crawler error: Cannot read properties of null (reading 'pk')
```

An account with nothing recent is a success with no posts. The reason lands in
`note`, not `error`.

## The rest of the API

The command covers one endpoint. The SDK has eight, documented in the
[Instagram Scraper API docs](https://docs.brightdata.com/products/scrapers/instagram/introduction).
Every snippet below is complete
and needs only `brightdata-sdk`: paste it as is. Every one of them runs in Actions each Monday, a smaller check
runs every other day, and the badge at the top is the latest result.

| you have | want | call |
| --- | --- | --- |
| a profile URL | recent posts | `client.search.instagram.posts(url, num_of_posts=5)` |
| a username | the profile | `client.search.instagram.profiles("nasa")` |
| a profile URL | the profile | `client.scrape.instagram.profiles(url)` |
| a profile URL | recent reels | `client.search.instagram.reels(url, num_of_posts=5, timeout=420)` |
| a profile URL | every reel ever | `client.search.instagram.reels_all(url)`, one credit per reel the account has posted |
| post URLs | those posts | `client.scrape.instagram.posts([url, url])` |
| reel URLs | those reels | `client.scrape.instagram.reels([url])` |
| a post or reel URL | its comments | `client.scrape.instagram.comments(url)`, one credit per comment |

Every one of these is an asynchronous job. The SDK triggers it, polls, and
returns when it is ready. That is why a call takes one to three minutes, and
why there is no faster path in Python. The API's
[synchronous endpoint](https://docs.brightdata.com/api-reference/scrapers/synchronous-requests),
20 URLs and a one-minute limit, is raw HTTP only.

Error rows, like the empty-window one above, appear because the SDK asks for
them with `include_errors=true`. The API default is off.

`search` calls return a list in `result.data`. `scrape` calls with one URL
return one record as a dict, and several as a list.

### Two accounts, one job

A list of URLs is one job, not one per account.

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    result = client.search.instagram.posts(
        ["https://www.instagram.com/nasa/", "https://www.instagram.com/natgeo/"], num_of_posts=1
    )
    for post in result.data:
        print(post["user_posted"], post["url"])
```

```
nasa https://www.instagram.com/p/DcOX3hWFiey/
natgeo https://www.instagram.com/reel/Dbru79IAdH-/
```

### Trigger now, fetch later

For anything bigger than a few accounts, do not block a process for an hour.
Trigger, keep the snapshot id, fetch when ready. Snapshots stay downloadable
for 30 days.

```python
import time

from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    job = client.scrape.instagram.posts_trigger("https://www.instagram.com/p/Dc1W1uFj-CW/")
    print("snapshot:", job.snapshot_id)
    while (status := client.scrape.instagram.posts_status(job.snapshot_id)) not in ("ready", "failed"):
        time.sleep(5)
    print("status:", status)
    record = client.scrape.instagram.posts_fetch(job.snapshot_id)[0]
    print("fetched:", record["url"], "likes:", record["likes"])
```

```
snapshot: sd_mtrapflrzynbfyid9
status: ready
fetched: https://www.instagram.com/p/Dc1W1uFj-CW/ likes: 184
```

### A date window

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    result = client.search.instagram.posts(
        "https://www.instagram.com/nasa/",
        num_of_posts=3,
        start_date="08-01-2026",   # MM-DD-YYYY
        end_date="09-07-2026",
    )
    for post in result.data:
        print(post["date_posted"], post["content_type"], post["url"])
```

```
2026-08-12T21:28:58.000Z Image https://www.instagram.com/p/Db9IVmrDvQ4/
2026-08-18T19:37:40.000Z Reel https://www.instagram.com/reel/DcMXl1IPNtB/
2026-08-19T14:11:47.000Z Image https://www.instagram.com/p/DcOX3hWFiey/
```

`post_type="Post"` keeps posts only and `post_type="Reels"` keeps reels only,
both verified. The SDK's docstring says `"Reel"`; that spelling returns an
error row and no reels ([sdk-python#59](https://github.com/brightdata/sdk-python/issues/59)).
`posts_to_not_include` takes a list of post IDs.

### A profile, by username, no URL

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    profile = client.search.instagram.profiles("nasa").data[0]
    print(profile["account"], "followers:", profile["followers"], "posts:", profile["posts_count"])
```

```
nasa followers: 104387874 posts: 4913
```

### Comments on a post

One credit per comment, so check `num_comments` on the post first.

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    comments = client.scrape.instagram.comments("https://www.instagram.com/p/Dc1W1uFj-CW/").data
    print(len(comments), "comments; first:", repr(comments[0]["comment"][:60]))
```

```
6 comments; first: 'Those two destroyed jazz'
```

### Recent reels

Reels discovery is slower. The default 180-second timeout expired; 420 did not.

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient(auto_create_zones=False) as client:
    reels = client.search.instagram.reels("https://www.instagram.com/nasa/", num_of_posts=2, timeout=420)
    for reel in reels.data:
        print(reel["date_posted"], reel["url"])
```

```
2026-08-18T19:37:40.000Z https://www.instagram.com/p/DcMXl1IPNtB/
2026-09-05T01:00:10.000Z https://www.instagram.com/p/Dc4u1yKPj_s/
```

## The data

The fields most people want:

```
url  date_posted  description  hashtags  likes  num_comments  user_posted
```

The code hardcodes no field list. Whatever the API returns lands in
`result.data`, and in the command's file.
A collaborative post carries the co-author's handle in `user_posted`, so a post
fetched from nasa can say `nasajohnson`; `coauthor_producers` lists everyone.

<!-- fields:start -->
<details>
<summary>All 44 fields, with type and description</summary>

Regenerated every day from the dataset schema, via
`client.datasets.instagram_posts.get_metadata()`, so it cannot go stale. A
post carries the fields that apply to it; the sample file has 34
of these 44.

| field | type | description |
| --- | --- | --- |
| `url` | url | The direct URL of the Instagram post |
| `user_posted` | text | Username of the post creator |
| `description` | text | Post text description |
| `hashtags` | array | Hashtags used in the post |
| `num_comments` | number | Number of comments |
| `date_posted` | date | Post publication date |
| `likes` | number | Number of likes on the post |
| `photos` | array | URLs of attached photos, URLs can be expired due to Instagram policy |
| `videos` | array | URLs of attached videos, URLs can be expired due to Instagram policy |
| `location` | array | Geographical location associated with the post |
| `location_details` | object | Detailed geographical location metadata as returned by Instagram |
| `latest_comments` | array | Recent comments on the post |
| `post_id` | text | Unique post identifier |
| `discovery_input` | object | Discovery input values used to trigger the collection |
| `has_handshake` | boolean | Indicates if the post has a handshake (collaborative agreement between accounts) |
| `display_url` | text | Deprecated: previously used as the display URL of the post media |
| `shortcode` | text | The shortcode of the Instagram post, used in the post URL path |
| `content_type` | text | The type of content: Posts or Reels |
| `pk` | text | The primary key of the media content as assigned by Instagram |
| `content_id` | text | The content ID of the media item |
| `engagement_score_view` | number | Video view count used as an engagement score metric |
| `thumbnail` | text | The URL of the post's display image or video thumbnail |
| `video_view_count` | text | The number of views on the video post |
| `product_type` | text | The type of product associated with the post, such as 'clips' for Reels |
| `coauthor_producers` | array | List of co-authors or producers who collaborated on the post |
| `tagged_users` | array | List of users tagged in the post |
| `video_play_count` | number | The number of times the video has been played |
| `followers` | number | Number of followers the post owner has at the time of collection |
| `posts_count` | number | The total count of posts made by the account at the time of collection |
| `profile_image_link` | text | URL linking directly to the Instagram profile image of the post owner |
| `is_verified` | boolean | Indicates whether the post owner's account is verified |
| `is_paid_partnership` | boolean | Indicates whether the post is a sponsored or paid partnership |
| `partnership_details` | object | Details of the paid partnership brand associated with the post |
| `user_posted_id` | text | The Instagram user ID of the account that posted the post |
| `post_content` | array | List of media items (photos or videos) attached to the post, including carousel items |
| `audio` | object | Audio track metadata associated with the post or Reel |
| `profile_url` | url | URL of the Instagram profile that posted the post |
| `videos_duration` | array | List of video durations for each video attached to the post |
| `images` | array | List of image objects attached to the post |
| `alt_text` | text | Accessibility alt text for the post's main image: descriptive text that conveys the meaning of the image for blind or visually impaired users |
| `photos_number` | number | Total number of photos attached to the post |
| `audio_url` | url | Direct URL of the audio track used in the post |
| `thumbnail_array` | array | Deprecated: array of thumbnail URLs for the post media |
| `country` | text | Some profiles are restricted by location. Please set the country code in Alpha-2 format |

</details>
<!-- fields:end -->

<details>
<summary>The start of a real output file, from <code>instagram-scraper nasa --limit 1</code></summary>

```json
{
  "generated_at": "2026-08-14T11:01:05.410349+00:00",
  "handles": [
    {
      "handle": "nasa",
      "posts": [
        {
          "url": "https://www.instagram.com/p/Db_SePSltfz/",
          "user_posted": "nasa",
          "description": "A dance of darkness and light\n\nThis composite image shows the total solar eclipse from beginning to end, as seen in San Mill\u00e1n de los Caballeros, Spain on Aug. 12, 2026.\n\nWhile eclipses are beautiful and magical to experience, they're also a great opportunity for science. Total solar eclipses are particularly important because they allow scientists to see a part of the Sun\u2019s atmosphere known as the corona. The corona is too faint to see except when the bright light of the Sun is blocked.\n\nStudying the corona is key to answering important questions about how heat and energy are transferred from the Sun out into the solar wind, the constant stream of particles that the Sun spews into the solar system.\n\nCredit: NASA\n\n#NASA #Sun #SolarEclipse #Moon",
          "hashtags": [
            "#NASA",
            "#Sun",
            "#SolarEclipse",
            "#Moon"
          ],
          "num_comments": 1109,
          "date_posted": "2026-08-13T17:36:02.000Z",
          "likes": 627573,
          "photos": [
  ...
```

The whole file, one post with every field, is
[examples/sample_output.json](examples/sample_output.json).

</details>

## When it fails

| you see | what it means |
| --- | --- |
| `API token required but not found.` | Exit 2, before any request. Set the token. |
| `failed  @name: ...` | Exit 1. No such account, usually a typo. The wording varies: "Sorry, this page isn't available." and "Crawler error: Cannot read properties of null" are both this. |
| `got     @name: 0 posts, the account has no public posts in the period searched` | Exit 0, and correct. The API reports an empty window as an error row. |
| `failed  @name: timeout` | Exit 1. A request gives up after 180 seconds. Run it again. |

Any failure exits 1, so a run is safe to gate a script on.

From the SDK, the same conditions look like this:

| you see | what it means |
| --- | --- |
| `AuthenticationError: Unauthorized (401)` | The token is set but wrong. |
| `result.success` is `False`, `result.status` is `"timeout"` | The SDK gave up waiting, 180 seconds by default. Pass `timeout=420`, or run it again. |
| a row in `result.data` with an `error` key | The API's answer for one input: an empty window, or no such account. The other rows are fine. |

## Coding agents

No Python, nothing installed. Paste both lines; the first opens a browser
once, or use `bdata login --device` over SSH and in CI:

```bash
npx -p @brightdata/cli bdata login
npx -p @brightdata/cli bdata pipelines instagram_posts "https://www.instagram.com/p/Db_SePSltfz/"
```

The CLI's four Instagram pipelines each take a post, reel or profile URL and
return that one record. Recent posts from a profile is the SDK call in the
Quickstart; the CLI has no route for it.

`npx skills add brightdata/skills` teaches Claude Code, Cursor and Codex these
commands and the docs, so plain language works afterwards. Full guide:
[Bright Data for your coding agent](https://docs.brightdata.com/quickstart-coding-agent).

No terminal, for a hosted assistant? The
[Bright Data MCP server](https://github.com/brightdata/brightdata-mcp#which-tool-to-use)
has the same four Instagram tools, one URL each, in its `social` group, which
is off unless you ask for it:

    https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN&groups=social

An agent can also open the account itself, no signup form:
[agent registration](https://brightdata.com/auth.md). Everything else Bright
Data connects to, from LangChain to Zapier and n8n:
[integrations](https://docs.brightdata.com/integrations/introduction).

<details>
<summary>Every Instagram command the CLI has, each run today</summary>

Four types: `instagram_profiles`, `instagram_posts`, `instagram_reels`,
`instagram_comments`. Each takes URLs, prints JSON, and costs one credit per
record. Prefix each command with `npx -p @brightdata/cli`, or install once with
`npm i -g @brightdata/cli`.

```bash
bdata pipelines instagram_profiles "https://www.instagram.com/nasa/" --pretty
```

1 record, 25 fields, 50 seconds. `"account": "nasa"`, `"followers": 104396028`.

```bash
bdata pipelines instagram_posts "https://www.instagram.com/p/Dc1W1uFj-CW/" --format csv -o posts.csv
```

```
Triggered collection with snapshot ID:sd_mtrcu6qpyebqgtcjg
Output written to posts.csv
```

37 seconds. The CSV header carries the same field names as the table below.

```bash
bdata pipelines instagram_reels "https://www.instagram.com/reel/DcMXl1IPNtB/" --pretty
```

1 record, 25 fields, 23 seconds.

```bash
bdata pipelines instagram_comments "https://www.instagram.com/p/Dc1W1uFj-CW/" --pretty
```

5 records, 11 fields, 9 seconds. One credit per comment, so check the post's
`num_comments` first.

`bdata pipelines list` prints every type. `bdata pipelines --help` shows
`--format json|csv|ndjson|jsonl`, `-o FILE` and `--timeout`.

</details>

## Support

Bugs in this repo:
[open an issue](https://github.com/brightdata/instagram-scraper-python/issues), and
[CONTRIBUTING.md](CONTRIBUTING.md) says what to put in it.
Anything about the API, your account or your credits:
[Bright Data support](https://brightdata.zendesk.com/hc/en-us/requests/new).

## License

MIT.
