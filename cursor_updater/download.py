"""Download and file management for Cursor Updater."""

import os
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from cursor_updater.config import (
    DOWNLOADS_DIR,
    CURSOR_APPIMAGE,
    CHUNK_SIZE,
    DOWNLOAD_TIMEOUT,
    USER_AGENT,
    DESKTOP_FILE,
    CURSOR_APPIMAGE_PATTERNS,
)
from cursor_updater.version import get_download_url, get_running_cursor_path
from cursor_updater.output import print_error, print_success, print_info


def get_appimage_path(version: str) -> Path:
    """Get the path to an AppImage file for a given version."""
    return DOWNLOADS_DIR / f"cursor-{version}.AppImage"


def bytes_to_mb(bytes_size: int) -> int:
    """Convert bytes to MB."""
    return bytes_size // 1024 // 1024


def _show_download_progress(downloaded: int, total_size: int) -> None:
    """Display download progress."""
    percent = (downloaded / total_size) * 100
    mb_downloaded = bytes_to_mb(downloaded)
    mb_total = bytes_to_mb(total_size)
    print(f"\r   {percent:.1f}% ({mb_downloaded}MB/{mb_total}MB)", end="", flush=True)


def download_file(url: str, filepath: Path) -> bool:
    """Download a file with progress indication."""
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        _show_download_progress(downloaded, total_size)

            print()
            os.chmod(filepath, 0o755)
            return True
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        print_error(f"Download failed: {e}")
        if filepath.exists():
            filepath.unlink()
        return False


def download_version(version: str) -> bool:
    """Download a specific version."""
    url = get_download_url(version)
    if not url:
        print_error(f"Could not get download URL for {version}")
        return False

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = get_appimage_path(version)

    if filepath.exists():
        print_success("Already downloaded")
        return True

    print_info(f"⬇️  Downloading {version}...")
    if not download_file(url, filepath):
        return False

    print_success("Download complete")
    return True


def _backup_existing_file(file_path: Path) -> None:
    """Backup an existing file by renaming it."""
    backup_path = file_path.with_suffix(".AppImage.backup")
    if backup_path.exists():
        backup_path.unlink()
    file_path.rename(backup_path)
    print_info("Backed up existing Cursor AppImage")


def _remove_case_variants(link: Path) -> None:
    """Remove any existing cursor appimage files with different case."""
    for pattern in CURSOR_APPIMAGE_PATTERNS:
        for existing_file in link.parent.glob(pattern):
            if (
                existing_file.name.lower() == "cursor.appimage"
                and existing_file != link
            ):
                if existing_file.is_symlink():
                    existing_file.unlink()
                elif existing_file.exists():
                    _backup_existing_file(existing_file)
                return  # Only handle one variant


def create_symlink(target: Path, link: Path) -> bool:
    """Create a symlink, removing existing one if present."""
    link.parent.mkdir(parents=True, exist_ok=True)

    # Remove any existing cursor appimage files with different case
    _remove_case_variants(link)

    # Remove the target link if it exists
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        _backup_existing_file(link)

    try:
        link.symlink_to(target)
        return True
    except OSError:
        return False


def update_desktop_file() -> bool:
    """Update desktop file to point to ~/.local/bin/cursor.AppImage."""
    if not DESKTOP_FILE.exists():
        return False

    try:
        with open(DESKTOP_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        updated = False
        for line in lines:
            if line.startswith("Exec="):
                parts = line.strip().split()
                args = " " + " ".join(parts[1:]) if len(parts) > 1 else ""
                new_lines.append(f"Exec={CURSOR_APPIMAGE}{args}\n")
                updated = True
            else:
                new_lines.append(line)

        if updated:
            DESKTOP_FILE.write_text("".join(new_lines), encoding="utf-8")
        return updated
    except OSError:
        return False


def select_version(version: str, show_success: bool = True) -> bool:
    """Select a version by creating symlink."""
    appimage_path = get_appimage_path(version)

    if not appimage_path.exists():
        print_error(f"Version {version} not found locally")
        return False

    if not create_symlink(appimage_path, CURSOR_APPIMAGE):
        print_error(f"Failed to activate {version}")
        return False

    update_desktop_file()

    running_path = get_running_cursor_path()
    if running_path and running_path.resolve() != CURSOR_APPIMAGE.resolve():
        if running_path.exists() and os.access(running_path.parent, os.W_OK):
            try:
                create_symlink(appimage_path, running_path)
            except OSError:
                pass

    if show_success:
        print_success(
            f"{version} is now active. Please restart Cursor to use the new version."
        )
    return True
