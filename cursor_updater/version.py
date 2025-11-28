"""Version management and caching for Cursor Updater."""

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from cursor_updater.config import (
    CACHE_FILE,
    CACHE_MAX_AGE,
    VERSION_HISTORY_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
    VERSION_PATTERN,
    DOWNLOADS_DIR,
    CURSOR_APPIMAGE,
    DESKTOP_FILE,
    CURSOR_APPIMAGE_PATTERNS,
    CURSOR_VERSIONED_PATTERNS,
)
from cursor_updater.spinner import show_spinner


@dataclass
class VersionInfo:
    """Container for version information."""

    local: Optional[str] = None
    latest_local: Optional[str] = None
    latest_remote: Optional[str] = None


def get_platform() -> str:
    """Detect platform architecture."""
    arch = platform.machine()
    platform_map = {
        "x86_64": "linux-x64",
        "aarch64": "linux-arm64",
        "arm64": "linux-arm64",
    }
    return platform_map.get(arch, "linux-x64")


def extract_version_from_filename(filename: str) -> Optional[str]:
    """Extract version number from filename."""
    match = VERSION_PATTERN.search(filename)
    return match.group(1) if match else None


def parse_version_tuple(version: str) -> Optional[tuple]:
    """Convert version string to tuple for comparison."""
    try:
        return tuple(map(int, version.split(".")))
    except ValueError:
        return None


def sort_versions(versions: list[str]) -> list[str]:
    """Sort versions in descending order."""
    return sorted(versions, key=parse_version_tuple, reverse=True)


class VersionHistoryCache:
    """Manages version history caching."""

    @staticmethod
    def is_cache_valid() -> bool:
        """Check if cache exists and is still valid."""
        if not CACHE_FILE.exists():
            return False
        cache_age = time.time() - CACHE_FILE.stat().st_mtime
        return cache_age < CACHE_MAX_AGE

    @staticmethod
    def load() -> Optional[dict]:
        """Load version history from cache."""
        if not VersionHistoryCache.is_cache_valid():
            return None
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def save(data: dict) -> None:
        """Save version history to cache."""
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    @staticmethod
    def load_stale() -> Optional[dict]:
        """Load stale cache as fallback."""
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None


def fetch_version_history() -> Optional[dict]:
    """Fetch version history from remote URL."""
    try:
        req = Request(VERSION_HISTORY_URL, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def _fetch_version_history_with_spinner() -> Optional[dict]:
    """Fetch version history with spinner indicator."""
    with show_spinner("Fetching version information"):
        return fetch_version_history()


def get_version_history() -> Optional[dict]:
    """Get version history from cache or remote."""
    cached = VersionHistoryCache.load()
    if cached:
        return cached

    data = _fetch_version_history_with_spinner()
    if data:
        VersionHistoryCache.save(data)
        return data

    return VersionHistoryCache.load_stale()


def get_platform_versions(version_history: dict) -> list[str]:
    """Extract versions available for current platform."""
    platform_name = get_platform()
    try:
        versions = version_history.get("versions", [])
        return [
            v["version"] for v in versions if v.get("platforms", {}).get(platform_name)
        ]
    except (KeyError, ValueError):
        return []


def get_latest_remote_version() -> Optional[str]:
    """Get latest remote version for current platform."""
    version_history = get_version_history()
    if not version_history:
        return None

    platform_versions = get_platform_versions(version_history)
    if not platform_versions:
        return None

    return sort_versions(platform_versions)[0]


def get_download_url(version: str) -> Optional[str]:
    """Get download URL for a specific version."""
    version_history = get_version_history()
    if not version_history:
        return None

    platform_name = get_platform()
    try:
        versions = version_history.get("versions", [])
        for v in versions:
            if v.get("version") == version:
                url = v.get("platforms", {}).get(platform_name)
                if url:
                    return url
    except (KeyError, ValueError):
        pass

    return None


def _find_appimage_path_in_line(line: str) -> Optional[Path]:
    """Extract AppImage path from a process line."""
    matches = re.findall(r"(/[^\s]+cursor[^\s]*\.AppImage)", line)
    for match in matches:
        path = Path(match)
        if path.exists():
            return path.resolve()

    parts = line.split()
    for part in parts:
        if part.endswith(".AppImage") and "cursor" in part.lower():
            path = Path(part)
            if path.exists():
                return path.resolve()
    return None


def get_running_cursor_path() -> Optional[Path]:
    """Find the path to the currently running Cursor executable from process list."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        for line in result.stdout.splitlines():
            if "cursor" in line.lower() and ".AppImage" in line:
                if path := _find_appimage_path_in_line(line):
                    return path
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    return None


def extract_version_from_appimage(appimage_path: Path) -> Optional[str]:
    """Extract version from AppImage file (package.json, desktop file, or filename)."""
    extract_dir = None
    try:
        extract_dir = Path(tempfile.mkdtemp(prefix="cursor_version_"))
        result = subprocess.run(
            [str(appimage_path), "--appimage-extract"],
            cwd=str(extract_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            package_json_paths = list(extract_dir.glob("**/resources/app/package.json"))
            for package_json_path in package_json_paths:
                try:
                    with open(package_json_path, "r", encoding="utf-8") as f:
                        package_data = json.load(f)
                        if version := package_data.get("version"):
                            return version
                except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                    continue

            desktop_files = list(extract_dir.glob("**/*.desktop"))
            for desktop_file in desktop_files:
                try:
                    with open(desktop_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("X-AppImage-Version="):
                                version = line.split("=", 1)[1].strip()
                                if version:
                                    return version
                except (OSError, UnicodeDecodeError):
                    continue
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    finally:
        if extract_dir and extract_dir.exists():
            try:
                shutil.rmtree(extract_dir)
            except OSError:
                pass

    try:
        result = subprocess.run(
            ["strings", str(appimage_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            if '"version"' in line and ":" in line:
                match = re.search(r'"version"\s*:\s*"([0-9.]+)"', line)
                if match:
                    return match.group(1)
            if "X-AppImage-Version=" in line:
                version = line.split("=", 1)[1].strip()
                if version:
                    return version
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass

    return extract_version_from_filename(appimage_path.name)


def _find_cursor_appimage_in_dir(directory: Path) -> Optional[Path]:
    """Find cursor AppImage file in directory (case-insensitive)."""
    if not directory.exists():
        return None

    # Check exact path first (case-sensitive)
    if CURSOR_APPIMAGE.exists() and CURSOR_APPIMAGE.parent == directory:
        return CURSOR_APPIMAGE

    # Case-insensitive search using glob patterns
    for pattern in CURSOR_APPIMAGE_PATTERNS:
        matches = [f for f in directory.glob(pattern) if f.is_file()]
        if matches:
            # Prefer exact match (case-insensitive)
            for match in matches:
                if match.name.lower() == "cursor.appimage":
                    return match
            return matches[0]

    return None


def _get_version_from_path(appimage_path: Path) -> Optional[str]:
    """Extract version from an AppImage path if it exists."""
    if not appimage_path.exists():
        return None
    return extract_version_from_appimage(appimage_path)


def _collect_versions_from_directory(directory: Path) -> list[str]:
    """Collect all versions from AppImage files in a directory (deduplicated)."""
    if not directory.exists():
        return []

    versions = set()
    seen_files = set()

    for pattern in CURSOR_VERSIONED_PATTERNS:
        for appimage in directory.glob(pattern):
            # Avoid processing the same file multiple times (case variations)
            file_key = appimage.resolve()
            if file_key in seen_files:
                continue
            seen_files.add(file_key)

            version = extract_version_from_filename(
                appimage.name
            ) or extract_version_from_appimage(appimage)
            if version:
                versions.add(version)

    return list(versions)


def get_local_version() -> Optional[str]:
    """Get currently active local version from the actual Cursor AppImage."""
    # Priority 1: Check running process
    running_path = get_running_cursor_path()
    if running_path and (version := _get_version_from_path(running_path)):
        return version

    # Priority 2: Check desktop file Exec path
    desktop_exec = get_desktop_file_exec()
    if desktop_exec and (version := _get_version_from_path(Path(desktop_exec))):
        return version

    # Priority 3: Check standard location (case-insensitive)
    local_bin = CURSOR_APPIMAGE.parent
    appimage_path = _find_cursor_appimage_in_dir(local_bin)
    if appimage_path and (version := _get_version_from_path(appimage_path)):
        return version

    return None


def get_latest_local_version() -> Optional[str]:
    """Get latest locally available version from downloads directory and installation location."""
    versions = set()

    # Check downloads directory (case-insensitive)
    versions.update(_collect_versions_from_directory(DOWNLOADS_DIR))

    # Check actual installation location
    local_bin = CURSOR_APPIMAGE.parent
    if local_bin.exists():
        # Check desktop file Exec path
        desktop_exec = get_desktop_file_exec()
        if desktop_exec and (version := _get_version_from_path(Path(desktop_exec))):
            versions.add(version)

        # Check for any cursor appimage in ~/.local/bin
        appimage_path = _find_cursor_appimage_in_dir(local_bin)
        if appimage_path and (version := _get_version_from_path(appimage_path)):
            versions.add(version)

    if not versions:
        return None

    return sort_versions(list(versions))[0]


def get_desktop_file_exec() -> Optional[str]:
    """Get the Exec path from the desktop file."""
    if not DESKTOP_FILE.exists():
        return None

    try:
        with open(DESKTOP_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Exec="):
                    exec_line = line[5:].strip()
                    return exec_line.split()[0] if exec_line.split() else exec_line
    except OSError:
        pass

    return None


def get_launch_info() -> dict:
    """Get information about how Cursor is launched."""
    info = {
        "running_from": None,
        "desktop_file_exec": None,
        "symlink_target": None,
        "symlink_exists": False,
        "symlink_path": None,
        "in_path": False,
    }

    running_path = get_running_cursor_path()
    if running_path:
        info["running_from"] = str(running_path.resolve())

    desktop_exec = get_desktop_file_exec()
    if desktop_exec:
        info["desktop_file_exec"] = desktop_exec

    # Check for cursor appimage (case-insensitive)
    local_bin = CURSOR_APPIMAGE.parent
    appimage_path = _find_cursor_appimage_in_dir(local_bin)
    if appimage_path:
        info["symlink_exists"] = True
        info["symlink_path"] = str(appimage_path)
        if appimage_path.is_symlink():
            try:
                info["symlink_target"] = str(appimage_path.readlink().resolve())
            except OSError:
                pass

    local_bin_str = str(Path.home() / ".local" / "bin")
    path_env = os.environ.get("PATH", "")
    info["in_path"] = local_bin_str in path_env.split(":")

    return info


def get_version_status() -> VersionInfo:
    """Get all version information."""
    return VersionInfo(
        local=get_local_version(),
        latest_local=get_latest_local_version(),
        latest_remote=get_latest_remote_version(),
    )
