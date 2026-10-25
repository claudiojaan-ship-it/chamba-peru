# Genera site/programas.json con tres partes:
#  1. el catálogo de programas gratuitos (tools/programas.json) con sus enlaces verificados,
#  2. noticias recientes de becas, bonos, cursos y empleo (gob.pe por RSS oficial, prensa y Rumbo Minero),
#  3. programas nuevos detectados automáticamente en esas noticias, que se borran solos al vencer.
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

# 2. Noticias
INCL=re.compile(r'\bbecas?\b|\bbonos?\b|subsidio|\bcursos?\b|capacitaci|gratuit|convocatoria|postula|inscrip|vacantes|pr[aá]cticas|techo propio|mivivienda|vivienda propia|empleo|pensi[oó]n 65|juntos|contigo|emprende|fondos? no reembolsable|certifica|talento|egresados',re.I)
EXCL=re.compile(r'prisi[oó]n|fiscal[ií]a|investigad|delito|contralor|sentencia|detenid|homicid|corrupci|accidente|fallec|lluvias|huaico|sismo|incendio|aniversario|conmemora|\bgana\b|reconocimiento|primer lugar|polic[ií]as|alcanza \d|r[eé]cord|reputaci|acuerdos? laboral|sindicat|creci[oó] \d',re.I)
FUENTES=["pronabec","vivienda","mtpe","midis","juntos","pension65","contigo","servir","minedu","produce","apci","sis","fondomivivienda","minem","inia","inacal"]
TERMS=["beca","bono","curso gratuito","capacitación gratuita","convocatoria prácticas","programa de prácticas"]
def txt(h): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',html.unescape(h or '')))).strip()
def rss_items(url,src):
    out=[]
    try: root=ET.fromstring(curl(url))
    except ET.ParseError: return out
    for i in root.iter('item'):
        t=html.unescape((i.findtext('title') or '').strip()); l=(i.findtext('link') or '').strip(); d=i.findtext('pubDate') or ''
        try: f=email.utils.parsedate_to_datetime(d).date()
        except (TypeError,ValueError): continue
        raw=html.unescape(i.findtext('description') or '')
        if t and l and '/noticias/' in l: out.append(dict(t=t,u=l,d=f.isoformat(),src=src,x=txt(raw)[:5000],links=re.findall(r'href="(https?://[^"]+)"',raw)))
    return out
def wp(url,src,mine=False):
    out=[]; body=curl(url)
    if not body.lstrip().startswith('['):   # a veces responde con una verificacion anti-robots: un reintento
        import time; time.sleep(8); body=subprocess.run(['curl','-sL','--max-time','30','-A','Mozilla/5.0 Chrome/130',url],capture_output=True).stdout.decode('utf-8','ignore')
    try:
        for p in json.loads(body):
            raw=p.get('excerpt',{}).get('rendered','')+' '+p.get('content',{}).get('rendered','')[:6000]
            out.append(dict(t=txt(p['title']['rendered']),u=p['link'],d=p['date'][:10],src=src,x=txt(raw)[:5000],links=re.findall(r'href="(https?://[^"]+)"',raw),mine=mine))
    except (ValueError,KeyError,TypeError): pass
    return out
urls=[(f"https://www.gob.pe/busquedas.rss?institucion[]={s}&contenido[]=noticias&sort_by=recent","gob.pe") for s in FUENTES]
urls+=[(f"https://www.gob.pe/busquedas.rss?contenido[]=noticias&term={urllib.parse.quote(t)}&sort_by=recent","gob.pe") for t in TERMS]
with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda x: rss_items(*x),urls))
news=[n for r in res for n in r]
for c in (6,10): news+=wp(f"https://elpaisano.pe/wp-json/wp/v2/posts?categories={c}&per_page=20&_fields=date,title,link,excerpt","Prensa")
news+=wp("https://www.rumbominero.com/wp-json/wp/v2/posts?categories=15136&per_page=25&_fields=date,title,link,excerpt,content","Rumbo Minero",mine=True)
def tema(t):
    t=t.lower()
    if re.search(r'beca',t): return 'becas'
    if re.search(r'vivienda|techo propio|mivivienda|casa propia|alquiler',t): return 'vivienda'
    if re.search(r'pr[aá]cticas|practicantes|early talent|talentos?\b|egresados',t): return 'practicas'
    if re.search(r'curso|capacita|taller|aprend|formaci|certifica|ingl[eé]s|diplomado',t): return 'cursos'
    if re.search(r'empleo|trabaj|vacantes|convocatoria|sueldo',t): return 'empleo'
    if re.search(r'emprend|mype|negocio|startup',t): return 'emprende'
    return 'programas'
seenk=set(); out=[]
for n in sorted(news,key=lambda n:n['d'],reverse=True):
    k=re.sub(r'\W+','',n['t'].lower())[:60]
    lim=(HOY-datetime.timedelta(days=60 if n.get('mine') else 30)).isoformat()
    if n['d']<lim or k in seenk or not INCL.search(n['t']) or EXCL.search(n['t']): continue
    seenk.add(k); n['cat']='mineria' if n.get('mine') else tema(n['t']); out.append(n)

# 3. Programas nuevos detectados en las noticias
MESES={m:i+1 for i,m in enumerate(['enero','febrero','marzo','abril','mayo','junio','julio','agosto','setiembre','octubre','noviembre','diciembre'])}; MESES['septiembre']=9
OPP=re.compile(r'\b(abre|abri[oó]|lanza|ofrece|convoca|inscripciones|inscr[ií]bete|postula|postular|convocatoria|vacantes|nueva edici[oó]n|ampl[ií]a plazo)\b',re.I)
KIND=re.compile(r'beca|curso|capacitaci|pr[aá]cticas|programa|taller|diplomado|vacantes|talento|egresados|concurso',re.I)
KEYW=re.compile(r'inscrip|postula|plazo|hasta|cierre|vence|registro|convocatoria|fecha l[ií]mite|disponible',re.I)
def fecha_cierre(texto,pub):
    out=[]
    for m in re.finditer(r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre)(?:\s+(?:de|del)\s+(\d{4}))?',texto,re.I):
        if not KEYW.search(texto[max(0,m.start()-110):m.start()]): continue
        y=int(m.group(3)) if m.group(3) else pub.year
        try: f=datetime.date(y,MESES[m.group(2).lower()],int(m.group(1)))
        except ValueError: continue
        if not m.group(3) and f<pub-datetime.timedelta(days=60): f=f.replace(year=y+1)
        if pub<=f<=pub+datetime.timedelta(days=150): out.append(f)
    return max(out) if out else None
INST={'minem':'Ministerio de Energía y Minas','inia':'INIA','inacal':'INACAL','pronabec':'Pronabec','mtpe':'Ministerio de Trabajo','produce':'Ministerio de la Producción','servir':'SERVIR','minedu':'Ministerio de Educación','vivienda':'Ministerio de Vivienda','midis':'MIDIS','apci':'APCI','sis':'SIS','mincetur':'Mincetur','pronacej':'PRONACEJ'}
IMG={'becas':'x-becas','cursos':'x-laptop','practicas':'x-library','empleo':'x-vivienda','emprende':'x-programas','vivienda':'x-hero','programas':'x-programas'}
SOCIAL=('gob.pe/institucion','wa.me','facebook','twitter','x.com','instagram','tiktok','youtube','linkedin.com/share','rumbominero','elpaisano')
titulos=[re.split(r'[:·(]',i['title'])[0].strip().lower() for i in cat]
auto=[]
for n in out:
    t=n['t']; tl=t.lower(); x=n.get('x','')
    if not (OPP.search(t) and KIND.search(t)) or any(len(k)>5 and k in tl for k in titulos): continue
    pub=datetime.date.fromisoformat(n['d']); cierra=fecha_cierre(t+'. '+x,pub)
    vence=cierra or pub+datetime.timedelta(days=21)
    if vence<HOY: continue
    slug=(re.search(r'/institucion/([^/]+)/',n['u']) or [None,''])[1]
    ext=[l for l in n.get('links',[]) if not any(s in l for s in SOCIAL)]
    c=('practicas' if re.search(r'pr[aá]ctic|talento|egresad|beca',tl) else 'empleo') if n.get('mine') else tema(t)
    para=[p for p,rx in [('est',r'estudiant|egresad|universit|escolar|bachiller'),('jov',r'j[oó]ven'),('trab',r'profesional|trabajador|t[eé]cnic'),('emp',r'emprend|mype')] if re.search(rx,tl+' '+x[:400].lower())]
    auto.append(dict(id='auto-'+re.sub(r'\W+','',tl)[:24],cat=c,ambito='intl' if re.search(r'extranjer|internacional',tl) else 'pe',para=para or ['trab'],
        img=IMG.get(c,'x-programas'),title=t,inst=INST.get(slug,slug.upper()) if slug else n['src'],desc=(x[:280]+'…') if len(x)>280 else x,facts=[],
        estado='fechas' if cierra else 'nuevo',abre=n['d'],cierra=cierra.isoformat() if cierra else None,vence=vence.isoformat(),
        url=ext[0] if ext else n['u'],more=[["Leer el aviso completo",n['u']]] if ext else [],src=n['src']+' · detectado automáticamente',auto=True,pub=n['d'],ok=True))
    if len(auto)>=24: break
for n in out:
    for k in ('x','links','mine'): n.pop(k,None)
out=[n for n in out if n['cat']!='mineria'][:50]+[n for n in out if n['cat']=='mineria'][:15]

json.dump({"gen":HOY.isoformat(),"items":cat+auto,"news":out},open(ROOT+'/site/programas.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
rotos=[i['id'] for i in cat if not i['ok']]
print(f"programas={len(cat)} automaticos={len(auto)} enlaces_rotos={len(rotos)} {rotos} noticias={len(out)}")
