#!/bin/env python3
"""Ensure all version links are present in the changelog.

By default it assumes it's being run from a Git repository and attempts to:

- Operate on ANY `CHANGELOG.md` filenames in the repository
- Guess the URL based off `git remote` found:
  - If GitHub or GitLab detected, assume it uses releases
- Blindly adds the link to the bottom of the `CHANGELOG.md` file

These can be overridden with the appropriate command-line arguments:

    $ changelog-versions-linked  # Default behavior
    $ changelog-versions-linked --insert-after-re '<!-- AFTER ME -->'
    $ changelog-versions-linked --url-template 'https://example.com/releases/<VERSION>'
    $ changelog-versions-linked HISTORY.md  # Custom changelog file

"""

from __future__ import annotations

import argparse
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import rich.pretty
import rich.traceback
from rich.logging import RichHandler

from .git import get_tracked_changelog_files, to_url_from_git
from .newlines_factories import EofNewlinesFactory, ReNewlinesFactory

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

_NAME = "changelog-versions-linked"
LOGGER = logging.getLogger(_NAME)


class _U(Protocol):
    """Protocol for URL creations functions."""

    def __call__(self, version: str) -> str:
        """Generate a URL for the given version."""


class _C(Protocol):
    """Protocol for newline factories."""

    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Create the new content with the lines to add."""


VERSION_RE = re.compile(
    r"^##\s*\[([^\]]+)\] - \d{4}-\d{2}-\d{2}", flags=re.MULTILINE | re.IGNORECASE
)
"""Regular expression to match version headers in the changelog."""


def on_ci() -> bool:
    """Whether we're on CI."""
    lower_true_values = ("true", "t", "1", "yes", "y", "on")
    return (value := os.getenv("CI")) and value.lower() in lower_true_values


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and read/write out ruff configurations."""
    module_docstrings = str(__doc__)  # Ensure at least 1 empty line in there!
    description, epilog = module_docstrings.split("\n\n", 1)
    parser = argparse.ArgumentParser(
        _NAME,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    v_help = "Verbosity (of LOGGER). WARNING by default, -v: INFO, -vv: DEBUG"
    parser.add_argument("-v", help=v_help, action="count", default=0)
    parser.add_argument(
        "-C",
        "--cwd",
        metavar="DIR",
        default=Path.cwd(),
        type=Path,
        help="Change to this directory before running.",
    )
    parser.add_argument(
        "--url-template",
        help="Explicit template for generating URLs, where <VERSION> will be replaced",
    )
    parser.add_argument(
        "--no-ci-skip", action="store_true", help="Force to still run even on CI"
    )

    parser.set_defaults(insert_method=EofNewlinesFactory())
    insert_group = parser.add_mutually_exclusive_group()
    insert_help_suffix = "the first line found matching the regular expression."
    insert_group.add_argument(
        "--insert-eof",
        dest="insert_method",
        action="store_const",
        const=EofNewlinesFactory(),
        help="Add new URL lines at the end of the file (default insert method).",
    )
    insert_group.add_argument(
        "--insert-after-re",
        metavar="REGEX",
        dest="insert_method",
        type=ReNewlinesFactory.after,
        help=f"Add new URL lines after {insert_help_suffix}",
    )
    insert_group.add_argument(
        "--insert-before-re",
        metavar="REGEX",
        dest="insert_method",
        type=ReNewlinesFactory.before,
        help=f"Insert new URL lines before {insert_help_suffix}",
    )
    parser.add_argument(
        "filenames", type=Path, nargs="*", help="Explicit CHANGELOG filenames to check."
    )
    args = parser.parse_args(argv)
    if args.cwd:  # Change working directory if requested
        os.chdir(args.cwd)

    verbose_index = max(0, min(2, args.v))  # Clamp within the range of levels
    LOGGER.setLevel([logging.WARNING, logging.INFO, logging.DEBUG][verbose_index])
    if on_ci() and not args.no_ci_skip:
        LOGGER.info("Skipping as we're on CI and --no-ci-skip not passed in")
    else:
        if not args.url_template:
            to_url = to_url_from_git()
        else:

            def to_url(version: str) -> str:
                return args.url_template.replace("<VERSION>", version)

        filenames = [] if args.filenames else get_tracked_changelog_files()
        for raw_filename in args.filenames:
            if (filename := raw_filename.resolve()).is_file():
                filenames.append(filename)
            else:
                parser.error(f"File not found: {str(raw_filename)!r}")

        LOGGER.info("%s filenames to check", len(filenames))
        errors = []
        for path in filenames:
            try:
                update_changelog_with_urls(args.insert_method, to_url, path)
            except Exception as e:  # noqa: BLE001 # We're raising it all later anyways
                errors.append(e)

        if errors:
            msg = "Errors occurred while updating changelogs"
            raise ExceptionGroup(msg, errors)


def update_changelog_with_urls(insert_method: _C, to_url: _U, path: Path) -> None:
    """Update the changelog at the given path with URLs for found versions."""
    LOGGER.info("Checking %s", path)
    contents = path.read_text()

    lines_to_add = [
        f"[{found_version[1]}]: {url}"
        for found_version in VERSION_RE.finditer(path.read_text())
        if (url := to_url(found_version[1]))
    ]

    existing_versions = {
        match[1].casefold()
        for match in re.finditer(
            r"^ {0,3}\[([^\]\n]+)\]:\s*\S+", contents, flags=re.MULTILINE
        )
    }
    lines_to_add = [
        line
        for line in lines_to_add
        if line.partition("]:")[0][1:].casefold() not in existing_versions
    ]

    if lines_to_add:
        new_contents = insert_method(contents, lines_to_add)
        if (
            isinstance(insert_method, ReNewlinesFactory)
            and insert_method.last_found is None
        ):
            LOGGER.warning(
                f"No lines matching {insert_method.re.pattern!r} in {path}, "
                "not edits made"
            )
        else:
            path.write_text(new_contents)


if __name__ == "__main__":
    rich.traceback.install(code_width=None, width=None)
    rich.pretty.install()
    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_width=None,
                tracebacks_code_width=None,
            )
        ],
    )
    main()
