"""Get a creator's recent Instagram posts by handle.

    handle -> search.instagram.posts -> full post records

No second collection step. Discovery returns the complete record: 34 fields on
2026-08-14, against 33 from collecting the same post afterwards. The extra call
cost a record per post, added 75 seconds, and dropped every reel.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from brightdata import SyncBrightDataClient

#: An empty date window comes back as an error row, not an empty list. Match on
#: the message: a dead page carries the same error_code.
EMPTY_WINDOW = "There are no public posts in the profile for the specified period"

_HANDLE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def clean_handle(handle: str) -> str:
    """Accept nasa, @nasa, or a profile URL. Reject anything else.

    A URL counts only when its host is instagram.com or a subdomain of it, so
    https://evil.com/instagram.com/nasa is rejected rather than read as nasa.
    """
    cleaned = (handle or "").strip().lstrip("@")
    if "/" in cleaned:
        url = urlsplit(cleaned if "://" in cleaned else f"https://{cleaned}")
        host = (url.hostname or "").lower()
        if host != "instagram.com" and not host.endswith(".instagram.com"):
            raise ValueError(f"{handle!r} is not an Instagram handle")
        segments = [part for part in url.path.split("/") if part]
        cleaned = segments[0] if segments else ""
    if not _HANDLE.match(cleaned):
        raise ValueError(f"{handle!r} is not an Instagram handle")
    return cleaned


def profile_url(handle: str) -> str:
    return f"https://www.instagram.com/{clean_handle(handle)}/"


def rows(result: Any) -> list[dict[str, Any]]:
    """Flatten a ScrapeResult, or a list of them, into plain dicts."""
    if isinstance(result, list):
        return [row for item in result for row in rows(item)]
    data = getattr(result, "data", result)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def envelope_error(result: Any) -> str | None:
    """A failed or timed out request carries no rows to explain itself.

    Without this check the run prints "0 posts", which reads like a creator with
    nothing recent rather than a request that never came back.
    """
    if getattr(result, "success", True):
        return None
    return str(getattr(result, "error", None) or getattr(result, "status", "request failed"))


def split(result: Any) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Sort rows into records, empty-window notes, and real errors."""
    records: list[dict[str, Any]] = []
    notes: list[str] = []
    errors: list[str] = []
    for row in rows(result):
        error = row.get("error")
        if not error:
            records.append(row)
        elif EMPTY_WINDOW in str(error):
            notes.append("the account has no public posts in the period searched")
        else:
            errors.append(str(error))
    return records, notes, errors


@dataclass
class Outcome:
    """What happened to one handle."""

    handle: str
    posts: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.error is None

    def line(self) -> str:
        """One line a reader can understand without having read the source."""
        if not self.ok:
            return f"failed  @{self.handle}: {self.error}"
        tail = f", {self.note}" if self.note else ""
        return f"got     @{self.handle}: {len(self.posts)} posts{tail}"


def scrape_handle(client: Any, handle: str, limit: int = 5) -> Outcome:
    """Fetch one handle. Never raises: a failure becomes an Outcome."""
    try:
        name = clean_handle(handle)
    except ValueError as exc:
        return Outcome(handle=str(handle), error=str(exc))

    outcome = Outcome(handle=name)
    try:
        result = client.search.instagram.posts(profile_url(name), num_of_posts=limit)
        failed = envelope_error(result)
        if failed:
            outcome.error = failed
            return outcome
        found, notes, errors = split(result)
        outcome.note = "; ".join(dict.fromkeys(notes))
        if errors:
            outcome.error = "; ".join(errors)
        else:
            outcome.posts = found
    except Exception as exc:  # one bad handle must not end the run
        outcome.error = f"{type(exc).__name__}: {exc}"
    return outcome


def client_context(client: Any = None) -> Any:
    """The client passed in, or one we open and own.

    SyncBrightDataClient builds its event loop in __enter__, so it must be
    entered. An unentered client fails with an AttributeError about
    run_until_complete. Callers wanting progress hold this open and drive
    scrape_handle themselves, as the CLI does.
    """
    # auto_create_zones defaults to True: the SDK tries to create a Web Unlocker
    # zone on startup, which this scraper never uses. Creating a zone needs a
    # payment method, so leaving it on breaks the first run for free accounts.
    return nullcontext(client) if client is not None else SyncBrightDataClient(
        auto_create_zones=False
    )


def scrape(handles: Iterable[str], limit: int = 5, client: Any = None) -> list[Outcome]:
    """Run every handle and return one Outcome each, in order."""
    with client_context(client) as opened:
        return [scrape_handle(opened, handle, limit) for handle in handles]


def write(outcomes: list[Outcome], path: str | Path) -> Path:
    """Write one JSON file: when it ran, and the posts found per handle."""
    document = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "handles": [{"handle": o.handle, "posts": o.posts} for o in outcomes],
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return target
