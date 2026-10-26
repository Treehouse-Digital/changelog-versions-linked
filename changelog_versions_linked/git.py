"""Git-related utilities for changelog versions linked."""

import re
import subprocess
from pathlib import Path

__all__ = ["get_tracked_changelog_files", "to_url_from_git"]


def _git(*args: str) -> str:
    """Run a git command and return its output as a string."""
    result = subprocess.run(
        ["git", *(str(arg) for arg in args)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_tracked_changelog_files() -> list[Path]:
    """Call git ls-files to get any tracked CHANGELOG.md."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "*CHANGELOG.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(filename) for filename in result.stdout.split("\0") if filename]


def to_url_from_git() -> callable[[str], str]:
    """Generate a URL template function based on the current Git remote."""
    current_branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    current_remote = _git("config", "--get", f"branch.{current_branch}.remote")
    remote_url = _git("config", "--get", f"remote.{current_remote}.url")

    if "github.com" in remote_url:
        prefix = remote_url.removesuffix(".git")
        prefix = re.sub(r".*?([^/:]+/[^/]+)$", r"\1", prefix)
        prefix = f"https://github.com/{prefix}/releases/tag/"

        def to_url(version: str) -> str:
            return f"{prefix}{version}"

    elif "gitlab.com" in remote_url:
        prefix = remote_url.removesuffix(".git")
        prefix = re.sub(r".*gitlab\.com[:/]", "", prefix)
        prefix = f"https://gitlab.com/{prefix}/-/releases/"

        def to_url(version: str) -> str:
            return f"{prefix}{version}"

    else:
        raise NotImplementedError

    return to_url
