import typing
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage
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
        self.actual: LiveQPainter | None = None
        self.expected: LiveQPainter | None = None
        self.name: typing.Optional[str] = None
        self.default_radius: int = 1
        self.radius = self.default_radius
        self.background = QColor('ivory')

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
        self.radius = self.default_radius
        self.actual = LiveQPainter(QPixmap(width, height))
        self.expected = LiveQPainter(QPixmap(width, height))
        self.actual.painter.setBackground(self.background)
        self.expected.painter.setBackground(self.background)
        window = self.actual.painter.window()
        self.actual.painter.eraseRect(window)
        self.expected.painter.eraseRect(window)
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
        width, height = size
        buffer = np.zeros(shape=(height, width, 4), dtype=np.uint8)
        self.diff = LiveNumpyPainter(buffer)

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
        if self.radius <= 1:
            return super().compare(actual, expected, file_prefix)

        smeared1 = self.smear(actual)
        smeared2 = self.smear(expected)

        compare = super().compare(smeared1, smeared2, file_prefix)
        return compare

    def smear(self, painter: 'LiveQPainter') -> 'LiveNumpyPainter':
        if self.radius > 6:
            # Smearing more than 127 neighbours can overflow uint16 dtype.
            raise ValueError('Maximum radius is 6.')
        a = pixmap_to_numpy(painter.pixmap)
        width, height = a.shape[:2]
        totals = np.zeros(shape=(width, height, 4), dtype=np.int16)
        counts = np.zeros(shape=(width, height, 1), dtype=np.uint8)
        for dx in range(-self.radius + 1, self.radius):
            for dy in range(-self.radius + 1, self.radius):
                src_start_x = src_end_x = None
                tgt_start_x = tgt_end_x = None
                if dx < 0:
                    src_start_x = -dx
                    tgt_end_x = dx
                elif 0 < dx:
                    src_end_x = -dx
                    tgt_start_x = dx
                src_start_y = src_end_y = None
                tgt_start_y = tgt_end_y = None
                if dy < 0:
                    src_start_y = -dy
                    tgt_end_y = dy
                elif 0 < dy:
                    src_end_y = -dy
                    tgt_start_y = dy
                tgt_slice = (slice(tgt_start_x, tgt_end_x),
                             slice(tgt_start_y, tgt_end_y))
                src_slice = (slice(src_start_x, src_end_x),
                             slice(src_start_y, src_end_y))
                totals[tgt_slice] += a[src_slice]
                counts[tgt_slice] += 1
        totals //= counts
        return LiveNumpyPainter(totals)

    def display_diff(self, actual: LivePainter, expected: LivePainter):
        super().display_diff(self.actual, self.expected)

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

    def __init__(self, pixmap: QPixmap, fill: QColor | None = WHITE):
        self.pixmap = pixmap
        self.painter = QPainter(self.pixmap)
        if fill is not None:
            self.pixmap.fill(fill)

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


class LiveNumpyPainter(LivePainter):
    def __init__(self, buffer: np.ndarray):
        if len(buffer.shape) != 3:
            raise ValueError('buffer shape must be (height, width, channels).')
        if buffer.shape[-1] != 4:
            raise ValueError('buffer must have 4 channels: RGBA.')
        self.buffer = buffer

    def set_pixel(self, position: LiveImage.Position, fill: LiveImage.Fill):
        x, y = position
        self.buffer[y, x] = fill

    def get_pixel(self, position: LiveImage.Position) -> LiveImage.Fill:
        x, y = position
        return tuple(self.buffer[y, x])

    def get_size(self) -> LiveImage.Size:
        height, width, channels = self.buffer.shape
        return width, height

    def convert_to_png(self) -> bytes:
        image = numpy_to_image(self.buffer)
        image_bytes = QByteArray()
        buffer = QBuffer(image_bytes)
        buffer.open(QIODevice.WriteOnly)
        try:
            # noinspection PyTypeChecker
            image.save(buffer, "PNG")
            return bytes(buffer.data())
        finally:
            buffer.close()


def pixmap_to_numpy(pixmap: QPixmap) -> np.ndarray:
    image = pixmap.toImage()
    buffer = image.bits().tobytes()
    a = np.frombuffer(buffer, dtype=np.uint8).reshape(
        (image.height(), image.width(), 4))
    return a


def numpy_to_image(a: np.ndarray) -> QImage:
    a_short = a.astype(np.uint8)
    height, width, channel = a_short.shape
    bytes_per_line = channel * width
    image = QImage(a_short.data,
                   width,
                   height,
                   bytes_per_line,
                   QImage.Format_RGBA8888)
    return image
