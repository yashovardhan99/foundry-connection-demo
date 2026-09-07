import re

from playwright.sync_api import Browser, expect


def test_hello_world_sample_page(browser: Browser) -> None:
    """Verify a minimal sample HTML page renders its greeting."""
    context = browser.new_context()
    page = context.new_page()
    try:
        page.set_content("<main><h1>Hello, world!</h1></main>")

        expect(page.locator("h1")).to_have_text("Hello, world!")
        expect(page).to_have_url(re.compile(r"about:blank"))
    finally:
        context.close()
