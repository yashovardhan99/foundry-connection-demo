"""ParaBank authentication scenarios generated from TC-AC001-P01 and TC-AC001-B01."""

import logging
import re

import pytest
from playwright.sync_api import Browser, Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
KNOWN_USERNAME = "john"
KNOWN_PASSWORD = "demo"
# No credentials for a one-character account were supplied. John is the shortest
# documented available username, so this is the requested fallback for TC-AC001-B01.
SHORTEST_KNOWN_AVAILABLE_USERNAME = KNOWN_USERNAME
SHORTEST_KNOWN_AVAILABLE_PASSWORD = KNOWN_PASSWORD

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def isolated_page(browser: Browser) -> Page:
    """Provide a per-scenario context and close it even if an assertion fails."""
    context = browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


def _report_step(case_id: str, step: int, outcome: str) -> None:
    """Emit a per-step pass record; assertion failures remain pytest defect output."""
    LOGGER.info("%s step %s PASS: %s", case_id, step, outcome)


def _login(page: Page, username: str, password: str) -> None:
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.get_by_role("button", name="Log In").click()


def test_tc_ac001_p01_happy_path_login(isolated_page: Page) -> None:
    """TC-AC001-P01: authenticate with the documented ParaBank credentials."""
    page = isolated_page

    page.goto(BASE_URL, wait_until="domcontentloaded")
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()
    expect(page.get_by_role("button", name="Log In")).to_be_visible()
    _report_step("TC-AC001-P01", 1, "Login page and required controls are visible")

    page.locator('input[name="username"]').fill(KNOWN_USERNAME)
    expect(page.locator('input[name="username"]')).to_have_value(KNOWN_USERNAME)
    _report_step("TC-AC001-P01", 2, "Username was entered")

    password = page.locator('input[name="password"]')
    password.fill(KNOWN_PASSWORD)
    expect(password).to_have_attribute("type", "password")
    expect(password).to_have_value(KNOWN_PASSWORD)
    _report_step("TC-AC001-P01", 3, "Password was entered in a masked field")

    page.get_by_role("button", name="Log In").click()
    _report_step("TC-AC001-P01", 4, "Log In was clicked")

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    _report_step("TC-AC001-P01", 5, "Redirected to Account Overview rather than login")

    expect(page.get_by_role("link", name="Log Out")).to_be_visible()
    _report_step("TC-AC001-P01", 6, "Log Out navigation link is visible")

    session_cookies = [
        cookie for cookie in page.context.cookies() if cookie["name"] == "JSESSIONID"
    ]
    assert session_cookies, "Defect: successful login did not establish a JSESSIONID cookie"
    assert session_cookies[0]["value"], "Defect: JSESSIONID cookie has an empty value"
    _report_step("TC-AC001-P01", 7, "Non-empty JSESSIONID cookie is present")


def test_tc_ac001_b01_shortest_known_available_username_login(isolated_page: Page) -> None:
    """TC-AC001-B01 fallback: validate login with the shortest supplied usable account.

    A one-character account and its corresponding password were not provided. This
    scenario therefore uses the shortest known available account, ``john``/``demo``.
    """
    page = isolated_page

    page.goto(BASE_URL, wait_until="domcontentloaded")
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()
    expect(page.get_by_role("button", name="Log In")).to_be_visible()
    _report_step("TC-AC001-B01", 1, "Login page is displayed")

    page.locator('input[name="username"]').fill(SHORTEST_KNOWN_AVAILABLE_USERNAME)
    expect(page.locator('input[name="username"]')).to_have_value(
        SHORTEST_KNOWN_AVAILABLE_USERNAME
    )
    _report_step(
        "TC-AC001-B01",
        2,
        "Entered shortest known available username fallback: "
        f"{SHORTEST_KNOWN_AVAILABLE_USERNAME!r}",
    )

    page.locator('input[name="password"]').fill(SHORTEST_KNOWN_AVAILABLE_PASSWORD)
    expect(page.locator('input[name="password"]')).to_have_attribute("type", "password")
    _report_step("TC-AC001-B01", 3, "Entered corresponding password in masked field")

    page.get_by_role("button", name="Log In").click()
    _report_step("TC-AC001-B01", 4, "Log In was clicked")

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()
    _report_step(
        "TC-AC001-B01",
        5,
        "Authenticated to Account Overview with an established Log Out session",
    )
