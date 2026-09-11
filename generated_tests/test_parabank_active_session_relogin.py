import re

from playwright.sync_api import Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
USERNAME = "john"
PASSWORD = "demo"


def log_in(page: Page) -> None:
    page.goto(BASE_URL)
    page.locator('input[name="username"]').fill(USERNAME)
    page.locator('input[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Log In").click()
    expect(page).to_have_url(re.compile(r".*/parabank/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()


def test_tc_ac001_e02_relogin_with_active_session(page: Page) -> None:
    """Verify an active ParaBank session remains usable when revisiting login in a new tab."""
    log_in(page)

    second_tab = page.context.new_page()
    try:
        second_tab.goto(BASE_URL)

        # The application may either retain the login form or redirect this tab to the overview.
        if second_tab.locator('input[name="username"]').is_visible():
            second_tab.locator('input[name="username"]').fill(USERNAME)
            second_tab.locator('input[name="password"]').fill(PASSWORD)
            second_tab.get_by_role("button", name="Log In").click()

        expect(second_tab).to_have_url(re.compile(r".*/parabank/overview\.htm.*"))
        expect(second_tab.get_by_role("heading", name="Accounts Overview")).to_be_visible()
        expect(second_tab.get_by_role("link", name="Log Out")).to_be_visible()
    finally:
        second_tab.close()
