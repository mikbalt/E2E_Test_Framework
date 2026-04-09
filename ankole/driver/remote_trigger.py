"""
Remote Trigger - Client for communicating with Remote Agents on other VMs.

Sends HTTP requests to Remote Agents running on remote Windows VMs to
trigger automation tasks: run scripts, bat files, commands, and capture
screenshots.

Single VM usage:
    trigger = RemoteTrigger(host="10.66.1.10", port=5050)
    trigger.wait_ready(timeout=30)
    result = trigger.run_script("setup_proxy.py")

Multi-VM usage:
    pool = RemoteAgentPool.from_config(config["remote_agents"])
    pool.wait_all_ready()
    pool["proxy_vm"].run_script("setup_proxy.py")
    pool["key_server_vm"].run_bat(r"C:\\Scripts\\prepare.bat")
"""

import logging
import os
import time

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class RemoteResult:
    """Result from a remote agent command execution."""

    def __init__(self, status, output="", stderr="", return_code=-1,
                 duration=0.0, message=""):
        self.status = status
        self.output = output
        self.stderr = stderr
        self.return_code = return_code
        self.duration = duration
        self.message = message
        self.ok = (status == "ok")

    def __repr__(self):
        return (
            f"RemoteResult(status={self.status!r}, "
            f"return_code={self.return_code}, "
            f"duration={self.duration}s)"
        )

    def __bool__(self):
        return self.ok


class RemoteTrigger:
    """Client for communicating with a Remote Agent on another VM.

    Args:
        host: IP or hostname of the remote VM.
        port: Port the Remote Agent is listening on (default: 5050).
        auth_token: Optional authentication token.
        timeout: Default HTTP request timeout in seconds.
    """

    def __init__(self, host, port=5050, auth_token=None, timeout=120):
        if not _HAS_REQUESTS:
            raise ImportError(
                "RemoteTrigger requires 'requests'. Install: pip install requests"
            )
        self._base_url = f"http://{host}:{port}"
        self._timeout = timeout
        self._session = requests.Session()
        if auth_token:
            self._session.headers["Authorization"] = f"Bearer {auth_token}"
        self._session.headers["Content-Type"] = "application/json"

        self.host = host
        self.port = port
        logger.info(f"RemoteTrigger initialized: {self._base_url}")

    def health_check(self):
        """Check if the remote agent is alive.

        Returns:
            dict with agent info if healthy, None if unreachable.
        """
        try:
            resp = self._session.get(f"{self._base_url}/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(
                    f"Remote agent healthy: {data.get('hostname', '?')} "
                    f"(Python {data.get('python', '?')})"
                )
                return data
        except requests.ConnectionError:
            logger.debug(f"Remote agent not reachable at {self._base_url}")
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
        return None

    def wait_ready(self, timeout=30, interval=2):
        """Wait until the remote agent is ready.

        Args:
            timeout: Max seconds to wait.
            interval: Seconds between retries.

        Returns:
            True if agent is ready, False if timed out.
        """
        logger.info(f"Waiting for remote agent at {self._base_url} ...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.health_check():
                logger.info("Remote agent is ready")
                return True
            time.sleep(interval)

        logger.error(f"Remote agent not ready after {timeout}s")
        return False

    def run_script(self, script, args=None, timeout=None):
        """Run a Python script on the remote VM.

        The script must be in the agent's scripts directory.

        Args:
            script: Script filename (e.g. "setup_proxy.py").
            args: Optional list of command-line arguments.
            timeout: Optional timeout override in seconds.

        Returns:
            RemoteResult with execution details.
        """
        payload = {"script": script}
        if args:
            payload["args"] = args
        if timeout:
            payload["timeout"] = timeout

        logger.info(f"Remote run-script: {script}")
        return self._post("/run-script", payload, timeout)

    def run_bat(self, path, args=None, timeout=None):
        """Run a .bat file on the remote VM.

        Args:
            path: Full path to the .bat file on the remote VM.
            args: Optional list of arguments.
            timeout: Optional timeout override in seconds.

        Returns:
            RemoteResult with execution details.
        """
        payload = {"path": path}
        if args:
            payload["args"] = args
        if timeout:
            payload["timeout"] = timeout

        logger.info(f"Remote run-bat: {path}")
        return self._post("/run-bat", payload, timeout)

    def run_command(self, command, timeout=None):
        """Run an arbitrary shell command on the remote VM.

        Args:
            command: Command string to execute.
            timeout: Optional timeout override in seconds.

        Returns:
            RemoteResult with execution details.
        """
        payload = {"command": command}
        if timeout:
            payload["timeout"] = timeout

        logger.info(f"Remote run-command: {command}")
        return self._post("/run-command", payload, timeout)

    def screenshot(self, name="remote_desktop", evidence=None):
        """Capture desktop screenshot from the remote VM.

        Args:
            name: Name for the screenshot file.
            evidence: Optional Evidence instance to save and attach to Allure.

        Returns:
            PNG bytes of the screenshot, or None on failure.
        """
        try:
            resp = self._session.get(
                f"{self._base_url}/screenshot",
                timeout=30,
            )
            if resp.status_code != 200:
                logger.warning(f"Remote screenshot failed: {resp.status_code}")
                return None

            png_bytes = resp.content
            logger.info(f"Remote screenshot captured: {name} ({len(png_bytes)} bytes)")

            # Save to evidence if provided
            if evidence and png_bytes:
                filepath = os.path.join(evidence.evidence_dir, f"{name}.png")
                with open(filepath, "wb") as f:
                    f.write(png_bytes)
                logger.info(f"Remote screenshot saved: {filepath}")

                # Attach to Allure
                try:
                    import allure
                    allure.attach(
                        png_bytes,
                        name=name,
                        attachment_type=allure.attachment_type.PNG,
                    )
                except ImportError:
                    pass

            return png_bytes

        except Exception as e:
            logger.error(f"Remote screenshot error: {e}")
            return None

    def list_scripts(self):
        """List available scripts on the remote agent.

        Returns:
            List of script filenames, or empty list on failure.
        """
        try:
            resp = self._session.get(
                f"{self._base_url}/list-scripts",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("scripts", [])
        except Exception as e:
            logger.error(f"List scripts failed: {e}")
        return []

    def _post(self, endpoint, payload, timeout=None):
        """Send POST request to the remote agent.

        Returns:
            RemoteResult instance.
        """
        http_timeout = (timeout or self._timeout) + 10  # buffer for HTTP overhead
        try:
            resp = self._session.post(
                f"{self._base_url}{endpoint}",
                json=payload,
                timeout=http_timeout,
            )
            data = resp.json()

            result = RemoteResult(
                status=data.get("status", "error"),
                output=data.get("output", ""),
                stderr=data.get("stderr", ""),
                return_code=data.get("return_code", -1),
                duration=data.get("duration", 0.0),
                message=data.get("message", ""),
            )

            log_fn = logger.info if result.ok else logger.warning
            log_fn(
                f"Remote {endpoint}: status={result.status}, "
                f"return_code={result.return_code}, "
                f"duration={result.duration}s"
            )

            if result.stderr:
                logger.debug(f"Remote stderr: {result.stderr[:300]}")

            return result

        except requests.Timeout:
            logger.error(f"Remote {endpoint} timed out after {http_timeout}s")
            return RemoteResult(
                status="error",
                message=f"HTTP request timed out after {http_timeout}s",
            )
        except requests.ConnectionError:
            logger.error(f"Cannot connect to remote agent at {self._base_url}")
            return RemoteResult(
                status="error",
                message=f"Connection refused: {self._base_url}",
            )
        except Exception as e:
            logger.error(f"Remote {endpoint} error: {e}")
            return RemoteResult(status="error", message=str(e))


class RemoteAgentPool:
    """Manage multiple RemoteTrigger instances for multi-VM automation.

    Access agents by name using dict-style syntax:
        pool["proxy_vm"].run_script("setup.py")
        pool["key_server_vm"].run_bat(r"C:\\Scripts\\keys.bat")

    Args:
        agents: Dict mapping agent names to RemoteTrigger instances.
    """

    def __init__(self, agents=None):
        self._agents = agents or {}

    @classmethod
    def from_config(cls, config):
        """Create pool from settings.yaml remote_agents config.

        Expected config structure:
            remote_agents:
              default_port: 5050
              default_timeout: 120
              agents:
                proxy_vm:
                  host: "10.66.1.10"
                  port: 5050
                  auth_token: ""
                key_server_vm:
                  host: "10.66.1.20"

        Args:
            config: Dict from settings.yaml remote_agents section.

        Returns:
            RemoteAgentPool instance with all configured agents.
        """
        default_port = config.get("default_port", 5050)
        default_timeout = config.get("default_timeout", 120)
        agents_cfg = config.get("agents", {})

        agents = {}
        for name, agent_cfg in agents_cfg.items():
            host = agent_cfg.get("host", "")
            if not host:
                logger.warning(f"Remote agent '{name}' has no host configured, skipping")
                continue

            trigger = RemoteTrigger(
                host=host,
                port=agent_cfg.get("port", default_port),
                auth_token=agent_cfg.get("auth_token") or None,
                timeout=agent_cfg.get("timeout", default_timeout),
            )
            trigger.name = name
            trigger.description = agent_cfg.get("description", "")
            agents[name] = trigger
            desc_suffix = f" ({trigger.description})" if trigger.description else ""
            logger.info(
                f"Remote agent '{name}' configured: {host}:{agent_cfg.get('port', default_port)}"
                f"{desc_suffix}"
            )

        return cls(agents)

    def __getitem__(self, name):
        """Get agent by name. Raises KeyError if not found."""
        if name not in self._agents:
            available = ", ".join(self._agents.keys()) or "(none)"
            raise KeyError(
                f"Remote agent '{name}' not found. Available: {available}"
            )
        return self._agents[name]

    def __contains__(self, name):
        return name in self._agents

    def __len__(self):
        return len(self._agents)

    def __iter__(self):
        return iter(self._agents)

    @property
    def names(self):
        """List of all agent names."""
        return list(self._agents.keys())

    def get(self, name, default=None):
        """Get agent by name, return default if not found."""
        return self._agents.get(name, default)

    def wait_all_ready(self, timeout=30, interval=2):
        """Wait until all agents are ready.

        Args:
            timeout: Max seconds to wait per agent.
            interval: Seconds between retries.

        Returns:
            Dict mapping agent names to ready status (True/False).
        """
        if not self._agents:
            logger.info("No remote agents configured, nothing to wait for")
            return {}

        from concurrent.futures import ThreadPoolExecutor

        results = {}

        def _check(name, trigger):
            ready = trigger.wait_ready(timeout=timeout, interval=interval)
            return name, ready

        with ThreadPoolExecutor(max_workers=len(self._agents)) as pool:
            futures = [
                pool.submit(_check, name, trigger)
                for name, trigger in self._agents.items()
            ]
            for future in futures:
                name, ready = future.result()
                results[name] = ready
                if not ready:
                    logger.warning(f"Remote agent '{name}' is not ready")

        ready_count = sum(1 for v in results.values() if v)
        logger.info(f"Remote agents ready: {ready_count}/{len(self._agents)}")
        return results

    def health_check_all(self):
        """Check health of all agents.

        Returns:
            Dict mapping agent names to health info (dict or None).
        """
        return {name: trigger.health_check() for name, trigger in self._agents.items()}
