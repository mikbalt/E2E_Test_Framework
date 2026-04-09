# Ankole Framework - Cookbook

Recipes for common tasks when extending the framework.

---

## Recipe 1: Add a Web Page Object

```python
# ankole/pages/web/settings_page.py
from ankole.pages.web.base_web_page import BaseWebPage

class SettingsPage(BaseWebPage):
    THEME_SELECT = "#theme-select"
    SAVE_BTN = "#save-settings"

    def goto(self):
        self.navigate_to("/settings")
        return self

    def change_theme(self, theme: str):
        with self._web_step(f"Change theme to {theme}"):
            self.driver.select_option(self.THEME_SELECT, theme)
            self.driver.click(self.SAVE_BTN)
```

---

## Recipe 2: Add an API Test

```python
# tests/api/test_settings_api.py
import pytest

@pytest.mark.api
class TestSettingsAPI:
    def test_get_settings(self, authed_api):
        resp = authed_api.get("/api/settings")
        resp.assert_status(200)
        resp.assert_json_key("theme")

    def test_update_settings(self, authed_api):
        resp = authed_api.put("/api/settings", json={"theme": "dark"})
        resp.assert_status(200)
```

---

## Recipe 3: Create a Flow

```python
# ankole/flows/workspace/settings.py
from ankole.flows.base import Flow, Step

def change_theme_flow(username, password, theme, base_url=""):
    from ankole.steps.workspace.login import full_login, logout

    def _change(ctx):
        from ankole.pages.web.settings_page import SettingsPage
        page = SettingsPage(ctx.driver, ctx.evidence, base_url)
        page.goto()
        page.change_theme(theme)

    return Flow("Change Theme", [
        full_login(username, password, base_url),
        Step(f"Set theme to {theme}", _change),
    ], cleanup_steps=[logout(base_url)])
```

---

## Recipe 4: Add Prometheus Metrics

The framework automatically pushes test results to Prometheus. To add custom metrics:

```python
from ankole.driver.grafana_push import MetricsPusher

pusher = MetricsPusher(
    pushgateway_url="http://localhost:9091",
    job_name="custom_tests",
    metric_prefix="ankole",
)
pusher.record_test("my_test", passed=True, duration=1.5, suite="settings")
pusher.push()
```

---

## Recipe 5: Use Flow Composition

```python
from ankole.flows.workspace.member_management import (
    add_member_flow, suspend_member_flow
)

# Compose flows with + operator
combined = add_member_flow(...) + suspend_member_flow(...)
combined.run(ctx)
```

---

## Recipe 6: Add a Desktop Page Object

```python
# ankole/pages/desktop/notepad_page.py
from ankole.pages.base_page import BasePage

class NotepadPage(BasePage):
    def type_content(self, text):
        with self._step("Type content"):
            self.driver.type_text(text, auto_id="15")

    def save_file(self):
        with self._step("Save file"):
            self.driver.click_element(title="File")
            self.driver.click_element(title="Save")
```

---

## Recipe 7: Kiwi TCMS Integration

Map tests to TCMS cases:

```python
@pytest.mark.tcms(case_id=12345)
def test_login():
    ...
```

Run against a specific TestRun:

```bash
pytest --kiwi-run-id=42
```

Create a new TestRun automatically:

```bash
pytest --kiwi-create-run --kiwi-plan-id=1
```
