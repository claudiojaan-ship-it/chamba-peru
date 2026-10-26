# Vacantes publicadas en los portales oficiales de mineras (feeds RSS de SuccessFactors) -> work/dl/mineras.json
# Si un portal no responde, se conserva lo último guardado (la PC lo sube a GitHub).
# Uso: py -P tools/mineras.py <carpeta chamba-peru>
import json,sys,re,html,subprocess,os,email.utils
import xml.etree.ElementTree as ET
ROOT=sys.argv[1]; OUT=ROOT+'/work/dl/mineras.json'
PORTALES=[("Antamina","https://mastalento.antamina.com"),("Buenaventura","https://trabajaconnosotros.buenaventura.pe")]
CLAVES=["(Peru)","(PE)","(Lima)","(Ancash)","(Arequipa)","(Cajamarca)","(Huancavelica)","(Pasco)","(Junin)","(Moquegua)"]
def get(url):
    r=subprocess.run(["curl","-sL","--max-time","40","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130",url],capture_output=True)
    return r.stdout.decode('utf-8','ignore')
viejo={j['u']:j for j in (json.load(open(OUT,encoding='utf-8')) if os.path.exists(OUT) else [])}
nuevos={}; ok=set()
for emp,base in PORTALES:
    for k in CLAVES:
        x=get(f"{base}/services/rss/job/?locale=es_ES&keywords={k}")
        try: root=ET.fromstring(x)
        except ET.ParseError: continue
        ok.add(emp)
        for i in root.iter('item'):
            t=html.unescape(i.findtext('title') or '').strip(); u=(i.findtext('link') or '').strip()
            try: pub=email.utils.parsedate_to_datetime(i.findtext('pubDate') or '').date().isoformat()
            except (TypeError,ValueError): continue
            desc=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',i.findtext('description') or ''))).strip()
            if t and u: nuevos[u]=dict(emp=emp,t=t,u=u,pub=pub,x=desc[:600])
# Portal que no respondió hoy: se mantienen sus vacantes anteriores
res=list(nuevos.values())+[j for u,j in viejo.items() if j['emp'] not in ok and u not in nuevos]
json.dump(res,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print(f"mineras={len(res)} portales_ok={sorted(ok)}")
