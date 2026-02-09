"""Lista de sendas disponibles y mapeo a SVGs.

En lugar de mantener un mapeo estático, generamos la lista y el
mapeo directamente a partir de los archivos SVG presentes en
`resources/sendas`. De este modo las opciones en la UI siempre
coincidirán con los ficheros disponibles.
"""

import os
import sys

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

BASE_DIR = get_resource_path("resources/sendas")

# Lista de opciones para el combo (incluye "Ninguno" al inicio)
SENDAS = ["Ninguno"]

# Mapeo de nombre legible -> nombre de archivo SVG
SENDA_SVG_MAP = {}

try:
    for fname in sorted(os.listdir(BASE_DIR)):
        if not fname.lower().endswith('.svg'):
            continue
        # Crear un nombre legible a partir del nombre de archivo
        stem = os.path.splitext(fname)[0]
        # Reemplazar guiones/underscores por espacios y capitalizar cada palabra
        readable = stem.replace('-', ' ').replace('_', ' ').title()
        SENDAS.append(readable)
        SENDA_SVG_MAP[readable] = fname
except FileNotFoundError:
    # Si no existe la carpeta, mantenemos solo "Ninguno" y un mapeo vacío
    SENDAS = ["Ninguno"]
    SENDA_SVG_MAP = {}
