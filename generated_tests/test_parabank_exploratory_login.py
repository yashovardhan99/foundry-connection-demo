"""Exploratory ParaBank login coverage for source issue #27."""

import re
import uuid

import pytest
from playwright.sync_api import Browser, Page, expect


LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"
REGISTER_URL = "https://parabank.parasoft.com/parabank/register.htm"


def _session_cookies(context):
    """Return authentication-session cookies visible to the browser context."""
    return [cookie for cookie in context.cookies() if cookie["name"] == "JSESSIONID"]


def _submit_login(page: Page, username: str, password: str) -> None:
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.get_by_role("button", name="Log In").click()


def _assert_login_failure(page: Page, context) -> None:
    expect(page).to_have_url(re.compile(r".*/parabank/(?:index|login)\.htm.*"))
    expect(page.get_by_role("heading", name="Customer Login")).to_be_visible()
    expect(page.get_by_text("Invalid username or password", exact=True)).to_be_visible()
    assert not _session_cookies(context), "An invalid login must not create a JSESSIONID cookie."


def _assert_login_success(page: Page, context) -> None:
    expect(page).to_have_url(re.compile(r".*/parabank/overview\.htm(?:[;?].*)?$"))
    expect(page.locator("body")).to_contain_text(re.compile(r"Accounts Overview|Welcome"))
    assert _session_cookies(context), "A successful login must create a JSESSIONID cookie."


@pytest.fixture
def registered_credentials(browser: Browser) -> tuple[str, str]:
    """Create an isolated, synthetic ParaBank user for each login scenario."""
    registration_context = browser.new_context()
    registration_page = registration_context.new_page()
    suffix = uuid.uuid4().hex[:12]
    username = f"qa{suffix}"
    password = f"Pwd{suffix}"

    try:
        registration_page.goto(REGISTER_URL)
        registration_page.locator('#customer\\.firstName').fill("QA")
        registration_page.locator('#customer\\.lastName').fill("Automation")
        registration_page.locator('#customer\\.address\\.street').fill("1 Test Way")
        registration_page.locator('#customer\\.address\\.city').fill("Testville")
        registration_page.locator('#customer\\.address\\.state').fill("CA")
        registration_page.locator('#customer\\.address\\.zipCode').fill("90210")
        registration_page.locator('#customer\\.phoneNumber').fill("5555550100")
        registration_page.locator('#customer\\.ssn').fill("000000000")
        registration_page.locator('#customer\\.username').fill(username)
        registration_page.locator('#customer\\.password').fill(password)
        registration_page.locator('#repeatedPassword').fill(password)
        registration_page.get_by_role("button", name="Register").click()
    finally:
        registration_context.close()

    return username, password


@pytest.fixture
def login_session(browser: Browser):
    """Provide a fresh login page and guarantee browser-context cleanup."""
    context = browser.new_context()
    page = context.new_page()
    try:
        page.goto(LOGIN_URL)
        context.clear_cookies()
        yield context, page
    finally:
        context.close()


def test_tc_001_successful_login(registered_credentials, login_session):
    """SC-001 / TC-001: valid credentials redirect to overview and set a session."""
    username, password = registered_credentials
    context, page = login_session

    _submit_login(page, username, password)

    _assert_login_success(page, context)


def test_tc_002_retry_after_wrong_password(registered_credentials, login_session):
    """SC-001 / TC-002: a failed attempt can be followed by successful authentication."""
    username, password = registered_credentials
    context, page = login_session

    _submit_login(page, username, f"wrong-{uuid.uuid4().hex}")
    _assert_login_failure(page, context)

    _submit_login(page, username, password)
    _assert_login_success(page, context)


def test_tc_003_username_whitespace_behavior(registered_credentials, login_session):
    """SC-001 / TC-003: record whether surrounding username whitespace is accepted."""
    username, password = registered_credentials
    context, page = login_session

    _submit_login(page, f"  {username}  ", password)
    expect(page.locator("body")).to_contain_text(
        re.compile(r"Accounts Overview|Welcome|Invalid username or password")
    )

    if re.search(r"/parabank/overview\.htm", page.url):
        print("Username whitespace behavior: accepted (leading/trailing whitespace was trimmed).")
        _assert_login_success(page, context)
    else:
        print("Username whitespace behavior: rejected with the standard invalid-credentials error.")
        _assert_login_failure(page, context)


def test_tc_004_clearly_wrong_password(registered_credentials, login_session):
    """SC-002 / TC-004: a clearly wrong password returns the generic login error."""
    username, _ = registered_credentials
    context, page = login_session

    _submit_login(page, username, f"definitely-wrong-{uuid.uuid4().hex}")

    _assert_login_failure(page, context)


def test_tc_005_one_character_password_difference(registered_credentials, login_session):
    """SC-002 / TC-005: changing exactly one password character is rejected."""
    username, password = registered_credentials
    context, page = login_session
    replacement = "0" if password[-1] != "0" else "1"
    one_character_off = f"{password[:-1]}{replacement}"

    _submit_login(page, username, one_character_off)

    _assert_login_failure(page, context)


def test_tc_006_password_missing_last_character(registered_credentials, login_session):
    """SC-002 / TC-006: a truncated correct password is rejected."""
    username, password = registered_credentials
    context, page = login_session

    _submit_login(page, username, password[:-1])

    _assert_login_failure(page, context)


def test_tc_007_blank_password_behavior(registered_credentials, login_session):
    """SC-002 / TC-007: record field validation or generic server-side rejection."""
    username, _ = registered_credentials
    context, page = login_session

    _submit_login(page, username, "")
    expect(page.locator("body")).to_contain_text(
        re.compile(r"Enter missing details|Invalid username or password")
    )
    body_text = page.locator("body").inner_text()

    if "Enter missing details" in body_text:
        print("Blank-password behavior: field-level 'Enter missing details' validation was shown.")
    else:
        print("Blank-password behavior: server returned 'Invalid username or password'.")
        expect(page.get_by_text("Invalid username or password", exact=True)).to_be_visible()

    assert not _session_cookies(context), "A blank-password login must not create a JSESSIONID cookie."
