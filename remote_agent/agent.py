"""
Remote Agent - Lightweight HTTP server for triggering automation on remote VMs.

Run this script on the remote Windows VM in an INTERACTIVE desktop session
(not via WinRM/SSH service) so that launched apps are visible and UI automation works.

Usage:
    python agent.py
    python agent.py --port 5050 --scripts-dir C:\\automation\\scripts
    python agent.py --auth-token mysecrettoken

Endpoints:
    GET  /health          - Health check
    POST /run-script      - Run a Python script
    POST /run-bat         - Run a .bat file
    POST /run-command     - Run an arbitrary shell command
    GET  /screenshot      - Capture desktop screenshot (PNG)
    GET  /list-scripts    - List available scripts in scripts directory
"""

import argparse
import hmac
import io
import json
import logging
import os
import platform
import subprocess
import sys
import time
from functools import wraps

from flask import Flask, request, jsonify, send_file, Response

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("remote_agent")

# --- Global config (set via CLI args) ---
CONFIG = {
    "scripts_dir": ".",
    "auth_token": "",
    "default_timeout": 120,
    "bat_dir": "",
}


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------
def require_auth(f):
    """Token-based authentication decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if CONFIG["auth_token"]:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not hmac.compare_digest(token, CONFIG["auth_token"]):
                return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
@require_auth
def health():
    """Health check - returns agent info."""
    return jsonify({
        "status": "ok",
        "hostname": platform.node(),
        "pid": os.getpid(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "scripts_dir": os.path.abspath(CONFIG["scripts_dir"]),
        "cwd": os.getcwd(),
    })


@app.route("/run-script", methods=["POST"])
@require_auth
def run_script():
    """Run a Python script from the scripts directory.

    Request JSON:
        script  (str):  Script filename (relative to scripts_dir)
        args    (list): Optional command-line arguments
        timeout (int):  Optional timeout in seconds (default: 120)

    Response JSON:
        status, output, stderr, return_code, duration
    """
    data = request.get_json(force=True)
    script = data.get("script", "")
    args = data.get("args", [])
    timeout = data.get("timeout", CONFIG["default_timeout"])

    if not script:
        return jsonify({"status": "error", "message": "Missing 'script' parameter"}), 400

    script_path = os.path.realpath(os.path.join(CONFIG["scripts_dir"], script))
    scripts_dir_real = os.path.realpath(CONFIG["scripts_dir"])
    if not script_path.startswith(scripts_dir_real + os.sep) and script_path != scripts_dir_real:
        return jsonify({
            "status": "error",
            "message": "Path traversal denied",
        }), 403
    if not os.path.isfile(script_path):
        return jsonify({
            "status": "error",
            "message": f"Script not found: {script_path}",
        }), 404

    cmd = [sys.executable, script_path] + [str(a) for a in args]
    logger.info(f"Running script: {' '.join(cmd)} (timeout={timeout}s)")

    return _run_subprocess(cmd, timeout, cwd=CONFIG["scripts_dir"])


@app.route("/run-bat", methods=["POST"])
@require_auth
def run_bat():
    """Run a .bat / .cmd file.

    Request JSON:
        path    (str):  Full path to .bat file
        args    (list): Optional arguments
        timeout (int):  Optional timeout in seconds
    """
    data = request.get_json(force=True)
    bat_path = data.get("path", "")
    args = data.get("args", [])
    timeout = data.get("timeout", CONFIG["default_timeout"])

    if not bat_path:
        return jsonify({"status": "error", "message": "Missing 'path' parameter"}), 400

    # Validate path stays within allowed bat directory
    if CONFIG.get("bat_dir"):
        bat_real = os.path.realpath(bat_path)
        bat_dir_real = os.path.realpath(CONFIG["bat_dir"])
        if not bat_real.startswith(bat_dir_real + os.sep) and bat_real != bat_dir_real:
            return jsonify({
                "status": "error",
                "message": f"Path not allowed. Must be within: {CONFIG['bat_dir']}",
            }), 403

    if not os.path.isfile(bat_path):
        return jsonify({
            "status": "error",
            "message": f"Bat file not found: {bat_path}",
        }), 404

    cmd = ["cmd.exe", "/c", bat_path] + [str(a) for a in args]
    cwd = os.path.dirname(bat_path) or None
    logger.info(f"Running bat: {bat_path} (timeout={timeout}s)")

    return _run_subprocess(cmd, timeout, cwd=cwd)


@app.route("/run-command", methods=["POST"])
@require_auth
def run_command():
    """Run an arbitrary shell command.

    Request JSON:
        command (str):  Command string to execute
        timeout (int):  Optional timeout in seconds
    """
    data = request.get_json(force=True)
    command = data.get("command", "")
    timeout = data.get("timeout", CONFIG["default_timeout"])

    if not command:
        return jsonify({"status": "error", "message": "Missing 'command' parameter"}), 400

    logger.info(f"Running command: {command} (timeout={timeout}s)")

    return _run_subprocess(command, timeout, shell=True)


@app.route("/screenshot", methods=["GET"])
@require_auth
def screenshot():
    """Capture desktop screenshot and return as PNG."""
    try:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            monitor = sct.monitors[0]  # Full virtual screen
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            logger.info("Desktop screenshot captured")
            return send_file(buf, mimetype="image/png", download_name="screenshot.png")

    except ImportError as e:
        return jsonify({
            "status": "error",
            "message": f"Screenshot dependencies missing: {e}. Install: pip install mss pillow",
        }), 500
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/list-scripts", methods=["GET"])
@require_auth
def list_scripts():
    """List available Python scripts in the scripts directory."""
    scripts_dir = CONFIG["scripts_dir"]
    if not os.path.isdir(scripts_dir):
        return jsonify({"status": "error", "message": f"Scripts dir not found: {scripts_dir}"}), 404

    scripts = []
    for f in sorted(os.listdir(scripts_dir)):
        if f.endswith(".py") and not f.startswith("_"):
            scripts.append(f)

    return jsonify({"status": "ok", "scripts": scripts, "scripts_dir": os.path.abspath(scripts_dir)})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run_subprocess(cmd, timeout, cwd=None, shell=False):
    """Execute a subprocess and return JSON result."""
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            shell=shell,
        )
        duration = round(time.time() - start, 2)

        status = "ok" if result.returncode == 0 else "error"
        log_fn = logger.info if status == "ok" else logger.warning
        log_fn(f"Process finished: return_code={result.returncode}, duration={duration}s")

        if result.stderr:
            logger.warning(f"stderr: {result.stderr[:500]}")

        return jsonify({
            "status": status,
            "output": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "duration": duration,
        })

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 2)
        logger.error(f"Process timed out after {timeout}s")
        return jsonify({
            "status": "error",
            "message": f"Timed out after {timeout}s",
            "output": "",
            "stderr": "",
            "return_code": -1,
            "duration": duration,
        }), 504

    except Exception as e:
        duration = round(time.time() - start, 2)
        logger.error(f"Process execution failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "output": "",
            "stderr": "",
            "return_code": -1,
            "duration": duration,
        }), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Remote Agent - HTTP server for triggering automation on remote VMs",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5050, help="Port (default: 5050)")
    parser.add_argument("--scripts-dir", default=".", help="Directory containing automation scripts")
    parser.add_argument("--auth-token", default="", help="Auth token for security (required unless --no-auth)")
    parser.add_argument("--no-auth", action="store_true", help="Explicitly disable authentication (not recommended)")
    parser.add_argument("--bat-dir", default="", help="Restrict /run-bat to files within this directory")
    parser.add_argument("--timeout", type=int, default=120, help="Default command timeout in seconds")
    args = parser.parse_args()

    # Require --auth-token OR explicit --no-auth
    if not args.auth_token and not args.no_auth:
        parser.error("--auth-token is required. Use --no-auth to explicitly disable authentication.")

    CONFIG["scripts_dir"] = os.path.abspath(args.scripts_dir)
    CONFIG["auth_token"] = args.auth_token
    CONFIG["default_timeout"] = args.timeout
    CONFIG["bat_dir"] = os.path.abspath(args.bat_dir) if args.bat_dir else ""

    logger.info("=" * 60)
    logger.info("Remote Agent Starting")
    logger.info(f"  Host:        {args.host}:{args.port}")
    logger.info(f"  Scripts dir: {CONFIG['scripts_dir']}")
    logger.info(f"  Bat dir:     {CONFIG['bat_dir'] or '(unrestricted)'}")
    logger.info(f"  Auth:        {'enabled' if args.auth_token else 'DISABLED (--no-auth)'}")
    logger.info(f"  Timeout:     {args.timeout}s")
    logger.info(f"  Hostname:    {platform.node()}")
    logger.info(f"  Python:      {sys.version.split()[0]}")
    logger.info("=" * 60)

    if not args.auth_token:
        logger.warning("Authentication is DISABLED. Anyone who can reach this port can execute commands.")

    logger.warning(
        "Flask dev server is not suitable for production. "
        "Consider using Waitress: waitress-serve --host %s --port %d remote_agent.agent:app",
        args.host, args.port,
    )

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
