import os
import yaml
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigValidator:
    """
    Validate YAML configuration against a schema class.
    Also attaches validation evidence.

    Features:
    - Recursive schema validation
    - Type checking
    - Required field enforcement
    - Allowed value validation
    - Evidence attachment (Allure/custom)
    """

    def __init__(self, schema_class, evidence=None):
        """
        Args:
            schema_class: Class that implements get_schema()
            evidence: Evidence collector (optional)
        """
        self.schema = schema_class.get_schema()
        self.evidence = evidence

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def validate(self, config_path):
        """
        Load and validate YAML config file.

        Args:
            config_path (str): Path to YAML file

        Returns:
            dict: Parsed and validated config

        Raises:
            ConfigValidationError
        """
        logger.info(f"Validating config: {config_path}")
        config = self._load_yaml(config_path)
        self._validate_section(config, self.schema)
        self._attach_success(config_path, config)

        return config

    # -------------------------------------------------
    # YAML Loader
    # -------------------------------------------------
    def _load_yaml(self, path):
        """Load YAML file safely."""
        if not os.path.exists(path):
            self._fail(f"Config file not found: {path}")

        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self._fail(f"Invalid YAML format: {e}")

    # -------------------------------------------------
    # Schema Validation (Recursive)
    # -------------------------------------------------
    def _validate_section(self, data, schema, parent=""):
        """
        Recursively validate config against schema.

        Args:
            data (dict): YAML data
            schema (dict): Schema definition
            parent (str): Parent key (for error message)
        """
        for field, rules in schema.items():

            full_key = f"{parent}.{field}" if parent else field
            value = data.get(field)

            # Nested object (no "type" means nested schema)
            if isinstance(rules, dict) and "type" not in rules:
                if field not in data:
                    continue
                if not isinstance(value, dict):
                    self._fail(f"{full_key} must be a dict")
                self._validate_section(value, rules, full_key)
                continue

            # Required field
            if rules.get("required") and value is None:
                self._fail(f"Missing required field: {full_key}")

            if value is None:
                continue

            # Type validation
            expected_type = self._resolve_type(rules.get("type"))
            if expected_type and not isinstance(value, expected_type):
                self._fail(
                    f"{full_key} must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

            # Allowed values validation
            if "allowed" in rules:
                if value not in rules["allowed"]:
                    self._fail(
                        f"{full_key} must be one of {rules['allowed']}, got '{value}'"
                    )

    # -------------------------------------------------
    # Evidence (Success)
    # -------------------------------------------------
    def _attach_success(self, config_path, config):
        """Attach successful validation evidence."""
        if not self.evidence:
            return

        try:
            import json

            content = {
                "config_path": config_path,
                "status": "PASSED",
                "timestamp": datetime.now().isoformat(),
                "config": config
            }

            self.evidence.attach_text(
                name="config_validation",
                content=json.dumps(content, indent=2)
            )

        except Exception as e:
            logger.warning(f"Failed to attach success evidence: {e}")

    # -------------------------------------------------
    # Failure Handling
    # -------------------------------------------------
    def _fail(self, message):
        """Handle validation failure and attach evidence."""
        logger.error(message)

        if self.evidence:
            try:
                self.evidence.attach_text(
                    name="config_validation_error",
                    content=message
                )
            except Exception:
                pass

        raise ConfigValidationError(message)

    def _resolve_type(self, type_def):
        """Convert string type to Python type if needed."""
        if isinstance(type_def, type):
            return type_def

        type_map = {
            "str": str,
            "int": int,
            "bool": bool,
            "list": list,
            "dict": dict,
            "float": float
        }

        if isinstance(type_def, str):
            return type_map.get(type_def)

        return None