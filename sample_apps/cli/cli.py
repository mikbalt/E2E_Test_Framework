"""
Ankole Framework - Click CLI Tool

A command-line interface that communicates with the Ankole REST API.
Authentication tokens are persisted to ~/.ankole-cli-token.
"""

import json
import os
import sys
from pathlib import Path

import click
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_API_URL = os.getenv("ANKOLE_API_URL", "http://localhost:8000")
TOKEN_FILE = Path.home() / ".ankole-cli-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api_url() -> str:
    return DEFAULT_API_URL.rstrip("/")


def _save_token(token: str) -> None:
    TOKEN_FILE.write_text(token, encoding="utf-8")


def _load_token() -> str | None:
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


def _clear_token() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def _auth_headers() -> dict:
    token = _load_token()
    if not token:
        click.echo("Error: Not authenticated. Run 'ankole auth login' first.", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {token}"}


def _handle_response(resp: requests.Response, success_msg: str | None = None):
    """Print JSON response or error details."""
    if resp.status_code in (200, 201):
        try:
            data = resp.json()
            click.echo(json.dumps(data, indent=2, default=str))
        except ValueError:
            click.echo(resp.text)
        if success_msg:
            click.echo(success_msg)
    elif resp.status_code == 204:
        click.echo(success_msg or "Done.")
    else:
        click.echo(f"Error {resp.status_code}: {resp.text}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="2.0.0", prog_name="ankole")
def cli():
    """Ankole Framework CLI - manage members, roles, projects, and more."""
    pass


# ===================================================================
# Auth commands
# ===================================================================

@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command()
@click.option("--username", "-u", prompt=True, help="Username")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Password")
def login(username: str, password: str):
    """Log in and store the access token."""
    resp = requests.post(
        f"{_api_url()}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        _save_token(data["access_token"])
        click.echo(f"Logged in as '{username}'. Token saved to {TOKEN_FILE}")
    else:
        click.echo(f"Login failed: {resp.text}", err=True)
        sys.exit(1)


@auth.command()
def logout():
    """Log out and remove the stored token."""
    token = _load_token()
    if token:
        # Attempt to call the server logout endpoint (best-effort)
        try:
            requests.post(
                f"{_api_url()}/api/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
        except requests.RequestException:
            pass
    _clear_token()
    click.echo("Logged out. Token removed.")


# ===================================================================
# Members commands
# ===================================================================

@cli.group()
def members():
    """Manage members."""
    pass


@members.command("list")
def members_list():
    """List all members."""
    resp = requests.get(
        f"{_api_url()}/api/members",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp)


@members.command("create")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--email", "-e", required=True, help="Email address")
@click.option("--password", "-p", required=True, help="Password")
@click.option("--role-id", "-r", required=True, type=int, help="Role ID")
def members_create(username: str, email: str, password: str, role_id: int):
    """Create a new member."""
    resp = requests.post(
        f"{_api_url()}/api/members",
        headers=_auth_headers(),
        json={
            "username": username,
            "email": email,
            "password": password,
            "role_id": role_id,
        },
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Member '{username}' created.")


@members.command("get")
@click.argument("member_id", type=int)
def members_get(member_id: int):
    """Get a member by ID."""
    resp = requests.get(
        f"{_api_url()}/api/members/{member_id}",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp)


@members.command("update")
@click.argument("member_id", type=int)
@click.option("--username", "-u", default=None, help="New username")
@click.option("--email", "-e", default=None, help="New email")
@click.option("--password", "-p", default=None, help="New password")
@click.option("--role-id", "-r", default=None, type=int, help="New role ID")
def members_update(member_id: int, username, email, password, role_id):
    """Update a member by ID."""
    payload = {}
    if username is not None:
        payload["username"] = username
    if email is not None:
        payload["email"] = email
    if password is not None:
        payload["password"] = password
    if role_id is not None:
        payload["role_id"] = role_id

    if not payload:
        click.echo("No fields to update. Use --username, --email, --password, or --role-id.")
        return

    resp = requests.put(
        f"{_api_url()}/api/members/{member_id}",
        headers=_auth_headers(),
        json=payload,
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Member {member_id} updated.")


@members.command("delete")
@click.argument("member_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this member?")
def members_delete(member_id: int):
    """Delete a member by ID."""
    resp = requests.delete(
        f"{_api_url()}/api/members/{member_id}",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Member {member_id} deleted.")


@members.command("suspend")
@click.argument("member_id", type=int)
def members_suspend(member_id: int):
    """Suspend a member (set is_active=False)."""
    resp = requests.post(
        f"{_api_url()}/api/members/{member_id}/suspend",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Member {member_id} suspended.")


@members.command("reactivate")
@click.argument("member_id", type=int)
def members_reactivate(member_id: int):
    """Reactivate a suspended member."""
    resp = requests.post(
        f"{_api_url()}/api/members/{member_id}/reactivate",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Member {member_id} reactivated.")


# ===================================================================
# Projects commands
# ===================================================================

@cli.group()
def projects():
    """Manage projects."""
    pass


@projects.command("list")
def projects_list():
    """List all projects."""
    resp = requests.get(
        f"{_api_url()}/api/projects",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp)


@projects.command("create")
@click.option("--name", "-n", required=True, help="Project name")
@click.option("--description", "-d", default=None, help="Project description")
@click.option("--required-approvals", "-a", default=3, type=int, help="Number of required approvals")
def projects_create(name: str, description: str | None, required_approvals: int):
    """Create a new project."""
    payload = {
        "name": name,
        "required_approvals": required_approvals,
    }
    if description is not None:
        payload["description"] = description

    resp = requests.post(
        f"{_api_url()}/api/projects",
        headers=_auth_headers(),
        json=payload,
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Project '{name}' created.")


@projects.command("get")
@click.argument("project_id", type=int)
def projects_get(project_id: int):
    """Get a project by ID (includes approvals)."""
    resp = requests.get(
        f"{_api_url()}/api/projects/{project_id}",
        headers=_auth_headers(),
        timeout=10,
    )
    _handle_response(resp)


@projects.command("approve")
@click.argument("project_id", type=int)
@click.option("--comment", "-c", default=None, help="Approval comment")
def projects_approve(project_id: int, comment: str | None):
    """Approve the current step of a project."""
    payload = {}
    if comment is not None:
        payload["comment"] = comment

    resp = requests.post(
        f"{_api_url()}/api/projects/{project_id}/approve",
        headers=_auth_headers(),
        json=payload,
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Project {project_id} approved.")


@projects.command("reject")
@click.argument("project_id", type=int)
@click.option("--comment", "-c", default=None, help="Rejection comment")
def projects_reject(project_id: int, comment: str | None):
    """Reject a project."""
    payload = {}
    if comment is not None:
        payload["comment"] = comment

    resp = requests.post(
        f"{_api_url()}/api/projects/{project_id}/reject",
        headers=_auth_headers(),
        json=payload,
        timeout=10,
    )
    _handle_response(resp, success_msg=f"Project {project_id} rejected.")


# ===================================================================
# System commands
# ===================================================================

@cli.group()
def system():
    """System administration commands."""
    pass


@system.command("health")
def system_health():
    """Check API health (no auth required)."""
    try:
        resp = requests.get(f"{_api_url()}/api/health", timeout=10)
        _handle_response(resp)
    except requests.ConnectionError:
        click.echo(f"Error: Cannot connect to API at {_api_url()}", err=True)
        sys.exit(1)


@system.command("seed")
@click.confirmation_option(prompt="This will re-seed seed users. Continue?")
def system_seed():
    """
    Re-seed default users by calling the API login endpoint for each seed user.
    This verifies that seed accounts are functional.
    """
    seed_users = [
        ("admin", "admin123"),
        ("approver1", "approver123"),
        ("approver2", "approver123"),
        ("approver3", "approver123"),
        ("member1", "member123"),
        ("member2", "member123"),
    ]
    for username, password in seed_users:
        try:
            resp = requests.post(
                f"{_api_url()}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                click.echo(f"  [OK]   {username}")
            else:
                click.echo(f"  [FAIL] {username}: {resp.status_code}")
        except requests.RequestException as exc:
            click.echo(f"  [ERR]  {username}: {exc}")
    click.echo("Seed verification complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
