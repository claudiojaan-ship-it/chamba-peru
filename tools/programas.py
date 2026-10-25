# Genera site/programas.json: catálogo de programas gratuitos (con enlaces verificados)
# y noticias recientes de becas, bonos, cursos y empleo desde gob.pe (RSS oficial) y El Paisano.
# Uso: py -P tools/programas.py <carpeta chamba-peru>
import json,sys,re,html,subprocess,datetime,email.utils,urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
ROOT=sys.argv[1]; HOY=datetime.date.today()
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"

def curl(url,body=True,timeout=25):
    args=["curl","-sL","-g","--connect-timeout","10","--max-time",str(timeout),"-k","-A",UA]
    if not body: args+=["-o","/dev/null","-w","%{http_code}","-r","0-2000"]
    r=subprocess.run(args+[url],capture_output=True)
    return r.stdout.decode('utf-8','ignore')

# 1. Catálogo con verificación de enlaces
cat=json.load(open(ROOT+'/tools/programas.json',encoding='utf-8'))['items']
def check(it):
    code=curl(urllib.parse.quote(it['url'],safe=":/?=&%#~+,;@!$'()*[]"),body=False)
    it['ok']=code not in ('404','410','400'); it['http']=code
    return it
with ThreadPoolExecutor(16) as ex: cat=list(ex.map(check,cat))

# 2. Noticias oficiales (gob.pe) y de El Paisano
INCL=re.compile(r'\bbecas?\b|\bbonos?\b|subsidio|\bcursos?\b|capacitaci|gratuit|convocatoria|postula|inscrip|vacantes|pr[aá]cticas|techo propio|mivivienda|vivienda propia|empleo|pensi[oó]n 65|juntos|contigo|emprende|fondos? no reembolsable|certifica',re.I)
EXCL=re.compile(r'prisi[oó]n|fiscal[ií]a|investigad|delito|contralor|sentencia|detenid|homicid|corrupci|accidente|fallec|lluvias|huaico|sismo|incendio|aniversario|conmemora|\bgana\b|reconocimiento|primer lugar|polic[ií]as',re.I)
FUENTES=["pronabec","vivienda","mtpe","midis","juntos","pension65","contigo","servir","minedu","produce","apci","sis","fondomivivienda"]
TERMS=["beca","bono","curso gratuito","capacitación gratuita","convocatoria prácticas"]
def rss_items(url,src):
    out=[]
    try: root=ET.fromstring(curl(url))
    except ET.ParseError: return out
    for i in root.iter('item'):
        t=html.unescape((i.findtext('title') or '').strip()); l=(i.findtext('link') or '').strip(); d=i.findtext('pubDate') or ''
        try: f=email.utils.parsedate_to_datetime(d).date()
        except (TypeError,ValueError): continue
        if t and l and '/noticias/' in l: out.append(dict(t=t,u=l,d=f.isoformat(),src=src))
    return out
urls=[(f"https://www.gob.pe/busquedas.rss?institucion[]={s}&contenido[]=noticias&sort_by=recent","gob.pe") for s in FUENTES]
urls+=[(f"https://www.gob.pe/busquedas.rss?contenido[]=noticias&term={urllib.parse.quote(t)}&sort_by=recent","gob.pe") for t in TERMS]
with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda x: rss_items(*x),urls))
news=[n for r in res for n in r]
for c in (6,10):   # El Paisano: educación y Perú
    try:
        for p in json.loads(curl(f"https://elpaisano.pe/wp-json/wp/v2/posts?categories={c}&per_page=20&_fields=date,title,link")):
            news.append(dict(t=html.unescape(re.sub('<[^>]+>','',p['title']['rendered'])).strip(),u=p['link'],d=p["date"][:10],src="Prensa"))
    except (ValueError,KeyError,TypeError): pass
def tema(t):
    t=t.lower()
    if re.search(r'beca',t): return 'becas'
    if re.search(r'vivienda|techo propio|mivivienda|casa propia|alquiler',t): return 'vivienda'
    if re.search(r'curso|capacita|taller|aprend|formaci|certifica|ingl[eé]s',t): return 'cursos'
    if re.search(r'pr[aá]cticas|empleo|trabaj|vacantes|convocatoria|sueldo',t): return 'empleo'
    if re.search(r'emprend|mype|negocio|startup',t): return 'emprende'
    return 'programas'
lim=(HOY-datetime.timedelta(days=30)).isoformat(); seen=set(); out=[]
for n in sorted(news,key=lambda n:n['d'],reverse=True):
    k=re.sub(r'\W+','',n['t'].lower())[:60]
    if n['d']<lim or k in seen or not INCL.search(n['t']) or EXCL.search(n['t']): continue
    seen.add(k); n['cat']=tema(n['t']); out.append(n)
out=out[:48]

json.dump({"gen":HOY.isoformat(),"items":cat,"news":out},open(ROOT+'/site/programas.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
rotos=[i['id'] for i in cat if not i['ok']]
print(f"programas={len(cat)} enlaces_rotos={len(rotos)} {rotos} noticias={len(out)}")
