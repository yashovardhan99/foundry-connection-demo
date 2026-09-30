import os
import re

import pytest
from playwright.sync_api import Browser, expect

BASE_URL = "https://parabank.parasoft.com/parabank/"
LOGIN_URL = f"{BASE_URL}index.htm"
PROTECTED_OVERVIEW_URL = f"{BASE_URL}overview.htm"
LOGIN_PAGE_URL = re.compile(r".*/(?:index|login)\.htm(?:;[^?]*)?(?:\?.*)?$")
OVERVIEW_PAGE_URL = re.compile(r".*/overview\.htm(?:;[^?]*)?(?:\?.*)?$")
WELCOME_TEXT = re.compile(r"welcome", re.IGNORECASE)


def _valid_credentials() -> tuple[str, str]:
    username = os.getenv("PARABANK_USERNAME")
    password = os.getenv("PARABANK_PASSWORD")
    assert username, "PARABANK_USERNAME must be configured for the valid-login scenario"
    assert password, "PARABANK_PASSWORD must be configured for the valid-login scenario"
    return username, password


def _cookie_fingerprint(cookies: list[dict]) -> set[tuple[str, str, str, str]]:
    return {
        (cookie["name"], cookie["value"], cookie["domain"], cookie["path"])
        for cookie in cookies
    }


def test_successful_login_redirects_and_persists_authenticated_session(browser: Browser) -> None:
    """SC-001 / AC-001: valid credentials open and retain an authenticated dashboard session."""
    username, password = _valid_credentials()
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        expect(page.locator("form[name='login']")).to_be_visible()

        page.locator("input[name='username']").fill(username)
        page.locator("input[name='password']").fill(password)
        page.get_by_role("button", name="Log In").click()

        expect(page).to_have_url(OVERVIEW_PAGE_URL)
        expect(page.locator("form[name='login']")).not_to_be_visible()
        welcome_indicator = page.get_by_text(WELCOME_TEXT).first
        expect(welcome_indicator).to_be_visible()

        session_cookies = context.cookies()
        assert session_cookies or welcome_indicator.is_visible(), (
            "A successful login must establish a session cookie and/or a visible welcome indicator"
        )

        page.goto(PROTECTED_OVERVIEW_URL, wait_until="domcontentloaded")
        expect(page).to_have_url(OVERVIEW_PAGE_URL)
        expect(page.locator("form[name='login']")).not_to_be_visible()
        expect(page.get_by_text(WELCOME_TEXT).first).to_be_visible()
    finally:
        context.close()


def test_invalid_password_shows_error_without_session_or_protected_access(browser: Browser) -> None:
    """SC-003 / AC-002: an invalid password is rejected without authenticating the browser."""
    username, _ = _valid_credentials()
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        cookies_before_login = _cookie_fingerprint(context.cookies())

        page.locator("input[name='username']").fill(username)
        page.locator("input[name='password']").fill("wrongpassword123")
        page.get_by_role("button", name="Log In").click()

        expect(page).to_have_url(LOGIN_PAGE_URL)
        expect(page.locator("form[name='login']")).to_be_visible()
        expect(page.get_by_text("Invalid username or password", exact=True)).to_be_visible()
        assert _cookie_fingerprint(context.cookies()) == cookies_before_login, (
            "A failed login must not create or modify session cookies"
        )

        page.goto(PROTECTED_OVERVIEW_URL, wait_until="domcontentloaded")
        expect(page.locator("form[name='login']")).to_be_visible()
        expect(page.get_by_text(WELCOME_TEXT).first).not_to_be_visible()
    finally:
        context.close()
