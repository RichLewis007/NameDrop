"""
Safe file operations for renaming files and folders
"""

import os
import shutil
from pathlib import Path
import time


class FileOperations:
    """Safe file operations for renaming"""

    # Invalid characters for Windows file names
    WINDOWS_INVALID_CHARS = set('<>:"|?*\\')
    # Invalid characters for macOS
    MACOS_INVALID_CHARS = set(":")
    # Invalid characters for Linux (most are allowed, but these are problematic)
    LINUX_INVALID_CHARS = set("/\0")

    # Control characters (0x00-0x1F, 0x7F)
    CONTROL_CHARS = set(chr(i) for i in range(32) if i != 9) | {chr(127)}

    def __init__(self):
        pass

    def is_valid_filename(self, filename: str) -> bool:
        """
        Check if filename is valid across major operating systems
        """
        if not filename or filename.strip() == "":
            return False

        # Check for invalid characters
        invalid_chars = (
            self.WINDOWS_INVALID_CHARS
            | self.MACOS_INVALID_CHARS
            | self.LINUX_INVALID_CHARS
            | self.CONTROL_CHARS
        )

        if any(char in invalid_chars for char in filename):
            return False

        # Windows reserved names
        windows_reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        name_upper = filename.upper().split(".")[0]
        if name_upper in windows_reserved:
            return False

        # Check for trailing periods/spaces (invalid on Windows)
        if filename.endswith(".") or filename.endswith(" "):
            return False

        # Check length (Windows MAX_PATH is 260, but we'll be more conservative)
        if len(filename) > 255:
            return False

        return True

    def create_backup(self, source: Path, backup_path: Path) -> bool:
        """
        Create a backup of a file or folder
        Returns True if successful, False otherwise
        """
        try:
            # If backup already exists, add a number suffix
            if backup_path.exists():
                base = backup_path
                counter = 1
                while backup_path.exists():
                    backup_path = base.parent / f"{base.name} ({counter})"
                    counter += 1

            if source.is_file():
                shutil.copy2(source, backup_path)
            elif source.is_dir():
                shutil.copytree(source, backup_path, dirs_exist_ok=False)
            else:
                return False

            return True
        except Exception as e:
            print(f"Backup error: {e}")
            return False

    def rename_file(self, old_path: Path, new_path: Path) -> bool:
        """
        Safely rename a file or folder
        Uses atomic operations where possible
        Returns True if successful, False otherwise
        """
        try:
            # Validate paths
            if not old_path.exists():
                return False

            if new_path.exists() and new_path != old_path:
                return False

            # Validate new filename
            if not self.is_valid_filename(new_path.name):
                return False

            # For files, try atomic rename first (most OSes support this)
            if old_path.is_file():
                # Use replace() which is atomic on most systems
                old_path.replace(new_path)
                return True
            elif old_path.is_dir():
                # For directories, rename is usually atomic but not always
                # Use rename() which should work on all platforms
                old_path.rename(new_path)
                return True
            else:
                return False

        except PermissionError:
            # File might be in use
            return False
        except OSError as e:
            # Various OS errors (disk full, etc.)
            print(f"Rename error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def safe_rename_with_retry(
        self, old_path: Path, new_path: Path, max_retries: int = 3
    ) -> bool:
        """
        Attempt rename with retries (useful for network drives or locked files)
        """
        for attempt in range(max_retries):
            if self.rename_file(old_path, new_path):
                return True
            if attempt < max_retries - 1:
                time.sleep(0.1)  # Brief pause before retry
        return False
