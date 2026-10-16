"""TokenHound: secret scanner for AI-era codebases."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tokenhound")
except PackageNotFoundError:  # pragma: no cover - only when running from a raw checkout
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
