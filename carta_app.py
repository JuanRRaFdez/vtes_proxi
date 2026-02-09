import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
)
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QPixmap
from logicas.recorte.constantes import VTES_CARD_ASPECT_RATIO

class CartaApp(QMainWindow):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Mantener proporción de carta VTES en QLabel o widget personalizado
        vtes_ratio = VTES_CARD_ASPECT_RATIO
        for label_name in ["cripta_label", "libreria_label"]:
            label = getattr(self, label_name, None)
            if label is not None:
                height = label.height()
                width = int(height * vtes_ratio)
                label.setFixedWidth(width)
                # Si hay imagen, reescalar para el nuevo tamaño
                # Compatibilidad con QLabel y CartaImageWidget
                pixmap = getattr(label, "pixmap", None)
                if callable(pixmap):
                    pixmap = pixmap()
                elif isinstance(pixmap, QPixmap):
                    pass
                else:
                    pixmap = None
                if pixmap:
                    KEEP_ASPECT_RATIO = 1  # Qt.KeepAspectRatio
                    SMOOTH_TRANSFORMATION = 1  # Qt.SmoothTransformation
                    if hasattr(label, "setPixmap"):
                        label.setPixmap(pixmap.scaled(width, height, KEEP_ASPECT_RATIO, SMOOTH_TRANSFORMATION))
                    elif hasattr(label, "set_pixmap"):
                        label.set_pixmap(pixmap.scaled(width, height, KEEP_ASPECT_RATIO, SMOOTH_TRANSFORMATION))
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Creador de Cartas VTES')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        from ventana.cripta_widget import CriptaWidget
        self.cripta_tab = CriptaWidget(importar_imagen_callback=self.importar_imagen)
        self.cripta_label = self.cripta_tab.cripta_label
        self.cripta_title = self.cripta_tab.cripta_title
        from ventana.libreria_widget import LibreriaWidget
        self.libreria_tab = LibreriaWidget(importar_imagen_callback=self.importar_imagen)
        self.libreria_label = self.libreria_tab.libreria_label
        # Pestaña Configuración
        from ventana.configuracion_widget import ConfiguracionWidget
        self.config_tab = ConfiguracionWidget(
            carta_title_label=self.cripta_title, 
            cripta_widget=self.cripta_tab,
            libreria_widget=self.libreria_tab
        )
        # Añadir pestañas
        self.tabs.addTab(self.cripta_tab, 'Cripta')
        self.tabs.addTab(self.libreria_tab, 'Librería')
        self.tabs.addTab(self.config_tab, 'Configuración')
        self.tabs.setMinimumSize(400, 400)
        self.setCentralWidget(self.tabs)

    @pyqtSlot()
    def importar_imagen(self, widget, *args, **kwargs):
        # Delegar el flujo completo al importador modular
        if widget is self.cripta_tab:
            label = self.cripta_label
        elif widget is self.libreria_tab:
            label = self.libreria_label
        else:
            label = None
        from logicas.seleccion.importador_imagen import importar_imagen
        def on_pixmap_ready(pixmap):
            self.mostrar_imagen_recortada(widget, pixmap)
        importar_imagen(self, label, on_pixmap_ready)

    def mostrar_imagen_recortada(self, widget, pixmap):
        # Muestra la imagen recortada ocupando todo el alto, alineada a la izquierda
        if widget is self.cripta_tab:
            label = self.cripta_label
        elif widget is self.libreria_tab:
            label = self.libreria_label
        else:
            return
        label.show()  # Asegura que el QLabel está visible
        # Para CartaImageWidget (cripta/librería), pasamos SIEMPRE el
        # pixmap recortado a resolución completa y dejamos que el widget
        # lo escale internamente. Para un QLabel normal, lo escalamos al
        # alto disponible manteniendo proporción.
        if hasattr(label, "set_pixmap") and not hasattr(label, "setPixmap"):
            # CartaImageWidget
            label.set_pixmap(pixmap)
        else:
            # QLabel u otro widget similar
            label_height = label.height()
            SMOOTH_TRANSFORMATION = 1  # Qt.SmoothTransformation
            if pixmap.height() > 0:
                scaled_pixmap = pixmap.scaledToHeight(label_height, SMOOTH_TRANSFORMATION)
            else:
                scaled_pixmap = pixmap
            if hasattr(label, "setPixmap"):
                label.setPixmap(scaled_pixmap)



## Punto de entrada movido a main.py
