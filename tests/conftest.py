from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from tests.pixmap_differ import PixmapDiffer


@pytest.fixture(scope='session')
def qt_application() -> QApplication:
    return QApplication()


@pytest.fixture(scope='session')
def session_pixmap_differ(qt_application, request) -> PixmapDiffer:
    """ Track all pixmaps compared in a session. """
    diffs_path = Path(__file__).parent / 'pixmap_diffs'
    differ = PixmapDiffer(diffs_path, request)
    yield differ
    differ.remove_common_prefix()


@pytest.fixture
def pixmap_differ(request, session_pixmap_differ):
    """ Pass the current request to the session pixmap differ. """
    session_pixmap_differ.request = request
    yield session_pixmap_differ
