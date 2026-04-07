"""Tests for the secret_store module."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock
import pytest

from app.secret_store import SecretStore
from app.exceptions import SecretError


class TestSecretStoreNonWindows:
    """Tests for SecretStore on non-Windows platforms."""

    def test_supports_dpapi_false_on_linux(self):
        """Test that DPAPI is not supported on Linux."""
        store = SecretStore()
        assert store.supports_dpapi is False

    def test_supports_dpapi_false_on_macos(self):
        """Test that DPAPI is not supported on macOS."""
        with patch.object(sys, "platform", "darwin"):
            store = SecretStore()
            assert store.supports_dpapi is False

    def test_encrypt_password_not_supported_on_linux(self):
        """Test that encrypt_password raises error on Linux."""
        store = SecretStore()
        with pytest.raises(SecretError) as exc_info:
            store.encrypt_password("password", Path("/tmp/out.dpapi"))
        assert "only supported on Windows" in str(exc_info.value.message)

    def test_decrypt_password_not_supported_on_linux(self):
        """Test that decrypt_password raises error on Linux."""
        store = SecretStore()
        with pytest.raises(SecretError) as exc_info:
            store.decrypt_password(Path("/tmp/in.dpapi"))
        assert "only supported on Windows" in str(exc_info.value.message)

    def test_supports_dpapi_property_returns_bool(self):
        """Test supports_dpapi property returns boolean."""
        store = SecretStore()
        assert isinstance(store.supports_dpapi, bool)


class TestSecretStorePlatformDetection:
    """Tests for platform detection."""

    def test_windows_detected_correctly(self):
        """Test that Windows platform is correctly detected."""
        with patch.object(sys, "platform", "win32"):
            store = SecretStore()
            assert store.supports_dpapi is True

    def test_linux_detected_correctly(self):
        """Test that Linux platform is correctly detected."""
        with patch.object(sys, "platform", "linux"):
            store = SecretStore()
            assert store.supports_dpapi is False

    def test_macos_detected_correctly(self):
        """Test that macOS platform is correctly detected."""
        with patch.object(sys, "platform", "darwin"):
            store = SecretStore()
            assert store.supports_dpapi is False


class TestSecretStoreInputValidation:
    """Tests for input validation."""

    def test_encrypt_password_empty_string_rejected(self):
        """Test that empty password string is rejected on Windows."""
        store = SecretStore()
        store._is_windows = True
        with pytest.raises(SecretError) as exc_info:
            store.encrypt_password("", Path("/tmp/out.dpapi"))
        assert "cannot be empty" in str(exc_info.value.message)

    def test_decrypt_password_none_path_rejected(self):
        """Test that None path is rejected for decryption."""
        store = SecretStore()
        with pytest.raises((SecretError, TypeError)):
            store.decrypt_password(None)

    def test_encrypt_password_none_path_rejected(self):
        """Test that None path is rejected for encryption."""
        store = SecretStore()
        with pytest.raises((SecretError, TypeError)):
            store.encrypt_password("password", None)

    def test_supports_dpapi_reflects_actual_platform(self):
        """Test that supports_dpapi correctly reflects actual platform."""
        store = SecretStore()
        if sys.platform == "win32":
            assert store.supports_dpapi is True
        else:
            assert store.supports_dpapi is False
