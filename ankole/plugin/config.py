"""Configuration loading and environment variable overrides."""

import logging
import os
import re
import threading

import yaml
from dotenv import load_dotenv

# Load .env file from project root (auto-loads TCMS credentials etc.)
load_dotenv()

logger = logging.getLogger(__name__)

_CONFIG_CACHE = None
_CONFIG_LOCK = threading.Lock()

_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


def load_config(config_path=None):
    """
    Load settings.yaml from the consumer repo.
    Searches: config/settings.yaml (relative to cwd), then env
    ANKOLE_CONFIG_PATH.
    After loading, applies environment variable overrides (see _apply_env_overrides).

    Thread-safe: uses a lock to prevent race conditions when multiple
    pytest-xdist workers load config simultaneously.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    with _CONFIG_LOCK:
        # Double-check after acquiring lock
        if _CONFIG_CACHE is not None:
            return _CONFIG_CACHE

        search_paths = [
            config_path,
            os.environ.get("ANKOLE_CONFIG_PATH"),
            os.path.join(os.getcwd(), "config", "settings.yaml"),
            os.path.join(os.getcwd(), "settings.yaml"),
        ]

        for path in search_paths:
            if path and os.path.exists(path):
                with open(path, "r") as f:
                    _CONFIG_CACHE = yaml.safe_load(f) or {}
                    logger.info(f"Config loaded from: {path}")
                    _CONFIG_CACHE = _resolve_placeholders(_CONFIG_CACHE)
                    _apply_env_overrides(_CONFIG_CACHE)
                    _validate_config(_CONFIG_CACHE)
                    return _CONFIG_CACHE

        logger.warning("No settings.yaml found, using defaults")
        _CONFIG_CACHE = {}
        _apply_env_overrides(_CONFIG_CACHE)
        return _CONFIG_CACHE


def _validate_config(cfg):
    """Validate critical config paths are not empty after placeholder resolution.

    Warns (does not raise) when required values are empty, so tests can still
    run in environments that only need a subset of the config.
    """
    critical_paths = []
    for dotted_path in critical_paths:
        obj = cfg
        for key in dotted_path.split("."):
            if isinstance(obj, dict):
                obj = obj.get(key)
            else:
                obj = None
                break
        if obj is not None and isinstance(obj, str) and not obj.strip():
            logger.warning(
                f"Config value at '{dotted_path}' is empty — "
                f"check that the corresponding env var is set"
            )


def _resolve_placeholders(obj):
    """
    Walk a nested dict/list and replace all '${VAR}' placeholder strings
    with the corresponding environment variable value (empty string if unset).

    This ensures no literal '${...}' strings survive in the config dict,
    regardless of whether _apply_env_overrides handles that specific key.
    """
    if isinstance(obj, dict):
        return {k: _resolve_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_placeholders(item) for item in obj]
    if isinstance(obj, str) and "${" in obj:
        def _replace(m):
            var_name = m.group(1)
            value = os.environ.get(var_name)
            if value is None:
                logger.warning(f"Unset env var placeholder: ${{{var_name}}} (resolved to empty string)")
                return ""
            return value
        return _PLACEHOLDER_RE.sub(_replace, obj)
    return obj


def _set_nested(cfg, dotted_path, value):
    """Set a value in a nested dict using a dotted key path.

    Example: _set_nested(cfg, "apps.e_admin.connection.ip", "10.0.0.1")
    creates intermediate dicts as needed via setdefault.
    """
    keys = dotted_path.split(".")
    for key in keys[:-1]:
        cfg = cfg.setdefault(key, {})
    cfg[keys[-1]] = value


_TYPE_CASTERS = {
    "int": int,
    "bool": lambda v: v.lower() in ("1", "true", "yes"),
}


def _parse_field_spec(field_spec):
    """Parse a field spec like ``"host"`` or ``"port:int?type=tcp"``.

    Returns:
        (field_name, type_hint_or_None, condition_dict_or_None)
    """
    condition = None
    if "?" in field_spec:
        field_spec, cond_str = field_spec.split("?", 1)
        condition = {}
        for pair in cond_str.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                condition[k.strip()] = v.strip()

    type_hint = None
    if ":" in field_spec:
        field_name, type_hint = field_spec.rsplit(":", 1)
    else:
        field_name = field_spec

    return field_name, type_hint, condition


def _check_condition(item, condition):
    """Check whether a dict item matches all key=value conditions."""
    for key, expected in condition.items():
        if str(item.get(key, "")) != expected:
            return False
    return True


def _apply_env_overrides(cfg):
    """
    Apply environment variable overrides using two data-driven sections
    from settings.yaml:

    1. ``env_overrides`` — scalar overrides at dotted config paths::

        env_overrides:
          HSM_IP: "apps.e_admin.connection.ip"
          KIWI_PLAN_ID: "kiwi_tcms.plan_id:int"

    2. ``env_overrides_list`` — overrides applied to every item in a
       list at a dotted path, with optional conditions::

        env_overrides_list:
          health_check.checks:
            HSM_IP: "host"
            HSM_PORT: "port:int?type=tcp"

    The dotted path supports an optional ``:type`` suffix (int, bool).
    List overrides support ``?key=value`` conditions (applied per item).
    """
    # --- Data-driven scalar overrides ---
    overrides = cfg.pop("env_overrides", None) or {}
    for env_var, path_spec in overrides.items():
        raw = os.environ.get(env_var, "").strip()
        if not raw:
            continue

        # Parse optional type hint (e.g. "kiwi_tcms.plan_id:int")
        if ":" in path_spec:
            dotted_path, type_hint = path_spec.rsplit(":", 1)
            caster = _TYPE_CASTERS.get(type_hint)
            if caster:
                raw = caster(raw)
        else:
            dotted_path = path_spec

        _set_nested(cfg, dotted_path, raw)

    # --- Data-driven list overrides ---
    list_overrides = cfg.pop("env_overrides_list", None) or {}
    for list_path, field_map in list_overrides.items():
        # Navigate to the list
        items = cfg
        for key in list_path.split("."):
            if isinstance(items, dict):
                items = items.get(key, {})
            else:
                items = {}
                break
        if not isinstance(items, list):
            continue

        for item in items:
            for env_var, field_spec in field_map.items():
                raw = os.environ.get(env_var, "").strip()
                if not raw:
                    continue
                field_name, type_hint, condition = _parse_field_spec(field_spec)
                if condition and not _check_condition(item, condition):
                    continue
                caster = _TYPE_CASTERS.get(type_hint) if type_hint else None
                item[field_name] = caster(raw) if caster else raw
