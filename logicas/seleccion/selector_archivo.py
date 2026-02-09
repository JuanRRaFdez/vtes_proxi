import tkinter as tk
from tkinter import filedialog

def seleccionar_imagen_tkinter():
    """
    Abre un diálogo de selección de archivos usando tkinter y devuelve la ruta seleccionada o None.
    """
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    root.attributes('-topmost', True)  # Asegura que el diálogo esté al frente
    file_path = filedialog.askopenfilename(
        filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.bmp')],
        title='Seleccionar imagen'
    )
    root.destroy()
    return file_path if file_path else None
