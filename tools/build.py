# Genera site/data.json a partir de work/dl/jobs.json, el estado de enlaces y los logos.
# Uso: py -P tools/build.py <carpeta chamba-peru> [AAAA-MM-DD]
import json,sys,re,unicodedata,collections,os,datetime
ROOT=sys.argv[1]; W=ROOT+'/work'; SITE=ROOT+'/site'
TODAY=sys.argv[2] if len(sys.argv)>2 else datetime.date.today().isoformat()
d=json.load(open(W+'/dl/jobs.json',encoding='utf-8'))
st={}
for f in ('status.tsv','re.tsv'):
    if os.path.exists(W+'/'+f):
        for l in open(W+'/'+f,encoding='utf-8'):
            if '\t' in l: c,u=l.rstrip('\n').split('\t',1); st[u.strip()]=c
logos=json.load(open(W+'/logos.json',encoding='utf-8')) if os.path.exists(W+'/logos.json') else {}
seen=json.load(open(W+'/seen.json',encoding='utf-8')) if os.path.exists(W+'/seen.json') else {}
REG=["Amazonas","Áncash","Apurímac","Arequipa","Ayacucho","Cajamarca","Callao","Cusco","Huancavelica","Huánuco","Ica","Junín","La Libertad","Lambayeque","Lima","Loreto","Madre de Dios","Moquegua","Pasco","Piura","Puno","San Martín","Tacna","Tumbes","Ucayali"]
def a(s): return unicodedata.normalize('NFD',s or '').encode('ascii','ignore').decode().strip().lower()
RM={a(r):r for r in REG}; RM['san isidro, lima']='Lima'; RM['peru']='Lima'
PRIV=r'\b(s\.?a\.?c?|e\.?i\.?r\.?l|s\.?r\.?l(tda)?|sac|s\.a\.a|sociedad anonima|manpower|securitas|eulen)\b'
def tipo(j):
    t=a(j['Puesto']+' '+j['Institución']+' '+j['¿Quiénes pueden Postular?'])
    if re.search(r'practica|practicante|secigra',t): return 'practicas'
    if re.search(PRIV,a(j['Institución'])) and not re.search(r'aeropuertos del peru|agrobanco|sedapal|petroperu|electro',a(j['Institución'])): return 'privado'
    if re.search(r'computrabajo|bumeran|linkedin|indeed',j['Enlace 1']): return 'privado'
    return 'estado'
def sector(j):
    t=a(j['Institución']+' '+j['Puesto'])
    for k,p in [('salud',r'salud|hospital|minsa|essalud|insn|sis\b|clinica|medic|enfermer|obstetr|diresa|geresa|instituto de salud|instituto nacional de (enfermedades|ciencias|oftal|rehab|salud)'),
                ('educacion',r'ugel|\bdre\b|educacion|minedu|colegio|docente|pronabec|sunedu|escuela'),
                ('universidad',r'universidad|\bunsa\b|\bunsch\b|\buni\b|unaj'),
                ('justicia',r'judicial|fiscal|minjus|justicia|inpe|defensoria|fuero|jne|onpe|reniec|tribunal|procuradur|sunarp|sucamec|policia|mininter'),
                ('municipal',r'municipalidad|muni\b'),
                ('regional',r'gobierno regional|gerencia|direccion regional|direccion de|direccion agraria|region|\bgore'),
                ('agro',r'senasa|agrari|agricultura|midagri|inia|\bana\b|agua|agrobanco|forestal|serfor|riego')]:
        if re.search(p,t): return k
    if tipo(j)=='privado' or re.search(PRIV,a(j['Institución'])): return 'privado'
    return 'nacional'
def nivel(j):
    t=a(j['¿Quiénes pueden Postular?']+' '+j['Puesto'])
    if re.search(r'practica|practicante|estudiante',t): return 'e'
    if re.search(r'titulad|bachiller|licenciad|profesional|universitari|maestr|colegiad|abogad|ingenier|medic|enfermer|contador|economist',t): return 'u'
    if re.search(r'tecnic|egresad|instituto|tecnolog',t): return 't'
    if re.search(r'secundaria|sin experiencia|primaria|ninguna',t): return 's'
    return ''
def clean(s): return re.sub(r'\s+',' ',(s or '')).strip()
def det(s):
    s=(s or '').split('\n',1)[-1]
    s=re.sub(r'<h2>(.*?)</h2>',r'\n§\1 ',s); s=re.sub('<[^>]+>','',s)
    s=re.sub(r'\s+',' ',s)
    out=[]
    for p in [p.strip() for p in s.split('§') if p.strip()]:
        if p.startswith('Recomend'): continue
        m=re.match(r'([^:]{2,40}\??):\s*(.*)',p)
        h,b=(m.group(1).strip('¿? '),m.group(2)) if m else ('',p)
        out.append([h,b[:300]+('…' if len(b)>300 else '')])
    return out[:3]
inst={}; jobs=[]; seen_keys=set(); dropped=0; dl=0
for j in d:
    f=j.get('Fecha Máxima') or ''
    if f<TODAY or f>'2027-12-31': continue
    r=RM.get(a(j['Región']))
    if not r: continue
    key='|'.join((a(j['Puesto']),a(j['Institución']),r,f))
    if key in seen_keys: continue
    seen_keys.add(key)
    L=[]
    for k in range(1,7):
        raw=(j.get(f'Enlace {k}') or '').strip()
        u=raw.replace(' target=','').strip()
        if not u.startswith('http'): continue
        if st.get(raw,'?') in ('404','410','400'): dl+=1; continue
        L.append(u)
    if not L: dropped+=1; continue
    nm=clean(j['Institución']).upper()
    if nm not in inst: inst[nm]=len(inst)
    s=re.sub(r'[^\d.]','',j['Salario'] or '')
    try: s=float(s) if s else 0
    except ValueError: s=0
    if key not in seen: seen[key]=TODAY
    jobs.append(dict(p=clean(j['Puesto']),n=inst[nm],r=r,f=f,s=s if 300<=s<=40000 else 0,q=clean(j['¿Quiénes pueden Postular?'])[:260],l=L,d=det(j.get('Contenido_IA')),t=tipo(j),c=sector(j),e=nivel(j),v=seen[key]))
names=[None]*len(inst)
for k,v in inst.items(): names[v]=k
seen={k:v for k,v in seen.items() if k.split('|')[3]>=TODAY}
json.dump(seen,open(W+'/seen.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({"gen":TODAY,"inst":names,"logo":[logos.get(n,"") for n in names],"jobs":jobs},open(SITE+'/data.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print(f'convocatorias={len(jobs)} sin_enlace={dropped} enlaces_rotos={dl} instituciones={len(inst)} con_logo={sum(1 for n in names if logos.get(n))} nuevas_hoy={sum(1 for x in jobs if x["v"]==TODAY)} tam={os.path.getsize(SITE+"/data.json")//1024}KB')
print(sorted(collections.Counter(x['r'] for x in jobs).items()))
