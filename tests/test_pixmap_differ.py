from PySide6.QtCore import QRectF

from tests.pixmap_differ import PixmapDiffer


def test_no_diff(pixmap_differ: PixmapDiffer):
    pixmap_differ.start(500, 250)
    try:
        expected = pixmap_differ.expected.painter
        actual = pixmap_differ.actual.painter

        expected.fillRect(QRectF(100, 100, 100, 100), 'black')

        actual.setRenderHint(actual.Antialiasing, True)
        actual.fillRect(QRectF(100, 100, 100, 100), 'black')
    finally:
        pixmap_differ.end()

    pixmap_differ.compare()
    assert pixmap_differ.diff_count == 0


def test_diff(pixmap_differ: PixmapDiffer):
    """ Reports a difference when not smeared. """
    pixmap_differ.start(500, 250)
    try:
        expected = pixmap_differ.expected.painter
        expected.fillRect(expected.window(), 'ivory')
        actual = pixmap_differ.actual.painter
        actual.fillRect(actual.window(), 'ivory')

        expected.fillRect(QRectF(100, 100, 100, 100), 'black')

        actual.setRenderHint(actual.Antialiasing, True)
        actual.fillRect(QRectF(100.5, 100, 100, 100), 'black')
    finally:
        pixmap_differ.end()

    pixmap_differ.compare()
    assert pixmap_differ.diff_count == 200


def test_diff_radius(pixmap_differ: PixmapDiffer):
    pixmap_differ.start(500, 250)
    try:
        pixmap_differ.radius = 3
        pixmap_differ.tolerance = 26
        expected = pixmap_differ.expected.painter
        actual = pixmap_differ.actual.painter

        expected.drawText(100, 50, 'Hello')
        expected.fillRect(QRectF(100, 100, 100, 100), 'black')

        actual.drawText(100, 50, 'HelIo')
        actual.setRenderHint(actual.Antialiasing, True)
        actual.fillRect(QRectF(100.5, 100, 100, 100), 'black')
    finally:
        pixmap_differ.end()
    pixmap_differ.compare()

    assert pixmap_differ.diff_count == 0


def test_diff_radius_catches_bigger_diffs(pixmap_differ: PixmapDiffer):
    pixmap_differ.start(500, 250)
    try:
        pixmap_differ.radius = 3
        pixmap_differ.tolerance = 26
        actual = pixmap_differ.actual.painter

        actual.drawLine(100, 100, 102, 100)
    finally:
        pixmap_differ.end()
    pixmap_differ.compare()

    assert pixmap_differ.diff_count > 0
