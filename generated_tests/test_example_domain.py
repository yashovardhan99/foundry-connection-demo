"""Generated Playwright smoke test for a simple sample HTML page."""

from playwright.sync_api import expect, sync_playwright


def test_example_domain_renders_sample_heading() -> None:
    """Verify the sample page renders its primary heading."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto("https://example.com", wait_until="domcontentloaded")

            expect(page.locator("h1")).to_have_text("Example Domain")
        finally:
            browser.close()
