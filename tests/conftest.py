from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from tests.pixmap_differ import PixmapDiffer


@pytest.fixture(scope='session')
def qt_application() -> QApplication:
    return QApplication()


@pytest.fixture(scope='session')
def pixmap_differ(qt_application, request) -> PixmapDiffer:
    diffs_path = Path(__file__).parent / 'pixmap_diffs'
    differ = PixmapDiffer(diffs_path, request)
    yield differ
    differ.remove_common_prefix()
