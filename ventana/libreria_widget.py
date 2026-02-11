import os
import json
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QListWidget, QAbstractItemView, QPlainTextEdit, QLineEdit, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase, QPainter, QColor
from functools import partial

# Importar CartaImageWidget desde cripta_widget
from ventana.cripta_widget import CartaImageWidget

from resources.listas.libreria_types_list import LIBRERIA_SVG_MAP
from resources.listas.sendas_list import SENDAS, SENDA_SVG_MAP
from resources.listas.costs_list import BLOOD, POOL, BLOOD_SVG_MAP, POOL_SVG_MAP
from resources.listas.disciplines_list import DISCIPLINAS_INFERIORES
from resources.listas.clans_list import CLANES, CLAN_SVG_MAP


def obtener_archivo_disciplina(nombre_disciplina):
    """Resuelve el archivo de icono para una disciplina en resources/disciplines.

    Nuevo patrón de nombres de archivo:
        - inferior: "<nombre>.svg" (por ejemplo, "oblivion.svg")
        - superior: "<nombre>sup.svg" (por ejemplo, "oblivionsup.svg")

    El nombre en la UI puede ser "Oblivion", "Oblivion Superior" o
    "Superior Oblivion"; todos se normalizan al mismo patrón.
    """
    if not nombre_disciplina or nombre_disciplina == "Ninguno":
        return None

    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "disciplines")
    if not os.path.isdir(base_dir):
        return None

    nombre_raw = nombre_disciplina.strip()
    if not nombre_raw:
        return None

    lower = nombre_raw.lower()
    es_superior = False

    # Aceptar tanto "Oblivion Superior" como "Superior Oblivion"
    if lower.startswith("superior "):
        es_superior = True
        base = nombre_raw[len("Superior "):].strip()
    elif lower.endswith(" superior"):
        es_superior = True
        base = nombre_raw[:-len(" superior")].strip()
    else:
        base = nombre_raw

    # Nombre de archivo: todo en minúsculas, sin espacios
    stem = base.replace(" ", "").lower()
    if not stem:
        return None

    if es_superior:
        fname = f"{stem}sup.svg"
    else:
        fname = f"{stem}.svg"

    ruta_directa = os.path.join(base_dir, fname)
    if os.path.exists(ruta_directa):
        return ruta_directa

    # Fallback heurístico: buscar por coincidencia de prefijo sobre cualquier
    # archivo *.svg (o imagen) existente en la carpeta.
    try:
        archivos = os.listdir(base_dir)
    except OSError:
        return None

    candidatos = []
    for archivo in archivos:
        ruta = os.path.join(base_dir, archivo)
        if not os.path.isfile(ruta):
            continue
        nombre_sin_ext, ext = os.path.splitext(archivo)
        ext = ext.lower()
        if ext not in (".svg", ".png", ".gif", ".jpg", ".jpeg", ".webp"):
            continue
        stem_norm = nombre_sin_ext.lower().replace("_", "").replace("-", "")
        candidatos.append((stem_norm, ruta))

    nombre_norm = stem
    mejor_match = None
    for stem_norm, ruta in candidatos:
        if stem_norm == nombre_norm:
            return ruta
        if stem_norm.startswith(nombre_norm) and mejor_match is None:
            mejor_match = ruta

    return mejor_match


def obtener_archivo_clan(nombre_clan):
    """Mapea el nombre del clan a su archivo SVG correspondiente usando CLAN_SVG_MAP."""
    if not nombre_clan or nombre_clan == "Ninguno":
        return None

    nombre_normalizado = nombre_clan.strip()
    archivo = CLAN_SVG_MAP.get(nombre_normalizado)

    if archivo:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "clans")
        ruta_completa = os.path.join(base_dir, archivo)
        if os.path.exists(ruta_completa):
            return ruta_completa
    return None


def obtener_archivo_tipo_libreria(nombre_tipo):
    """Mapea el nombre del tipo de carta de librería a su archivo SVG correspondiente usando LIBRERIA_SVG_MAP."""
    if not nombre_tipo or nombre_tipo == "Ninguno":
        return None

    nombre_normalizado = nombre_tipo.strip()
    archivo = LIBRERIA_SVG_MAP.get(nombre_normalizado)

    if archivo:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "libreria")
        ruta_completa = os.path.join(base_dir, archivo)
        if os.path.exists(ruta_completa):
            return ruta_completa
    return None

def get_resource_path(relative_path):
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Cargar config desde config/textos/config_data.json
from configuracion import load_config_data

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
        "simbolo_libreria": {
            "tamano": 35,
            "alineacion": "izquierda"
        },
        "simbolo_senda": {
            "tamano": 50,
            "alineacion": "izquierda"
        }
    }

    data = load_config_data({})
    return _deep_merge_dicts(defaults, data)

class LibreriaWidget(QWidget):
    def __init__(self, importar_imagen_callback):
        super().__init__()
        self.layout = QHBoxLayout()
        config = cargar_config()
        # Campo de nombre editable
        from PyQt5.QtWidgets import QLineEdit, QLabel
        self.libreria_name_edit = QLineEdit()
        self.libreria_name_edit.setPlaceholderText("Nombre de la carta")
        self.libreria_name_edit.setText("")
        self.libreria_name_edit.textChanged.connect(self.set_title_from_edit)
        # Widget personalizado para imagen y título (igual que en cripta)
        self.libreria_card_widget = CartaImageWidget()
        self.libreria_card_widget.setMinimumHeight(400)
        # En librería queremos que el segundo símbolo se apile debajo del primero
        self.libreria_card_widget.clan2_stack = True
        # Activar reborde blanco detrás de los símbolos sólo para librería
        self.libreria_card_widget.clan_draw_border = True
        self.libreria_card_widget.setStyleSheet("background: #232629;")
        self.libreria_card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.libreria_card_widget, stretch=2)
        # Para compatibilidad con el resto de la app
        self.libreria_label = self.libreria_card_widget
        # Cargar fuente desde archivo
        nombre_config = config["nombre_carta"]
        font_path = nombre_config["fuente"]
        # Convertir ruta relativa a absoluta si es necesario
        if not os.path.isabs(font_path):
            font_path = get_resource_path(font_path)
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], nombre_config["tamano"])
            else:
                font = QFont(font_path, nombre_config["tamano"])
        else:
            font = QFont(font_path, nombre_config["tamano"])
        self.libreria_title_font = font
        self.libreria_title_color = nombre_config["color"]
        # Configurar alineación
        self.libreria_card_widget.title_alignment = nombre_config.get("alineacion", "centro")
        # Configurar tamaño y alineación del símbolo de tipo de librería
        simbolo_config = config.get("simbolo_libreria", {})
        self.libreria_card_widget.clan_size = simbolo_config.get("tamano", 40)
        self.libreria_card_widget.clan_alignment = simbolo_config.get("alineacion", "izquierda")
        # Tamaño de iconos de disciplina (librería)
        simbolo_disciplina_config = config.get("simbolo_disciplina", {})
        self.libreria_card_widget.discipline_size = simbolo_disciplina_config.get("tamano", 24)
        # Activar halo/borde blanco semitransparente alrededor de los iconos de disciplina
        self.libreria_card_widget.discipline_draw_border = True
        # Tamaño del símbolo de coste (blood/pool)
        simbolo_coste_config = config.get("simbolo_coste", {})
        self.libreria_card_widget.cost_size = simbolo_coste_config.get("tamano", 80)
        # Configuración de texto de habilidades
        texto_hab_config = config.get("texto_habilidad", {})
        hab_font_path = texto_hab_config.get("fuente", "fonts/Gill Sans.otf")
        if not os.path.isabs(hab_font_path):
            hab_font_path = get_resource_path(hab_font_path)
        hab_size = texto_hab_config.get("tamano", 12)
        hab_color = texto_hab_config.get("color", "#ffffff")
        hab_opacidad_pct = texto_hab_config.get("opacidad_fondo", 50)
        try:
            hab_opacidad_pct = int(hab_opacidad_pct)
        except Exception:
            hab_opacidad_pct = 50
        hab_opacidad_pct = max(0, min(100, hab_opacidad_pct))
        hab_opacidad = int(hab_opacidad_pct * 2.55)

        hab_font_id = QFontDatabase.addApplicationFont(hab_font_path)
        if hab_font_id != -1:
            hab_families = QFontDatabase.applicationFontFamilies(hab_font_id)
            if hab_families:
                hab_font = QFont(hab_families[0], hab_size)
            else:
                hab_font = QFont(hab_font_path, hab_size)
        else:
            hab_font = QFont(hab_font_path, hab_size)

        self.libreria_ability_font = hab_font
        self.libreria_ability_color = hab_color
        self.libreria_ability_bg_opacity = hab_opacidad
        self.libreria_card_widget.ability_font = hab_font
        self.libreria_card_widget.ability_color = hab_color
        self.libreria_card_widget.ability_bg_opacity = hab_opacidad
        # Para compatibilidad, crear un atributo libreria_title que apunte al widget
        self.libreria_title = self.libreria_card_widget
        # Selector de tipo de carta de librería (primer tipo)
        from PyQt5.QtWidgets import QComboBox
        from resources.listas.libreria_types_list import TIPOS_LIBRERIA
        self.libreria_type_combo = QComboBox()
        self.libreria_type_combo.addItems(TIPOS_LIBRERIA)
        self.libreria_type_combo.setCurrentText("Ninguno")
        self.libreria_type_combo.currentTextChanged.connect(self.set_tipo_from_combo)
        # Selector de segundo tipo de carta de librería
        self.libreria_type2_combo = QComboBox()
        self.libreria_type2_combo.addItems(TIPOS_LIBRERIA)
        self.libreria_type2_combo.setCurrentText("Ninguno")
        self.libreria_type2_combo.currentTextChanged.connect(self.set_tipo2_from_combo)
        # Selector de senda (debajo de los símbolos de tipo)
        self.libreria_senda_combo = QComboBox()
        self.libreria_senda_combo.addItems(SENDAS)
        self.libreria_senda_combo.setCurrentText("Ninguno")
        self.libreria_senda_combo.currentTextChanged.connect(self.set_senda_from_combo)
        # Selector de coste (tipo y valor) se añade en el panel derecho
        # Panel derecho con dos columnas, similar a Configuración
        self.libreria_right_panel = QWidget()
        self.libreria_right_layout = QVBoxLayout()

        columnas_layout = QHBoxLayout()
        col1_layout = QVBoxLayout()
        col2_layout = QVBoxLayout()

        # Columna 1: nombre, tipos, senda/clan, coste
        col1_layout.addWidget(QLabel("Nombre:"))
        col1_layout.addWidget(self.libreria_name_edit)
        col1_layout.addWidget(QLabel("Tipo 1:"))
        col1_layout.addWidget(self.libreria_type_combo)
        col1_layout.addWidget(QLabel("Tipo 2:"))
        col1_layout.addWidget(self.libreria_type2_combo)
        col1_layout.addWidget(QLabel("Senda:"))
        col1_layout.addWidget(self.libreria_senda_combo)
        # Clan opcional (en lugar de senda)
        col1_layout.addWidget(QLabel("Clan (en lugar de senda):"))
        self.libreria_clan_combo = QComboBox()
        self.libreria_clan_combo.addItems(CLANES)
        self.libreria_clan_combo.setCurrentText("Ninguno")
        self.libreria_clan_combo.currentTextChanged.connect(self.set_libreria_clan_from_combo)
        col1_layout.addWidget(self.libreria_clan_combo)
        # Coste: tipo+valor
        col1_layout.addWidget(QLabel("Coste tipo:"))
        self.libreria_cost_type_combo = QComboBox()
        self.libreria_cost_type_combo.addItems(["Ninguno", "Blood", "Pool"])
        self.libreria_cost_type_combo.setCurrentText("Ninguno")
        self.libreria_cost_type_combo.currentTextChanged.connect(self.set_cost_type_from_combo)
        col1_layout.addWidget(self.libreria_cost_type_combo)

        col1_layout.addWidget(QLabel("Coste valor:"))
        self.libreria_cost_value_combo = QComboBox()
        for v in ["1","2","3","4","5","6","X"]:
            self.libreria_cost_value_combo.addItem(v)
        self.libreria_cost_value_combo.setCurrentText("1")
        self.libreria_cost_value_combo.currentTextChanged.connect(self.set_cost_value_from_combo)
        col1_layout.addWidget(self.libreria_cost_value_combo)

        # Columna 2: texto de habilidades, disciplinas e ilustrador
        col2_layout.addWidget(QLabel("Texto de habilidades:"))
        self.libreria_ability_edit = QPlainTextEdit()
        self.libreria_ability_edit.setPlaceholderText("Escribe el texto de habilidades (**negrita**)...")
        # Hacer el área de edición más cómoda y expandible
        self.libreria_ability_edit.setMinimumHeight(150)
        self.libreria_ability_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.libreria_ability_edit.textChanged.connect(self.set_ability_from_edit)
        col2_layout.addWidget(self.libreria_ability_edit)

        col2_layout.addWidget(QLabel("Disciplinas (inferiores):"))
        self.libreria_disciplines_list = QListWidget()
        self.libreria_disciplines_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for d in DISCIPLINAS_INFERIORES:
            self.libreria_disciplines_list.addItem(d)
        self.libreria_disciplines_list.itemSelectionChanged.connect(self.set_disciplines_from_list)
        col2_layout.addWidget(self.libreria_disciplines_list)

        # Ilustrador (nombre en la parte inferior de la carta)
        col2_layout.addWidget(QLabel("Ilustrador:"))
        self.libreria_illustrator_edit = QLineEdit()
        self.libreria_illustrator_edit.setPlaceholderText("Nombre del ilustrador original")
        self.libreria_illustrator_edit.textChanged.connect(self.set_illustrator_from_edit)
        col2_layout.addWidget(self.libreria_illustrator_edit)

        columnas_layout.addLayout(col1_layout)
        columnas_layout.addLayout(col2_layout)

        self.libreria_right_layout.addLayout(columnas_layout)
        self.libreria_right_layout.addStretch(1)

        botones_layout = QHBoxLayout()
        btn_importar_libreria = QPushButton('Importar Imagen')
        btn_importar_libreria.setMinimumWidth(100)
        btn_importar_libreria.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_importar_libreria.clicked.connect(partial(importar_imagen_callback, self))
        btn_guardar_libreria = QPushButton('Guardar')
        btn_guardar_libreria.setMinimumWidth(100)
        btn_guardar_libreria.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_guardar_libreria.clicked.connect(self.guardar_carta_libreria)
        btn_guardar_online_libreria = QPushButton('Guardar para Online')
        btn_guardar_online_libreria.setMinimumWidth(100)
        btn_guardar_online_libreria.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_guardar_online_libreria.clicked.connect(self.guardar_carta_libreria_online)
        botones_layout.addWidget(btn_importar_libreria, stretch=1)
        botones_layout.addWidget(btn_guardar_libreria, stretch=1)
        botones_layout.addWidget(btn_guardar_online_libreria, stretch=1)
        self.libreria_right_layout.addLayout(botones_layout)
        self.libreria_right_panel.setLayout(self.libreria_right_layout)
        self.layout.addWidget(self.libreria_right_panel, stretch=1)
        self.setLayout(self.layout)

    def guardar_carta_libreria(self):
        """Guarda la carta de librería actual (PNG o JPG, 63x88mm a 300 DPI)."""
        nombre_base = self.libreria_name_edit.text().strip() if hasattr(self, 'libreria_name_edit') else ""
        if not nombre_base:
            nombre_base = "carta_libreria"
        safe_name = "".join(c for c in nombre_base if c.isalnum() or c in (" ", "-", "_")).strip()
        if not safe_name:
            safe_name = "carta_libreria"
        default_path = os.path.join(os.getcwd(), safe_name.replace(" ", "_") + ".png")

        # Permitir guardar tanto en PNG como en JPG; el formato real lo
        # determina la extensión del archivo.
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar carta de librería",
            default_path,
            "Imagen PNG/JPEG (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return
        self.libreria_card_widget.export_png(filename)

    def guardar_carta_libreria_online(self):
        """Guarda la carta de librería en formato optimizado para juego online (358x500px)."""
        from logicas.recorte.constantes import VTES_CARD_WIDTH_ONLINE, VTES_CARD_HEIGHT_ONLINE
        
        nombre_base = self.libreria_name_edit.text().strip() if hasattr(self, 'libreria_name_edit') else ""
        if not nombre_base:
            nombre_base = "carta_libreria_online"
        safe_name = "".join(c for c in nombre_base if c.isalnum() or c in (" ", "-", "_")).strip()
        if not safe_name:
            safe_name = "carta_libreria_online"
        default_path = os.path.join(os.getcwd(), safe_name.replace(" ", "_") + "_online.png")

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar carta de librería para online",
            default_path,
            "Imagen PNG/JPEG (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return
        self.libreria_card_widget.export_png(
            filename,
            width=VTES_CARD_WIDTH_ONLINE,
            height=VTES_CARD_HEIGHT_ONLINE
        )

    def set_title_from_edit(self, text):
        self.libreria_card_widget.set_title(
            text, 
            font=self.libreria_title_font, 
            color=self.libreria_title_color,
            alignment=self.libreria_card_widget.title_alignment
        )
    
    def set_tipo_from_combo(self, nombre_tipo):
        """Actualiza el primer símbolo del tipo de carta cuando se selecciona uno"""
        tipo_svg_path = obtener_archivo_tipo_libreria(nombre_tipo)
        if tipo_svg_path and nombre_tipo != "Ninguno":
            # Actualizar los atributos del widget para usar el tipo de librería
            self.libreria_card_widget.clan = nombre_tipo
            self.libreria_card_widget.clan_svg_path = tipo_svg_path
        else:
            # Si no hay tipo seleccionado, limpiar
            self.libreria_card_widget.clan = None
            self.libreria_card_widget.clan_svg_path = None
        self.libreria_card_widget.update()
    
    def set_tipo2_from_combo(self, nombre_tipo):
        """Actualiza el segundo símbolo del tipo de carta cuando se selecciona uno"""
        tipo_svg_path = obtener_archivo_tipo_libreria(nombre_tipo)
        if tipo_svg_path and nombre_tipo != "Ninguno":
            # Actualizar el segundo símbolo
            self.libreria_card_widget.clan2 = nombre_tipo
            self.libreria_card_widget.clan2_svg_path = tipo_svg_path
        else:
            # Si no hay segundo tipo seleccionado, limpiar
            self.libreria_card_widget.clan2 = None
            self.libreria_card_widget.clan2_svg_path = None
        self.libreria_card_widget.update()

    def set_senda_from_combo(self, nombre_senda):
        """Actualiza el símbolo de senda debajo de los símbolos de tipo"""
        # Si se elige una senda explícita, limpiar clan de librería para que sean excluyentes
        if hasattr(self, 'libreria_clan_combo') and nombre_senda and nombre_senda != "Ninguno":
            if self.libreria_clan_combo.currentText() != "Ninguno":
                self.libreria_clan_combo.blockSignals(True)
                self.libreria_clan_combo.setCurrentText("Ninguno")
                self.libreria_clan_combo.blockSignals(False)

        if nombre_senda and nombre_senda != "Ninguno":
            # resolver ruta desde el mapeo, si existe
            archivo = SENDA_SVG_MAP.get(nombre_senda)
            svg_path = None
            if archivo:
                base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sendas")
                ruta_completa = os.path.join(base_dir, archivo)
                if os.path.exists(ruta_completa):
                    svg_path = ruta_completa
            # Si no hay archivo mapeado, intentar construir nombre a partir del texto (lower)
            if not svg_path:
                posible = nombre_senda.replace(' ', '').lower() + '.svg'
                posible_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sendas', posible)
                if os.path.exists(posible_path):
                    svg_path = posible_path

            self.libreria_card_widget.set_senda(
                nombre_senda,
                size=self.libreria_card_widget.senda_size,
                alignment=self.libreria_card_widget.senda_alignment,
                svg_path=svg_path
            )
        else:
            self.libreria_card_widget.set_senda(None, svg_path=None)
        self.libreria_card_widget.update()

    def set_libreria_clan_from_combo(self, nombre_clan):
        """Selecciona un clan para cartas de librería en lugar de una senda."""
        # Si se elige un clan, limpiar la senda para que sean excluyentes
        if hasattr(self, 'libreria_senda_combo') and nombre_clan and nombre_clan != "Ninguno":
            if self.libreria_senda_combo.currentText() != "Ninguno":
                self.libreria_senda_combo.blockSignals(True)
                self.libreria_senda_combo.setCurrentText("Ninguno")
                self.libreria_senda_combo.blockSignals(False)

        if nombre_clan and nombre_clan != "Ninguno":
            clan_svg_path = obtener_archivo_clan(nombre_clan)
            self.libreria_card_widget.set_senda(
                nombre_clan,
                size=self.libreria_card_widget.senda_size,
                alignment=self.libreria_card_widget.senda_alignment,
                svg_path=clan_svg_path
            )
        else:
            # Si se deselecciona el clan, dejar que la senda (si la hay) se encargue
            if hasattr(self, 'libreria_senda_combo'):
                self.set_senda_from_combo(self.libreria_senda_combo.currentText())
            else:
                self.libreria_card_widget.set_senda(None, svg_path=None)
        self.libreria_card_widget.update()

    def set_cost_type_from_combo(self, tipo):
        """Actualiza el icono de coste mostrado según el tipo seleccionado y el valor actual."""
        svg_path = None
        current_value = None
        if hasattr(self, 'libreria_cost_value_combo'):
            current_value = self.libreria_cost_value_combo.currentText()

        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        # Intentar resolver por patrón con los nuevos nombres, dando
        # prioridad a SVG si existe: bloodcost{value}.svg/png o poolcost{value}.svg/png
        if tipo == 'Blood' and current_value:
            stem = f"bloodcost{current_value.lower()}"
            svg_candidate = os.path.join(base_dir, 'blood', stem + ".svg")
            png_candidate = os.path.join(base_dir, 'blood', stem + ".png")
            if os.path.exists(svg_candidate):
                svg_path = svg_candidate
            elif os.path.exists(png_candidate):
                svg_path = png_candidate
        elif tipo == 'Pool' and current_value:
            stem = f"poolcost{current_value.lower()}"
            svg_candidate = os.path.join(base_dir, 'pool', stem + ".svg")
            png_candidate = os.path.join(base_dir, 'pool', stem + ".png")
            if os.path.exists(svg_candidate):
                svg_path = svg_candidate
            elif os.path.exists(png_candidate):
                svg_path = png_candidate

        # Si no hay archivo por patrón, usar el primer icono disponible como fallback
        if not svg_path:
            if tipo == "Blood":
                if len(BLOOD) > 1:
                    archivo = BLOOD_SVG_MAP.get(BLOOD[1])
                    if archivo:
                        posible = os.path.join(base_dir, 'blood', archivo)
                        if os.path.exists(posible):
                            svg_path = posible
            elif tipo == "Pool":
                if len(POOL) > 1:
                    archivo = POOL_SVG_MAP.get(POOL[1])
                    if archivo:
                        posible = os.path.join(base_dir, 'pool', archivo)
                        if os.path.exists(posible):
                            svg_path = posible

        # Aplicar coste con el tamaño configurado
        if tipo == "Ninguno":
            self.libreria_card_widget.set_cost(None, svg_path=None, size=self.libreria_card_widget.cost_size)
        else:
            self.libreria_card_widget.set_cost(tipo.lower(), svg_path=svg_path, size=self.libreria_card_widget.cost_size, value=current_value)
        self.libreria_card_widget.update()

    def set_cost_value_from_combo(self, value):
        """Actualiza el valor numérico (o X) del coste mostrado en la carta"""
        tipo = self.libreria_cost_type_combo.currentText()
        if tipo == "Ninguno":
            # no mostrar nada
            self.libreria_card_widget.set_cost(None, svg_path=None)
            self.libreria_card_widget.update()
            return

        # Resolver svg_path por patrón tipo+valor con los nuevos nombres
        # (ej. bloodcost3.png o poolcostX.png)
        svg_path = None
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
        candidate = None
        if tipo == 'Blood':
            stem = f"bloodcost{str(value).lower()}"
            svg_candidate = os.path.join(base_dir, 'blood', stem + ".svg")
            png_candidate = os.path.join(base_dir, 'blood', stem + ".png")
            if os.path.exists(svg_candidate):
                svg_path = svg_candidate
            elif os.path.exists(png_candidate):
                svg_path = png_candidate
        elif tipo == 'Pool':
            stem = f"poolcost{str(value).lower()}"
            svg_candidate = os.path.join(base_dir, 'pool', stem + ".svg")
            png_candidate = os.path.join(base_dir, 'pool', stem + ".png")
            if os.path.exists(svg_candidate):
                svg_path = svg_candidate
            elif os.path.exists(png_candidate):
                svg_path = png_candidate

        # Si no se encontró por patrón, intentar 'X' mapeado o el svg ya establecido
        if not svg_path:
            if str(value).upper() == 'X':
                if tipo == 'Blood' and BLOOD_SVG_MAP.get('X'):
                    posible = os.path.join(base_dir, 'blood', BLOOD_SVG_MAP.get('X'))
                    if os.path.exists(posible):
                        svg_path = posible
                elif tipo == 'Pool' and POOL_SVG_MAP.get('X'):
                    posible = os.path.join(base_dir, 'pool', POOL_SVG_MAP.get('X'))
                    if os.path.exists(posible):
                        svg_path = posible

        if not svg_path:
            svg_path = getattr(self.libreria_card_widget, 'cost_svg_path', None)

        # Si aún no hay svg, usar el primer disponible según el tipo
        if not svg_path:
            if tipo == 'Blood' and len(BLOOD) > 1:
                archivo = BLOOD_SVG_MAP.get(BLOOD[1])
                if archivo:
                    posible = os.path.join(base_dir, 'blood', archivo)
                    if os.path.exists(posible):
                        svg_path = posible
            elif tipo == 'Pool' and len(POOL) > 1:
                archivo = POOL_SVG_MAP.get(POOL[1])
                if archivo:
                    posible = os.path.join(base_dir, 'pool', archivo)
                    if os.path.exists(posible):
                        svg_path = posible

        # Aplicar valor y refrescar
        self.libreria_card_widget.set_cost(tipo.lower() if tipo != 'Ninguno' else None, svg_path=svg_path, size=self.libreria_card_widget.cost_size, value=value)
        self.libreria_card_widget.update()

    def set_cost_icon_from_combo(self, icon_name):
        """Establece el icono de coste seleccionado en el widget"""
        tipo = self.libreria_cost_type_combo.currentText()
        if icon_name == "Ninguno" or tipo == "Ninguno":
            self.libreria_card_widget.set_cost(None, svg_path=None)
            self.libreria_card_widget.update()
            return

        svg_path = None
        if tipo == "Blood":
            archivo = BLOOD_SVG_MAP.get(icon_name)
            if archivo:
                posible = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'blood', archivo)
                if os.path.exists(posible):
                    svg_path = posible
        elif tipo == "Pool":
            archivo = POOL_SVG_MAP.get(icon_name)
            if archivo:
                posible = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'pool', archivo)
                if os.path.exists(posible):
                    svg_path = posible

        # Aplicar coste con el tamaño configurado
        self.libreria_card_widget.set_cost(tipo.lower() if tipo != "Ninguno" else None, svg_path=svg_path, size=self.libreria_card_widget.cost_size)
        self.libreria_card_widget.update()

    def set_ability_from_edit(self):
        """Actualiza el texto de habilidades desde el editor de texto."""
        if hasattr(self, 'libreria_ability_edit'):
            text = self.libreria_ability_edit.toPlainText()
        else:
            text = ""
        self.libreria_card_widget.set_ability_text(
            text,
            font=getattr(self, 'libreria_ability_font', self.libreria_card_widget.ability_font),
            color=getattr(self, 'libreria_ability_color', self.libreria_card_widget.ability_color),
            bg_opacity=getattr(self, 'libreria_ability_bg_opacity', self.libreria_card_widget.ability_bg_opacity),
        )

    def set_illustrator_from_edit(self):
        """Actualiza el nombre del ilustrador mostrado en la parte inferior de la carta."""
        if hasattr(self, 'libreria_illustrator_edit'):
            name = self.libreria_illustrator_edit.text()
        else:
            name = ""
        # Fuente fija para el ilustrador
        illustrator_font = QFont("Arial", 8)  # Cambia "Arial" y 8 por lo que prefieras
        self.libreria_card_widget.set_illustrator(
            name,
            font=illustrator_font,
            color=getattr(self, 'libreria_ability_color', self.libreria_card_widget.ability_color),
        )

    def set_disciplines_from_list(self):
        """Lee la selección del listado y actualiza las disciplinas en la carta."""
        items = self.libreria_disciplines_list.selectedItems() if hasattr(self, 'libreria_disciplines_list') else []
        disciplinas = []
        for it in items:
            nombre = it.text()
            svg_path = obtener_archivo_disciplina(nombre)
            if svg_path:
                disciplinas.append({"nombre": nombre, "svg_path": svg_path})

        self.libreria_card_widget.set_disciplines(disciplinas, size=self.libreria_card_widget.discipline_size)
        self.libreria_card_widget.update()
    
    def actualizar_configuracion(self):
        """Actualiza el título con la configuración actual"""
        config = cargar_config()
        nombre_config = config["nombre_carta"]
        
        # Cargar fuente
        font_path = nombre_config["fuente"]
        if not os.path.isabs(font_path):
            font_path = get_resource_path(font_path)
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], nombre_config["tamano"])
            else:
                font = QFont(font_path, nombre_config["tamano"])
        else:
            font = QFont(font_path, nombre_config["tamano"])
        
        self.libreria_title_font = font
        self.libreria_title_color = nombre_config["color"]
        self.libreria_card_widget.title_alignment = nombre_config.get("alineacion", "centro")
        
        # Actualizar tamaño y alineación del símbolo de tipo de librería
        simbolo_config = config.get("simbolo_libreria", {})
        self.libreria_card_widget.clan_size = simbolo_config.get("tamano", 40)
        self.libreria_card_widget.clan_alignment = simbolo_config.get("alineacion", "izquierda")
        # Actualizar tamaño y alineación del símbolo de senda
        simbolo_senda_config = config.get("simbolo_senda", {})
        self.libreria_card_widget.senda_size = simbolo_senda_config.get("tamano", 24)
        self.libreria_card_widget.senda_alignment = simbolo_senda_config.get("alineacion", "izquierda")
        # Actualizar configuración de texto de habilidades
        texto_hab_config = config.get("texto_habilidad", {})
        hab_font_path = texto_hab_config.get("fuente", "fonts/Gill Sans.otf")
        if not os.path.isabs(hab_font_path):
            hab_font_path = get_resource_path(hab_font_path)
        hab_size = texto_hab_config.get("tamano", 12)
        hab_color = texto_hab_config.get("color", "#ffffff")
        hab_opacidad_pct = texto_hab_config.get("opacidad_fondo", 50)
        try:
            hab_opacidad_pct = int(hab_opacidad_pct)
        except Exception:
            hab_opacidad_pct = 50
        hab_opacidad_pct = max(0, min(100, hab_opacidad_pct))
        hab_opacidad = int(hab_opacidad_pct * 2.55)

        hab_font_id = QFontDatabase.addApplicationFont(hab_font_path)
        if hab_font_id != -1:
            hab_families = QFontDatabase.applicationFontFamilies(hab_font_id)
            if hab_families:
                hab_font = QFont(hab_families[0], hab_size)
            else:
                hab_font = QFont(hab_font_path, hab_size)
        else:
            hab_font = QFont(hab_font_path, hab_size)

        self.libreria_ability_font = hab_font
        self.libreria_ability_color = hab_color
        self.libreria_ability_bg_opacity = hab_opacidad
        self.libreria_card_widget.ability_font = hab_font
        self.libreria_card_widget.ability_color = hab_color
        self.libreria_card_widget.ability_bg_opacity = hab_opacidad
        # Actualizar tamaño de los iconos de disciplina
        simbolo_disciplina_config = config.get("simbolo_disciplina", {})
        self.libreria_card_widget.discipline_size = simbolo_disciplina_config.get("tamano", 24)
        # Mantener activado el halo/borde de disciplina tras cambios de configuración
        self.libreria_card_widget.discipline_draw_border = True
        # Actualizar tamaño del símbolo de coste
        simbolo_coste_config = config.get("simbolo_coste", {})
        self.libreria_card_widget.cost_size = simbolo_coste_config.get("tamano", 80)
        
        # Actualizar el título si hay texto
        texto_actual = self.libreria_card_widget.title
        if texto_actual:
            self.libreria_card_widget.set_title(
                texto_actual, 
                font=font, 
                color=nombre_config["color"],
                alignment=nombre_config.get("alineacion", "centro")
            )
        
        # Actualizar los símbolos de tipo si hay alguno seleccionado
        if hasattr(self, 'libreria_type_combo'):
            tipo_actual = self.libreria_type_combo.currentText()
            if tipo_actual and tipo_actual != "Ninguno":
                tipo_svg_path = obtener_archivo_tipo_libreria(tipo_actual)
                if tipo_svg_path:
                    self.libreria_card_widget.clan = tipo_actual
                    self.libreria_card_widget.clan_svg_path = tipo_svg_path
                else:
                    self.libreria_card_widget.clan = None
                    self.libreria_card_widget.clan_svg_path = None
            else:
                self.libreria_card_widget.clan = None
                self.libreria_card_widget.clan_svg_path = None
        
        if hasattr(self, 'libreria_type2_combo'):
            tipo2_actual = self.libreria_type2_combo.currentText()
            if tipo2_actual and tipo2_actual != "Ninguno":
                tipo2_svg_path = obtener_archivo_tipo_libreria(tipo2_actual)
                if tipo2_svg_path:
                    self.libreria_card_widget.clan2 = tipo2_actual
                    self.libreria_card_widget.clan2_svg_path = tipo2_svg_path
                else:
                    self.libreria_card_widget.clan2 = None
                    self.libreria_card_widget.clan2_svg_path = None
            else:
                self.libreria_card_widget.clan2 = None
                self.libreria_card_widget.clan2_svg_path = None

        # Actualizar clan de librería o senda, según lo que esté seleccionado
        clan_lib_actual = None
        if hasattr(self, 'libreria_clan_combo'):
            clan_lib_actual = self.libreria_clan_combo.currentText()

        if clan_lib_actual and clan_lib_actual != "Ninguno":
            clan_svg_path = obtener_archivo_clan(clan_lib_actual)
            self.libreria_card_widget.set_senda(
                clan_lib_actual,
                size=self.libreria_card_widget.senda_size,
                alignment=self.libreria_card_widget.senda_alignment,
                svg_path=clan_svg_path
            )
        elif hasattr(self, 'libreria_senda_combo'):
            senda_actual = self.libreria_senda_combo.currentText()
            if senda_actual and senda_actual != "Ninguno":
                archivo = SENDA_SVG_MAP.get(senda_actual)
                svg_path = None
                if archivo:
                    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sendas")
                    ruta_completa = os.path.join(base_dir, archivo)
                    if os.path.exists(ruta_completa):
                        svg_path = ruta_completa
                # intentar fallback por nombre simple
                if not svg_path:
                    posible = senda_actual.replace(' ', '').lower() + '.svg'
                    posible_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'sendas', posible)
                    if os.path.exists(posible_path):
                        svg_path = posible_path

                self.libreria_card_widget.set_senda(
                    senda_actual,
                    size=self.libreria_card_widget.senda_size,
                    alignment=self.libreria_card_widget.senda_alignment,
                    svg_path=svg_path
                )
            else:
                self.libreria_card_widget.set_senda(None, svg_path=None)

        # Actualizar disciplinas según la selección actual
        if hasattr(self, 'libreria_disciplines_list'):
            self.set_disciplines_from_list()
        
        self.libreria_card_widget.update()

    def set_pixmap(self, pixmap):
        self.libreria_card_widget.set_pixmap(pixmap)
