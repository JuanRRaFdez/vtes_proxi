from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRectF

def recortar_pixmap(pixmap, crop_rect, pixmap_rect_scene, crop_top_left, crop_bottom_right, aspect_ratio=None):
    """
    Recorta un QPixmap según las coordenadas de recorte y el aspect ratio deseado.
    Garantiza que el resultado final tenga exactamente las proporciones correctas de cartas VTES.
    
    - pixmap: QPixmap original
    - crop_rect: QRect de selección en la vista
    - pixmap_rect_scene: QRectF del pixmap en la escena
    - crop_top_left, crop_bottom_right: QPointF en la escena
    - aspect_ratio: float (opcional, si es None se mantiene la proporción del recorte)
    """
    pixmap_width = pixmap.width()
    pixmap_height = pixmap.height()
    
    # Convertir coordenadas de la escena a coordenadas del pixmap original
    x1 = (crop_top_left.x() - pixmap_rect_scene.x()) / pixmap_rect_scene.width() * pixmap_width
    y1 = (crop_top_left.y() - pixmap_rect_scene.y()) / pixmap_rect_scene.height() * pixmap_height
    x2 = (crop_bottom_right.x() - pixmap_rect_scene.x()) / pixmap_rect_scene.width() * pixmap_width
    y2 = (crop_bottom_right.y() - pixmap_rect_scene.y()) / pixmap_rect_scene.height() * pixmap_height
    
    # Calcular el rectángulo de recorte en coordenadas del pixmap
    x = int(max(0, min(x1, x2, pixmap_width-1)))
    y = int(max(0, min(y1, y2, pixmap_height-1)))
    w = int(max(1, min(abs(x2 - x1), pixmap_width - x)))
    h = int(max(1, min(abs(y2 - y1), pixmap_height - y)))
    
    # Recortar la imagen
    cropped = pixmap.copy(x, y, w, h)
    
    # Aplicar el aspect ratio exacto si se especifica
    if aspect_ratio is not None:
        crop_w, crop_h = cropped.width(), cropped.height()
        current_ratio = crop_w / crop_h if crop_h != 0 else 1
        
        # Si la proporción actual difiere del objetivo, ajustar
        if abs(current_ratio - aspect_ratio) > 0.001:  # Tolerancia más estricta
            if current_ratio > aspect_ratio:
                # La imagen es más ancha de lo necesario, recortar los lados
                new_w = int(crop_h * aspect_ratio)
                if new_w > 0 and new_w <= crop_w:
                    offset = (crop_w - new_w) // 2
                    cropped = cropped.copy(offset, 0, new_w, crop_h)
            else:
                # La imagen es más alta de lo necesario, recortar arriba/abajo
                new_h = int(crop_w / aspect_ratio)
                if new_h > 0 and new_h <= crop_h:
                    offset = (crop_h - new_h) // 2
                    cropped = cropped.copy(0, offset, crop_w, new_h)
    
    return cropped
