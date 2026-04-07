"""DPAPI secret store for secure password handling on Windows."""

import sys
from pathlib import Path
from typing import Optional

from app.exceptions import SecretError

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        """Windows CRYPTPROTECT_LOCAL Structure for DPAPI."""

        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    class CRYPTPROTECT_LOCAL_MACHINE(ctypes.Structure):
        """Structure for CRYPTPROTECT_LOCAL_MACHINE flag."""

        _fields_ = [
            ("dwFlags", wintypes.DWORD),
            ("szDatarep", ctypes.c_char_p),
        ]


class SecretStore:
    """Manages DPAPI-encrypted password files on Windows."""

    def __init__(self) -> None:
        self._is_windows = sys.platform == "win32"

    def encrypt_password(self, password: str, output_path: Path) -> None:
        """Encrypt a password using DPAPI and save to a file.

        Args:
            password: The plain-text password to encrypt.
            output_path: Path where the encrypted data will be saved.

        Raises:
            SecretError: If encryption fails or platform is not Windows.
        """
        if not self._is_windows:
            raise SecretError(
                "DPAPI encryption is only supported on Windows. "
                "Current platform: {}".format(sys.platform)
            )

        if not password:
            raise SecretError("Password cannot be empty")

        if not output_path:
            raise SecretError("Output path cannot be empty")

        try:
            password_bytes = password.encode("utf-16le")

            data_in = DATA_BLOB()
            data_in.cbData = len(password_bytes)
            data_in.pbData = ctypes.cast(
                ctypes.create_string_buffer(password_bytes),
                ctypes.POINTER(ctypes.c_byte),
            )

            data_out = DATA_BLOB()

            result = ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(data_in), None, None, None, None, 0, ctypes.byref(data_out)
            )

            if not result:
                raise SecretError("CryptProtectData failed")

            encrypted_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(encrypted_bytes)

            ctypes.windll.kernel32.LocalFree(data_out.pbData)

        except ctypes.error as e:
            raise SecretError("DPAPI encryption failed: {}".format(str(e)))
        except IOError as e:
            raise SecretError(
                "Failed to write encrypted file to {}: {}".format(output_path, str(e))
            )

    def decrypt_password(self, input_path: Path) -> str:
        """Read and decrypt a DPAPI-encrypted password file.

        Args:
            input_path: Path to the encrypted password file.

        Returns:
            The decrypted plain-text password.

        Raises:
            SecretError: If decryption fails, file is missing, or platform is not Windows.
        """
        if not self._is_windows:
            raise SecretError(
                "DPAPI decryption is only supported on Windows. "
                "Current platform: {}".format(sys.platform)
            )

        if not input_path:
            raise SecretError("Input path cannot be empty")

        if not input_path.exists():
            raise SecretError(
                "Secret file not found: {}. "
                "Please create it using the encrypt-password command.".format(
                    input_path
                )
            )

        try:
            encrypted_bytes = input_path.read_bytes()

            if not encrypted_bytes:
                raise SecretError("Encrypted file is empty")

            data_in = DATA_BLOB()
            data_in.cbData = len(encrypted_bytes)
            data_in.pbData = ctypes.cast(
                ctypes.create_string_buffer(encrypted_bytes),
                ctypes.POINTER(ctypes.c_byte),
            )

            data_out = DATA_BLOB()

            result = ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(data_in), None, None, None, None, 0, ctypes.byref(data_out)
            )

            if not result:
                raise SecretError(
                    "CryptUnprotectData failed. The secret may have been "
                    "encrypted on a different Windows account or machine."
                )

            decrypted_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)

            password = decrypted_bytes.decode("utf-16le")

            ctypes.windll.kernel32.LocalFree(data_out.pbData)

            return password

        except ctypes.error as e:
            raise SecretError("DPAPI decryption failed: {}".format(str(e)))
        except IOError as e:
            raise SecretError(
                "Failed to read encrypted file from {}: {}".format(input_path, str(e))
            )

    @property
    def supports_dpapi(self) -> bool:
        """Check if DPAPI is supported on this platform."""
        return self._is_windows
