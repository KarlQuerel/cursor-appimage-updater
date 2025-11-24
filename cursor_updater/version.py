"""Version management and caching for Cursor Updater."""

import json
import platform
import time
from dataclasses import dataclass
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
    ACTIVE_SYMLINK,
)


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


def get_version_history() -> Optional[dict]:
    """Get version history from cache or remote."""
    cached = VersionHistoryCache.load()
    if cached:
        return cached

    data = fetch_version_history()
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
            v["version"]
            for v in versions
            if v.get("platforms", {}).get(platform_name)
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

    sorted_versions = sort_versions(platform_versions)
    return sorted_versions[0]


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


def get_local_version() -> Optional[str]:
    """Get currently active local version."""
    if not ACTIVE_SYMLINK.exists() or not ACTIVE_SYMLINK.is_symlink():
        return None

    try:
        target = ACTIVE_SYMLINK.resolve()
        return extract_version_from_filename(target.name)
    except (OSError, ValueError):
        return None


def get_latest_local_version() -> Optional[str]:
    """Get latest locally available version."""
    if not DOWNLOADS_DIR.exists():
        return None

    versions = [
        extract_version_from_filename(appimage.name)
        for appimage in DOWNLOADS_DIR.glob("cursor-*.AppImage")
    ]
    versions = [v for v in versions if v]

    if not versions:
        return None

    sorted_versions = sort_versions(versions)
    return sorted_versions[0]


def get_version_status() -> VersionInfo:
    """Get all version information."""
    return VersionInfo(
        local=get_local_version(),
        latest_local=get_latest_local_version(),
        latest_remote=get_latest_remote_version(),
    )

