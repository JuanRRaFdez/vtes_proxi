#!/usr/bin/env bash
set -euo pipefail

DIR="$(dirname "$(realpath "$0")")"

# Importante cuando se lanza desde un .desktop: el cwd suele ser $HOME,
# y la app puede depender de rutas relativas (config/, resources/, fonts/, etc.).
cd "$DIR"

# Log para diagnosticar cierres al lanzar desde el escritorio.
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/vtesproxi"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/vtesproxi.log"

if [[ -x "$DIR/dist/main" ]]; then
	"$DIR/dist/main" "$@" >>"$LOG_FILE" 2>&1
else
	# Fallback para desarrollo: ejecuta desde el venv sin necesidad de 'activate'.
	PYTHON="$DIR/.venv/bin/python"
	"$PYTHON" "$DIR/main.py" "$@" >>"$LOG_FILE" 2>&1
fi
