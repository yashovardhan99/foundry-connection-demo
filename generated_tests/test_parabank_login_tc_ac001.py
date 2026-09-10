"""Playwright coverage for ParaBank login scenarios TC-AC001-P01 and TC-AC001-B01.

The B01 scenario uses a provisioned one-character account when supplied through
PARABANK_MIN_USERNAME and PARABANK_MIN_PASSWORD. In its absence it deliberately
attempts the documented shortest known account (john/demo) and fails with a defect
rather than falsely reporting the one-character boundary as covered.
"""

import logging
import os
import re
from contextlib import contextmanager

import pytest
from playwright.sync_api import Page, expect


LOGIN_URL = "https://parabank.parasoft.com/parabank/index.htm"
HAPPY_PATH_USERNAME = "john"
HAPPY_PATH_PASSWORD = "demo"
# Issue #6 records that no genuine one-character account was available.
BOUNDARY_USERNAME = os.getenv("PARABANK_MIN_USERNAME", HAPPY_PATH_USERNAME)
BOUNDARY_PASSWORD = os.getenv("PARABANK_MIN_PASSWORD", HAPPY_PATH_PASSWORD)


@contextmanager
def report_step(description: str):
    """Log a per-step pass/fail result while preserving assertion failures."""
    try:
        yield
    except Exception:
        logging.exception("FAIL: %s", description)
        raise
    else:
        logging.info("PASS: %s", description)


def login(page: Page, username: str, password: str) -> None:
    """Perform the ParaBank login form interaction with observable assertions."""
    with report_step("Navigate to the ParaBank login page and verify login controls"):
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Customer Login")).to_be_visible()
        expect(page.locator("input[name='username']")).to_be_visible()
        expect(page.locator("input[name='password']")).to_be_visible()
        expect(page.get_by_role("button", name="Log In")).to_be_visible()

    with report_step(f"Enter username with {len(username)} character(s)"):
        page.locator("input[name='username']").fill(username)
        expect(page.locator("input[name='username']")).to_have_value(username)

    with report_step("Enter the corresponding password and verify that it is masked"):
        password_input = page.locator("input[name='password']")
        password_input.fill(password)
        assert password_input.evaluate("element => element.type") == "password"

    with report_step("Click Log In"):
        page.get_by_role("button", name="Log In").click()


def assert_authenticated(page: Page) -> None:
    with report_step("Verify redirect to Account Overview instead of the login page"):
        expect(page).to_have_url(re.compile(r".*/overview\.htm.*"))
        expect(page.get_by_role("heading", name="Accounts Overview")).to_be_visible()

    with report_step("Verify the Log Out navigation link is visible"):
        expect(page.get_by_role("link", name="Log Out")).to_be_visible()


def test_tc_ac001_p01_happy_path_login(page: Page) -> None:
    """TC-AC001-P01: john/demo authenticates and establishes a web session."""
    try:
        login(page, HAPPY_PATH_USERNAME, HAPPY_PATH_PASSWORD)
        assert_authenticated(page)

        with report_step("Verify a non-empty JSESSIONID cookie is present"):
            session_cookies = [
                cookie
                for cookie in page.context.cookies()
                if cookie["name"] == "JSESSIONID" and cookie["value"]
            ]
            assert session_cookies, "Expected a non-empty JSESSIONID cookie after login"
    finally:
        # Remove authentication state even if an assertion fails.
        page.context.clear_cookies()


def test_tc_ac001_b01_minimum_username_length_login(page: Page) -> None:
    """TC-AC001-B01: exercise a provisioned 1-character account or log the defect."""
    try:
        login(page, BOUNDARY_USERNAME, BOUNDARY_PASSWORD)
        assert_authenticated(page)

        if len(BOUNDARY_USERNAME) != 1:
            defect = (
                "DEFECT TC-AC001-B01 / GitHub issue #6: no provisioned one-character "
                "ParaBank account credentials were supplied. The shortest known available "
                f"account ({BOUNDARY_USERNAME!r}) authenticated, but the true minimum-length "
                "boundary remains unverified. Set PARABANK_MIN_USERNAME and "
                "PARABANK_MIN_PASSWORD to genuine one-character account credentials."
            )
            logging.error(defect)
            pytest.fail(defect)
    finally:
        page.context.clear_cookies()
