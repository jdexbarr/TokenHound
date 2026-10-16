"""Exception hierarchy. The CLI maps every :class:`TokenHoundError` to exit code 2."""


class TokenHoundError(Exception):
    """Base class for expected, user-facing errors (bad input, unreadable rules, ...)."""


class SourceError(TokenHoundError):
    """A source cannot be read (missing path, not a git repository, ...)."""
