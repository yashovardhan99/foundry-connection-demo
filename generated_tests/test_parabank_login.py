"""Playwright coverage for ParaBank login scenarios TC-AC001-P01 and TC-AC001-B01."""
import logging
import re
from contextlib import contextmanager

import pytest
from playwright.sync_api import Browser, Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
LOGGER = logging.getLogger(__name__)


@contextmanager
def report_step(test_case: str, number: int, description: str):
    """Log an explicit pass/fail result for each business step."""
    label = f"{test_case} step {number}: {description}"
    LOGGER.info("START %s", label)
    try:
        yield
    except Exception:
        LOGGER.exception("FAIL %s", label)
        raise
    else:
        LOGGER.info("PASS %s", label)


def open_login_page(browser: Browser) -> tuple[object, Page]:
    """Create an isolated browser context that is always closed by the caller."""
    context = browser.new_context()
    page = context.new_page()
    return context, page


def assert_authenticated_dashboard(page: Page) -> None:
    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()


@pytest.mark.parametrize("username,password", [("john", "demo")])
def test_tc_ac001_p01_happy_path_login(browser: Browser, username: str, password: str) -> None:
    """TC-AC001-P01: authenticate with the documented valid ParaBank account."""
    context, page = open_login_page(browser)
    try:
        with report_step("TC-AC001-P01", 1, "open and verify the login page"):
            page.goto(BASE_URL, wait_until="domcontentloaded")
            expect(page.get_by_role("heading", name="Customer Login")).to_be_visible()
            expect(page.locator("input[name='username']")).to_be_visible()
            expect(page.locator("input[name='password']")).to_be_visible()
            expect(page.get_by_role("button", name="Log In")).to_be_visible()
        with report_step("TC-AC001-P01", 2, "enter username john"):
            page.locator("input[name='username']").fill(username)
            expect(page.locator("input[name='username']")).to_have_value(username)
        with report_step("TC-AC001-P01", 3, "enter a masked password"):
            password_input = page.locator("input[name='password']")
            expect(password_input).to_have_attribute("type", "password")
            password_input.fill(password)
            expect(password_input).to_have_value(password)
        with report_step("TC-AC001-P01", 4, "submit the login form"):
            page.get_by_role("button", name="Log In").click()
        with report_step("TC-AC001-P01", 5, "reach Account Overview instead of login"):
            assert_authenticated_dashboard(page)
        with report_step("TC-AC001-P01", 6, "verify the Log Out navigation link"):
            expect(page.get_by_role("link", name="Log Out")).to_be_visible()
        with report_step("TC-AC001-P01", 7, "verify a non-empty JSESSIONID session cookie"):
            jsessionid = [cookie for cookie in context.cookies() if cookie["name"] == "JSESSIONID"]
            assert jsessionid and jsessionid[0]["value"], "Expected a non-empty JSESSIONID cookie after login"
    finally:
        context.close()


def test_tc_ac001_b01_shortest_available_username_login(browser: Browser, record_property: pytest.RecordProperty) -> None:
    """TC-AC001-B01 fallback using the shortest credentials supplied to this test run."""
    # No one-character account and corresponding password were supplied. John (4 characters)
    # is the shortest available documented credential, so it is used per the scenario fallback.
    username, password = "john", "demo"
    record_property("boundary_username", username)
    record_property("boundary_username_length", len(username))
    record_property("boundary_deviation", "No one-character account credentials were provided; used shortest documented account john.")
    context, page = open_login_page(browser)
    try:
        with report_step("TC-AC001-B01", 1, "open the login page"):
            page.goto(BASE_URL, wait_until="domcontentloaded")
            expect(page.locator("input[name='username']")).to_be_visible()
            expect(page.locator("input[name='password']")).to_be_visible()
            expect(page.get_by_role("button", name="Log In")).to_be_visible()
        with report_step("TC-AC001-B01", 2, "enter the shortest available documented username"):
            assert len(username) == 4, "The supplied fallback username should be the documented four-character account"
            page.locator("input[name='username']").fill(username)
            expect(page.locator("input[name='username']")).to_have_value(username)
        with report_step("TC-AC001-B01", 3, "enter its corresponding documented password"):
            page.locator("input[name='password']").fill(password)
            expect(page.locator("input[name='password']")).to_have_value(password)
        with report_step("TC-AC001-B01", 4, "submit the login form"):
            page.get_by_role("button", name="Log In").click()
        with report_step("TC-AC001-B01", 5, "verify authentication, Account Overview, and session navigation"):
            assert_authenticated_dashboard(page)
    finally:
        context.close()
