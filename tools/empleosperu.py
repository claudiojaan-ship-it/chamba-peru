# Descarga las ofertas públicas de Empleos Perú (bolsa del Ministerio de Trabajo) a work/dl/empleosperu.json
# Uso: py -P tools/empleosperu.py <carpeta chamba-peru>
import json,sys,subprocess
ROOT=sys.argv[1]
API="https://mtpe-candidatos.empleosperu.gob.pe/api/jobs"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130"
def page(offset):
    r=subprocess.run(["curl","-sf","--retry","3","--retry-delay","5","--max-time","60","-A",UA,"-H","Accept: application/json",f"{API}?offset={offset}&limit=100"],capture_output=True)
    return json.loads(r.stdout.decode('utf-8'))
first=page(0); jobs=first['data']; total=first['totalCount']
off=len(jobs)
while off<total and off<5000:
    try: d=page(off)
    except (ValueError,json.JSONDecodeError): break
    if not d.get('data'): break
    jobs+=d['data']; off+=len(d['data'])
json.dump(jobs,open(ROOT+'/work/dl/empleosperu.json','w',encoding='utf-8'),ensure_ascii=False)
print(f"empleosperu={len(jobs)} de {total}")
