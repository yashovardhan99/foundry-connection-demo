"""Executable login coverage for ParaBank TC-AC001-P01 and TC-AC001-B01."""

import re

from playwright.sync_api import Page, expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"


def _record_step(record_property, case_id: str, step_number: int, detail: str) -> None:
    """Expose successful scenario steps in the JUnit report."""
    record_property(f"{case_id} step {step_number}", f"PASS: {detail}")


def _login(page: Page, username: str, password: str) -> None:
    page.locator("input[name='username']").fill(username)
    page.locator("input[name='password']").fill(password)
    page.get_by_role("button", name="Log In").click()


def test_tc_ac001_p01_happy_path_login(page: Page, record_property) -> None:
    """TC-AC001-P01: john/demo can authenticate and receives a session."""
    page.goto(BASE_URL)
    username = page.locator("input[name='username']")
    password = page.locator("input[name='password']")
    login_button = page.get_by_role("button", name="Log In")
    expect(username).to_be_visible()
    expect(password).to_be_visible()
    expect(login_button).to_be_visible()
    _record_step(record_property, "TC-AC001-P01", 1, "Login controls are displayed")

    username.fill("john")
    expect(username).to_have_value("john")
    _record_step(record_property, "TC-AC001-P01", 2, "Username entered")

    password.fill("demo")
    expect(password).to_have_value("demo")
    expect(password).to_have_attribute("type", "password")
    _record_step(record_property, "TC-AC001-P01", 3, "Password entered and masked")

    login_button.click()
    _record_step(record_property, "TC-AC001-P01", 4, "Log In clicked")

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    _record_step(record_property, "TC-AC001-P01", 5, "Redirected to Account Overview")

    expect(page.get_by_role("link", name="Log Out")).to_be_visible()
    _record_step(record_property, "TC-AC001-P01", 6, "Log Out navigation link is visible")

    session_cookies = [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "JSESSIONID" and cookie["value"]
    ]
    assert session_cookies, "Defect: authentication did not establish a non-empty JSESSIONID cookie"
    _record_step(record_property, "TC-AC001-P01", 7, "Non-empty JSESSIONID cookie is present")


def test_tc_ac001_b01_shortest_available_username_login(page: Page, record_property) -> None:
    """TC-AC001-B01 fallback using the shortest supplied working account."""
    # The scenario supplies no one-character account credentials. john/demo is the
    # shortest known available account, so this records the permitted fallback outcome.
    username_value = "john"
    password_value = "demo"
    record_property(
        "TC-AC001-B01 boundary-deviation",
        "No one-character account credentials were supplied; used shortest known working username 'john' (length 4).",
    )

    page.goto(BASE_URL)
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.get_by_role("button", name="Log In")).to_be_visible()
    _record_step(record_property, "TC-AC001-B01", 1, "Login page is displayed")

    page.locator("input[name='username']").fill(username_value)
    expect(page.locator("input[name='username']")).to_have_value(username_value)
    _record_step(
        record_property,
        "TC-AC001-B01",
        2,
        "Entered shortest known available username 'john' (length 4; one-character credentials unavailable)",
    )

    page.locator("input[name='password']").fill(password_value)
    expect(page.locator("input[name='password']")).to_have_value(password_value)
    _record_step(record_property, "TC-AC001-B01", 3, "Entered corresponding password")

    page.get_by_role("button", name="Log In").click()
    _record_step(record_property, "TC-AC001-B01", 4, "Log In clicked")

    expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
    expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()
    session_cookies = [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"] == "JSESSIONID" and cookie["value"]
    ]
    assert session_cookies, "Defect: authenticated fallback login did not establish JSESSIONID"
    _record_step(
        record_property,
        "TC-AC001-B01",
        5,
        "Authenticated to Account Overview with Log Out link and active session",
    )
