"""Functional configuration loader for masking rules."""

import json
from pathlib import Path
from typing import Any, Dict, List

from app.exceptions import ConfigurationError
from app.models import FunctionalConfig, MaskingRule


class ConfigLoader:
    """Loads and validates the functional masking configuration."""

    REQUIRED_GLOBAL_FIELDS = frozenset({"maskingFormat", "padLength"})
    REQUIRED_RULE_FIELDS = frozenset({"schema", "table", "column", "orderBy"})

    def load(self, config_path: Path) -> FunctionalConfig:
        """Load and parse a functional configuration file.

        Args:
            config_path: Path to the JSON configuration file.

        Returns:
            A validated FunctionalConfig object.

        Raises:
            ConfigurationError: If the file is missing, invalid, or fails validation.
        """
        if not config_path or str(config_path) == "":
            raise ConfigurationError("Configuration file path cannot be empty")

        if not config_path.exists():
            raise ConfigurationError(
                "Functional configuration file not found: {}".format(config_path)
            )

        try:
            raw_content = config_path.read_text(encoding="utf-8")
        except IOError as e:
            raise ConfigurationError(
                "Failed to read configuration file {}: {}".format(config_path, str(e))
            )

        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                "Invalid JSON in configuration file {}: {}".format(config_path, str(e))
            )

        if not isinstance(data, dict):
            raise ConfigurationError(
                "Configuration file {} must contain a JSON object at root".format(
                    config_path
                )
            )

        return self._parse_and_validate(data, str(config_path))

    def _parse_and_validate(
        self, data: Dict[str, Any], source: str
    ) -> FunctionalConfig:
        """Parse and validate the configuration data."""
        global_config = self._parse_global(data.get("global", {}), source)
        masking_rules = self._parse_rules(data.get("maskingRules", []), source)

        return FunctionalConfig(
            masking_format=global_config["maskingFormat"],
            pad_length=global_config["padLength"],
            masking_rules=masking_rules,
        )

    def _parse_global(self, global_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Parse and validate the global section."""
        if not isinstance(global_data, dict):
            raise ConfigurationError(
                "The 'global' section in {} must be an object".format(source)
            )

        missing_fields = self.REQUIRED_GLOBAL_FIELDS - set(global_data.keys())
        if missing_fields:
            raise ConfigurationError(
                "Missing required field(s) in 'global' section of {}: {}".format(
                    source, ", ".join(sorted(missing_fields))
                )
            )

        masking_format = global_data.get("maskingFormat")
        if not isinstance(masking_format, str) or not masking_format:
            raise ConfigurationError(
                "maskingFormat in {} must be a non-empty string".format(source)
            )

        if not isinstance(masking_format, str) or not masking_format:
            raise ConfigurationError(
                "maskingFormat in {} must be a non-empty string".format(source)
            )

        pad_length = global_data.get("padLength")
        if not isinstance(pad_length, int):
            raise ConfigurationError(
                "padLength in {} must be an integer".format(source)
            )

        if pad_length <= 0:
            raise ConfigurationError(
                "padLength in {} must be a strictly positive integer (got {})".format(
                    source, pad_length
                )
            )

        return {"maskingFormat": masking_format, "padLength": pad_length}

    def _parse_rules(self, rules_data: Any, source: str) -> List[MaskingRule]:
        """Parse and validate the masking rules list."""
        if not isinstance(rules_data, list):
            raise ConfigurationError(
                "The 'maskingRules' section in {} must be an array".format(source)
            )

        if len(rules_data) == 0:
            raise ConfigurationError(
                "The 'maskingRules' section in {} cannot be empty".format(source)
            )

        rules: List[MaskingRule] = []
        for i, rule in enumerate(rules_data):
            if not isinstance(rule, dict):
                raise ConfigurationError(
                    "Masking rule at index {} in {} must be an object".format(i, source)
                )

            missing_fields = self.REQUIRED_RULE_FIELDS - set(rule.keys())
            if missing_fields:
                raise ConfigurationError(
                    "Missing required field(s) in masking rule at index {} of {}: {}".format(
                        i, source, ", ".join(sorted(missing_fields))
                    )
                )

            for field in self.REQUIRED_RULE_FIELDS:
                value = rule.get(field)
                if not isinstance(value, str) or not value:
                    raise ConfigurationError(
                        "Field '{}' in masking rule at index {} of {} "
                        "must be a non-empty string".format(field, i, source)
                    )

            rules.append(
                MaskingRule(
                    schema=rule["schema"],
                    table=rule["table"],
                    column=rule["column"],
                    order_by=rule["orderBy"],
                )
            )

        return rules
