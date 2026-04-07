"""Tests for the exceptions module."""

import pytest

from app.exceptions import (
    DatamaskerError,
    ConfigurationError,
    SecretError,
    ValidationError,
    SQLGenerationError,
    MetadataError,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_datamasker_error_is_base(self):
        """Test DatamaskerError is the base exception."""
        error = DatamaskerError("test message")
        assert isinstance(error, Exception)
        assert error.message == "test message"

    def test_configuration_error_inherits_from_base(self):
        """Test ConfigurationError inherits from DatamaskerError."""
        error = ConfigurationError("config error")
        assert isinstance(error, DatamaskerError)
        assert isinstance(error, Exception)
        assert error.message == "config error"

    def test_secret_error_inherits_from_base(self):
        """Test SecretError inherits from DatamaskerError."""
        error = SecretError("secret error")
        assert isinstance(error, DatamaskerError)
        assert isinstance(error, Exception)
        assert error.message == "secret error"

    def test_validation_error_inherits_from_base(self):
        """Test ValidationError inherits from DatamaskerError."""
        error = ValidationError("validation error")
        assert isinstance(error, DatamaskerError)
        assert isinstance(error, Exception)
        assert error.message == "validation error"

    def test_sql_generation_error_inherits_from_base(self):
        """Test SQLGenerationError inherits from DatamaskerError."""
        error = SQLGenerationError("sql generation error")
        assert isinstance(error, DatamaskerError)
        assert isinstance(error, Exception)
        assert error.message == "sql generation error"

    def test_metadata_error_inherits_from_base(self):
        """Test MetadataError inherits from DatamaskerError."""
        error = MetadataError("metadata error")
        assert isinstance(error, DatamaskerError)
        assert isinstance(error, Exception)
        assert error.message == "metadata error"


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_exception_str_method(self):
        """Test that str(exception) returns the message."""
        error = ConfigurationError("configuration problem")
        assert str(error) == "configuration problem"

    def test_exception_message_attribute(self):
        """Test that message attribute is set correctly."""
        error = SecretError("secret problem")
        assert error.message == "secret problem"

    def test_exception_empty_message(self):
        """Test exception with empty message."""
        error = ValidationError("")
        assert error.message == ""


class TestExceptionCatching:
    """Tests for exception catching patterns."""

    def test_catch_datamasker_error_catches_all(self):
        """Test that catching DatamaskerError catches all custom exceptions."""
        errors = [
            ConfigurationError("config"),
            SecretError("secret"),
            ValidationError("validation"),
            SQLGenerationError("sql"),
            MetadataError("metadata"),
        ]

        for error in errors:
            with pytest.raises(DatamaskerError):
                raise error

    def test_catch_specific_errors(self):
        """Test catching specific exception types."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("config")

        with pytest.raises(SecretError):
            raise SecretError("secret")

        with pytest.raises(ValidationError):
            raise ValidationError("validation")

    def test_exception_chaining(self):
        """Test that exceptions can be chained."""
        original = ValueError("original")
        try:
            raise ConfigurationError("config") from original
        except ConfigurationError as e:
            assert e.__cause__ is original
