"""Validator for masking rules against SQL Server metadata."""

from typing import List, Tuple

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
            rule_errors = self._validate_rule(rule, processed_rules)
            errors.extend(rule_errors)
            processed_rules.append((rule.schema, rule.table, rule.column))

        if errors:
            return errors
        return []

    def _validate_rule(
        self, rule: MaskingRule, processed_rules: List[Tuple[str, str, str]]
    ) -> List[ValidationError]:
        """Validate a single masking rule.

        Args:
            rule: The masking rule to validate.
            processed_rules: List of already-processed (schema, table, column) tuples.

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
