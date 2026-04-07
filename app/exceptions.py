"""Custom exceptions for Datamasker."""


class DatamaskerError(Exception):
    """Base exception for all Datamasker errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigurationError(DatamaskerError):
    """Raised when configuration is invalid or missing."""


class SecretError(DatamaskerError):
    """Raised when secret file operations fail."""


class ValidationError(DatamaskerError):
    """Raised when SQL Server validation fails."""


class SQLGenerationError(DatamaskerError):
    """Raised when SQL script generation fails."""


class MetadataError(DatamaskerError):
    """Raised when SQL Server metadata queries fail."""
