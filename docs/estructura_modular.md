# Documentación de la estructura y modularización de VTESProxi

## Estructura de carpetas y módulos (enero 2026)

```
proyectos/vtesproxi/
├── main.py
├── carta_app.py
├── image_crop_view.py
├── configuracion.py
├── configuracion_widget.py
├── config_data.json
├── docs/
│   └── estructura_modular.md  # ← Este archivo
├── logicas/
│   ├── recorte/
│   │   └── recorte.py
│   └── seleccion/
│       ├── selector_archivo.py
│       └── importador_imagen.py
├── ventana/
│   ├── cripta_widget.py
│   └── libreria_widget.py
├── resources/
│   ├── listas/
│   │   ├── clans_list.py
│   │   └── disciplines_list.py
│   └── ...
└── fonts/
```

## Modularización y responsabilidades

### 1. `main.py`
- Punto de entrada de la aplicación.
- Inicializa QApplication y aplica el tema.
- Lanza la ventana principal (`CartaApp`).

### 2. `carta_app.py`
- Ventana principal (QMainWindow).
- Gestiona las pestañas (Cripta, Librería, Configuración).
- Delegación de la importación de imágenes a un módulo externo.
- Solo contiene lógica de orquestación y UI principal.

### 3. `ventana/cripta_widget.py` y `ventana/libreria_widget.py`
- Widgets independientes para cada pestaña.
- Cada uno gestiona su propio QLabel y botones.
- Reciben el callback de importación de imagen.

### 4. `configuracion.py` y `configuracion_widget.py`
- Persistencia y edición de la configuración global (fuentes, colores, etc).
- Configuración editable desde la interfaz.

### 5. `logicas/recorte/recorte.py`
- Función `recortar_pixmap`: lógica pura de recorte de QPixmap según coordenadas y aspect ratio.
- No depende de la UI.

### 6. `logicas/seleccion/selector_archivo.py`
- Función `seleccionar_imagen_tkinter`: selector de archivos multiplataforma usando tkinter.
- Soluciona problemas de QFileDialog en VS Code/Linux.

### 7. `logicas/seleccion/importador_imagen.py`
- Orquesta el flujo completo de importación:
  - Selección de archivo (tkinter)
  - Recorte de imagen (ImageCropView)
  - Callback con el QPixmap recortado
- No depende de la UI principal, solo recibe parent y QLabel destino.

### 8. `image_crop_view.py`
- Widget de recorte de imagen (QWidget + QGraphicsView).
- Permite seleccionar área y confirma el recorte.
- Emite señal con el QPixmap recortado.

### 9. `resources/` y `fonts/`
- Recursos gráficos, listas de clanes/disciplinas y fuentes.

## Flujo de importación de imagen (modularizado)
1. El usuario pulsa "Importar Imagen" en una pestaña.
2. El widget llama a `CartaApp.importar_imagen`.
3. `CartaApp` delega a `importador_imagen.importar_imagen(self, label, callback)`.
4. Se abre el selector de archivos (tkinter).
5. Si se selecciona una imagen, se abre el recorte (ImageCropView).
6. Al confirmar el recorte, el callback recibe el QPixmap recortado y lo muestra en el QLabel destino.

## Notas de portabilidad y robustez
- El selector de archivos usa tkinter para máxima compatibilidad en VS Code y Linux.
- El recorte y la lógica de imagen están desacoplados de la UI principal.
- La estructura permite añadir más lógicas (exportar, borrar, etc.) en logicas/.

---

**Actualizado a 30 de enero de 2026.**
