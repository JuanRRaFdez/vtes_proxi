from logicas.seleccion.selector_archivo import seleccionar_imagen_tkinter
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from logicas.recorte.image_crop_view import ImageCropView
from logicas.recorte.constantes import VTES_CARD_ASPECT_RATIO

def importar_imagen(parent, label_widget, on_pixmap_ready):
    """
    Flujo completo: selector de archivo (tkinter), recorte (ImageCropView), callback con QPixmap recortado.
    parent: QWidget padre (para el QDialog)
    label_widget: QLabel destino (para aspect ratio)
    on_pixmap_ready: función callback(QPixmap)
    """
    selected_file = seleccionar_imagen_tkinter()
    if not selected_file:
        return
    pixmap = QPixmap(selected_file)
    # Usar SIEMPRE la proporción oficial de carta VTES (63x88mm)
    # para que el recorte resultante tenga exactamente esa relación.
    aspect_ratio = VTES_CARD_ASPECT_RATIO
    # Abrir ventana de recorte
    dialog = QDialog(parent)
    dialog.setWindowTitle("Recortar imagen")
    dialog.setModal(True)
    dialog_layout = QVBoxLayout(dialog)
    image_crop_view = ImageCropView(pixmap, aspect_ratio=aspect_ratio)
    dialog_layout.addWidget(image_crop_view)
    def on_crop_confirmed(cropped):
        dialog.accept()
        on_pixmap_ready(cropped)
    image_crop_view.cropConfirmed.connect(on_crop_confirmed)
    dialog.exec_()
