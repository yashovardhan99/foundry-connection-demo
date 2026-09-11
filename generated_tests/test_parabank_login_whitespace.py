import re

from playwright.sync_api import expect


BASE_URL = "https://parabank.parasoft.com/parabank/index.htm"


def test_tc_ac001_e01_username_with_leading_whitespace(browser, record_property):
    """Accept and document ParaBank's behavior for a leading-space username."""
    context = browser.new_context()
    page = context.new_page()

    try:
        page.goto(BASE_URL, wait_until="domcontentloaded")

        username = page.locator('form[name="login"] input[name="username"]')
        password = page.locator('form[name="login"] input[name="password"]')
        login_button = page.locator('form[name="login"] input[type="submit"][value="Log In"]')

        expect(page.get_by_role("heading", name="Customer Login")).to_be_visible()
        expect(username).to_be_visible()
        expect(password).to_be_visible()
        expect(login_button).to_be_visible()

        username.fill(" john")
        expect(username).to_have_value(" john")

        password.fill("demo")
        expect(password).to_have_value("demo")
        expect(password).to_have_attribute("type", "password")

        login_button.click()

        invalid_credentials = page.get_by_text("Invalid username or password", exact=True)
        logout_link = page.get_by_role("link", name="Log Out")

        if invalid_credentials.is_visible():
            expect(invalid_credentials).to_be_visible()
            expect(logout_link).not_to_be_visible()
            record_property(
                "observed_whitespace_behavior",
                "not_trimmed: invalid username or password was displayed and no session was created",
            )
        else:
            expect(page).to_have_url(re.compile(r".*/overview\\.htm.*"))
            expect(logout_link).to_be_visible()
            record_property(
                "observed_whitespace_behavior",
                "trimmed: authenticated and redirected to Account Overview",
            )
    finally:
        context.close()
