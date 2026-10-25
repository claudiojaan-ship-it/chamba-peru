# Descarga las ofertas públicas de Empleos Perú (bolsa del Ministerio de Trabajo) a work/dl/empleosperu.json
# Si la API no responde (por ejemplo desde servidores fuera del Perú), se conserva el último archivo descargado.
# Uso: py -P tools/empleosperu.py <carpeta chamba-peru>
import json,sys,subprocess,os
ROOT=sys.argv[1]; OUT=ROOT+'/work/dl/empleosperu.json'
API="https://mtpe-candidatos.empleosperu.gob.pe/api/jobs"
HDR=["-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
     "-H","Accept: application/json, text/plain, */*","-H","Accept-Language: es-PE,es;q=0.9",
     "-H","Referer: https://mtpe-candidatos.empleosperu.gob.pe/search-jobs"]
def page(offset):
    r=subprocess.run(["curl","-s","--retry","3","--retry-delay","5","--connect-timeout","20","--max-time","60","-w","\n%{http_code}",*HDR,f"{API}?offset={offset}&limit=100"],capture_output=True)
    body,_,code=r.stdout.decode('utf-8','ignore').rpartition('\n')
    try: return json.loads(body)
    except ValueError:
        print(f"Empleos Perú respondió {code or 'sin conexión'}: {body[:160]!r}"); return None
first=page(0)
if not first or 'data' not in first:
    print("Se mantiene el archivo anterior de Empleos Perú" if os.path.exists(OUT) else "Sin datos de Empleos Perú"); sys.exit(0)
jobs=first['data']; total=first['totalCount']; off=len(jobs)
while off<total and off<5000:
    d=page(off)
    if not d or not d.get('data'): break
    jobs+=d['data']; off+=len(d['data'])
json.dump(jobs,open(OUT,'w',encoding='utf-8'),ensure_ascii=False)
print(f"empleosperu={len(jobs)} de {total}")
