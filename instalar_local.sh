#!/usr/bin/env bash
set -euo pipefail

# Instala VTESProxi en el HOME del usuario (sin rutas del repo):
# - ~/.local/share/vtesproxi/ (binario + datos)
# - ~/.local/bin/vtesproxi (wrapper)
# - ~/.local/share/applications/vtesproxi.desktop (lanzador)
#
# Uso:
#   ./instalar_local.sh            # construye con PyInstaller y luego instala
#   ./instalar_local.sh --no-build # instala usando dist/main ya existente

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NO_BUILD=0

if [[ "${1:-}" == "--no-build" ]]; then
  NO_BUILD=1
fi

if [[ $NO_BUILD -eq 0 ]]; then
  if [[ -x "$DIR/.venv/bin/python" ]]; then
    PY="$DIR/.venv/bin/python"
  else
    PY="python3"
  fi

  "$PY" -m PyInstaller --clean -y "$DIR/main.spec"
fi

if [[ ! -x "$DIR/dist/main" ]]; then
  echo "ERROR: No existe $DIR/dist/main. Ejecuta sin --no-build o compila primero." >&2
  exit 1
fi

SHARE_DIR="$HOME/.local/share/vtesproxi"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

mkdir -p "$SHARE_DIR" "$BIN_DIR" "$APP_DIR"

# Copiar binario y datos necesarios
rm -rf "$SHARE_DIR"/*
install -m 0755 "$DIR/dist/main" "$SHARE_DIR/main"
install -m 0755 "$DIR/lanzar.sh" "$SHARE_DIR/lanzar.sh"

# Datos (si existen)
[[ -d "$DIR/config" ]] && cp -a "$DIR/config" "$SHARE_DIR/"
[[ -d "$DIR/resources" ]] && cp -a "$DIR/resources" "$SHARE_DIR/"
[[ -d "$DIR/fonts" ]] && cp -a "$DIR/fonts" "$SHARE_DIR/"

# Wrapper en ~/.local/bin (permite Exec=vtesproxi en el .desktop)
cat > "$BIN_DIR/vtesproxi" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SHARE_DIR="$HOME/.local/share/vtesproxi"
exec "$SHARE_DIR/lanzar.sh" "$@"
EOF
chmod +x "$BIN_DIR/vtesproxi"

# Desktop entry
ICON_PATH="$SHARE_DIR/resources/iconos/icono.png"
cat > "$APP_DIR/vtesproxi.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VTES Proxi
Comment=Lanzador de la aplicación VTES Proxi
Exec=vtesproxi
Path=$SHARE_DIR
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Application;
EOF
chmod +x "$APP_DIR/vtesproxi.desktop"

echo "Instalado en: $SHARE_DIR"
echo "Lanzador: $APP_DIR/vtesproxi.desktop"
echo "Comando: vtesproxi (en $BIN_DIR)"
echo
echo "Nota: si tu entorno no ve ~/.local/bin en PATH para lanzadores, cambia Exec a:"
echo "  Exec=$BIN_DIR/vtesproxi"
