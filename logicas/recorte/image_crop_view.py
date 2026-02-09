from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QRubberBand, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QRect, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap

# Importar la función de recorte modularizada y constantes
from logicas.recorte.recorte import recortar_pixmap
from logicas.recorte.constantes import VTES_CARD_ASPECT_RATIO

class CropGraphicsView(QGraphicsView):
    def __init__(self, pixmap, aspect_ratio=None, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.aspect_ratio = aspect_ratio
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self.pixmap_item)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.crop_rect = QRect()
        self.setDragMode(QGraphicsView.NoDrag)
        from PyQt5.QtGui import QPainter
        self.setRenderHint(QPainter.Antialiasing)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # Usar valores literales para ScrollBarPolicy y AspectRatioMode
        self.setHorizontalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOff
        self.setVerticalScrollBarPolicy(1)    # Qt.ScrollBarAlwaysOff
        self.fitInView(self.pixmap_item, 1)  # Qt.KeepAspectRatio

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.pixmap_item, 1)  # Qt.KeepAspectRatio

    def mousePressEvent(self, event):
        if event.button() == 1:
            self.origin = event.pos()
            # Si ya hay una selección, la reemplazamos
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            # Usar el aspect ratio pasado como parámetro, o el estándar de VTES
            aspect_ratio = self.aspect_ratio if self.aspect_ratio is not None else VTES_CARD_ASPECT_RATIO
            start = self.origin
            end = event.pos()
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            if abs(dx) > abs(dy):
                width = dx
                height = int(abs(dx) / aspect_ratio) * (1 if dy >= 0 else -1)
            else:
                height = dy
                width = int(abs(dy) * aspect_ratio) * (1 if dx >= 0 else -1)
            new_end = QPoint(start.x() + width, start.y() + height)
            rect = QRect(start, new_end).normalized()
            self.rubberBand.setGeometry(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.origin.isNull():
            self.crop_rect = self.rubberBand.geometry()
            # La selección permanece visible hasta confirmar o crear una nueva
            self.origin = QPoint()  # Reset para permitir nueva selección
        super().mouseReleaseEvent(event)

    def clear_selection(self):
        self.rubberBand.hide()

    def get_crop_rect(self):
        return self.crop_rect

class ImageCropView(QWidget):
    cropConfirmed = pyqtSignal(QPixmap)

    def __init__(self, pixmap, aspect_ratio=None, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.view = CropGraphicsView(pixmap, aspect_ratio=aspect_ratio)
        self.btn_confirm = QPushButton('Confirmar recorte')
        self.btn_confirm.clicked.connect(self.confirm_crop)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.btn_confirm)
        self.setLayout(layout)

    def confirm_crop(self):
        crop_rect = self.view.get_crop_rect()
        if not crop_rect.isNull():
            pixmap_item = self.view.pixmap_item
            pixmap_rect_scene = pixmap_item.sceneBoundingRect()
            crop_top_left = self.view.mapToScene(crop_rect.topLeft())
            crop_bottom_right = self.view.mapToScene(crop_rect.bottomRight())
            # Usar el aspect ratio pasado como parámetro, o el estándar de VTES
            aspect_ratio = self.view.aspect_ratio if (hasattr(self.view, 'aspect_ratio') and self.view.aspect_ratio is not None) else VTES_CARD_ASPECT_RATIO
            cropped = recortar_pixmap(
                self.pixmap,
                crop_rect,
                pixmap_rect_scene,
                crop_top_left,
                crop_bottom_right,
                aspect_ratio=None  # No forzar aspect ratio ni recorte extra
            )
            self.cropConfirmed.emit(cropped)
        self.view.clear_selection()
