"""Playwright coverage for ParaBank login acceptance cases.

Credentials are read only from the execution environment so this repository does
not store passwords. Configure PARABANK_USERNAME and PARABANK_PASSWORD for the
happy-path account, and PARABANK_MIN_USERNAME and PARABANK_MIN_PASSWORD for the
one-character account.
"""

import logging
import os
import re
from contextlib import contextmanager

import pytest
from playwright.sync_api import Browser, Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
OVERVIEW_URL = re.compile(r".*/overview\.htm(?:;[^?]*)?(?:\?.*)?$")
LOGGER = logging.getLogger(__name__)


@contextmanager
def report_step(test_case: str, step_number: int, description: str):
    """Log the result of every stated test step without logging credentials."""
    try:
        yield
    except Exception:
        LOGGER.exception("%s step %s FAILED: %s", test_case, step_number, description)
        raise
    else:
        LOGGER.info("%s step %s PASSED: %s", test_case, step_number, description)


def environment_value(variable_name: str) -> str:
    """Return a required runtime credential without exposing its value."""
    value = os.getenv(variable_name)
    assert value, (
        f"Missing required runtime configuration: {variable_name}. "
        "Provide it through the test environment; do not store credentials in the test file."
    )
    return value


def new_page(browser: Browser) -> tuple:
    """Create an isolated context; callers close it in finally blocks."""
    context = browser.new_context()
    return context, context.new_page()


def assert_login_page(page: Page) -> None:
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("input[type='submit'][value='Log In']")).to_be_visible()


def assert_authenticated_session(page: Page) -> None:
    expect(page).to_have_url(OVERVIEW_URL)
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()


def assert_jsessionid(page: Page) -> None:
    cookies = page.context.cookies()
    assert any(
        cookie["name"] == "JSESSIONID" and bool(cookie["value"])
        for cookie in cookies
    ), "Expected a JSESSIONID cookie with a non-empty value after authentication."


def test_tc_ac001_p01_happy_path_login(browser: Browser) -> None:
    """TC-AC001-P01: authenticate using the configured ParaBank happy-path account."""
    context, page = new_page(browser)
    try:
        with report_step("TC-AC001-P01", 1, "Open the login page and verify its controls"):
            page.goto(BASE_URL, wait_until="domcontentloaded")
            assert_login_page(page)

        with report_step("TC-AC001-P01", 2, "Enter the configured username"):
            username = environment_value("PARABANK_USERNAME")
            page.locator("input[name='username']").fill(username)

        with report_step("TC-AC001-P01", 3, "Enter the configured password and verify masking"):
            password = environment_value("PARABANK_PASSWORD")
            password_input = page.locator("input[name='password']")
            password_input.fill(password)
            expect(password_input).to_have_attribute("type", "password")

        with report_step("TC-AC001-P01", 4, "Submit the login form"):
            page.locator("input[type='submit'][value='Log In']").click()

        with report_step("TC-AC001-P01", 5, "Verify redirect to Account Overview"):
            expect(page).to_have_url(OVERVIEW_URL)

        with report_step("TC-AC001-P01", 6, "Verify the Log Out navigation link"):
            expect(page.get_by_role("link", name="Log Out")).to_be_visible()

        with report_step("TC-AC001-P01", 7, "Verify an authenticated JSESSIONID cookie"):
            assert_jsessionid(page)
    finally:
        context.close()


def test_tc_ac001_b01_minimum_length_username_login(browser: Browser) -> None:
    """TC-AC001-B01: authenticate with the configured one-character account."""
    context, page = new_page(browser)
    try:
        with report_step("TC-AC001-B01", 1, "Open the login page"):
            page.goto(BASE_URL, wait_until="domcontentloaded")
            assert_login_page(page)

        with report_step("TC-AC001-B01", 2, "Enter a one-character username"):
            username = environment_value("PARABANK_MIN_USERNAME")
            assert len(username) == 1, (
                "PARABANK_MIN_USERNAME must identify the precondition account with a "
                "one-character username."
            )
            page.locator("input[name='username']").fill(username)

        with report_step("TC-AC001-B01", 3, "Enter the corresponding password"):
            password = environment_value("PARABANK_MIN_PASSWORD")
            password_input = page.locator("input[name='password']")
            password_input.fill(password)
            expect(password_input).to_have_attribute("type", "password")

        with report_step("TC-AC001-B01", 4, "Submit the login form"):
            page.locator("input[type='submit'][value='Log In']").click()

        with report_step("TC-AC001-B01", 5, "Verify Account Overview and established session"):
            assert_authenticated_session(page)
    finally:
        context.close()
