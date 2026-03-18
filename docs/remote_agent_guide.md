# Remote Agent Guide

Trigger automation on remote Windows VMs from the local test runner via HTTP.
Supports **multiple VMs** — each running its own agent.

## Architecture

```
Local VM (Test Runner)                     Remote VMs
──────────────────────                     ──────────────────────────────
pytest                                     VM-A (10.66.1.10) — Proxy
  │                                          │ python agent.py --port 5050
  ├─ POST /run-bat ────────────────────────→ ├─ Execute .bat file
  ├─ POST /run-script ─────────────────────→ ├─ Run Python script
  │                                          │   └─ UIDriver: open app, click, etc.
  ←── {"status":"ok", "output":"..."} ──────┤
  │
  │                                        VM-B (10.66.1.20) — Key Server
  │                                          │ python agent.py --port 5050
  ├─ POST /run-script ─────────────────────→ ├─ Run Python script
  ←── {"status":"ok"} ─────────────────────┤
  │
  ├─ GET  /screenshot ─────────────────────→ Capture desktop screenshot
  ├─ GET  /health ─────────────────────────→ Health check
  └─ GET  /list-scripts ───────────────────→ List available scripts
```

> **Important**: The agent **must** be started in an **interactive desktop session**
> (logged in via RDP or console), **not** via WinRM/SSH service. Due to Windows
> Session 0 Isolation, apps launched from a service session are invisible on the desktop.

---

## Remote VM Setup

### 1. Install Python + Dependencies

```powershell
# On the remote VM
pip install flask mss pillow pywinauto
```

Or install the full framework:

```powershell
pip install -e git+https://gitlab.yourcompany.com/qa/sphere-e2e-test-framework.git
pip install flask
```

### 2. Prepare Scripts Directory

Create a folder for automation scripts:

```powershell
mkdir C:\automation\scripts
```

Example script (`C:\automation\scripts\setup_proxy.py`):

```python
"""Setup HSM Proxy — executed by Remote Agent."""
import sys
from sphere_e2e_test_framework import UIDriver

def main():
    driver = UIDriver(
        app_path=r"C:\Program Files\HSMProxy\proxy.exe",
        backend="uia",
        startup_wait=5,
    )
    driver.start()

    # Click Connect
    driver.click_button("Connect")

    # Wait for Connected status
    driver.wait_for_element(
        title="Connected",
        control_type="Text",
        timeout=30,
    )

    print("Proxy setup complete - status: Connected")
    # Don't close — keep app running
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Example script that runs a .bat file then configures UI:

```python
"""Run prerequisite bat then configure app."""
import subprocess
import sys
from sphere_e2e_test_framework import UIDriver

def main():
    # Step 1: Run bat file
    result = subprocess.run(
        [r"C:\Scripts\prepare_env.bat"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"Bat failed: {result.stderr}", file=sys.stderr)
        return 1
    print(f"Bat output: {result.stdout}")

    # Step 2: Open app and configure
    driver = UIDriver(app_path=r"C:\MyApp\app.exe", backend="uia")
    driver.start()
    driver.click_button(name="Settings")
    driver.type_text("192.168.1.100", auto_id="txtServerIP")
    driver.click_button(name="Save")
    driver.click_button(name="Connect")

    # Verify
    driver.wait_for_element(title="Ready", control_type="Text", timeout=30)
    print("App configured and connected")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 3. Start the Agent

```powershell
# Basic (no auth)
python agent.py --port 5050 --scripts-dir C:\automation\scripts

# With auth token
python agent.py --port 5050 --scripts-dir C:\automation\scripts --auth-token mysecret123

# Custom timeout
python agent.py --port 5050 --scripts-dir C:\automation\scripts --timeout 300
```

Expected output:

```
2026-03-05 10:00:00 [INFO] remote_agent: ============================================================
2026-03-05 10:00:00 [INFO] remote_agent: Remote Agent Starting
2026-03-05 10:00:00 [INFO] remote_agent:   Host:        0.0.0.0:5050
2026-03-05 10:00:00 [INFO] remote_agent:   Scripts dir: C:\automation\scripts
2026-03-05 10:00:00 [INFO] remote_agent:   Auth:        disabled
2026-03-05 10:00:00 [INFO] remote_agent:   Timeout:     120s
2026-03-05 10:00:00 [INFO] remote_agent: ============================================================
```

### 4. Open Firewall

```powershell
netsh advfirewall firewall add rule name="RemoteAgent" dir=in action=allow protocol=tcp localport=5050
```

### 5. Verify from Local VM

```powershell
curl http://10.66.1.10:5050/health
```

---

## Configuration

### Multi-VM Setup (`config/settings.yaml`)

```yaml
remote_agents:
  enabled: true
  default_port: 5050
  default_timeout: 120
  agents:
    proxy_vm:
      host: "10.66.1.10"
      port: 5050
      auth_token: ""
      description: "HSM Proxy VM"
    key_server_vm:
      host: "10.66.1.20"
      port: 5050
      auth_token: ""
      description: "Key Server VM"
```

Or via `.env`:

```env
REMOTE_AGENT_PROXY_HOST=10.66.1.10
REMOTE_AGENT_KEYS_HOST=10.66.1.20
```

---

## Usage in Tests

### Multi-VM Fixture (Recommended)

```python
# conftest.py
import pytest
from sphere_e2e_test_framework import RemoteAgentPool

@pytest.fixture(scope="session")
def remote(config):
    """Pool of remote agents for multi-VM automation."""
    cfg = config.get("remote_agents", {})
    if not cfg.get("enabled", False):
        pytest.skip("Remote agents not enabled")

    pool = RemoteAgentPool.from_config(cfg)
    status = pool.wait_all_ready(timeout=30)
    failed = [name for name, ready in status.items() if not ready]
    assert not failed, f"Remote agents not reachable: {failed}"
    return pool
```

### In Test — Multi-VM

```python
def test_key_ceremony(remote, e_admin_driver, evidence):
    # Step 1: Setup proxy on VM-A
    result = remote["proxy_vm"].run_script("setup_proxy.py", timeout=60)
    assert result.ok, f"Proxy setup failed: {result.stderr}"

    # Step 2: Prepare keys on VM-B
    result = remote["key_server_vm"].run_bat(r"C:\Scripts\prepare_keys.bat")
    assert result.ok, f"Key prep failed: {result.output}"

    # Step 3: Capture remote screenshots as evidence
    remote["proxy_vm"].screenshot(name="proxy_after_setup", evidence=evidence)
    remote["key_server_vm"].screenshot(name="keys_after_setup", evidence=evidence)

    # Step 4: Continue local test
    e_admin_driver.click_button("Start Key Ceremony")
    # ...
```

### Parallel Execution on Multiple VMs

```python
from concurrent.futures import ThreadPoolExecutor

def test_parallel_setup(remote):
    with ThreadPoolExecutor() as pool:
        future_a = pool.submit(remote["proxy_vm"].run_script, "setup_proxy.py")
        future_b = pool.submit(remote["key_server_vm"].run_script, "setup_keys.py")

        result_a = future_a.result()
        result_b = future_b.result()

    assert result_a.ok, f"VM-A failed: {result_a.stderr}"
    assert result_b.ok, f"VM-B failed: {result_b.stderr}"
```

### Single VM (Simple Usage)

```python
from sphere_e2e_test_framework import RemoteTrigger

trigger = RemoteTrigger(host="10.66.1.10", port=5050)

if trigger.wait_ready():
    result = trigger.run_script("setup_proxy.py")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    result = trigger.run_bat(r"C:\Scripts\backup.bat")
    result = trigger.run_command("dir C:\\logs")
    png = trigger.screenshot()
```

---

## API Reference — Agent Endpoints

### `GET /health`

Returns agent status and system info.

```json
{
  "status": "ok",
  "hostname": "REMOTE-VM-01",
  "pid": 12345,
  "python": "3.11.5",
  "platform": "Windows-10-...",
  "scripts_dir": "C:\\automation\\scripts",
  "cwd": "C:\\automation"
}
```

### `POST /run-script`

Run a Python script from the scripts directory.

**Request:**
```json
{
  "script": "setup_proxy.py",
  "args": ["--verbose"],
  "timeout": 60
}
```

**Response:**
```json
{
  "status": "ok",
  "output": "Proxy setup complete\n",
  "stderr": "",
  "return_code": 0,
  "duration": 12.5
}
```

### `POST /run-bat`

Run a .bat/.cmd file by full path.

**Request:**
```json
{
  "path": "C:\\Scripts\\prepare.bat",
  "args": ["param1"],
  "timeout": 60
}
```

### `POST /run-command`

Run an arbitrary shell command.

**Request:**
```json
{
  "command": "dir C:\\logs",
  "timeout": 30
}
```

### `GET /screenshot`

Returns a full desktop screenshot as PNG binary data.

### `GET /list-scripts`

Returns list of available `.py` scripts in the scripts directory.

```json
{
  "status": "ok",
  "scripts": ["setup_proxy.py", "configure_app.py"],
  "scripts_dir": "C:\\automation\\scripts"
}
```

---

## Python Client API

### RemoteTrigger (Single VM)

```python
from sphere_e2e_test_framework import RemoteTrigger

trigger = RemoteTrigger(
    host="10.66.1.10",    # Remote VM IP
    port=5050,            # Agent port
    auth_token=None,      # Optional auth token
    timeout=120,          # Default timeout (seconds)
)
```

| Method | Return | Description |
|---|---|---|
| `health_check()` | `dict \| None` | Check if agent is alive |
| `wait_ready(timeout, interval)` | `bool` | Wait until agent is ready |
| `run_script(script, args, timeout)` | `RemoteResult` | Run a Python script |
| `run_bat(path, args, timeout)` | `RemoteResult` | Run a .bat file |
| `run_command(command, timeout)` | `RemoteResult` | Run a shell command |
| `screenshot(name, evidence)` | `bytes \| None` | Capture remote desktop |
| `list_scripts()` | `list[str]` | List available scripts |

### RemoteAgentPool (Multi-VM)

```python
from sphere_e2e_test_framework import RemoteAgentPool

pool = RemoteAgentPool.from_config(config["remote_agents"])
```

| Method | Return | Description |
|---|---|---|
| `pool["name"]` | `RemoteTrigger` | Get agent by name |
| `pool.get("name")` | `RemoteTrigger \| None` | Get agent (returns None if missing) |
| `pool.names` | `list[str]` | List all agent names |
| `pool.wait_all_ready(timeout)` | `dict[str, bool]` | Wait for all agents (parallel) |
| `pool.health_check_all()` | `dict[str, dict]` | Health check all agents |
| `len(pool)` | `int` | Number of agents |
| `"name" in pool` | `bool` | Check if agent exists |

### RemoteResult

```python
result = trigger.run_script("setup.py")
result.ok           # True if status == "ok"
result.status       # "ok" or "error"
result.output       # stdout from the command
result.stderr       # stderr from the command
result.return_code  # Process exit code (0 = success)
result.duration     # Execution time in seconds
result.message      # Error message (if failed)
bool(result)        # Same as result.ok
```

---

## Troubleshooting

### Agent not reachable from local VM

```
Remote agent not reachable at http://10.66.1.10:5050
```

1. Verify agent is running: `curl http://10.66.1.10:5050/health`
2. Check firewall: `netsh advfirewall firewall show rule name="RemoteAgent"`
3. Check port is listening: `netstat -an | findstr 5050`
4. Check connectivity: `ping 10.66.1.10`

### App not visible on desktop

The agent must be started in an **interactive desktop session**:
- Log into the remote VM via RDP
- Open Command Prompt / PowerShell
- Run `python agent.py` from there

**Do NOT** start the agent via:
- WinRM (`winrs`, `Invoke-Command`)
- SSH service
- Windows Service / Task Scheduler (runs in Session 0)

### Script timeout

Increase the timeout:

```python
result = trigger.run_script("long_setup.py", timeout=300)
```

Or on the agent side:

```powershell
python agent.py --timeout 300
```

### Auth error (401 Unauthorized)

Ensure the token matches on both sides:

```powershell
# Agent
python agent.py --auth-token mysecret

# Client
trigger = RemoteTrigger(host="10.66.1.10", auth_token="mysecret")
```

---

## Security Notes

- The agent is designed for **internal networks only** — do not expose to the internet
- Use `--auth-token` for basic authentication
- The agent can execute **any command** on the VM — restrict network access accordingly
- For production environments, consider HTTPS via a reverse proxy (e.g. nginx)
