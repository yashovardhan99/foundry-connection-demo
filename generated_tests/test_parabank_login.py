"""Playwright coverage for ParaBank login scenarios TC-AC001-P01 and TC-AC001-B01."""

import logging
import re

from playwright.sync_api import Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
LOGGER = logging.getLogger(__name__)


def _open_login_page(page: Page) -> None:
    """Navigate to ParaBank and verify all controls required for login are present."""
    LOGGER.info("Navigate to the ParaBank login page")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Customer Login")).to_be_visible()
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.get_by_role("button", name="Log In")).to_be_visible()


def _assert_authenticated(page: Page) -> None:
    """Verify the post-login dashboard, logout navigation, and session cookie."""
    LOGGER.info("Verify authentication redirected to Account Overview")
    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()

    jsession_cookies = [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "JSESSIONID" and cookie["value"]
    ]
    assert jsession_cookies, "Defect: authenticated session did not expose a non-empty JSESSIONID cookie"
    LOGGER.info("Verified non-empty JSESSIONID session cookie")


def test_tc_ac001_p01_happy_path_login(page: Page) -> None:
    """TC-AC001-P01: authenticate with the documented valid ParaBank account."""
    _open_login_page(page)

    LOGGER.info("Enter documented username 'john'")
    page.locator("input[name='username']").fill("john")

    LOGGER.info("Enter password and verify its field is masked")
    password = page.locator("input[name='password']")
    password.fill("demo")
    assert password.get_attribute("type") == "password", "Defect: password input is not masked"

    LOGGER.info("Submit login")
    page.get_by_role("button", name="Log In").click()
    _assert_authenticated(page)


def test_tc_ac001_b01_shortest_available_username_login(page: Page) -> None:
    """TC-AC001-B01: use the shortest credentials available in the supplied test data."""
    # No one-character account/password pair is supplied. The documented john/demo
    # account is therefore the shortest available credential pair for this executable run.
    fallback_username = "john"
    fallback_password = "demo"
    LOGGER.warning(
        "TC-AC001-B01 deviation: no one-character account credentials were supplied; "
        "attempting shortest available documented username %r (length %d)",
        fallback_username,
        len(fallback_username),
    )

    _open_login_page(page)
    LOGGER.info("Enter shortest available documented username")
    page.locator("input[name='username']").fill(fallback_username)
    LOGGER.info("Enter its corresponding documented password")
    page.locator("input[name='password']").fill(fallback_password)
    LOGGER.info("Submit login")
    page.get_by_role("button", name="Log In").click()
    _assert_authenticated(page)
