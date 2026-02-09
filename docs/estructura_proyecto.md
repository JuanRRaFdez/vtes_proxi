# Estructura del Proyecto VTESProxi

Este documento describe la organización de carpetas y archivos del proyecto para facilitar su mantenimiento y escalabilidad.

## Raíz del proyecto
- **main.py**: Punto de entrada de la aplicación.
- **carta_app.py**: Lógica principal de la interfaz y gestión de pestañas.
- **configuracion.py**: Módulo central de configuración y persistencia.
- **configuracion_widget.py**: Widget para editar la configuración desde la interfaz.

## Carpetas principales

### /resources
Contiene todos los recursos gráficos y listas necesarias para la app, organizados por tipo:
- **blood/**: Iconos de sangre.
- **clans/**: Iconos y datos de clanes.
- **costes/**: Iconos de costes.
- **disciplines/**: Iconos de disciplinas.
- **libreria/**: Iconos de tipos de carta de la librería.
- **listas/**: Listas de clanes y disciplinas.
- **pool/**: Iconos de pool.
- **sendas/**: Iconos de sendas.

### /fonts
Fuentes tipográficas utilizadas en la app.

### /logicas
Carpeta para la lógica de cada módulo de la app. Subcarpetas preparadas para:
- **borrado/**: Lógica de borrado de cartas o recursos.
- **configuracion/**: Lógica avanzada de configuración.
- **cripta/**: Lógica específica de la pestaña Cripta.
- **exportador/**: Funcionalidad de exportación de cartas o datos.
- **libreria/**: Lógica específica de la pestaña Librería.
- **recorte/**: Lógica para el recorte de imágenes.

### /ventana
Espacio reservado para widgets o lógica de las ventanas principales.

### /config
Archivos de configuración persistente (por ejemplo, JSON).

### /docs
Documentación del proyecto.

## Notas
- Cada carpeta de lógica debe contener un __init__.py si se va a importar como módulo.
- Los recursos gráficos y fuentes deben estar bien nombrados y organizados para facilitar su uso.
- La configuración es persistente y editable desde la interfaz.

---

Esta estructura está pensada para facilitar el desarrollo colaborativo y la escalabilidad del proyecto.
