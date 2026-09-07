"""Generated Playwright smoke test for a simple sample HTML page."""

from playwright.sync_api import Browser, expect


def test_example_domain_displays_hello_world_equivalent(browser: Browser) -> None:
    """Verify a simple public sample page renders its primary greeting heading."""
    page = browser.new_page()
    try:
        page.goto("https://example.com", wait_until="domcontentloaded")
        expect(page).to_have_title("Example Domain")
        expect(page.get_by_role("heading", name="Example Domain")).to_be_visible()
    finally:
        page.close()
