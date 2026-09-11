import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"
USERNAME = "john"
PASSWORD = "demo"
SCREENSHOT_DIR = Path("test-results/screenshots")


def _take_final_screenshot(page: Page, filename: str) -> str:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / filename
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def _login(page: Page, username: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    expect(page.locator('input[name="username"]')).to_be_visible()
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.get_by_role("button", name="Log In").click()


def _expect_account_overview(page: Page) -> None:
    expect(
        page.get_by_role("heading", name=re.compile(r"Accounts? Overview", re.IGNORECASE))
    ).to_be_visible()


def test_login_with_leading_whitespace_username(page: Page, record_property) -> None:
    """TC-AC001-E01: record the observed whitespace-handling behavior."""
    actual_results = ["Login page displayed."]

    _login(page, f" {USERNAME}", PASSWORD)
    actual_results.extend(
        [
            "Username field accepted a leading-space value.",
            "Password field accepted the provided password.",
            "Login form submitted.",
        ]
    )

    error_message = page.get_by_text("Invalid username or password", exact=True)
    try:
        _expect_account_overview(page)
    except PlaywrightTimeoutError:
        try:
            expect(error_message).to_be_visible()
        except PlaywrightTimeoutError:
            screenshot = _take_final_screenshot(page, "tc_ac001_e01_final.png")
            record_property("TC-AC001-E01.status", "Fail")
            record_property("TC-AC001-E01.actual_results", json.dumps(actual_results))
            record_property("TC-AC001-E01.final_screenshot", screenshot)
            pytest.fail(
                "Login with leading whitespace produced neither Account(s) Overview "
                "nor the documented invalid-credentials error."
            )
        actual_results.append(
            "Observation: leading whitespace was treated as part of the username; "
            "the application displayed 'Invalid username or password'."
        )
        status = "Observation"
    else:
        actual_results.append(
            "Observation: leading whitespace was trimmed and the user reached Account(s) Overview."
        )
        status = "Observation"

    screenshot = _take_final_screenshot(page, "tc_ac001_e01_final.png")
    record_property("TC-AC001-E01.status", status)
    record_property("TC-AC001-E01.actual_results", json.dumps(actual_results))
    record_property("TC-AC001-E01.final_screenshot", screenshot)


def test_login_when_session_is_already_active(page: Page, record_property) -> None:
    """TC-AC001-E02: verify re-login behavior in a second tab sharing the active session."""
    actual_results = []
    _login(page, USERNAME, PASSWORD)
    _expect_account_overview(page)
    actual_results.append("Initial login succeeded and Account(s) Overview was displayed.")

    second_tab = page.context.new_page()
    try:
        second_tab.goto(LOGIN_URL, wait_until="domcontentloaded")
        login_form = second_tab.locator("#loginPanel form")

        if login_form.is_visible():
            actual_results.append("Second tab displayed the login page.")
            second_tab.locator('input[name="username"]').fill(USERNAME)
            second_tab.locator('input[name="password"]').fill(PASSWORD)
            second_tab.get_by_role("button", name="Log In").click()
            actual_results.append("Second-tab login form submitted with the same credentials.")
        else:
            actual_results.append("Second tab reused the active session without showing the login form.")

        _expect_account_overview(second_tab)
        expect(
            second_tab.get_by_text("Invalid username or password", exact=True)
        ).not_to_be_visible()
        actual_results.append(
            "Account(s) Overview was displayed in the second tab and no invalid-credentials error appeared."
        )
        screenshot = _take_final_screenshot(second_tab, "tc_ac001_e02_final.png")
        record_property("TC-AC001-E02.status", "Pass")
        record_property("TC-AC001-E02.actual_results", json.dumps(actual_results))
        record_property("TC-AC001-E02.final_screenshot", screenshot)
    finally:
        second_tab.close()
