# Módulo de configuración para la app de cartas VTES
# Aquí se definen las opciones de configuración globales

import json
import os
import sys

def get_resource_path(relative_path):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        base_path = meipass
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

DEFAULT_CONFIG_RELATIVE_PATH = os.path.join('config', 'textos', 'config_data.json')


def get_default_config_path() -> str:
    return get_resource_path(DEFAULT_CONFIG_RELATIVE_PATH)


def get_user_config_path() -> str:
    xdg_config_home = os.environ.get(
        'XDG_CONFIG_HOME',
        os.path.join(os.path.expanduser('~'), '.config'),
    )
    return os.path.join(xdg_config_home, 'vtesproxi', 'config_data.json')


def _deep_merge_dicts(defaults: dict, overrides: dict) -> dict:
    merged = dict(defaults)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config_data(fallback: dict | None = None) -> dict:
    """Carga config_data.json.

    Prioridad:
    1) Config de usuario (~/.config/vtesproxi/config_data.json)
    2) Config por defecto incluida en el bundle (config/textos/config_data.json)
    3) fallback
    """
    user_path = get_user_config_path()
    if os.path.exists(user_path):
        with open(user_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    default_path = get_default_config_path()
    if os.path.exists(default_path):
        with open(default_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    return dict(fallback or {})


def save_config_data(data: dict) -> str:
    """Guarda config_data.json en el path de usuario y devuelve la ruta."""
    user_path = get_user_config_path()
    os.makedirs(os.path.dirname(user_path), exist_ok=True)
    with open(user_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return user_path

class Configuracion:
    def __init__(self):
        # Tamaño de los iconos en la carta (por defecto 32x32)
        self.icon_size = 32
        # Fuente para los textos principales
        self.font_main = "Times New Roman"
        # Fuente para los títulos
        self.font_title = "Arial"
        # Fuente para los iconos
        self.font_icon = "Symbola"
        # Tamaño de fuente para textos principales
        self.font_size_main = 14
        # Tamaño de fuente para títulos
        self.font_size_title = 18
        # Tamaño de fuente para iconos
        self.font_size_icon = 12
        # Configuración visual del título de la carta
        self.title_text = "Título de la carta"
        self.title_font = self.font_title
        self.title_font_size = self.font_size_title
        self.title_color = "white"

        self.load()

    def save(self):
        data = {
            'icon_size': self.icon_size,
            'font_main': self.font_main,
            'font_title': self.font_title,
            'font_icon': self.font_icon,
            'font_size_main': self.font_size_main,
            'font_size_title': self.font_size_title,
            'font_size_icon': self.font_size_icon,
            'title_text': self.title_text,
            'title_font': self.title_font,
            'title_font_size': self.title_font_size,
            'title_color': self.title_color
        }
        save_config_data(data)

    def load(self):
        data = load_config_data({})
        self.icon_size = data.get('icon_size', self.icon_size)
        self.font_main = data.get('font_main', self.font_main)
        self.font_title = data.get('font_title', self.font_title)
        self.font_icon = data.get('font_icon', self.font_icon)
        self.font_size_main = data.get('font_size_main', self.font_size_main)
        self.font_size_title = data.get('font_size_title', self.font_size_title)
        self.font_size_icon = data.get('font_size_icon', self.font_size_icon)
        self.title_text = data.get('title_text', self.title_text)
        self.title_font = data.get('title_font', self.title_font)
        self.title_font_size = data.get('title_font_size', self.title_font_size)
        self.title_color = data.get('title_color', self.title_color)

    def set_icon_size(self, size):
        self.icon_size = size
        self.save()
    def set_font_main(self, font):
        self.font_main = font
        self.save()
    def set_font_title(self, font):
        self.font_title = font
        self.save()
    def set_font_icon(self, font):
        self.font_icon = font
        self.save()
    def set_font_size_main(self, size):
        self.font_size_main = size
        self.save()
    def set_font_size_title(self, size):
        self.font_size_title = size
        self.save()
    def set_font_size_icon(self, size):
        self.font_size_icon = size
        self.save()
    def set_title_text(self, text):
        self.title_text = text
        self.save()
    def set_title_font(self, font):
        self.title_font = font
        self.save()
    def set_title_font_size(self, size):
        self.title_font_size = size
        self.save()
    def set_title_color(self, color):
        self.title_color = color
        self.save()

# Instancia global de configuración
configuracion_global = Configuracion()
