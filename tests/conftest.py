import pytest
from PySide6.QtWidgets import QApplication

from tests.pixmap_differ import PixmapDiffer


@pytest.fixture(scope='session')
def qt_application() -> QApplication:
    return QApplication()


@pytest.fixture(scope='session')
def pixmap_differ(qt_application) -> PixmapDiffer:
    return PixmapDiffer()
