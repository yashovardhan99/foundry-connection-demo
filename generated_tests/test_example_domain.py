"""Smoke test for the public Example Domain sample page."""

from playwright.sync_api import Page, expect


SAMPLE_URL = "https://example.com/"


def test_example_domain_page_displays_sample_content(page: Page) -> None:
    """Verify that the simple public sample page loads its primary content."""
    page.goto(SAMPLE_URL, wait_until="domcontentloaded")

    expect(page).to_have_title("Example Domain")
    expect(page.get_by_role("heading", name="Example Domain")).to_be_visible()
    expect(page.locator("body")).to_contain_text(
        "This domain is for use in documentation examples"
    )
