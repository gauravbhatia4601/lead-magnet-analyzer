from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def sync_playwright():
    yield MagicMock()
