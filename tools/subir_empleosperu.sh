#!/usr/bin/env bash
# Corre en la PC (en el Perú) porque Empleos Perú bloquea conexiones desde fuera del país.
# Descarga los avisos y los sube a GitHub; la actualización en la nube (6:00 y 18:00) los usa.
# Lo ejecuta la tarea de Windows "Chamba Peru - Empleos Peru" a las 5:30 y 17:30.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
export PYTHONIOENCODING=utf-8 GIT_TERMINAL_PROMPT=0
{
  echo "== $(date '+%Y-%m-%d %H:%M')"
  git pull -q --rebase --autostash || echo "git pull falló"
  py -P tools/empleosperu.py . || { echo "descarga falló"; exit 0; }
  py -P tools/logos.py . --ep || echo "logos fallaron"
  git add work/dl/empleosperu.json work/eplogos
  if git diff --cached --quiet; then echo "sin cambios"; else
    git commit -qm "Empleos Perú: avisos del $(date +%Y-%m-%d)" && git push -q && echo "subido"
  fi
} >> work/subir_empleosperu.log 2>&1
