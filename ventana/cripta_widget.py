import os
import json
import html
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QPlainTextEdit, QFileDialog
from PyQt5.QtCore import Qt, QSize, QRectF, QUrl
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QFontDatabase, QFontMetrics, QImage
from PyQt5.QtSvg import QSvgRenderer
from functools import partial

from resources.listas.clans_list import CLAN_SVG_MAP
from resources.listas.sendas_list import SENDA_SVG_MAP, SENDAS
from logicas.recorte.constantes import (
    VTES_CARD_ASPECT_RATIO,
    VTES_CARD_WIDTH_300DPI,
    VTES_CARD_HEIGHT_300DPI,
)


def get_resource_path(relative_path):
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extrae los archivos a _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def obtener_archivo_coste_cripta(valor):
    """Resuelve el archivo de icono de coste de cripta (capacidad) desde resources/costes.

    Los archivos siguen el patrón cap{N}.gif (por ejemplo, cap3.gif).
    """
    if not valor or str(valor).lower() == "ninguno":
        return None

    base_dir = get_resource_path(os.path.join("resources", "costes"))
    if not os.path.isdir(base_dir):
        return None

    num = str(valor).strip()
    candidate = f"cap{num}.gif"
    ruta = os.path.join(base_dir, candidate)
    if os.path.exists(ruta):
        return ruta
    return None


def obtener_archivo_clan(nombre_clan):
    """Mapea el nombre del clan a su archivo SVG correspondiente usando CLAN_SVG_MAP."""
    if not nombre_clan or nombre_clan == "Ninguno":
        return None

    nombre_normalizado = nombre_clan.strip()
    archivo = CLAN_SVG_MAP.get(nombre_normalizado)

    if archivo:
        base_dir = get_resource_path(os.path.join("resources", "clans"))
        ruta_completa = os.path.join(base_dir, archivo)
        if os.path.exists(ruta_completa):
            return ruta_completa
    return None


def obtener_archivo_senda(nombre_senda):
    """Mapea el nombre de la senda a su archivo SVG correspondiente usando SENDA_SVG_MAP."""
    if not nombre_senda or nombre_senda == "Ninguno":
        return None

    nombre_normalizado = nombre_senda.strip()
    archivo = SENDA_SVG_MAP.get(nombre_normalizado)

    if archivo:
        base_dir = get_resource_path(os.path.join("resources", "sendas"))
        ruta_completa = os.path.join(base_dir, archivo)
        if os.path.exists(ruta_completa):
            return ruta_completa
    return None


def obtener_archivo_disciplina_texto(nombre_disciplina):
    """Resuelve el archivo de icono para una disciplina usada en el texto de habilidades.

    Se intenta primero con el nombre completo tal cual aparece entre corchetes
    (p. ej. "Superior Oblivion") y, si no se encuentra, con la versión
    sin "Superior" para reutilizar el mismo icono.
    """
    if not nombre_disciplina:
        return None

    base_dir = get_resource_path(os.path.join("resources", "disciplines"))
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

    # Fallback heurístico: buscar coincidencias dentro de la carpeta
    try:
        archivos = os.listdir(base_dir)
    except OSError:
        return None

    archivos_validos = []
    for archivo in archivos:
        ruta = os.path.join(base_dir, archivo)
        if not os.path.isfile(ruta):
            continue
        nombre_sin_ext, ext = os.path.splitext(archivo)
        ext = ext.lower()
        if ext not in (".svg", ".png", ".gif", ".jpg", ".jpeg", ".webp"):
            continue
        stem_norm = nombre_sin_ext.lower().replace(" ", "").replace("_", "").replace("-", "")
        archivos_validos.append((stem_norm, ruta))

    cand_norm = stem
    mejor_match = None
    for stem_norm, ruta in archivos_validos:
        if stem_norm == cand_norm:
            return ruta
        if stem_norm.startswith(cand_norm) and mejor_match is None:
            mejor_match = ruta

    return mejor_match

# Widget personalizado para mostrar imagen y texto superpuesto
class CartaImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Proporción de carta VTES/MTG: ancho/alto = 63/88
        self.aspect_ratio = VTES_CARD_ASPECT_RATIO
        self.pixmap = None
        self.title = ""
        self.title_font = QFont()
        self.title_color = "#ffffff"
        self.title_alignment = "centro"  # "centro" o "izquierda"
        self.clan = None  # Nombre del clan
        self.clan_svg_path = None  # Ruta al SVG del clan
        self.clan_size = 40  # Tamaño del símbolo del clan en píxeles
        self.clan_alignment = "izquierda"  # "izquierda", "centro", "derecha"
        # Segundo símbolo (solo para tipos de librería con dos tipos)
        self.clan2 = None
        self.clan2_svg_path = None
        # Controla si el segundo símbolo se dibuja apilado (debajo) o en línea (lado a lado)
        self.clan2_stack = False
        # Controla si se dibuja un reborde blanco detrás del símbolo (por defecto False)
        # Se activará desde `LibreriaWidget` para mantener Cripta sin recuadro
        self.clan_draw_border = False
        # Senda (símbolo que va debajo del clan)
        self.senda = None
        self.senda_svg_path = None
        self.senda_size = 24
        self.senda_alignment = "izquierda"  # "izquierda" o "derecha"
        self.senda_draw_border = False
        # Texto de habilidades (recuadro inferior semitransparente)
        self.ability_text = ""
        self.ability_font = QFont()
        self.ability_color = "#ffffff"
        # Opacidad del fondo (0-255)
        self.ability_bg_opacity = 128
        # Modo de maquetación del texto de habilidades: "default" o "cripta"
        self.ability_layout_mode = "default"
        # Disciplinas (columna de iconos en el borde izquierdo)
        # Lista de elementos de disciplina: cada uno es un dict con claves
        # {"nombre": str, "svg_path": str}
        self.disciplines = []
        self.discipline_size = 24
        # Halo/borde blanco semitransparente alrededor del icono de disciplina
        self.discipline_draw_border = False
        # Modo de anclaje vertical de las disciplinas:
        #   "centro" (por defecto, usado en librería)
        #   "inferior" (anclar el primer icono en el tercio inferior y apilar hacia arriba)
        self.discipline_anchor_mode = "centro"
        # Ilustrador (texto en la parte inferior, debajo del cuadro de habilidades)
        self.illustrator_text = ""
        self.illustrator_font = QFont()
        self.illustrator_color = "#ffffff"
        # Grupo de cripta (número pequeño 1-9 sobre el cuadro de texto)
        self.crypt_group = None
        self.crypt_group_font = QFont()
        self.crypt_group_color = "#ffffff"
        # Coste (usado por Librería y Cripta)
        self.cost_type = None  # 'blood', 'pool', 'capacity' o None
        self.cost_svg_path = None
        self.cost_size = 20
        self.cost_draw_border = False
        self.cost_alignment = "izquierda"  # "izquierda" o "derecha"
        # Valor del coste: '1'..'6' o 'X' o None
        self.cost_value = None

        # Para depurar tamaños nativos de iconos de coste y evitar
        # saturar la consola, registramos qué rutas ya hemos informado.
        self._logged_cost_icon_sizes = set()

        # Asegurar que el layout tenga en cuenta heightForWidth
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def export_png(
        self,
        filename,
        width=VTES_CARD_WIDTH_300DPI,
        height=VTES_CARD_HEIGHT_300DPI,
        dpi=300,
    ):
        """Exporta la carta a un PNG con el tamaño oficial 63x88mm a 300 DPI.

        Usa por defecto 744x1038 píxeles (63x88mm a 300 DPI) y centra la carta
        dentro de ese lienzo respetando siempre la proporción.
        """
        if not filename:
            return False

        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        # Ajustar metadatos de resolución a ~300 DPI
        try:
            dots_per_meter = int(dpi / 0.0254)
            image.setDotsPerMeterX(dots_per_meter)
            image.setDotsPerMeterY(dots_per_meter)
        except Exception:
            pass

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # Queremos que el área de carta (la ilustración más todo lo
        # superpuesto) llene por completo el archivo, sin bordes extra.
        # Para ello calculamos el rectángulo de carta igual que en
        # paintEvent y sólo escalamos esa zona al lienzo de salida.

        src_w = float(self.width() or width)
        src_h = float(self.height() or height)
        if src_w <= 0 or src_h <= 0:
            painter.end()
            return False

        # Rectángulo de carta dentro del widget
        if self.pixmap and not self.pixmap.isNull():
            pw = float(self.pixmap.width())
            ph = float(self.pixmap.height())
            if pw > 0 and ph > 0:
                # Mismo criterio que en paintEvent: KeepAspectRatio
                scale = min(src_w / pw, src_h / ph)
                card_w = pw * scale
                card_h = ph * scale
                card_x = (src_w - card_w) / 2.0
                card_y = (src_h - card_h) / 2.0
            else:
                card_x = 0.0
                card_y = 0.0
                card_w = src_w
                card_h = src_h
        else:
            card_x = 0.0
            card_y = 0.0
            card_w = src_w
            card_h = src_h

        if card_w <= 0 or card_h <= 0:
            painter.end()
            return False

        # Factor de escala para llevar exactamente ese rectángulo de carta
        # al tamaño final (744x1038). Como ambas tienen la misma proporción
        # 63/88, usamos un único factor.
        scale_factor = width / card_w

        # Trasladar el origen al rectángulo de carta y escalar de forma
        # que dicho rectángulo ocupe todo el lienzo de salida.
        painter.translate(-card_x * scale_factor, -card_y * scale_factor)
        painter.scale(scale_factor, scale_factor)

        # Renderizar el widget completo; sólo la zona de carta rellenará
        # el archivo, eliminando los bordes externos.
        self.render(painter)

        painter.end()

        # Determinar formato de salida según la extensión del archivo
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".jpg", ".jpeg"):
            fmt = "JPEG"
        else:
            fmt = "PNG"

        return image.save(filename, fmt)

    def hasHeightForWidth(self):
        # Informar al layout de que usamos heightForWidth para mantener la proporción
        return True

    def heightForWidth(self, w):
        """Calcula la altura en función del ancho para mantener la proporción de carta."""
        if self.aspect_ratio and self.aspect_ratio > 0:
            return int(w / self.aspect_ratio)
        return super().heightForWidth(w)

    def sizeHint(self):
        """Tamaño sugerido manteniendo la proporción estándar de carta."""
        base_width = 320
        h = self.heightForWidth(base_width)
        return QSize(base_width, h)
        
    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()
        
    def set_title(self, text, font=None, color=None, alignment=None):
        self.title = text
        if font:
            self.title_font = font
        if color:
            self.title_color = color
        if alignment:
            self.title_alignment = alignment
        self.update()
        
    def set_clan(self, nombre_clan, size=None, alignment=None):
        """Establece el clan y carga su símbolo SVG"""
        self.clan = nombre_clan
        self.clan_svg_path = obtener_archivo_clan(nombre_clan)
        if size is not None:
            self.clan_size = size
        if alignment is not None:
            self.clan_alignment = alignment
        self.update()
    
    def set_clan2(self, nombre_clan2, svg_path=None):
        """Establece el segundo símbolo (para tipos de librería con dos tipos)"""
        self.clan2 = nombre_clan2
        self.clan2_svg_path = svg_path
        self.update()

    def set_senda(self, nombre_senda, size=None, alignment=None, svg_path=None):
        """Establece la senda y carga su símbolo SVG"""
        self.senda = nombre_senda
        # permitir pasar ruta svg ya resuelta
        if svg_path:
            self.senda_svg_path = svg_path
        else:
            self.senda_svg_path = obtener_archivo_senda(nombre_senda)
        if size is not None:
            self.senda_size = size
        if alignment is not None:
            self.senda_alignment = alignment
        self.update()

    def set_cost(self, cost_type, svg_path=None, size=None, value=None, alignment=None):
        """Establece el coste (tipo 'blood', 'pool' o 'capacity'), la ruta del icono y el valor opcional."""
        if cost_type is None or cost_type == "Ninguno":
            self.cost_type = None
            self.cost_svg_path = None
            self.cost_value = None
        else:
            self.cost_type = cost_type
            self.cost_svg_path = svg_path
            # conservar el valor si no se pasa explicitamente
            if value is not None:
                self.cost_value = value
        if size is not None:
            self.cost_size = size
        if alignment is not None:
            self.cost_alignment = alignment
        self.update()

    def set_disciplines(self, disciplines, size=None):
        """Establece la lista de disciplinas a dibujar en el borde izquierdo.

        disciplines debe ser una lista de dicts con forma
        {"nombre": str, "svg_path": str}.
        """
        self.disciplines = disciplines or []
        if size is not None:
            self.discipline_size = size
        self.update()

    def set_ability_text(self, text, font=None, color=None, bg_opacity=None):
        """Establece el texto de habilidades y su configuración visual."""
        self.ability_text = text or ""
        if font is not None:
            self.ability_font = font
        if color is not None:
            self.ability_color = color
        if bg_opacity is not None:
            # Se espera un valor 0-255
            self.ability_bg_opacity = max(0, min(255, int(bg_opacity)))
        self.update()

    def set_illustrator(self, text, font=None, color=None):
        """Establece el nombre del ilustrador que se dibuja debajo del recuadro de habilidades."""
        self.illustrator_text = text or ""
        # Siempre usar la fuente fija para el ilustrador
        self.illustrator_font = QFont("Arial", 8)  # Cambia "Arial" y 8 por lo que prefieras
        if color is not None:
            self.illustrator_color = color
        self.update()

    def set_crypt_group(self, value, font=None, color=None):
        """Establece el grupo de cripta (1-9) que se dibuja sobre el cuadro de texto.

        Si value es None, "" o "Ninguno", no se dibuja nada.
        """
        if value is None or str(value).strip() == "" or str(value).strip().lower() == "ninguno":
            self.crypt_group = None
        else:
            self.crypt_group = str(value).strip()
        if font is not None:
            self.crypt_group_font = font
        if color is not None:
            self.crypt_group_color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Reiniciar la referencia del borde inferior del cuadro de texto de
        # habilidades para este repintado
        self._last_overlay_bottom = None
        
        # Dibujar imagen de fondo y calcular el rectángulo exacto de la carta
        if self.pixmap:
            # Ajustar la imagen completa dentro del widget manteniendo SIEMPRE
            # la proporción (sin recortar), para que se vea entera la
            # ilustración importada.
            scaled = self.pixmap.scaled(
                self.width(),
                self.height(),
                1,  # Qt.KeepAspectRatio
                Qt.SmoothTransformation,
            )
            card_w = scaled.width()
            card_h = scaled.height()
            card_x = int((self.width() - card_w) / 2)
            card_y = int((self.height() - card_h) / 2)
            painter.drawPixmap(card_x, card_y, scaled)
        else:
            card_x = 0
            card_y = 0
            card_w = self.width()
            card_h = self.height()

        margin = 16

        # Centro común de la columna izquierda (clan/senda/disciplinas)
        # Nota: NO usamos cost_size aquí para que al agrandar el icono de coste
        # no se desplace hacia la derecha toda la columna de símbolos.
        max_icon_col = max(
            getattr(self, 'clan_size', 0),
            getattr(self, 'senda_size', 0),
            getattr(self, 'discipline_size', 0),
        )
        left_col_center_x = card_x + (margin + (max_icon_col / 2.0) if max_icon_col > 0 else margin)
        
        # Dibujar título
        painter.setFont(self.title_font)
        color = QColor(self.title_color) if isinstance(self.title_color, str) else self.title_color
        painter.setPen(color)
        
        # Calcular posición del título dentro del rectángulo de la carta
        title_rect = QRectF(
            card_x + margin,
            card_y + margin,
            max(1, card_w - 2 * margin),
            40,
        )
        if self.title_alignment == "izquierda":
            alignment_flags = Qt.AlignLeft | Qt.AlignTop
        else:  # centro por defecto
            alignment_flags = Qt.AlignCenter | Qt.AlignTop
        painter.drawText(title_rect, alignment_flags, self.title)
        
            # Dibujar símbolo del clan (o tipo en Librería) debajo del nombre
        if self.clan_svg_path and os.path.exists(self.clan_svg_path):
            # Calcular posición Y del símbolo (debajo del título)
            title_height = painter.fontMetrics().height()
            clan_y = card_y + margin + title_height + 8  # 8 píxeles de separación
            
            # Calcular posición X según la alineación configurada
            if self.clan_alignment == "derecha":
                clan_x = card_x + card_w - margin - self.clan_size
            elif self.clan_alignment == "centro":
                clan_x = card_x + (card_w - self.clan_size) // 2
            else:  # "izquierda" por defecto: centrar en la columna izquierda
                clan_x = left_col_center_x - (self.clan_size / 2.0)
            
            # Renderizar SVG con reborde blanco
            svg_renderer = QSvgRenderer(self.clan_svg_path)
            if svg_renderer.isValid():
                from PyQt5.QtGui import QBrush, QPen

                # Reborde más fino: sólo contorno blanco alrededor del icono

                # Dibujar reborde blanco sólo si la bandera está activada
                if getattr(self, 'clan_draw_border', False):
                    border_width = max(1, int(self.clan_size * 0.04))
                    border_rect = QRectF(
                        clan_x,
                        clan_y,
                        self.clan_size,
                        self.clan_size,
                    )
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(QColor(255, 255, 255, 255), border_width))
                    painter.drawRoundedRect(border_rect, 3, 3)

                # Renderizar el símbolo SVG (siempre)
                clan_rect = QRectF(clan_x, clan_y, self.clan_size, self.clan_size)
                svg_renderer.render(painter, clan_rect)
            
            # Dibujar segundo símbolo si existe (para tipos de librería con dos tipos)
            if self.clan2_svg_path and os.path.exists(self.clan2_svg_path):
                # Renderizar segundo SVG con reborde blanco (más fino)
                svg_renderer2 = QSvgRenderer(self.clan2_svg_path)
                if svg_renderer2.isValid():
                    from PyQt5.QtGui import QBrush, QPen

                    # Separación entre símbolos
                    spacing = 4

                    # Si clan2_stack es True, dibujar el segundo símbolo debajo del primero
                    if getattr(self, 'clan2_stack', False):
                        clan2_x = clan_x
                        clan2_y = clan_y + self.clan_size + spacing
                    else:
                        # Comportamiento por defecto: lado a lado
                        clan2_x = clan_x + self.clan_size + spacing
                        clan2_y = clan_y

                    # Dibujar reborde blanco para el segundo símbolo sólo si la bandera está activada
                    if getattr(self, 'clan_draw_border', False):
                        border_width2 = max(1, int(self.clan_size * 0.04))
                        border_rect2 = QRectF(
                            clan2_x,
                            clan2_y,
                            self.clan_size,
                            self.clan_size,
                        )
                        painter.setBrush(Qt.NoBrush)
                        painter.setPen(QPen(QColor(255, 255, 255, 255), border_width2))
                        painter.drawRoundedRect(border_rect2, 3, 3)

                    # Renderizar el segundo símbolo SVG encima del reborde (si existe)
                    clan2_rect = QRectF(clan2_x, clan2_y, self.clan_size, self.clan_size)
                    svg_renderer2.render(painter, clan2_rect)

                    # fin bloque clan/clan2

        # Dibujar senda si existe (se dibuja incluso si no hay clan)
        if getattr(self, 'senda_svg_path', None) and os.path.exists(self.senda_svg_path):
            svg_renderer_senda = QSvgRenderer(self.senda_svg_path)
            if svg_renderer_senda.isValid():
                from PyQt5.QtGui import QBrush

                # Recalcular altura del título para posicionamiento
                title_height = painter.fontMetrics().height()
                base_y = card_y + margin + title_height + 8

                # Determinar la Y inferior según si hay clan/clan2 dibujados
                bottom_y = base_y
                if self.clan_svg_path and os.path.exists(self.clan_svg_path):
                    bottom_y += self.clan_size
                # Si existe clan2 y está apilado, añadir espacio adicional
                spacing = 6
                if self.clan2_svg_path and os.path.exists(self.clan2_svg_path) and getattr(self, 'clan2_stack', False):
                    bottom_y += self.clan_size + spacing

                senda_y = bottom_y + spacing

                # Calcular X según alineación de la senda
                if self.senda_alignment == 'derecha':
                    senda_x = card_x + card_w - margin - self.senda_size
                else:  # izquierda por defecto: centrar en la columna izquierda
                    senda_x = left_col_center_x - (self.senda_size / 2.0)

                # Dibujar reborde si está activado y renderizar la senda
                border_width = 1

                # Mantener la proporción original del SVG al escalar
                svg_default = svg_renderer_senda.defaultSize()
                svg_w = svg_default.width() if svg_default.width() > 0 else 1
                svg_h = svg_default.height() if svg_default.height() > 0 else 1
                # Usar self.senda_size como tamaño máximo (lado mayor)
                scale = min(self.senda_size / svg_w, self.senda_size / svg_h)
                target_w = svg_w * scale
                target_h = svg_h * scale

                # Ajustar X según alineación usando el ancho real objetivo
                if self.senda_alignment == 'derecha':
                    senda_x = card_x + card_w - margin - target_w
                else:
                    # izquierda por defecto: centrar en la columna izquierda
                    senda_x = left_col_center_x - (target_w / 2.0)

                # Dibujar reborde (basado en las dimensiones reales)
                if getattr(self, 'senda_draw_border', False):
                    border_rect_s = QRectF(
                        senda_x - border_width,
                        senda_y - border_width,
                        target_w + (border_width * 2),
                        target_h + (border_width * 2)
                    )
                    painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(border_rect_s, 3, 3)

                # Renderizar senda respetando su proporción
                senda_rect = QRectF(senda_x, senda_y, target_w, target_h)
                svg_renderer_senda.render(painter, senda_rect)

        # Recuadro de texto de habilidades (parte inferior de la carta)
        ability_text_str = getattr(self, 'ability_text', "").strip()
        illustrator_text_str = getattr(self, 'illustrator_text', "").strip()

        if ability_text_str:
            from PyQt5.QtGui import QTextDocument, QTextOption

            # Configuración del recuadro de habilidades: tamaño y posición
            layout_mode = getattr(self, 'ability_layout_mode', 'default')

            if layout_mode == 'cripta':
                # En cripta queremos un recuadro algo más pequeño y más bajo
                # para dejar más aire al resto de elementos.
                overlay_height = max(60, int(card_h * 0.22))
                overlay_height = min(overlay_height, max(60, card_h - margin * 3))
            else:
                overlay_height = max(80, int(card_h * 0.28))
                overlay_height = min(overlay_height, max(80, card_h - margin * 3))

            # Reservar espacio para el texto del ilustrador debajo del recuadro.
            # En cripta lo reservamos siempre (haya texto o no) para que la
            # posición vertical del cuadro de habilidades no cambie.
            extra_for_illustrator = 0
            ill_font = self.illustrator_font if self.illustrator_font is not None else self.ability_font
            if layout_mode == 'cripta' or illustrator_text_str:
                fm_ill = QFontMetrics(ill_font)
                extra_for_illustrator = fm_ill.height() + 4

            if layout_mode == 'cripta':
                # Bajar ligeramente el recuadro en cripta para que quede
                # algo más cerca del borde inferior.
                offset = margin * 0.5
                overlay_y = card_y + card_h - margin - overlay_height - extra_for_illustrator + offset
            else:
                overlay_y = card_y + card_h - margin - overlay_height - extra_for_illustrator

            # Dejar una columna libre a la izquierda para coste/disciplinas.
            # En cripta ampliamos un poco más esa columna para que haya
            # más aire entre los iconos de disciplina y el cuadro de texto.
            icon_col = max(getattr(self, 'discipline_size', 0), getattr(self, 'cost_size', 0))
            extra_icon_space = 0
            if layout_mode == 'cripta':
                # En cripta dejamos una separación clara respecto a la columna
                # de disciplinas/coste: usamos todo el ancho de icon_col más
                # un pequeño extra para que el fondo no toque los iconos.
                base_icon_offset = icon_col
                extra_icon_space = int(icon_col * 0.5)
                left_free = card_x + margin + base_icon_offset + extra_icon_space + 2
            else:
                # En librería queremos ganar algo de ancho de texto, así que
                # reducimos la reserva horizontal para la columna de iconos.
                base_icon_offset = int(icon_col * 0.6)
                left_free = card_x + margin + base_icon_offset + extra_icon_space + 2
            overlay_rect = QRectF(left_free, overlay_y, card_x + card_w - margin - left_free, overlay_height)

            # Guardar el borde inferior del cuadro de texto para alinear
            # las disciplinas con él (en modo cripta)
            self._last_overlay_bottom = overlay_rect.bottom()

            # Dibujar, si existe, el número de grupo de cripta justo encima del
            # cuadro de texto, pequeñito y alineado a la izquierda de dicho cuadro.
            group_value = getattr(self, 'crypt_group', None)
            if group_value:
                painter.save()
                group_font = self.crypt_group_font if self.crypt_group_font is not None else self.ability_font
                painter.setFont(group_font)
                group_color = self.crypt_group_color if not isinstance(self.crypt_group_color, str) else QColor(self.crypt_group_color)
                painter.setPen(group_color)

                fm_group = QFontMetrics(group_font)
                text = str(group_value)
                text_w = fm_group.horizontalAdvance(text)
                text_h = fm_group.height()

                # Pequeño margen desde la izquierda del cuadro de texto
                # (lo movemos un poco más a la derecha junto con el cuadro).
                margin_x = 6
                # Colocar el número justo por encima del recuadro
                group_rect = QRectF(
                    overlay_rect.left() + margin_x,
                    overlay_rect.top() - text_h - 2,
                    text_w,
                    text_h,
                )
                painter.drawText(group_rect, Qt.AlignLeft | Qt.AlignBottom, text)
                painter.restore()

            # Fondo semitransparente
            bg_opacity = getattr(self, 'ability_bg_opacity', 128)
            bg_opacity = max(0, min(255, int(bg_opacity)))
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, bg_opacity))
            painter.drawRoundedRect(overlay_rect, 6, 6)

            # Preparar texto con soporte básico de **negrita** y [Disciplina]
            # Altura del icono de disciplina ~ altura de la fuente de habilidades
            fm = QFontMetrics(self.ability_font)
            icon_h = max(8, fm.height() - 2)

            inline_images = {}

            def _ability_to_html(source: str) -> str:
                res = []
                bold = False
                i = 0
                while i < len(source):
                    if source[i:i+2] == "**":
                        res.append("</b>" if bold else "<b>")
                        bold = not bold
                        i += 2
                        continue
                    if source[i] == "[":
                        end = source.find("]", i + 1)
                        if end != -1:
                            tag = source[i+1:end].strip()
                            icon_path = obtener_archivo_disciplina_texto(tag)
                            if icon_path:
                                # Si el recurso es SVG, lo convertimos a QImage y lo
                                # registramos explícitamente en el QTextDocument para
                                # que pueda renderizarlo dentro del texto.
                                ext = os.path.splitext(icon_path)[1].lower()
                                if ext == ".svg":
                                    # Usamos una URL lógica para el recurso, independiente de la ruta física
                                    url_str = f"disciplina:{os.path.basename(icon_path)}"
                                    if url_str not in inline_images:
                                        svg_renderer = QSvgRenderer(icon_path)
                                        if svg_renderer.isValid():
                                            default_size = svg_renderer.defaultSize()
                                            native_w = default_size.width() if default_size.width() > 0 else icon_h
                                            native_h = default_size.height() if default_size.height() > 0 else icon_h
                                            scale = icon_h / max(native_w, native_h)
                                            target_w = max(1, int(native_w * scale))
                                            target_h = max(1, int(native_h * scale))

                                            image = QImage(target_w, target_h, QImage.Format_ARGB32)
                                            image.fill(Qt.transparent)
                                            p = QPainter(image)
                                            p.setRenderHint(QPainter.Antialiasing)
                                            svg_renderer.render(p, QRectF(0, 0, target_w, target_h))
                                            p.end()

                                            inline_images[url_str] = image

                                    res.append(f'<img src="{url_str}" />')
                                else:
                                    # Formatos raster se pueden usar directamente
                                    res.append(f'<img src="{icon_path}" height="{icon_h}" />')
                                i = end + 1
                                continue
                            # Si no se encuentra icono, dejar el texto tal cual
                            res.append(html.escape(source[i:end+1]))
                            i = end + 1
                            continue
                    ch = source[i]
                    if ch == "\n":
                        res.append("<br/>")
                    else:
                        res.append(html.escape(ch))
                    i += 1
                if bold:
                    res.append("</b>")
                return "".join(res)

            ability_html = _ability_to_html(self.ability_text)

            doc = QTextDocument()
            doc.setDefaultFont(self.ability_font)
            html_color = self.ability_color if isinstance(self.ability_color, str) else QColor(self.ability_color).name()
            # Reducir ligeramente el interlineado. En cripta lo hacemos
            # todavía un poco más compacto que en librería.
            if layout_mode == 'cripta':
                line_height = "90%"
            else:
                line_height = "95%"
            doc.setHtml(f'<div style="color:{html_color}; line-height: {line_height};">{ability_html}</div>')

            # Registrar recursos de imagen generados a partir de SVG para que
            # QTextDocument pueda resolver las URLs usadas en los <img src="...">.
            if inline_images:
                for url_str, image in inline_images.items():
                    doc.addResource(QTextDocument.ImageResource, QUrl(url_str), image)
            opt = QTextOption()
            opt.setWrapMode(QTextOption.WordWrap)
            # Texto centrado horizontalmente; el centrado vertical real
            # lo controlamos desplazando el área de dibujo según la altura
            # real del QTextDocument.
            opt.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            doc.setDefaultTextOption(opt)
            doc.setTextWidth(overlay_rect.width() - 16)

            # Dibujar el texto dentro del recuadro con padding; en cripta
            # centramos verticalmente calculando el alto real del contenido.
            avail_h = overlay_rect.height() - 16
            content_h = doc.size().height()
            if layout_mode == 'cripta':
                extra_top = max(0.0, (avail_h - content_h) / 2.0)
            else:
                extra_top = 0.0

            painter.translate(
                overlay_rect.left() + 8,
                overlay_rect.top() + 8 + extra_top,
            )
            clip_rect = QRectF(0, 0, overlay_rect.width() - 16, avail_h)
            painter.setClipRect(clip_rect)
            doc.drawContents(painter, clip_rect)
            painter.restore()

            # Texto de ilustrador bajo el recuadro de habilidades
            if illustrator_text_str:
                painter.save()
                painter.setFont(ill_font)
                ill_color = self.illustrator_color if isinstance(self.illustrator_color, str) else QColor(self.illustrator_color).name()
                painter.setPen(QColor(ill_color) if isinstance(ill_color, str) else ill_color)

                fm_ill = QFontMetrics(ill_font)
                ill_h = fm_ill.height()
                ill_rect = QRectF(
                    overlay_rect.left(),
                    overlay_rect.bottom() + 2,
                    overlay_rect.width(),
                    ill_h + 2,
                )
                painter.drawText(ill_rect, Qt.AlignHCenter | Qt.AlignTop, illustrator_text_str)
                painter.restore()

        # Dibujar disciplinas (columna de iconos en el borde izquierdo)
        if getattr(self, 'disciplines', None):
            from PyQt5.QtGui import QBrush

            # Filtrar entradas con ruta válida existente
            valid_items = [d for d in self.disciplines if d.get("svg_path") and os.path.exists(d["svg_path"])]
            if valid_items:
                # Espaciado vertical entre iconos (mismo para todas las disciplinas)
                base_size = max(8, self.discipline_size)
                spacing = max(6, int(base_size * 0.35))

                # Preparar lista de iconos con sus tamaños reales ya calculados
                prepared = []
                for item in valid_items:
                    path = item["svg_path"]
                    ext = os.path.splitext(path)[1].lower()
                    is_svg = ext == '.svg'

                    svg_renderer_d = None
                    pixmap_d = None
                    if is_svg:
                        svg_renderer_d = QSvgRenderer(path)
                        if not svg_renderer_d.isValid():
                            svg_renderer_d = None
                    else:
                        pixmap_d = QPixmap(path)
                        if pixmap_d.isNull():
                            pixmap_d = None

                    if svg_renderer_d is None and pixmap_d is None:
                        continue

                    # Determinar si esta disciplina es "Superior" según su nombre
                    nombre_disc = str(item.get("nombre", ""))
                    lower_name = nombre_disc.lower()
                    es_superior = lower_name.startswith("superior ") or lower_name.endswith(" superior")

                    # Obtener dimensiones nativas
                    if svg_renderer_d:
                        svg_default = svg_renderer_d.defaultSize()
                        native_w = svg_default.width() if svg_default.width() > 0 else 1
                        native_h = svg_default.height() if svg_default.height() > 0 else 1
                    else:
                        native_w = pixmap_d.width() if pixmap_d.width() > 0 else 1
                        native_h = pixmap_d.height() if pixmap_d.height() > 0 else 1

                    # Hacer que las disciplinas superiores sean más grandes
                    # que las inferiores.
                    icon_size = base_size * (1.3 if es_superior else 1.0)
                    scale = min(icon_size / native_w, icon_size / native_h)
                    target_w = native_w * scale
                    target_h = native_h * scale

                    prepared.append({
                        "item": item,
                        "path": path,
                        "svg_renderer": svg_renderer_d,
                        "pixmap": pixmap_d,
                        "es_superior": es_superior,
                        "target_w": target_w,
                        "target_h": target_h,
                    })

                if not prepared:
                    return

                # Altura total de la columna: suma de alturas reales + huecos iguales
                total_h = sum(p["target_h"] for p in prepared) + spacing * (len(prepared) - 1)

                mode = getattr(self, 'discipline_anchor_mode', 'centro')
                if mode == 'inferior':
                    # En cripta, anclar la columna al borde inferior del cuadro
                    # de texto de habilidades (si existe); en caso contrario,
                    # usar el borde inferior de la carta.
                    bottom_limit = card_y + card_h - margin
                    if getattr(self, 'ability_layout_mode', 'default') == 'cripta':
                        overlay_bottom = getattr(self, '_last_overlay_bottom', None)
                        if overlay_bottom is not None:
                            bottom_limit = overlay_bottom

                    start_y = max(card_y + margin, bottom_limit - total_h)
                else:
                    # Centrar aproximadamente la columna en la altura disponible
                    start_y = max(card_y + margin, (card_y + card_h - total_h) / 2.0)

                y = start_y
                for data in prepared:
                    item = data["item"]
                    svg_renderer_d = data["svg_renderer"]
                    pixmap_d = data["pixmap"]
                    es_superior = data["es_superior"]
                    target_w = data["target_w"]
                    target_h = data["target_h"]

                    # Centrar cada icono en la misma columna vertical
                    x = left_col_center_x - (target_w / 2.0)

                    # Opcionalmente halo/borde blanco (igual estilo que tipos/clan).
                    # Para disciplinas superiores, usamos borde en forma de rombo
                    # para diferenciarlas visualmente.
                    if getattr(self, 'discipline_draw_border', False):
                        from PyQt5.QtGui import QPen
                        from PyQt5.QtCore import QPointF
                        from PyQt5.QtGui import QPolygonF

                        painter.setBrush(Qt.NoBrush)
                        # Grosor proporcional al tamaño del icono, como en clan/tipo
                        border_width = max(1, int(base_size * 0.04))
                        painter.setPen(QPen(QColor(255, 255, 255, 255), border_width))

                        if es_superior:
                            # Rombo centrado en el icono
                            cx = x + (target_w / 2.0)
                            cy = y + (target_h / 2.0)
                            rx = target_w / 2.0
                            ry = target_h / 2.0
                            puntos = [
                                QPointF(cx, cy - ry),  # arriba
                                QPointF(cx + rx, cy),  # derecha
                                QPointF(cx, cy + ry),  # abajo
                                QPointF(cx - rx, cy),  # izquierda
                            ]
                            painter.drawPolygon(QPolygonF(puntos))
                        else:
                            border_rect_d = QRectF(
                                x,
                                y,
                                target_w,
                                target_h,
                            )
                            painter.drawRoundedRect(border_rect_d, 3, 3)

                    if svg_renderer_d:
                        d_rect = QRectF(x, y, target_w, target_h)
                        svg_renderer_d.render(painter, d_rect)
                    else:
                        scaled_d = pixmap_d.scaled(int(round(target_w)), int(round(target_h)), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        painter.drawPixmap(int(round(x)), int(round(y)), scaled_d)

                    # Avanzar Y para el siguiente icono manteniendo siempre
                    # la misma distancia entre bordes inferiores y superiores.
                    y += target_h + spacing

        # Coste (se dibuja en la esquina inferior izquierda/derecha según configuración)
        if getattr(self, 'cost_svg_path', None) and os.path.exists(self.cost_svg_path):
            from PyQt5.QtGui import QBrush, QFont

            ext = os.path.splitext(self.cost_svg_path)[1].lower()
            is_svg = ext == '.svg'

            svg_renderer_cost = None
            pixmap_cost = None
            if is_svg:
                svg_renderer_cost = QSvgRenderer(self.cost_svg_path)
                if not svg_renderer_cost.isValid():
                    svg_renderer_cost = None
            else:
                pixmap_cost = QPixmap(self.cost_svg_path)
                if pixmap_cost.isNull():
                    pixmap_cost = None

            if svg_renderer_cost is None and pixmap_cost is None:
                pass
            else:
                # Obtener dimensiones nativas
                if svg_renderer_cost:
                    svg_default = svg_renderer_cost.defaultSize()
                    native_w = svg_default.width() if svg_default.width() > 0 else 1
                    native_h = svg_default.height() if svg_default.height() > 0 else 1
                else:
                    native_w = pixmap_cost.width() if pixmap_cost.width() > 0 else 1
                    native_h = pixmap_cost.height() if pixmap_cost.height() > 0 else 1

                scale = min(self.cost_size / native_w, self.cost_size / native_h)
                target_w = native_w * scale
                target_h = native_h * scale

                # Log sencillo para ver si estamos ampliando demasiado los
                # iconos de coste (especialmente pool/blood) y provocar
                # pixelado en la exportación.
                try:
                    key = (self.cost_svg_path, native_w, native_h, self.cost_size)
                    if hasattr(self, '_logged_cost_icon_sizes') and key not in self._logged_cost_icon_sizes:
                        self._logged_cost_icon_sizes.add(key)
                        print(
                            f"[COST_ICON] type={self.cost_type} path={self.cost_svg_path} "
                            f"native={native_w}x{native_h}px target={target_w:.1f}x{target_h:.1f}px"
                        )
                except Exception:
                    pass

                # Posición horizontal: izquierda (columna de iconos) o derecha
                if getattr(self, 'cost_alignment', 'izquierda') == 'derecha':
                    # Esquina inferior derecha de la carta
                    cost_x = card_x + card_w - margin - target_w
                else:
                    # Esquina inferior izquierda, centrado en la columna de iconos
                    cost_x = left_col_center_x - (target_w / 2.0)
                # Elevar ligeramente el icono para que no quede pegado al borde inferior
                extra_offset = max(4, int(target_h * 0.25))
                cost_y = max(card_y + margin, card_y + card_h - margin - target_h - extra_offset)

                # Espaciado entre iconos cuando hay varios
                spacing = 4

                # Independientemente del valor (1..6 o X), dibujar siempre un único icono
                border_width = 1
                if getattr(self, 'cost_draw_border', False):
                    border_rect_c = QRectF(
                        cost_x - border_width,
                        cost_y - border_width,
                        target_w + (border_width * 2),
                        target_h + (border_width * 2)
                    )
                    painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(border_rect_c, 3, 3)

                if svg_renderer_cost:
                    cost_rect = QRectF(cost_x, cost_y, target_w, target_h)
                    svg_renderer_cost.render(painter, cost_rect)
                else:
                    scaled = pixmap_cost.scaled(int(round(target_w)), int(round(target_h)), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    painter.drawPixmap(int(round(cost_x)), int(round(cost_y)), scaled)

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
        "simbolo_clan": {
            "tamano": 40,
            "alineacion": "izquierda"
        }
        ,
        "simbolo_senda": {
            "tamano": 24,
            "alineacion": "izquierda"
        }
    }

    data = load_config_data({})
    return _deep_merge_dicts(defaults, data)

class CriptaWidget(QWidget):
    @property
    def cripta_title(self):
        # Devuelve el texto actual del título para compatibilidad
        return self.cripta_card_widget.title

    def __init__(self, importar_imagen_callback):
        super().__init__()
        self.layout = QHBoxLayout()
        config = cargar_config()
        # Widget personalizado para imagen y título
        from PyQt5.QtWidgets import QLineEdit
        self.cripta_card_widget = CartaImageWidget()
        self.cripta_card_widget.setMinimumHeight(400)
        self.cripta_card_widget.setStyleSheet("background: #232629;")
        self.cripta_card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.cripta_card_widget, stretch=2)
        # Para compatibilidad con el resto de la app
        self.cripta_label = self.cripta_card_widget
        # Cargar fuente desde archivo
        nombre_config = config["nombre_carta"]
        fuente_archivo = nombre_config["fuente"]
        font_path = os.path.join(get_resource_path("fonts"), fuente_archivo)
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], nombre_config["tamano"])
            else:
                font = QFont(fuente_archivo, nombre_config["tamano"])
        else:
            font = QFont(fuente_archivo, nombre_config["tamano"])
        self.cripta_title_font = font
        self.cripta_title_color = nombre_config["color"]
        # Configurar alineación
        self.cripta_card_widget.title_alignment = nombre_config.get("alineacion", "centro")
        # Configurar tamaño y alineación del símbolo de clan
        simbolo_config = config.get("simbolo_clan", {})
        self.cripta_card_widget.clan_size = simbolo_config.get("tamano", 40)
        self.cripta_card_widget.clan_alignment = simbolo_config.get("alineacion", "izquierda")
        # Configurar tamaño y alineación del símbolo de senda (debajo del clan)
        simbolo_senda_config = config.get("simbolo_senda", {})
        self.cripta_card_widget.senda_size = simbolo_senda_config.get("tamano", 24)
        self.cripta_card_widget.senda_alignment = simbolo_senda_config.get("alineacion", "izquierda")
        # Tamaño de iconos de disciplina (cripta) compartido con librería
        simbolo_disciplina_config = config.get("simbolo_disciplina", {})
        self.cripta_card_widget.discipline_size = simbolo_disciplina_config.get("tamano", 24)
        # Activar halo de disciplina también en cripta
        self.cripta_card_widget.discipline_draw_border = True
        # En cripta las disciplinas se anclan en el tercio inferior y se apilan hacia arriba
        self.cripta_card_widget.discipline_anchor_mode = "inferior"
        # Tamaño de símbolo de coste (compartido con librería)
        simbolo_coste_config = config.get("simbolo_coste", {})
        self.cripta_card_widget.cost_size = simbolo_coste_config.get("tamano", 40)
        # Tamaño de iconos de disciplina (cripta) compartido con librería
        simbolo_disciplina_config = config.get("simbolo_disciplina", {})
        self.cripta_card_widget.discipline_size = simbolo_disciplina_config.get("tamano", 24)
        # Configuración de texto de habilidades
        texto_hab_config = config.get("texto_habilidad", {})
        hab_fuente_archivo = texto_hab_config.get("fuente", "Gill Sans.otf")
        hab_font_path = os.path.join(get_resource_path("fonts"), hab_fuente_archivo)
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
                hab_font = QFont(hab_fuente_archivo, hab_size)
        else:
            hab_font = QFont(hab_fuente_archivo, hab_size)

        self.cripta_ability_font = hab_font
        self.cripta_ability_color = hab_color
        self.cripta_ability_bg_opacity = hab_opacidad
        self.cripta_card_widget.ability_font = hab_font
        self.cripta_card_widget.ability_color = hab_color
        self.cripta_card_widget.ability_bg_opacity = hab_opacidad
        # Configurar fuente y color para el grupo de cripta (un poco más pequeño
        # que el texto de habilidades, reutilizando la misma familia/color)
        group_font = QFont(hab_font)
        group_font.setPointSize(max(6, hab_size - 2))
        self.cripta_group_font = group_font
        self.cripta_group_color = hab_color
        self.cripta_card_widget.crypt_group_font = group_font
        self.cripta_card_widget.crypt_group_color = hab_color
        # Activar el modo de maquetación de habilidades específico de cripta
        self.cripta_card_widget.ability_layout_mode = "cripta"
        # Campo de nombre editable
        self.cripta_name_edit = QLineEdit()
        self.cripta_name_edit.setPlaceholderText("Nombre de la carta")
        self.cripta_name_edit.setText("")
        self.cripta_name_edit.textChanged.connect(self.set_title_from_edit)
        # Selector de clan
        from PyQt5.QtWidgets import QComboBox
        from resources.listas.clans_list import CLANES
        self.cripta_clan_combo = QComboBox()
        self.cripta_clan_combo.addItems(CLANES)
        self.cripta_clan_combo.setCurrentText("Ninguno")
        self.cripta_clan_combo.currentTextChanged.connect(self.set_clan_from_combo)
        # Selector de senda (debajo del clan)
        from resources.listas.sendas_list import SENDAS
        self.cripta_senda_combo = QComboBox()
        self.cripta_senda_combo.addItems(SENDAS)
        self.cripta_senda_combo.setCurrentText("Ninguno")
        self.cripta_senda_combo.currentTextChanged.connect(self.set_senda_from_combo)
        self.cripta_right_panel = QWidget()
        self.cripta_right_layout = QVBoxLayout()

        columnas_layout = QHBoxLayout()
        col1_layout = QVBoxLayout()
        col2_layout = QVBoxLayout()

        # Columna 1: nombre, clan, senda, coste
        col1_layout.addWidget(QLabel("Nombre:"))
        col1_layout.addWidget(self.cripta_name_edit)
        col1_layout.addWidget(QLabel("Clan:"))
        col1_layout.addWidget(self.cripta_clan_combo)
        col1_layout.addWidget(QLabel("Senda:"))
        col1_layout.addWidget(self.cripta_senda_combo)

        # Grupo de cripta (número pequeño 1-9 sobre el cuadro de texto)
        col1_layout.addWidget(QLabel("Grupo de cripta:"))
        self.cripta_group_combo = QComboBox()
        self.cripta_group_combo.addItem("Ninguno")
        for i in range(1, 10):
            self.cripta_group_combo.addItem(str(i))
        self.cripta_group_combo.setCurrentText("Ninguno")
        self.cripta_group_combo.currentTextChanged.connect(self.set_cripta_group_from_combo)
        col1_layout.addWidget(self.cripta_group_combo)

        # Selector de coste (capacidad) para cripta
        from PyQt5.QtWidgets import QListWidget, QAbstractItemView, QComboBox, QLineEdit
        from resources.listas.disciplines_list import DISCIPLINAS
        col1_layout.addWidget(QLabel("Coste (capacidad):"))
        self.cripta_cost_combo = QComboBox()
        self.cripta_cost_combo.addItem("Ninguno")
        # Detectar valores disponibles a partir de la carpeta resources/costes
        base_costes = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "costes")
        try:
            for fname in sorted(os.listdir(base_costes)):
                if fname.lower().startswith("cap") and fname.lower().endswith(".gif"):
                    stem = os.path.splitext(fname)[0]
                    num = stem[3:]
                    if num.isdigit():
                        self.cripta_cost_combo.addItem(num)
        except FileNotFoundError:
            pass
        self.cripta_cost_combo.setCurrentText("Ninguno")
        self.cripta_cost_combo.currentTextChanged.connect(self.set_cripta_cost_from_combo)
        col1_layout.addWidget(self.cripta_cost_combo)

        # Columna 2: disciplinas, texto de habilidades, ilustrador
        col2_layout.addWidget(QLabel("Disciplinas:"))
        self.cripta_disciplines_list = QListWidget()
        self.cripta_disciplines_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for d in DISCIPLINAS:
            self.cripta_disciplines_list.addItem(d)
        self.cripta_disciplines_list.itemSelectionChanged.connect(self.set_disciplines_from_list)
        col2_layout.addWidget(self.cripta_disciplines_list)

        col2_layout.addWidget(QLabel("Texto de habilidades:"))
        self.cripta_ability_edit = QPlainTextEdit()
        self.cripta_ability_edit.setPlaceholderText("Escribe el texto de habilidades (**negrita**)...")
        # Hacer el área de edición más cómoda y expandible
        self.cripta_ability_edit.setMinimumHeight(150)
        self.cripta_ability_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cripta_ability_edit.textChanged.connect(self.set_ability_from_edit)
        col2_layout.addWidget(self.cripta_ability_edit)

        # Ilustrador (nombre en la parte inferior de la carta)
        col2_layout.addWidget(QLabel("Ilustrador:"))
        self.cripta_illustrator_edit = QLineEdit()
        self.cripta_illustrator_edit.setPlaceholderText("Nombre del ilustrador original")
        self.cripta_illustrator_edit.textChanged.connect(self.set_illustrator_from_edit)
        col2_layout.addWidget(self.cripta_illustrator_edit)

        columnas_layout.addLayout(col1_layout)
        columnas_layout.addLayout(col2_layout)

        self.cripta_right_layout.addLayout(columnas_layout)
        self.cripta_right_layout.addStretch(1)
        botones_layout = QHBoxLayout()
        btn_importar_cripta = QPushButton('Importar Imagen')
        btn_importar_cripta.setMinimumWidth(100)
        btn_importar_cripta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_importar_cripta.clicked.connect(partial(importar_imagen_callback, self))
        btn_guardar_cripta = QPushButton('Guardar')
        btn_guardar_cripta.setMinimumWidth(100)
        btn_guardar_cripta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_guardar_cripta.clicked.connect(self.guardar_carta_cripta)
        btn_guardar_online_cripta = QPushButton('Guardar para Online')
        btn_guardar_online_cripta.setMinimumWidth(100)
        btn_guardar_online_cripta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_guardar_online_cripta.clicked.connect(self.guardar_carta_cripta_online)
        botones_layout.addWidget(btn_importar_cripta, stretch=1)
        botones_layout.addWidget(btn_guardar_cripta, stretch=1)
        botones_layout.addWidget(btn_guardar_online_cripta, stretch=1)
        self.cripta_right_layout.addLayout(botones_layout)
        self.cripta_right_panel.setLayout(self.cripta_right_layout)
        self.layout.addWidget(self.cripta_right_panel, stretch=1)
        self.setLayout(self.layout)

    def guardar_carta_cripta(self):
        """Guarda la carta de cripta actual (PNG o JPG, 63x88mm a 300 DPI)."""
        if hasattr(self, 'cripta_name_edit'):
            nombre_base = self.cripta_name_edit.text().strip()
        else:
            nombre_base = ""
        if not nombre_base:
            nombre_base = "carta_cripta"
        safe_name = "".join(c for c in nombre_base if c.isalnum() or c in (" ", "-", "_")).strip()
        if not safe_name:
            safe_name = "carta_cripta"
        default_path = os.path.join(os.getcwd(), safe_name.replace(" ", "_") + ".png")

        # Permitir guardar tanto en PNG como en JPG; el formato real lo
        # determina la extensión del archivo.
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar carta de cripta",
            default_path,
            "Imagen PNG/JPEG (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return
        self.cripta_card_widget.export_png(filename)

    def guardar_carta_cripta_online(self):
        """Guarda la carta de cripta en formato optimizado para juego online (358x500px)."""
        from logicas.recorte.constantes import VTES_CARD_WIDTH_ONLINE, VTES_CARD_HEIGHT_ONLINE
        
        if hasattr(self, 'cripta_name_edit'):
            nombre_base = self.cripta_name_edit.text().strip()
        else:
            nombre_base = ""
        if not nombre_base:
            nombre_base = "carta_cripta_online"
        safe_name = "".join(c for c in nombre_base if c.isalnum() or c in (" ", "-", "_")).strip()
        if not safe_name:
            safe_name = "carta_cripta_online"
        default_path = os.path.join(os.getcwd(), safe_name.replace(" ", "_") + "_online.png")

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar carta de cripta para online",
            default_path,
            "Imagen PNG/JPEG (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return
        self.cripta_card_widget.export_png(
            filename,
            width=VTES_CARD_WIDTH_ONLINE,
            height=VTES_CARD_HEIGHT_ONLINE
        )

    def set_title_from_edit(self, text):
        self.cripta_card_widget.set_title(
            text, 
            font=self.cripta_title_font, 
            color=self.cripta_title_color,
            alignment=self.cripta_card_widget.title_alignment
        )
    
    def set_clan_from_combo(self, nombre_clan):
        """Actualiza el símbolo del clan cuando se selecciona uno"""
        self.cripta_card_widget.set_clan(
            nombre_clan, 
            size=self.cripta_card_widget.clan_size,
            alignment=self.cripta_card_widget.clan_alignment
        )

    def set_senda_from_combo(self, nombre_senda):
        """Actualiza el símbolo de senda cuando se selecciona uno"""
        # Solo actualizamos la senda en el widget de carta
        if nombre_senda and nombre_senda != "Ninguno":
            svg_path = obtener_archivo_senda(nombre_senda)
            self.cripta_card_widget.set_senda(
                nombre_senda,
                size=self.cripta_card_widget.senda_size,
                alignment=self.cripta_card_widget.senda_alignment,
                svg_path=svg_path
            )
        else:
            # limpiar
            self.cripta_card_widget.set_senda(None, svg_path=None)
        self.cripta_card_widget.update()
    # No es necesario sobreescribir resizeEvent, el widget personalizado se adapta solo

    def update_title_position(self):
        pass  # Ya no es necesario

    def set_pixmap(self, pixmap):
        self.cripta_card_widget.set_pixmap(pixmap)

    def set_title(self, text=None, font=None, size=None, color=None):
        f = self.cripta_title_font
        if font is not None:
            f.setFamily(font)
        if size is not None:
            f.setPointSize(size)
        c = self.cripta_title_color
        if color is not None:
            c = color
        if text is not None:
            self.cripta_card_widget.set_title(text, font=f, color=c)

    def set_ability_from_edit(self):
        """Actualiza el texto de habilidades desde el editor de texto."""
        if hasattr(self, 'cripta_ability_edit'):
            text = self.cripta_ability_edit.toPlainText()
        else:
            text = ""
        self.cripta_card_widget.set_ability_text(
            text,
            font=getattr(self, 'cripta_ability_font', self.cripta_card_widget.ability_font),
            color=getattr(self, 'cripta_ability_color', self.cripta_card_widget.ability_color),
            bg_opacity=getattr(self, 'cripta_ability_bg_opacity', self.cripta_card_widget.ability_bg_opacity),
        )

    def set_illustrator_from_edit(self):
        """Actualiza el nombre del ilustrador mostrado en la parte inferior de la carta de cripta."""
        if hasattr(self, 'cripta_illustrator_edit'):
            name = self.cripta_illustrator_edit.text()
        else:
            name = ""
        # Fuente fija para el ilustrador
        illustrator_font = QFont("Arial", 8)  # Cambia "Arial" y 8 por lo que prefieras
        self.cripta_card_widget.set_illustrator(
            name,
            font=illustrator_font,
            color=getattr(self, 'cripta_ability_color', self.cripta_card_widget.ability_color),
        )

    def set_disciplines_from_list(self):
        """Lee la selección del listado y actualiza las disciplinas en la carta de cripta."""
        items = self.cripta_disciplines_list.selectedItems() if hasattr(self, 'cripta_disciplines_list') else []
        disciplinas = []
        for it in items:
            nombre = it.text()
            svg_path = obtener_archivo_disciplina_texto(nombre)
            if svg_path:
                disciplinas.append({"nombre": nombre, "svg_path": svg_path})

        self.cripta_card_widget.set_disciplines(disciplinas, size=self.cripta_card_widget.discipline_size)
        self.cripta_card_widget.update()

    def set_cripta_group_from_combo(self, valor):
        """Actualiza el número de grupo de cripta (1-9) dibujado sobre el cuadro de texto."""
        if not valor or valor == "Ninguno":
            self.cripta_card_widget.set_crypt_group(
                None,
                font=getattr(self, 'cripta_group_font', self.cripta_card_widget.crypt_group_font),
                color=getattr(self, 'cripta_group_color', self.cripta_card_widget.crypt_group_color),
            )
        else:
            self.cripta_card_widget.set_crypt_group(
                valor,
                font=getattr(self, 'cripta_group_font', self.cripta_card_widget.crypt_group_font),
                color=getattr(self, 'cripta_group_color', self.cripta_card_widget.crypt_group_color),
            )
        self.cripta_card_widget.update()

    def set_cripta_cost_from_combo(self, valor):
        """Actualiza el icono de coste de cripta (capacidad) en la esquina inferior derecha."""
        if not valor or valor == "Ninguno":
            self.cripta_card_widget.set_cost(None, svg_path=None)
            self.cripta_card_widget.update()
            return

        svg_path = obtener_archivo_coste_cripta(valor)
        if svg_path:
            self.cripta_card_widget.set_cost(
                "capacity",
                svg_path=svg_path,
                size=self.cripta_card_widget.cost_size,
                value=valor,
                alignment="derecha",
            )
        else:
            self.cripta_card_widget.set_cost(None, svg_path=None)

        self.cripta_card_widget.update()
