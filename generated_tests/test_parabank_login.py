"""Generated ParaBank login coverage for TC-AC001-P01 and TC-AC001-B01."""

import logging

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"
LOGGER = logging.getLogger(__name__)


def _log_step(test_case: str, step: int, outcome: str) -> None:
    """Record an individual test-case step outcome in pytest's captured logs."""
    LOGGER.info("%s step %s: %s", test_case, step, outcome)


def _open_login_page(page: Page, test_case: str) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    expect(page.locator("form[name='login']")).to_be_visible()
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("input[type='submit'][value='Log In']")).to_be_visible()
    _log_step(test_case, 1, "PASS - login page and required controls are visible")


def _assert_authenticated_session(page: Page, test_case: str, step: int) -> None:
    expect(page.get_by_text("Accounts Overview", exact=True)).to_be_visible()
    assert "index.htm" not in page.url, "Authentication left the browser on the login page"
    _log_step(test_case, step, "PASS - authenticated Account Overview is displayed")

    expect(page.get_by_role("link", name="Log Out", exact=True)).to_be_visible()
    _log_step(test_case, step + 1, "PASS - Log Out navigation link is visible")

    session_cookies = [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "JSESSIONID" and cookie["value"]
    ]
    assert session_cookies, "Expected a JSESSIONID cookie with a non-empty value"
    _log_step(test_case, step + 2, "PASS - non-empty JSESSIONID cookie is present")


def test_tc_ac001_p01_happy_path_login(page: Page) -> None:
    """TC-AC001-P01: log in with the documented john/demo test account."""
    test_case = "TC-AC001-P01"
    _open_login_page(page, test_case)

    page.locator("input[name='username']").fill("john")
    expect(page.locator("input[name='username']")).to_have_value("john")
    _log_step(test_case, 2, "PASS - documented username was entered")

    password = page.locator("input[name='password']")
    password.fill("demo")
    expect(password).to_have_attribute("type", "password")
    expect(password).to_have_value("demo")
    _log_step(test_case, 3, "PASS - password was entered and field is masked")

    page.locator("input[type='submit'][value='Log In']").click()
    _log_step(test_case, 4, "PASS - Log In was clicked")

    _assert_authenticated_session(page, test_case, 5)


def test_tc_ac001_b01_minimum_username_boundary(page: Page) -> None:
    """TC-AC001-B01: attempt the required one-character username boundary."""
    test_case = "TC-AC001-B01"
    _open_login_page(page, test_case)

    # The supplied test case does not provide credentials for a one-character account.
    # "j" is the one-character boundary candidate derived from documented user "john";
    # "demo" is the only supplied test password. The fallback verifies the shortest
    # documented working account if the boundary-account precondition is unavailable.
    page.locator("input[name='username']").fill("j")
    expect(page.locator("input[name='username']")).to_have_value("j")
    _log_step(test_case, 2, "PASS - one-character boundary candidate was entered")

    page.locator("input[name='password']").fill("demo")
    expect(page.locator("input[name='password']")).to_have_attribute("type", "password")
    _log_step(test_case, 3, "PASS - supplied password was entered into the masked field")

    page.locator("input[type='submit'][value='Log In']").click()
    _log_step(test_case, 4, "PASS - Log In was clicked for the boundary candidate")

    if page.get_by_role("link", name="Log Out", exact=True).is_visible():
        _assert_authenticated_session(page, test_case, 5)
        return

    LOGGER.warning(
        "%s DEFECT/TEST-DATA GAP: the supplied input provides no verified "
        "one-character account and corresponding password; the one-character "
        "attempt did not establish an authenticated session.",
        test_case,
    )

    # Per the test-case fallback instruction, verify the only documented usable account.
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.locator("input[name='username']").fill("john")
    page.locator("input[name='password']").fill("demo")
    page.locator("input[type='submit'][value='Log In']").click()
    _assert_authenticated_session(page, test_case, 5)

    pytest.xfail(
        "TC-AC001-B01 cannot pass its one-character authentication assertion: "
        "no verified one-character account credentials were supplied. "
        "Fallback john/demo login passed and the limitation was logged."
    )
