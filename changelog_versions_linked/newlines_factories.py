"""Factories for creating newlines in changelog files."""

from __future__ import annotations

import abc
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

__all__ = ["EofNewlinesFactory", "ReNewlinesFactory"]


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

    @classmethod
    def before(cls, re_pattern: str) -> Self:
        """Create callable for inserting newlines before a matching regex."""
        return cls(re_pattern, use_insert=True)

    @classmethod
    def after(cls, re_pattern: str) -> Self:
        """Create callable for inserting newlines after a matching regex."""
        return cls(re_pattern, use_insert=False)

    def __init__(
        self,
        re_pattern: str,
        flags: int = 0,
        *,
        use_insert: bool = False,
    ) -> None:
        """Initialize the regex pattern with flags."""
        self.re = re.compile(re_pattern, flags=flags)
        self.last_found = None
        self.use_insert = use_insert

    def __call__(self, contents: str, lines_to_add: Iterable[str]) -> str:
        """Override to insert newlines before a matching regular expression."""
        found = None
        results = []
        for line in contents.splitlines():
            if found is not None or not (found := self.re.search(line)):
                new_lines = [line]
            elif self.use_insert:
                new_lines = (*lines_to_add, line)
            else:
                new_lines = (line, *lines_to_add)

            self.last_found = found
            results.extend(new_lines)

        return "\n".join(results)
