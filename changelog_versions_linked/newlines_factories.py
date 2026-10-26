"""Factories for creating newlines in changelog files."""

import abc
import re
from collections.abc import Iterable

__all__ = [
    "EofNewlinesFactory",
    "NewlinesAfterFactory",
    "NewlinesBeforeFactory",
    "ReNewlinesFactory",
]


class AbcNewlinesFactory(abc.ABC):
    """Abstract base class for newline factories."""

    @abc.abstractmethod
    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Create the new content with the lines to add."""


class EofNewlinesFactory(AbcNewlinesFactory):
    """Factory for inserting newlines at the end of the file."""

    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Explicitly insert newlines at the end of the file."""
        return "\n".join([contents, *lines_to_add])


class ReNewlinesFactory(AbcNewlinesFactory):
    """Abstract base class for regex-based newline factories."""

    def __init__(self, re_pattern: str, flags: int = 0) -> None:
        """Initialize the regex pattern with flags."""
        self.re = re.compile(re_pattern, flags=flags)


class NewlinesBeforeFactory(AbcNewlinesFactory):
    """Factory for inserting newlines before a matching regular expression."""

    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Override to insert newlines before a matching regular expression."""
        results = []
        found = None
        for line in contents.splitlines():
            if found is None and (found := self.re.search(line)):
                results += lines_to_add
            results.append(line)
        return "\n".join(results)


class NewlinesAfterFactory(AbcNewlinesFactory):
    """Factory for inserting newlines after a matching regular expression."""

    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Override to insert newlines after a matching regular expression."""
        results = []
        found = None
        for line in contents.splitlines():
            results.append(line)
            if found is None and (found := self.re.search(line)):
                results += lines_to_add
        return "\n".join(results)
