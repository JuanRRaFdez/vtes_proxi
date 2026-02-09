"""Genera listas y mapeos de iconos de coste a partir de las carpetas resources/blood y resources/pool."""
import os
import sys

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

BASE_BLOOD = get_resource_path('resources/blood')
BASE_POOL = get_resource_path('resources/pool')

BLOOD = ["Ninguno"]
POOL = ["Ninguno"]

BLOOD_SVG_MAP = {}
POOL_SVG_MAP = {}

# Helper para añadir archivos de una carpeta al listado y mapeo
def _scan_dir(base_dir, target_list, target_map):
    """Escanea base_dir y añade a la lista/mapa solo archivos de iconos válidos.

    Antes solo se aceptaban .svg; ahora soportamos también .png/.gif para
    adaptarnos a los nuevos nombres de archivos de coste (bloodcostX.png, etc.).
    """
    try:
        for fname in sorted(os.listdir(base_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in (".svg", ".png", ".gif"):
                continue
            stem = os.path.splitext(fname)[0]
            readable = stem.replace('-', ' ').replace('_', ' ').title()
            target_list.append(readable)
            target_map[readable] = fname
    except FileNotFoundError:
        pass

_scan_dir(BASE_BLOOD, BLOOD, BLOOD_SVG_MAP)
_scan_dir(BASE_POOL, POOL, POOL_SVG_MAP)
