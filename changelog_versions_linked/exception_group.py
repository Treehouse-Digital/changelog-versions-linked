"""Custom exception group for errors occurring while updating changelogs."""

from __future__ import annotations

import contextlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType

if sys.version_info < (3, 11):

    class _GroupedError(Exception):
        def __init__(self, msg: str, errors: list[Exception]) -> None:
            lines = [msg, *(f"{type(error).__name__}: {error}" for error in errors)]
            super().__init__("\n".join(lines))
            self.errors = errors
else:
    _GroupedError = ExceptionGroup  # noqa: F821

__all__ = ["GroupedError"]


class GroupedError(_GroupedError):
    """Custom exception group for errors occurring while updating changelogs."""

    @classmethod
    @contextlib.contextmanager
    def capture(cls, msg: str) -> Generator[type[contextlib.suppress]]:
        """Context manager to capture exceptions and raise if any occurred."""
        errors: list[Exception] = []

        class Capture(contextlib.suppress):
            """Context manager to append captured exceptions to the errors list."""

            def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc_value: BaseException | None,
                exc_tb: TracebackType | None,
            ) -> bool | None:
                if result := super().__exit__(exc_type, exc_value, exc_tb):
                    errors.append(exc_value)
                return result

        try:
            yield Capture
        finally:
            if errors:
                raise cls(msg, errors)
