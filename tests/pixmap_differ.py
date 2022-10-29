import typing
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPixmap, QPainter, QColor
from space_tracer import LiveImageDiffer, LivePainter
from space_tracer.live_image import LiveImage


class PixmapDiffer(LiveImageDiffer):
    def __init__(self, diffs_path: Path = None, request=None, is_displayed=True):
        """ Initialize the object and clean out the diffs path.

        :param diffs_path: The folder to write comparison images in, or None
            if you don't want to write any. Will be created if it doesn't exist.
        :param request: The Pytest request fixture, if you want to generate
            default file names based on the current test name.
        :param is_displayed: True if the comparison should be displayed on the
            live canvas.
        """
        super().__init__(diffs_path, request, is_displayed)
        self.actual = self.expected = None
        self.name: typing.Optional[str] = None

    @contextmanager
    def create_painters(
            self,
            width: int,
            height: int,
            name: str = None,
            max_diff: int = 0) -> typing.Iterator[typing.Tuple[QPainter, QPainter]]:
        self.tolerance = max_diff
        try:
            yield self.start(width, height, name)
        finally:
            self.end()
        self.assert_equal(self.actual, self.expected)

    def start(self,
              width: int,
              height: int,
              name: str = None) -> typing.Tuple[QPainter, QPainter]:
        """ Create painters for the actual and expected images.

        Caller must either call end() or assert_equal() to properly clean up
        the painters and pixmaps. Caller may either paint through the returned
        painters, or call the end() method and create a new painter on the
        same device. Order matters, though!
        """
        self.name = name
        self.actual = LiveQPainter(QPixmap(width, height))
        self.expected = LiveQPainter(QPixmap(width, height))
        return self.actual.painter, self.expected.painter

    def end(self):
        if self.actual is not None:
            self.actual.end()
        if self.expected is not None:
            self.expected.end()

    def start_diff(self, size: LiveImage.Size):
        """ Start the comparison by creating a diff painter.

        Overrides must set self.diff to a LivePainter object.
        :param size: the size of painter to put in self.diff.
        """
        self.diff = LiveQPainter(QPixmap(*size))

    def end_diff(self) -> LiveImage:
        self.diff.end()
        self.end()
        return self.diff

    def compare(self,
                actual: LiveImage = None,
                expected: LiveImage = None,
                file_prefix: str = None) -> LiveImage:
        if file_prefix is None:
            file_prefix = self.name
        if actual is None:
            actual = self.actual
        if expected is None:
            expected = self.expected
        return super().compare(actual, expected, file_prefix)

    def assert_equal(self,
                     actual: LiveImage = None,
                     expected: LiveImage = None,
                     file_prefix: str = None):
        __tracebackhide__ = True
        if file_prefix is None:
            file_prefix = self.name
        if actual is None:
            actual = self.actual
        if expected is None:
            expected = self.expected
        super().assert_equal(actual, expected, file_prefix)


class LiveQPainter(LivePainter):
    WHITE = QColor('white')

    def __init__(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.painter = QPainter(self.pixmap)
        self.pixmap.fill(self.WHITE)

    def set_pixel(self, position: LiveImage.Position, fill: LiveImage.Fill):
        self.painter.setPen(QColor(*fill))
        self.painter.drawPoint(*position)

    def get_pixel(self, position: LiveImage.Position) -> LiveImage.Fill:
        return self.painter.device().toImage().pixelColor(*position).toTuple()

    def get_size(self) -> LiveImage.Size:
        return self.pixmap.size().toTuple()

    def convert_to_png(self) -> bytes:
        self.end()
        image_bytes = QByteArray()
        buffer = QBuffer(image_bytes)
        buffer.open(QIODevice.WriteOnly)
        try:
            # noinspection PyTypeChecker
            self.pixmap.toImage().save(buffer, "PNG")
            return bytes(buffer.data())
        finally:
            buffer.close()

    def end(self):
        if self.painter.isActive():
            self.painter.end()
