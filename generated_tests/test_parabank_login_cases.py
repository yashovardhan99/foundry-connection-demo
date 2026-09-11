"""Playwright coverage for ParaBank login cases TC-AC001-P01 and TC-AC001-B01."""

import logging
import re

import pytest
from playwright.sync_api import Browser, Page, expect


LOGGER = logging.getLogger(__name__)
LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"
HAPPY_PATH_USERNAME = "john"
HAPPY_PATH_PASSWORD = "demo"

# Issue #6 confirms that no provisioned one-character account is available. These
# are the shortest known working credentials and are used only to perform the
# required fallback login attempt for TC-AC001-B01.
SHORTEST_KNOWN_USERNAME = "john"
SHORTEST_KNOWN_PASSWORD = "demo"


def _new_page(browser: Browser):
    """Create an isolated browser context that is closed by each test."""
    context = browser.new_context()
    return context, context.new_page()


def _verify_login_form(page: Page) -> None:
    """Verify the observed ParaBank login controls are present."""
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()
    expect(page.locator('input[type="submit"][value="Log In"]')).to_be_visible()


def _log_in(page: Page, username: str, password: str) -> None:
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.locator('input[type="submit"][value="Log In"]').click()


def _verify_authenticated(page: Page) -> None:
    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()


def test_tc_ac001_p01_happy_path_login(browser: Browser) -> None:
    """TC-AC001-P01: authenticate with the documented valid credentials."""
    context, page = _new_page(browser)
    try:
        LOGGER.info("TC-AC001-P01 step 1: navigate to the login page and verify its controls")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        _verify_login_form(page)

        LOGGER.info("TC-AC001-P01 steps 2-3: enter the documented credentials and verify masking")
        page.locator('input[name="username"]').fill(HAPPY_PATH_USERNAME)
        password = page.locator('input[name="password"]')
        password.fill(HAPPY_PATH_PASSWORD)
        assert password.get_attribute("type") == "password"

        LOGGER.info("TC-AC001-P01 steps 4-6: submit and verify Account Overview and Log Out")
        page.locator('input[type="submit"][value="Log In"]').click()
        _verify_authenticated(page)

        LOGGER.info("TC-AC001-P01 step 7: verify a non-empty JSESSIONID cookie")
        jsession_cookies = [
            cookie for cookie in context.cookies() if cookie["name"] == "JSESSIONID"
        ]
        assert jsession_cookies, "Expected a JSESSIONID cookie after successful login"
        assert jsession_cookies[0]["value"], "Expected JSESSIONID to have a non-empty value"
    finally:
        context.close()


def test_tc_ac001_b01_shortest_known_available_username_login(browser: Browser) -> None:
    """TC-AC001-B01: attempt the documented fallback when no one-character account exists."""
    context, page = _new_page(browser)
    try:
        LOGGER.info("TC-AC001-B01 step 1: navigate to the login page")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        _verify_login_form(page)

        LOGGER.warning(
            "TC-AC001-B01 defect/limitation: no one-character ParaBank account "
            "credentials are available (repository issue #6). Attempting the shortest "
            "known available username, %r, which has length %d.",
            SHORTEST_KNOWN_USERNAME,
            len(SHORTEST_KNOWN_USERNAME),
        )
        LOGGER.info("TC-AC001-B01 steps 2-4: attempt login with the shortest known credentials")
        _log_in(page, SHORTEST_KNOWN_USERNAME, SHORTEST_KNOWN_PASSWORD)

        LOGGER.info("TC-AC001-B01 step 5: verify the fallback account is authenticated")
        _verify_authenticated(page)

        pytest.fail(
            "TC-AC001-B01 cannot pass as the minimum-length boundary: the attempted "
            f"username {SHORTEST_KNOWN_USERNAME!r} has length "
            f"{len(SHORTEST_KNOWN_USERNAME)}, not the required length of 1. "
            "A provisioned one-character account and corresponding password are required."
        )
    finally:
        context.close()
