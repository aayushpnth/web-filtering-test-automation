"""
Browser driver: navigate to a URL, decide allowed vs blocked, capture a screenshot.

Uses Playwright. Install browsers once with:  playwright install chromium

"Blocked" is inferred from a navigation error (connection reset / timeout, the
common signature of a silent drop) or from block-page indicators in the page
content. Tune BLOCK_PAGE_MARKERS for your environment. No vendor hosts or
credentials appear here.
"""
from __future__ import annotations
import os
from dataclasses import dataclass

# Generic block-page text markers. Extend for the products you test.
BLOCK_PAGE_MARKERS = (
    "access denied", "blocked", "web page blocked", "request blocked",
    "this site is blocked", "security policy", "content blocked",
)


@dataclass
class VisitResult:
    url: str
    loaded: bool            # page rendered normally (treated as "allowed")
    blocked: bool           # navigation failed or a block page was shown
    screenshot_path: str
    detail: str             # short note (error type or marker matched)


def visit(url: str, screenshot_dir: str, headless: bool = True, timeout_s: int = 30) -> VisitResult:
    """Visit a single URL and classify the outcome. Import Playwright lazily."""
    from playwright.sync_api import sync_playwright, Error as PWError

    os.makedirs(screenshot_dir, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in url)[:120]
    shot = os.path.join(screenshot_dir, f"{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            resp = page.goto(url, timeout=timeout_s * 1000, wait_until="domcontentloaded")
            body = (page.content() or "").lower()
            page.screenshot(path=shot)
            marker = next((m for m in BLOCK_PAGE_MARKERS if m in body), "")
            if marker:
                return VisitResult(url, loaded=False, blocked=True, screenshot_path=shot,
                                   detail=f"block page marker: {marker}")
            status = resp.status if resp else 0
            return VisitResult(url, loaded=True, blocked=False, screenshot_path=shot,
                               detail=f"http {status}")
        except PWError as e:
            # Connection reset / timeout / DNS failure: typical of a silent drop.
            try:
                page.screenshot(path=shot)
            except Exception:
                shot = ""
            return VisitResult(url, loaded=False, blocked=True, screenshot_path=shot,
                               detail=f"nav error: {type(e).__name__}")
        finally:
            browser.close()
