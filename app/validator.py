"""Validator for masking rules against SQL Server metadata."""

from typing import List, Optional, Tuple

from app.exceptions import ValidationError
from app.models import FunctionalConfig, MaskingRule
from app.sqlserver_metadata import SQLServerMetadata


class Validator:
    """Validates masking rules against SQL Server system catalogs."""

    def __init__(self, metadata: SQLServerMetadata) -> None:
        """Initialize with a SQL Server metadata handler.

        Args:
            metadata: SQLServerMetadata instance for querying catalogs.
        """
        self._metadata = metadata

    def validate(self, config: FunctionalConfig) -> List[ValidationError]:
        """Validate all masking rules against SQL Server metadata.

        This method validates each rule and returns a list of all errors found,
        rather than failing on the first error. This allows comprehensive feedback.

        Args:
            config: The functional configuration to validate.

        Returns:
            A list of ValidationError objects. Empty list means all validations passed.

        Raises:
            ValidationError: If a rule violates a mandatory security constraint.
        """
        errors: List[ValidationError] = []
        processed_rules: List[Tuple[str, str, str]] = []

        for rule in config.masking_rules:
            rule_errors = self._validate_rule(rule, processed_rules, config)
            errors.extend(rule_errors)
            processed_rules.append((rule.schema, rule.table, rule.column))

        if errors:
            return errors
        return []

    def _validate_rule(
        self,
        rule: MaskingRule,
        processed_rules: List[Tuple[str, str, str]],
        config: FunctionalConfig,
    ) -> List[ValidationError]:
        """Validate a single masking rule.

        Args:
            rule: The masking rule to validate.
            processed_rules: List of already-processed (schema, table, column) tuples.
            config: The functional configuration containing masking format and pad_length.

        Returns:
            List of validation errors for this rule.
        """
        errors: List[ValidationError] = []

        if not self._metadata.schema_exists(rule.schema):
            errors.append(
                ValidationError(
                    "Schema '{}' does not exist in the database".format(rule.schema)
                )
            )
            return errors

        if not self._metadata.table_exists(rule.schema, rule.table):
            errors.append(
                ValidationError(
                    "Table '{}.{}' does not exist in the database".format(
                        rule.schema, rule.table
                    )
                )
            )
            return errors

        if not self._metadata.column_exists(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}' in table '{}.{}' does not exist".format(
                        rule.column, rule.schema, rule.table
                    )
                )
            )
            return errors

        if not self._metadata.column_exists(rule.schema, rule.table, rule.order_by):
            errors.append(
                ValidationError(
                    "orderBy column '{}' in table '{}.{}' does not exist".format(
                        rule.order_by, rule.schema, rule.table
                    )
                )
            )
            return errors

        length_error = self._validate_masked_value_length(rule, config)
        if length_error:
            errors.append(length_error)

        if self._metadata.is_primary_key(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}.{}.{}' is a PRIMARY KEY and cannot be masked".format(
                        rule.schema, rule.table, rule.column
                    )
                )
            )

        if self._metadata.is_unique(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}.{}.{}' has a UNIQUE constraint and cannot be masked".format(
                        rule.schema, rule.table, rule.column
                    )
                )
            )

        if self._metadata.is_computed(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}.{}.{}' is a COMPUTED column and cannot be masked".format(
                        rule.schema, rule.table, rule.column
                    )
                )
            )

        if self._metadata.is_foreign_key_source(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}.{}.{}' is involved in an outgoing FOREIGN KEY and cannot be masked".format(
                        rule.schema, rule.table, rule.column
                    )
                )
            )

        if self._metadata.is_foreign_key_target(rule.schema, rule.table, rule.column):
            errors.append(
                ValidationError(
                    "Column '{}.{}.{}' is involved in an incoming FOREIGN KEY and cannot be masked".format(
                        rule.schema, rule.table, rule.column
                    )
                )
            )

        return errors

    def _validate_masked_value_length(
        self, rule: MaskingRule, config: FunctionalConfig
    ) -> Optional[ValidationError]:
        """Validate that the masked value fits within the column's max length.

        Args:
            rule: The masking rule to validate.
            config: The functional configuration containing masking format and pad_length.

        Returns:
            A ValidationError if the masked value exceeds the column length, None otherwise.
        """
        max_length = self._metadata.get_column_max_length(
            rule.schema, rule.table, rule.column
        )
        if max_length is None:
            return ValidationError(
                "Could not determine max length for column '{}.{}.{}'".format(
                    rule.schema, rule.table, rule.column
                )
            )

        column_type = self._metadata.get_column_type(
            rule.schema, rule.table, rule.column
        )
        if column_type is None:
            return ValidationError(
                "Could not determine data type for column '{}.{}.{}'".format(
                    rule.schema, rule.table, rule.column
                )
            )

        max_counter = "0" * config.pad_length
        masked_value_template = config.masking_format.replace(
            "{column}", rule.column.upper()
        ).replace("{counter}", max_counter)

        masked_value_length = len(masked_value_template)

        if column_type.lower() in ("nvarchar", "nchar", "ntext"):
            effective_max_length = max_length // 2
        else:
            effective_max_length = max_length

        if masked_value_length > effective_max_length:
            return ValidationError(
                "Masked value length ({}) exceeds column '{}.{}.{}' max length ({}) for data type '{}'".format(
                    masked_value_length,
                    rule.schema,
                    rule.table,
                    rule.column,
                    effective_max_length,
                    column_type,
                )
            )

        return None
