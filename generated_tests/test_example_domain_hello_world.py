"""Playwright smoke test for the Example Domain sample page."""

import re

from playwright.sync_api import Page, expect


def test_example_domain_displays_hello_world_sample(page: Page) -> None:
    """Verify the selected sample page loads and presents its primary message."""
    page.goto("https://example.com/", wait_until="domcontentloaded")

    expect(page).to_have_url(re.compile(r"^https://example\.com/?$"))
    expect(page.locator("h1")).to_have_text("Example Domain")
    expect(page.get_by_text("This domain is for use in documentation examples", exact=False)).to_be_visible()
