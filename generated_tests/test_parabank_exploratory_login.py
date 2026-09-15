"""Exploratory login coverage for ParaBank issue #27.

Each test creates an isolated, synthetic ParaBank account through the observed
registration form. This avoids embedding or relying on shared credentials.
"""

import re
import uuid

import pytest
from playwright.sync_api import Page, expect


LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"
REGISTRATION_URL = "https://parabank.parasoft.com/parabank/register.htm"
OVERVIEW_URL = re.compile(r".*/parabank/overview\.htm(?:;.*)?(?:\?.*)?$")
INVALID_CREDENTIALS_MESSAGE = "Invalid username or password"


def _new_credentials() -> dict[str, str]:
    unique = uuid.uuid4().hex
    return {
        "username": f"e2e{unique[:12]}",
        "password": f"P{unique[12:24]}!9",
    }


@pytest.fixture
def registered_credentials(page: Page) -> dict[str, str]:
    """Create an isolated synthetic account, then return to a clean login page."""
    credentials = _new_credentials()
    synthetic_ssn = f"9{uuid.uuid4().int % 100_000_000:08d}"

    page.goto(REGISTRATION_URL)
    registration_fields = {
        "#customer.firstName": "Para",
        "#customer.lastName": "BankTest",
        "#customer.address.street": "1 Test Way",
        "#customer.address.city": "Testville",
        "#customer.address.state": "CA",
        "#customer.address.zipCode": "90210",
        "#customer.phoneNumber": "5555550100",
        "#customer.ssn": synthetic_ssn,
        "#customer.username": credentials["username"],
        "#customer.password": credentials["password"],
        "#repeatedPassword": credentials["password"],
    }
    for selector, value in registration_fields.items():
        page.locator(selector).fill(value)

    page.locator("form#customerForm input[type='submit']").click()
    expect(page.locator("form#customerForm")).to_have_count(0)

    page.context.clear_cookies()
    page.goto(LOGIN_URL)
    expect(page.locator("form[name='login']")).to_be_visible()
    return credentials


def _login(page: Page, username: str, password: str) -> None:
    page.locator("form[name='login'] input[name='username']").fill(username)
    page.locator("form[name='login'] input[name='password']").fill(password)
    page.locator("form[name='login'] input[type='submit']").click()


def _session_cookies(page: Page) -> list[dict[str, object]]:
    return [
        cookie
        for cookie in page.context.cookies()
        if cookie["name"].upper() == "JSESSIONID"
    ]


def _assert_successful_login(page: Page) -> None:
    expect(page).to_have_url(OVERVIEW_URL)
    expect(page.get_by_text(re.compile(r"Accounts Overview|Welcome"))).to_be_visible()
    assert _session_cookies(page), "A successful login must create a JSESSIONID cookie."


def _assert_invalid_login_has_no_session(page: Page) -> None:
    expect(page.get_by_text(INVALID_CREDENTIALS_MESSAGE, exact=True)).to_be_visible()
    expect(page.locator("form[name='login']")).to_be_visible()
    assert not _session_cookies(page), "An invalid login must not create a JSESSIONID cookie."


def test_tc_001_successful_login(page: Page, registered_credentials: dict[str, str]) -> None:
    """TC-001: Correct credentials redirect to the account overview with a session."""
    _login(page, registered_credentials["username"], registered_credentials["password"])
    _assert_successful_login(page)


def test_tc_002_retry_after_wrong_password_succeeds(
    page: Page, registered_credentials: dict[str, str]
) -> None:
    """TC-002: A wrong-password attempt leaves no session; retrying correctly succeeds."""
    _login(page, registered_credentials["username"], "clearly-wrong-password")
    _assert_invalid_login_has_no_session(page)

    _login(page, registered_credentials["username"], registered_credentials["password"])
    _assert_successful_login(page)


def test_tc_003_whitespace_padded_username_outcome_is_documented(
    page: Page, registered_credentials: dict[str, str], record_property: object
) -> None:
    """TC-003: Record whether the application trims username whitespace or rejects it."""
    _login(
        page,
        f"  {registered_credentials['username']}  ",
        registered_credentials["password"],
    )

    if re.search(r"/parabank/overview\.htm", page.url):
        record_property("whitespace_username_outcome", "trimmed_and_authenticated")
        _assert_successful_login(page)
    else:
        record_property("whitespace_username_outcome", "rejected_as_invalid_credentials")
        _assert_invalid_login_has_no_session(page)


def test_tc_004_clearly_wrong_password_is_rejected(
    page: Page, registered_credentials: dict[str, str]
) -> None:
    """TC-004: A clearly wrong password yields the generic error and no session."""
    _login(page, registered_credentials["username"], "definitely-not-the-password")
    _assert_invalid_login_has_no_session(page)


def test_tc_005_one_character_password_difference_is_rejected(
    page: Page, registered_credentials: dict[str, str]
) -> None:
    """TC-005: A password differing by exactly one character is rejected."""
    password = registered_credentials["password"]
    replacement = "X" if password[-1] != "X" else "Y"
    one_character_different = f"{password[:-1]}{replacement}"

    _login(page, registered_credentials["username"], one_character_different)
    _assert_invalid_login_has_no_session(page)


def test_tc_006_password_missing_last_character_is_rejected(
    page: Page, registered_credentials: dict[str, str]
) -> None:
    """TC-006: The correct password minus its final character is rejected."""
    _login(page, registered_credentials["username"], registered_credentials["password"][:-1])
    _assert_invalid_login_has_no_session(page)


def test_tc_007_blank_password_outcome_is_documented(
    page: Page, registered_credentials: dict[str, str], record_property: object
) -> None:
    """TC-007: Record field validation versus server-side invalid-credentials handling."""
    _login(page, registered_credentials["username"], "")

    invalid_credentials = page.get_by_text(INVALID_CREDENTIALS_MESSAGE, exact=True)
    if invalid_credentials.is_visible():
        record_property("blank_password_outcome", "server_invalid_credentials")
        _assert_invalid_login_has_no_session(page)
    else:
        record_property("blank_password_outcome", "field_level_validation")
        expect(page.locator("form[name='login']")).to_be_visible()
        assert not _session_cookies(page), "A blank password must not create a JSESSIONID cookie."
