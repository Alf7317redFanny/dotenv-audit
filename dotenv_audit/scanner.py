"""Scanner module for discovering .env files in a project directory."""

import os
from pathlib import Path
from typing import Generator

DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
}

ENV_FILE_PATTERNS = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.staging",
    ".env.production",
    ".env.test",
    ".env.example",
    ".env.sample",
}


def is_env_file(filename: str) -> bool:
    """Return True if the filename matches a known .env pattern."""
    name = os.path.basename(filename)
    if name in ENV_FILE_PATTERNS:
        return True
    # catch variants like .env.local.bak or .env.2024
    if name.startswith(".env"):
        return True
    return False


def scan_directory(
    root: str | Path,
    ignore_dirs: set[str] | None = None,
) -> Generator[Path, None, None]:
    """Walk *root* and yield paths to every .env file found.

    Args:
        root: The top-level directory to scan.
        ignore_dirs: Directory names to skip (defaults to DEFAULT_IGNORE_DIRS).

    Yields:
        Absolute Path objects pointing to discovered .env files.
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    root = Path(root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(f"'{root}' is not a directory or does not exist.")

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place so os.walk skips them
        dirnames[:] = [
            d for d in dirnames if d not in ignore_dirs and not d.startswith(".")
            or d == "."  # keep root-level hidden dirs that aren't in ignore list
        ]
        # Re-apply ignore list cleanly
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        for filename in filenames:
            if is_env_file(filename):
                yield Path(dirpath) / filename
