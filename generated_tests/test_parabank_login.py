"""Playwright tests for ParaBank login scenarios from issue #27."""

import re

import pytest
from playwright.sync_api import Page, expect


LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"


def submit_login(page: Page, username: str, password: str) -> None:
    """Submit the observed ParaBank customer login form."""
    page.goto(LOGIN_URL)
    page.locator("input[name='username']").fill(username)
    page.locator("input[name='password']").fill(password)
    page.get_by_role("button", name="Log In").click()


def session_cookies(page: Page) -> list[dict[str, object]]:
    """Return JSESSIONID cookies in the browser context."""
    return [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "JSESSIONID"
    ]


@pytest.mark.parametrize("username,password", [("john", "demo")])
def test_tc_001_successful_login_with_valid_credentials(
    page: Page, username: str, password: str
) -> None:
    """TC-001: Valid credentials authenticate the user to Accounts Overview."""
    submit_login(page, username, password)

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()

    cookies = session_cookies(page)
    assert cookies, "Expected a JSESSIONID cookie after successful login."
    assert all(cookie["value"] for cookie in cookies), (
        "Expected each JSESSIONID cookie to have a non-empty value."
    )


def test_tc_002_session_established_after_successful_login(page: Page) -> None:
    """TC-002: Successful login establishes a non-empty JSESSIONID cookie."""
    submit_login(page, "john", "demo")

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    cookies = session_cookies(page)
    assert cookies, "Expected a JSESSIONID cookie after successful login."
    assert all(cookie["value"] for cookie in cookies), (
        "Expected each JSESSIONID cookie to have a non-empty value."
    )


def test_tc_004_login_fails_with_correct_username_and_wrong_password(
    page: Page,
) -> None:
    """TC-004: Wrong password shows the generic error and creates no session."""
    submit_login(page, "john", "wrongpass")

    expect(page.get_by_text("Invalid username or password", exact=True)).to_be_visible()
    expect(page).to_have_url(re.compile(r".*/(?:index|login)\.htm.*"))

    assert not session_cookies(page), (
        "A JSESSIONID cookie must not be present after a failed login attempt."
    )
