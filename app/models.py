"""Data models for Datamasker."""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MaskingRule:
    """Represents a single masking rule from the functional configuration."""

    schema: str
    table: str
    column: str
    order_by: str


@dataclass(frozen=True)
class FunctionalConfig:
    """Represents the functional configuration file."""

    masking_format: str
    pad_length: int
    masking_rules: List[MaskingRule]

    @property
    def pad_length_strictly_positive(self) -> bool:
        """Check if pad_length is strictly positive."""
        return self.pad_length > 0


@dataclass(frozen=True)
class ConnectionConfig:
    """Represents the technical/connection configuration file."""

    server: str
    database: str
    username: str
    password_file: str

    @property
    def password_file_path(self) -> "PurePath":
        """Return the password file as a path."""
        from pathlib import PurePath

        return PurePath(self.password_file)
