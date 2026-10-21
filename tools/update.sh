#!/usr/bin/env bash
# Actualización diaria de Chamba Perú: descarga, verifica enlaces, logos, datos y HTML.
# Uso: bash tools/update.sh   (desde cualquier carpeta)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; W="$ROOT/work"; T="$ROOT/tools"
export PYTHONIOENCODING=utf-8
PY="${PY:-py -P}"   # en GitHub Actions: PY="python3 -P"
mkdir -p "$W/dl" "$W/logos_raw" "$ROOT/site/logos"
echo "== 1/7 Descargando convocatorias de El Paisano"
curl -sfL --retry 4 --retry-delay 15 --retry-all-errors --connect-timeout 20 --max-time 300 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130" "https://elpaisano.pe/wp-content/uploads/json-jobs/jobs.json?v=$(date +%s)" -o "$W/dl/jobs.new.json"
$PY -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));assert isinstance(d,list) and len(d)>500,len(d);print(len(d),'registros')" "$W/dl/jobs.new.json"
mv "$W/dl/jobs.new.json" "$W/dl/jobs.json"
echo "== 2/7 Listando enlaces"; $PY "$T/urls.py" "$ROOT"
echo "== 3/7 Verificando enlaces"
timeout 1200 xargs -d '\n' -P 32 -n 1 bash "$T/chk.sh" < "$W/urls.txt" > "$W/status.tsv" 2>/dev/null || true
$PY "$T/rechk.py" "$W/status.tsv" "$W/re.tsv"
cut -f1 "$W/status.tsv" | sort | uniq -c | tr '\n' ' '; echo
echo "== 4/7 Logos de instituciones"; $PY "$T/logos.py" "$ROOT"
echo "== 5/7 Datos"; $PY "$T/build.py" "$ROOT"
echo "== 6/7 Programas gratuitos y noticias"; $PY "$T/programas.py" "$ROOT"
echo "== 7/7 HTML"; $PY "$T/assemble.py" "$ROOT"
echo "LISTO $(date '+%Y-%m-%d %H:%M')"
