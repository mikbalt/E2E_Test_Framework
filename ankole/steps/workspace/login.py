"""Login step factories for workspace flows."""

from ankole.flows.base import Step


def full_login(username: str, password: str, base_url: str = "") -> Step:
    """Step: navigate to login page and authenticate."""

    def _action(ctx):
        from ankole.pages.web.login_page import LoginPage

        page = LoginPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        page.login(username, password)
        ctx.set("login_page", page)

    return Step(f"Login as {username}", _action)


def logout(base_url: str = "") -> Step:
    """Step: logout from the application."""

    def _action(ctx):
        ctx.driver.goto(f"{base_url}/logout")

    return Step("Logout", _action)
