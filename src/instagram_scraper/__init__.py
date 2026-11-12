"""An Instagram scraper on Bright Data's Scraper API."""

from .scrape import Outcome, rows, scrape, scrape_handle, write

__all__ = ["Outcome", "rows", "scrape", "scrape_handle", "write"]
__version__ = "0.1.1"
