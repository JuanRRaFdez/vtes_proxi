import json
import os
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QColorDialog, QComboBox, QSlider
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from configuracion import load_config_data, save_config_data

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

FONTS_DIR = get_resource_path("fonts")

def _deep_merge_dicts(defaults: dict, overrides: dict) -> dict:
    merged = dict(defaults)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged

def cargar_config():
    defaults = {
        "nombre_carta": {
            "fuente": "fonts/MatrixExtraBold.otf",
            "tamano": 18,
            "color": "#ffffff",
            "alineacion": "centro"
        },
        "texto_habilidad": {
            "fuente": "fonts/Gill Sans.otf",
            "tamano": 12,
            "color": "#ffffff",
            "opacidad_fondo": 50
        }
    }

    data = load_config_data({})
    return _deep_merge_dicts(defaults, data)

def guardar_config(data):
    save_config_data(data)

def obtener_fuentes_disponibles():
    """Obtiene la lista de fuentes disponibles en la carpeta fonts/"""
    fuentes = []
    if os.path.exists(FONTS_DIR):
        for archivo in os.listdir(FONTS_DIR):
            if archivo.endswith(('.otf', '.ttf', '.ttc')):
                nombre_display = os.path.splitext(archivo)[0]
                fuentes.append((nombre_display, archivo))  # Solo el nombre del archivo
    return fuentes

class ConfiguracionWidget(QWidget):
    def __init__(self, carta_title_label=None, cripta_widget=None, libreria_widget=None):
        super().__init__()
        self.carta_title_label = carta_title_label
        self.cripta_widget = cripta_widget
        self.libreria_widget = libreria_widget
        # Layout principal con tres columnas para ganar espacio horizontal
        self.main_layout = QHBoxLayout()
        self.col1_layout = QVBoxLayout()  # Texto (fuente, tamaño, color, alineación)
        self.col2_layout = QVBoxLayout()  # Clan y Senda
        self.col3_layout = QVBoxLayout()  # Librería, Coste y Disciplinas
        self.main_layout.addLayout(self.col1_layout)
        self.main_layout.addLayout(self.col2_layout)
        self.main_layout.addLayout(self.col3_layout)
        self.config = cargar_config()
        
        # Fuente
        self.col1_layout.addWidget(QLabel("Fuente del nombre:"))
        self.font_combo = QComboBox()
        fuentes_disponibles = obtener_fuentes_disponibles()
        fuente_actual = self.config["nombre_carta"].get("fuente", "MatrixExtraBold.otf")
        for nombre, archivo in fuentes_disponibles:
            self.font_combo.addItem(nombre, archivo)
            if archivo == fuente_actual:
                self.font_combo.setCurrentText(nombre)
        self.font_combo.currentIndexChanged.connect(self.cambiar_fuente)
        self.col1_layout.addWidget(self.font_combo)
        
        # Tamaño
        self.col1_layout.addWidget(QLabel("Tamaño de fuente:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self.config["nombre_carta"].get("tamano", 18))
        self.size_spin.valueChanged.connect(self.cambiar_tamano)
        self.col1_layout.addWidget(self.size_spin)
        
        # Color
        self.col1_layout.addWidget(QLabel("Color de fuente:"))
        self.color_btn = QPushButton()
        self.color_btn.setText("Seleccionar color")
        color_actual = self.config["nombre_carta"].get("color", "#ffffff")
        self.color_btn.setStyleSheet(f"background: {color_actual}; color: black;")
        self.color_btn.clicked.connect(self.cambiar_color)
        self.col1_layout.addWidget(self.color_btn)
        
        # Alineación
        self.col1_layout.addWidget(QLabel("Alineación del texto:"))
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItem("Centro", "centro")
        self.alignment_combo.addItem("Izquierda", "izquierda")
        alineacion_actual = self.config["nombre_carta"].get("alineacion", "centro")
        index = self.alignment_combo.findData(alineacion_actual)
        if index >= 0:
            self.alignment_combo.setCurrentIndex(index)
        self.alignment_combo.currentIndexChanged.connect(self.cambiar_alineacion)
        self.col1_layout.addWidget(self.alignment_combo)

        # Configuración de texto de habilidades
        self.col1_layout.addWidget(QLabel(""))
        self.col1_layout.addWidget(QLabel("=== Texto de habilidades ==="))

        texto_hab_config = self.config.get("texto_habilidad", {})

        # Fuente de habilidades
        self.col1_layout.addWidget(QLabel("Fuente de habilidades:"))
        self.ability_font_combo = QComboBox()
        fuentes_disponibles_hab = obtener_fuentes_disponibles()
        fuente_hab_actual = texto_hab_config.get("fuente", "Gill Sans.otf")
        for nombre, archivo in fuentes_disponibles_hab:
            self.ability_font_combo.addItem(nombre, archivo)
            if archivo == fuente_hab_actual:
                self.ability_font_combo.setCurrentText(nombre)
        self.ability_font_combo.currentIndexChanged.connect(self.cambiar_fuente_habilidad)
        self.col1_layout.addWidget(self.ability_font_combo)

        # Tamaño de habilidades
        self.col1_layout.addWidget(QLabel("Tamaño de fuente (habilidades):"))
        self.ability_size_spin = QSpinBox()
        self.ability_size_spin.setRange(8, 48)
        self.ability_size_spin.setValue(texto_hab_config.get("tamano", 12))
        self.ability_size_spin.valueChanged.connect(self.cambiar_tamano_habilidad)
        self.col1_layout.addWidget(self.ability_size_spin)

        # Color de habilidades
        self.col1_layout.addWidget(QLabel("Color de texto (habilidades):"))
        self.ability_color_btn = QPushButton()
        self.ability_color_btn.setText("Seleccionar color")
        color_hab_actual = texto_hab_config.get("color", "#ffffff")
        self.ability_color_btn.setStyleSheet(f"background: {color_hab_actual}; color: black;")
        self.ability_color_btn.clicked.connect(self.cambiar_color_habilidad)
        self.col1_layout.addWidget(self.ability_color_btn)

        # Opacidad del fondo de habilidades
        self.col1_layout.addWidget(QLabel("Opacidad fondo habilidades (%):"))
        self.ability_opacity_slider = QSlider()
        self.ability_opacity_slider.setOrientation(Qt.Horizontal)
        self.ability_opacity_slider.setRange(0, 100)
        self.ability_opacity_slider.setValue(texto_hab_config.get("opacidad_fondo", 50))
        self.ability_opacity_slider.valueChanged.connect(self.cambiar_opacidad_habilidad)
        self.col1_layout.addWidget(self.ability_opacity_slider)
        self.col1_layout.addStretch()
        
        # Columna 2: Clan y Senda
        self.col2_layout.addWidget(QLabel("=== Símbolo de Clan ==="))
        
        # Tamaño del símbolo de clan
        self.col2_layout.addWidget(QLabel("Tamaño del símbolo de clan:"))
        self.clan_size_spin = QSpinBox()
        self.clan_size_spin.setRange(20, 100)
        simbolo_config = self.config.get("simbolo_clan", {})
        self.clan_size_spin.setValue(simbolo_config.get("tamano", 40))
        self.clan_size_spin.valueChanged.connect(self.cambiar_tamano_clan)
        self.col2_layout.addWidget(self.clan_size_spin)
        
        # Alineación del símbolo de clan
        self.col2_layout.addWidget(QLabel("Alineación del símbolo de clan:"))
        self.clan_alignment_combo = QComboBox()
        self.clan_alignment_combo.addItem("Izquierda", "izquierda")
        self.clan_alignment_combo.addItem("Centro", "centro")
        self.clan_alignment_combo.addItem("Derecha", "derecha")
        alineacion_clan_actual = simbolo_config.get("alineacion", "izquierda")
        index_clan = self.clan_alignment_combo.findData(alineacion_clan_actual)
        if index_clan >= 0:
            self.clan_alignment_combo.setCurrentIndex(index_clan)
        self.clan_alignment_combo.currentIndexChanged.connect(self.cambiar_alineacion_clan)
        self.col2_layout.addWidget(self.clan_alignment_combo)
        
        self.col2_layout.addWidget(QLabel(""))  # Espacio
        self.col2_layout.addWidget(QLabel("=== Símbolo de Senda ==="))

        # Tamaño del símbolo de senda
        self.col2_layout.addWidget(QLabel("Tamaño del símbolo de senda:"))
        self.senda_size_spin = QSpinBox()
        self.senda_size_spin.setRange(12, 100)
        simbolo_senda_config = self.config.get("simbolo_senda", {})
        self.senda_size_spin.setValue(simbolo_senda_config.get("tamano", 24))
        self.senda_size_spin.valueChanged.connect(self.cambiar_tamano_senda)
        self.col2_layout.addWidget(self.senda_size_spin)

        # Alineación del símbolo de senda
        self.col2_layout.addWidget(QLabel("Alineación del símbolo de senda:"))
        self.senda_alignment_combo = QComboBox()
        self.senda_alignment_combo.addItem("Izquierda", "izquierda")
        self.senda_alignment_combo.addItem("Derecha", "derecha")
        alineacion_senda_actual = simbolo_senda_config.get("alineacion", "izquierda")
        index_senda = self.senda_alignment_combo.findData(alineacion_senda_actual)
        if index_senda >= 0:
            self.senda_alignment_combo.setCurrentIndex(index_senda)
        self.senda_alignment_combo.currentIndexChanged.connect(self.cambiar_alineacion_senda)
        self.col2_layout.addWidget(self.senda_alignment_combo)
        self.col2_layout.addStretch()
        
        # Columna 3: Librería, Coste y Disciplinas
        self.col3_layout.addWidget(QLabel("=== Símbolo de Librería ==="))
        
        # Tamaño del símbolo de librería
        simbolo_libreria_config = self.config.get("simbolo_libreria", {})
        self.col3_layout.addWidget(QLabel("Tamaño del símbolo de librería:"))
        self.libreria_size_spin = QSpinBox()
        self.libreria_size_spin.setRange(20, 100)
        self.libreria_size_spin.setValue(simbolo_libreria_config.get("tamano", 40))
        self.libreria_size_spin.valueChanged.connect(self.cambiar_tamano_libreria)
        self.col3_layout.addWidget(self.libreria_size_spin)
        
        # Alineación del símbolo de librería
        self.col3_layout.addWidget(QLabel("Alineación del símbolo de librería:"))
        self.libreria_alignment_combo = QComboBox()
        self.libreria_alignment_combo.addItem("Izquierda", "izquierda")
        self.libreria_alignment_combo.addItem("Centro", "centro")
        self.libreria_alignment_combo.addItem("Derecha", "derecha")
        alineacion_libreria_actual = simbolo_libreria_config.get("alineacion", "izquierda")
        index_libreria = self.libreria_alignment_combo.findData(alineacion_libreria_actual)
        if index_libreria >= 0:
            self.libreria_alignment_combo.setCurrentIndex(index_libreria)
        self.libreria_alignment_combo.currentIndexChanged.connect(self.cambiar_alineacion_libreria)
        self.col3_layout.addWidget(self.libreria_alignment_combo)
        
        self.col3_layout.addWidget(QLabel(""))  # Espacio
        self.col3_layout.addWidget(QLabel("=== Símbolo de Coste (Librería/Cripta) ==="))

        # Tamaño del símbolo de coste
        self.col3_layout.addWidget(QLabel("Tamaño del símbolo de coste:"))
        self.cost_size_spin = QSpinBox()
        self.cost_size_spin.setRange(8, 120)
        simbolo_coste_config = self.config.get("simbolo_coste", {})
        self.cost_size_spin.setValue(simbolo_coste_config.get("tamano", 80))
        self.cost_size_spin.valueChanged.connect(self.cambiar_tamano_coste)
        self.col3_layout.addWidget(self.cost_size_spin)

        self.col3_layout.addWidget(QLabel(""))  # Espacio
        self.col3_layout.addWidget(QLabel("=== Símbolos de Disciplina (Librería) ==="))

        # Tamaño del símbolo de disciplina
        self.col3_layout.addWidget(QLabel("Tamaño de los iconos de disciplina:"))
        self.discipline_size_spin = QSpinBox()
        self.discipline_size_spin.setRange(8, 64)
        simbolo_disciplina_config = self.config.get("simbolo_disciplina", {})
        self.discipline_size_spin.setValue(simbolo_disciplina_config.get("tamano", 24))
        self.discipline_size_spin.valueChanged.connect(self.cambiar_tamano_disciplina)
        self.col3_layout.addWidget(self.discipline_size_spin)
        self.col3_layout.addStretch()

        self.setLayout(self.main_layout)

    def cambiar_fuente(self, index):
        fuente_archivo = self.font_combo.itemData(index)
        if fuente_archivo:
            self.config["nombre_carta"]["fuente"] = fuente_archivo
            guardar_config(self.config)
            self.actualizar_cripta_widget()

    def cambiar_tamano(self, value):
        self.config["nombre_carta"]["tamano"] = value
        guardar_config(self.config)
        self.actualizar_cripta_widget()

    def cambiar_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            self.config["nombre_carta"]["color"] = color_hex
            guardar_config(self.config)
            self.color_btn.setStyleSheet(f"background: {color_hex}; color: black;")
            self.actualizar_cripta_widget()

    def cambiar_alineacion(self, index):
        alineacion = self.alignment_combo.itemData(index)
        if alineacion:
            self.config["nombre_carta"]["alineacion"] = alineacion
            guardar_config(self.config)
            self.actualizar_cripta_widget()

    def cambiar_fuente_habilidad(self, index):
        fuente_archivo = self.ability_font_combo.itemData(index)
        if fuente_archivo:
            if "texto_habilidad" not in self.config:
                self.config["texto_habilidad"] = {}
            self.config["texto_habilidad"]["fuente"] = fuente_archivo
            guardar_config(self.config)
            self.actualizar_cripta_widget()

    def cambiar_tamano_habilidad(self, value):
        if "texto_habilidad" not in self.config:
            self.config["texto_habilidad"] = {}
        self.config["texto_habilidad"]["tamano"] = value
        guardar_config(self.config)
        self.actualizar_cripta_widget()

    def cambiar_color_habilidad(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            if "texto_habilidad" not in self.config:
                self.config["texto_habilidad"] = {}
            self.config["texto_habilidad"]["color"] = color_hex
            guardar_config(self.config)
            self.ability_color_btn.setStyleSheet(f"background: {color_hex}; color: black;")
            self.actualizar_cripta_widget()

    def cambiar_opacidad_habilidad(self, value):
        if "texto_habilidad" not in self.config:
            self.config["texto_habilidad"] = {}
        self.config["texto_habilidad"]["opacidad_fondo"] = int(value)
        guardar_config(self.config)
        self.actualizar_cripta_widget()
    
    def cambiar_tamano_clan(self, value):
        if "simbolo_clan" not in self.config:
            self.config["simbolo_clan"] = {}
        self.config["simbolo_clan"]["tamano"] = value
        guardar_config(self.config)
        self.actualizar_cripta_widget()
    
    def cambiar_alineacion_clan(self, index):
        alineacion = self.clan_alignment_combo.itemData(index)
        if alineacion:
            if "simbolo_clan" not in self.config:
                self.config["simbolo_clan"] = {}
            self.config["simbolo_clan"]["alineacion"] = alineacion
            guardar_config(self.config)
            self.actualizar_cripta_widget()
    
    def cambiar_tamano_libreria(self, value):
        if "simbolo_libreria" not in self.config:
            self.config["simbolo_libreria"] = {}
        self.config["simbolo_libreria"]["tamano"] = value
        guardar_config(self.config)
        self.actualizar_cripta_widget()
    
    def cambiar_alineacion_libreria(self, index):
        alineacion = self.libreria_alignment_combo.itemData(index)
        if alineacion:
            if "simbolo_libreria" not in self.config:
                self.config["simbolo_libreria"] = {}
            self.config["simbolo_libreria"]["alineacion"] = alineacion
            guardar_config(self.config)
            self.actualizar_cripta_widget()

    def cambiar_tamano_coste(self, value):
        if "simbolo_coste" not in self.config:
            self.config["simbolo_coste"] = {}
        self.config["simbolo_coste"]["tamano"] = value
        guardar_config(self.config)
        # actualizar libreria directamente
        if self.libreria_widget and hasattr(self.libreria_widget, 'actualizar_configuracion'):
            self.libreria_widget.actualizar_configuracion()
        # y también la cripta (mismo tamaño de coste)
        self.actualizar_cripta_widget()

    def cambiar_tamano_disciplina(self, value):
        if "simbolo_disciplina" not in self.config:
            self.config["simbolo_disciplina"] = {}
        self.config["simbolo_disciplina"]["tamano"] = value
        guardar_config(self.config)
        # actualizar libreria directamente
        if self.libreria_widget and hasattr(self.libreria_widget, 'actualizar_configuracion'):
            self.libreria_widget.actualizar_configuracion()
        # y también la cripta (mismo tamaño de disciplinas)
        self.actualizar_cripta_widget()

    def cambiar_tamano_senda(self, value):
        if "simbolo_senda" not in self.config:
            self.config["simbolo_senda"] = {}
        self.config["simbolo_senda"]["tamano"] = value
        guardar_config(self.config)
        self.actualizar_cripta_widget()

    def cambiar_alineacion_senda(self, index):
        alineacion = self.senda_alignment_combo.itemData(index)
        if alineacion:
            if "simbolo_senda" not in self.config:
                self.config["simbolo_senda"] = {}
            self.config["simbolo_senda"]["alineacion"] = alineacion
            guardar_config(self.config)
            self.actualizar_cripta_widget()

    def actualizar_cripta_widget(self):
        """Actualiza el widget de cripta con la nueva configuración"""
        if self.cripta_widget:
            config = cargar_config()
            nombre_config = config["nombre_carta"]
            from PyQt5.QtGui import QFontDatabase
            fuente_archivo = nombre_config["fuente"]
            font_path = os.path.join(FONTS_DIR, fuente_archivo)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font = QFont(font_families[0], nombre_config["tamano"])
                else:
                    font = QFont(fuente_archivo, nombre_config["tamano"])
            else:
                font = QFont(fuente_archivo, nombre_config["tamano"])
            self.cripta_widget.cripta_title_font = font
            self.cripta_widget.cripta_title_color = nombre_config["color"]
            self.cripta_widget.cripta_card_widget.title_alignment = nombre_config.get("alineacion", "centro")
            # Actualizar tamaño y alineación del símbolo de clan
            simbolo_config = config.get("simbolo_clan", {})
            clan_size = simbolo_config.get("tamano", 40)
            clan_alignment = simbolo_config.get("alineacion", "izquierda")
            self.cripta_widget.cripta_card_widget.clan_size = clan_size
            self.cripta_widget.cripta_card_widget.clan_alignment = clan_alignment
            # Actualizar tamaño y alineación del símbolo de senda
            simbolo_senda_config = config.get("simbolo_senda", {})
            senda_size = simbolo_senda_config.get("tamano", 24)
            senda_alignment = simbolo_senda_config.get("alineacion", "izquierda")
            self.cripta_widget.cripta_card_widget.senda_size = senda_size
            self.cripta_widget.cripta_card_widget.senda_alignment = senda_alignment
            # Actualizar tamaño de iconos de disciplina también en cripta
            simbolo_disciplina_config = config.get("simbolo_disciplina", {})
            discipline_size = simbolo_disciplina_config.get("tamano", 24)
            self.cripta_widget.cripta_card_widget.discipline_size = discipline_size
            # Actualizar tamaño de coste también en cripta
            simbolo_coste_config = config.get("simbolo_coste", {})
            cost_size = simbolo_coste_config.get("tamano", 40)
            self.cripta_widget.cripta_card_widget.cost_size = cost_size
            
            # Actualizar el título si hay texto
            texto_actual = self.cripta_widget.cripta_card_widget.title
            if texto_actual:
                self.cripta_widget.cripta_card_widget.set_title(
                    texto_actual, 
                    font=font, 
                    color=nombre_config["color"],
                    alignment=nombre_config.get("alineacion", "centro")
                )
            
            # Actualizar el símbolo del clan si hay uno seleccionado
            if hasattr(self.cripta_widget, 'cripta_clan_combo'):
                clan_actual = self.cripta_widget.cripta_clan_combo.currentText()
                if clan_actual:
                    self.cripta_widget.cripta_card_widget.set_clan(
                        clan_actual, 
                        size=clan_size,
                        alignment=clan_alignment
                    )

            # Actualizar configuración de texto de habilidades en Cripta
            texto_hab_config = config.get("texto_habilidad", {})
            hab_font_path = texto_hab_config.get("fuente", "fonts/Gill Sans.otf")
            if not os.path.isabs(hab_font_path):
                hab_font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), hab_font_path)
            hab_size = texto_hab_config.get("tamano", 12)
            hab_color = texto_hab_config.get("color", "#ffffff")
            hab_opacidad_pct = texto_hab_config.get("opacidad_fondo", 50)
            try:
                hab_opacidad_pct = int(hab_opacidad_pct)
            except Exception:
                hab_opacidad_pct = 50
            hab_opacidad_pct = max(0, min(100, hab_opacidad_pct))
            hab_opacidad = int(hab_opacidad_pct * 2.55)

            from PyQt5.QtGui import QFontDatabase
            hab_font_id = QFontDatabase.addApplicationFont(hab_font_path)
            if hab_font_id != -1:
                hab_families = QFontDatabase.applicationFontFamilies(hab_font_id)
                if hab_families:
                    hab_font = QFont(hab_families[0], hab_size)
                else:
                    hab_font = QFont(hab_font_path, hab_size)
            else:
                hab_font = QFont(hab_font_path, hab_size)

            self.cripta_widget.cripta_ability_font = hab_font
            self.cripta_widget.cripta_ability_color = hab_color
            self.cripta_widget.cripta_ability_bg_opacity = hab_opacidad
            self.cripta_widget.cripta_card_widget.ability_font = hab_font
            self.cripta_widget.cripta_card_widget.ability_color = hab_color
            self.cripta_widget.cripta_card_widget.ability_bg_opacity = hab_opacidad

            # Reaplicar texto de habilidades actual si existe
            if hasattr(self.cripta_widget, 'cripta_ability_edit'):
                texto_hab_actual = self.cripta_widget.cripta_ability_edit.toPlainText()
                self.cripta_widget.cripta_card_widget.set_ability_text(
                    texto_hab_actual,
                    font=hab_font,
                    color=hab_color,
                    bg_opacity=hab_opacidad,
                )
        
        # Actualizar también el widget de librería
        if self.libreria_widget and hasattr(self.libreria_widget, 'actualizar_configuracion'):
            self.libreria_widget.actualizar_configuracion()
        
        # Actualizar tamaño y alineación del símbolo de librería
        if self.libreria_widget:
            simbolo_libreria_config = config.get("simbolo_libreria", {})
            libreria_size = simbolo_libreria_config.get("tamano", 40)
            libreria_alignment = simbolo_libreria_config.get("alineacion", "izquierda")
            self.libreria_widget.libreria_card_widget.clan_size = libreria_size
            self.libreria_widget.libreria_card_widget.clan_alignment = libreria_alignment
            
            # Actualizar el símbolo del tipo si hay uno seleccionado
            if hasattr(self.libreria_widget, 'libreria_type_combo'):
                tipo_actual = self.libreria_widget.libreria_type_combo.currentText()
                if tipo_actual and tipo_actual != "Ninguno":
                    # Importar aquí para evitar importación circular
                    try:
                        from ventana.libreria_widget import obtener_archivo_tipo_libreria
                        tipo_svg_path = obtener_archivo_tipo_libreria(tipo_actual)
                        if tipo_svg_path:
                            self.libreria_widget.libreria_card_widget.clan = tipo_actual
                            self.libreria_widget.libreria_card_widget.clan_svg_path = tipo_svg_path
                            self.libreria_widget.libreria_card_widget.update()
                    except ImportError:
                        pass  # Si no se puede importar, simplemente no actualizar

            # Actualizar configuración de texto de habilidades en Librería
            texto_hab_config = config.get("texto_habilidad", {})
            hab_font_path = texto_hab_config.get("fuente", "fonts/Gill Sans.otf")
            if not os.path.isabs(hab_font_path):
                hab_font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), hab_font_path)
            hab_size = texto_hab_config.get("tamano", 12)
            hab_color = texto_hab_config.get("color", "#ffffff")
            hab_opacidad_pct = texto_hab_config.get("opacidad_fondo", 50)
            try:
                hab_opacidad_pct = int(hab_opacidad_pct)
            except Exception:
                hab_opacidad_pct = 50
            hab_opacidad_pct = max(0, min(100, hab_opacidad_pct))
            hab_opacidad = int(hab_opacidad_pct * 2.55)

            from PyQt5.QtGui import QFontDatabase
            hab_font_id = QFontDatabase.addApplicationFont(hab_font_path)
            if hab_font_id != -1:
                hab_families = QFontDatabase.applicationFontFamilies(hab_font_id)
                if hab_families:
                    hab_font = QFont(hab_families[0], hab_size)
                else:
                    hab_font = QFont(hab_font_path, hab_size)
            else:
                hab_font = QFont(hab_font_path, hab_size)

            self.libreria_widget.libreria_ability_font = hab_font
            self.libreria_widget.libreria_ability_color = hab_color
            self.libreria_widget.libreria_ability_bg_opacity = hab_opacidad
            self.libreria_widget.libreria_card_widget.ability_font = hab_font
            self.libreria_widget.libreria_card_widget.ability_color = hab_color
            self.libreria_widget.libreria_card_widget.ability_bg_opacity = hab_opacidad

            # Reaplicar texto de habilidades actual si existe
            if hasattr(self.libreria_widget, 'libreria_ability_edit'):
                texto_hab_actual = self.libreria_widget.libreria_ability_edit.toPlainText()
                self.libreria_widget.libreria_card_widget.set_ability_text(
                    texto_hab_actual,
                    font=hab_font,
                    color=hab_color,
                    bg_opacity=hab_opacidad,
                )