#!/usr/bin/env bash
# Regenera datos, renders marcados y la app, y corre las pruebas.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python src/precalc.py all
python scripts/marcar_renders.py
python build.py
python -m pytest
