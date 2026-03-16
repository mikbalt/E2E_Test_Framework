"""
Console Runner - Execute and validate console/CLI based tests.

Wraps subprocess execution with logging, output capture, and evidence.
Designed for PKCS#11 tools (Golang, Java, C++) and similar CLI programs.

Usage:
    runner = ConsoleRunner()
    result = runner.run("pkcs11-tool.exe", ["--list-slots"], timeout=30)
    assert result.returncode == 0
    assert "Slot 0" in result.stdout
"""

import logging
import os
import platform
import subprocess
import time

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def resolve_platform_config(tool_config):
    """
    Resolve platform-specific values from a tool config dict.

    Looks for keys like 'command_windows'/'command_linux' and returns
    the appropriate value for the current OS. Falls back to 'command' if
    no platform-specific key exists.

    Returns:
        dict with resolved 'command' and 'working_dir' keys.
    """
    suffix = "windows" if IS_WINDOWS else "linux"
    resolved = dict(tool_config)

    for key in ("command", "working_dir", "log_path", "log_dir", "gtest_xml"):
        platform_key = f"{key}_{suffix}"
        if platform_key in tool_config:
            resolved[key] = tool_config[platform_key]
        elif key not in resolved:
            resolved[key] = None

    return resolved


class CommandResult:
    """Result of a console command execution."""

    def __init__(self, command, returncode, stdout, stderr, duration, timed_out=False):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.timed_out = timed_out

    @property
    def success(self):
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self):
        """Combined stdout + stderr."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)

    def assert_success(self, message=None):
        """Assert command completed successfully."""
        if not self.success:
            error_msg = message or f"Command failed: {self.command}"
            error_msg += f"\nReturn code: {self.returncode}"
            if self.stderr:
                error_msg += f"\nStderr: {self.stderr}"
            if self.timed_out:
                error_msg += "\n(Command timed out)"
            raise AssertionError(error_msg)

    def assert_output_contains(self, expected, case_sensitive=True):
        """Assert output contains expected string."""
        output = self.output
        check = expected
        if not case_sensitive:
            output = output.lower()
            check = expected.lower()

        if check not in output:
            raise AssertionError(
                f"Expected '{expected}' in output.\n"
                f"Actual output:\n{self.output}"
            )

    def assert_output_not_contains(self, unexpected, case_sensitive=True):
        """Assert output does NOT contain unexpected string."""
        output = self.output
        check = unexpected
        if not case_sensitive:
            output = output.lower()
            check = unexpected.lower()

        if check in output:
            raise AssertionError(
                f"Unexpected '{unexpected}' found in output.\n"
                f"Actual output:\n{self.output}"
            )

    def __repr__(self):
        status = "OK" if self.success else f"FAIL(rc={self.returncode})"
        return f"CommandResult({status}, {self.duration:.2f}s)"


class ConsoleRunner:
    """Execute console commands with full evidence capture."""

    def __init__(self, working_dir=None, env_vars=None):
        """
        Args:
            working_dir: Default working directory for commands.
            env_vars: Additional environment variables (merged with OS env).
        """
        self.working_dir = working_dir
        self.env = os.environ.copy()
        if env_vars:
            self.env.update(env_vars)

    def run(self, command, args=None, timeout=60, working_dir=None, env_vars=None,
            input_text=None):
        """
        Execute a console command and capture output.

        Args:
            command: Executable path or name.
            args: List of command arguments.
            timeout: Timeout in seconds.
            working_dir: Override working directory.
            env_vars: Override environment variables.
            input_text: Text to pipe to stdin.

        Returns:
            CommandResult with stdout, stderr, returncode, duration.
        """
        cmd_list = [command]
        if args:
            cmd_list.extend(args)

        cmd_str = " ".join(cmd_list)
        cwd = working_dir or self.working_dir
        env = self.env.copy()
        if env_vars:
            env.update(env_vars)

        logger.info(f"Running: {cmd_str}")
        if cwd:
            logger.info(f"  Working dir: {cwd}")

        start_time = time.time()
        timed_out = False

        try:
            proc = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
                input=input_text,
            )
            duration = time.time() - start_time

            result = CommandResult(
                command=cmd_str,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            result = CommandResult(
                command=cmd_str,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                duration=duration,
                timed_out=True,
            )

        except FileNotFoundError:
            duration = time.time() - start_time
            result = CommandResult(
                command=cmd_str,
                returncode=-1,
                stdout="",
                stderr=f"Command not found: {command}",
                duration=duration,
            )

        logger.info(f"  Result: {result}")
        if result.stdout:
            for line in result.stdout.strip().split("\n")[:20]:
                logger.debug(f"  stdout: {line}")
        if result.stderr:
            for line in result.stderr.strip().split("\n")[:10]:
                logger.warning(f"  stderr: {line}")

        return result

    def run_script(self, script_path, args=None, **kwargs):
        """Run a script file (batch, shell, etc.)."""
        if script_path.endswith((".bat", ".cmd")):
            return self.run("cmd", ["/c", script_path] + (args or []), **kwargs)
        elif script_path.endswith(".ps1"):
            return self.run(
                "powershell",
                ["-ExecutionPolicy", "Bypass", "-File", script_path] + (args or []),
                **kwargs,
            )
        else:
            return self.run(script_path, args, **kwargs)

    def run_java(self, jar_path=None, class_name=None, args=None,
                 classpath=None, **kwargs):
        """Run a Java program."""
        cmd_args = []
        if classpath:
            cmd_args.extend(["-cp", classpath])
        if jar_path:
            cmd_args.extend(["-jar", jar_path])
        elif class_name:
            cmd_args.append(class_name)
        if args:
            cmd_args.extend(args)

        return self.run("java", cmd_args, **kwargs)

    def run_go(self, binary_path, args=None, **kwargs):
        """Run a Go compiled binary."""
        return self.run(binary_path, args, **kwargs)

    def run_make(self, target=None, makefile_dir=None, args=None, **kwargs):
        """
        Run a Makefile target.

        Args:
            target: Make target (e.g., 'test', 'build', 'clean'). None = default target.
            makefile_dir: Directory containing the Makefile.
            args: Additional make arguments.
        """
        cmd_args = []
        if target:
            cmd_args.append(target)
        if args:
            cmd_args.extend(args)

        make_cmd = "make"
        if IS_WINDOWS:
            # Try mingw32-make or nmake on Windows
            make_cmd = "mingw32-make"

        return self.run(make_cmd, cmd_args, working_dir=makefile_dir, **kwargs)

    def run_cmake_build(self, build_dir, config="Release", target=None, **kwargs):
        """
        Run cmake --build.

        Args:
            build_dir: Path to the CMake build directory.
            config: Build configuration (Release, Debug, etc.).
            target: Specific target to build.
        """
        cmd_args = ["--build", build_dir, "--config", config]
        if target:
            cmd_args.extend(["--target", target])

        return self.run("cmake", cmd_args, **kwargs)

    def run_executable(self, exe_path, args=None, **kwargs):
        """
        Run any compiled executable (C++, Go, Rust, etc.).

        Convenience wrapper that handles platform differences for
        executable paths (adds .exe on Windows if missing).

        Args:
            exe_path: Path to the executable.
            args: Command-line arguments.
        """
        if IS_WINDOWS and not exe_path.endswith(".exe"):
            # Check if .exe version exists
            if os.path.exists(exe_path + ".exe"):
                exe_path = exe_path + ".exe"

        return self.run(exe_path, args, **kwargs)
