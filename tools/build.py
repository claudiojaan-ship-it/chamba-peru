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

# Empleos Perú (bolsa pública del MTPE): no publica fecha de cierre, se considera vigente 30 días desde su publicación
DEP={'01':'Amazonas','02':'Áncash','03':'Apurímac','04':'Arequipa','05':'Ayacucho','06':'Cajamarca','07':'Callao','08':'Cusco','09':'Huancavelica','10':'Huánuco','11':'Ica','12':'Junín','13':'La Libertad','14':'Lambayeque','15':'Lima','16':'Loreto','17':'Madre de Dios','18':'Moquegua','19':'Pasco','20':'Piura','21':'Puno','22':'San Martín','23':'Tacna','24':'Tumbes','25':'Ucayali'}
EDU={'secundaria':'s','primaria':'s','sin estudios':'s','tecnica':'t','universitaria estudiando':'e','tecnica estudiando':'e'}
links={u for x in jobs for u in x['l']}; ep=0
EPF=W+'/dl/empleosperu.json'
for j in (json.load(open(EPF,encoding='utf-8')) if os.path.exists(EPF) else []):
    r=DEP.get((j.get('location') or {}).get('DEPARTMENT') or '')
    pub=(j.get('datePosted') or '')[:10]
    if not r or not pub or not j.get('active',True): continue
    f=(datetime.date.fromisoformat(pub)+datetime.timedelta(days=30)).isoformat()
    if f<TODAY: continue
    url=f"https://mtpe-candidatos.empleosperu.gob.pe/search-jobs/description?jobId={j['id']}"
    if url in links: continue
    nm=clean(j.get('companyName') or 'Empresa confidencial').upper()
    if nm not in inst: inst[nm]=len(inst)
    edu=(j.get('educationDegree') or {}).get('name') or ''
    e=next((v for k,v in EDU.items() if a(edu).startswith(k)), 'u' if 'universitaria' in a(edu) or 'maestria' in a(edu) else '')
    pk=(j.get('offeredRemunerationPackages') or [{}])[0] if j.get('displaySalary') else {}
    s=float(pk.get('minimumAmount') or 0)
    cont=(j.get('contractType') or {}).get('name'); hrs=(j.get('hoursPerWeek') or {}).get('name')
    q=' · '.join(x for x in [f"Estudios: {edu}" if edu else '', cont, hrs, (f"S/ {pk['minimumAmount']}–{pk['maximumAmount']}" if pk.get('maximumAmount') else '')] if x)
    dd=[['Empresa',clean(j['companyDescription'])[:300]]] if j.get('companyDescription') and 'DESCRIPTION' not in (j.get('confidentialFields') or []) else []
    title=clean(j['positionTitle'])
    t='practicas' if re.search(r'practica|practicante',a(title)) else 'privado'
    key='ep|'+j['id']
    if key not in seen: seen[key]=TODAY
    jobs.append(dict(p=title,n=inst[nm],r=r,f=f,s=s if 300<=s<=40000 else 0,q=q[:260],l=[url],d=dd,t=t,c=sector({'Institución':'','Puesto':title,'¿Quiénes pueden Postular?':'','Enlace 1':''}) if t=='practicas' else 'privado',e=e,v=seen[key],pub=pub,o='ep'))
    ep+=1

# Vacantes de portales oficiales de mineras (vigentes 30 días desde su publicación)
MF=W+'/dl/mineras.json'; mn=0
SEDE={'Antamina':'Áncash','Buenaventura':'Lima'}
for j in (json.load(open(MF,encoding='utf-8')) if os.path.exists(MF) else []):
    f=(datetime.date.fromisoformat(j['pub'])+datetime.timedelta(days=30)).isoformat()
    if f<TODAY or j['u'] in links: continue
    loc=re.search(r'\(\d{2} - ([^,]+), PE\)',j['t'])
    r=next((v for v in DEP.values() if loc and a(v)==a(loc.group(1))), SEDE.get(j['emp'],'Lima'))
    title=re.sub(r'\s*\((\d{2} - [^)]*|Peru)\)\s*$','',j['t']).strip()
    nm=('COMPAÑÍA DE MINAS BUENAVENTURA' if j['emp']=='Buenaventura' else 'COMPAÑÍA MINERA ANTAMINA')
    if nm not in inst: inst[nm]=len(inst)
    key='mina|'+j['u']
    if key not in seen: seen[key]=TODAY
    jobs.append(dict(p=title,n=inst[nm],r=r,f=f,s=0,q=f"Vacante publicada en el portal oficial de empleo de {j['emp']}."[:260],l=[j['u']],d=[['Descripción',j['x'][:300]]] if j.get('x') else [],t='privado',c='privado',e='',v=seen[key],pub=j['pub'],o='mina',km=1))
    mn+=1

# Carreras: etiquetas para filtrar por profesión u oficio
CARR=[('mineria',r'miner|\bmina\b|geolog|metalurg|perforac|voladur|chancad|concentrador|planta concentradora|relaves'),
 ('enfermeria',r'enfermer'),
 ('salud',r'medic[oa]\b|\bmedico|obstetr|odontolog|quimico farmac|farmac|tecnologo medico|psicolog|nutricion|biolog|laboratori|radiolog|terapeut|cirujan|salud'),
 ('ingenieria',r'ingenier|ing\.'),
 ('derecho',r'abogad|derecho|legal|juridic'),
 ('contabilidad',r'contad|contab|finanz|tesorer|auditor|tribut|econom'),
 ('educacion',r'docente|profesor|auxiliar de educacion|educacion inicial|tutor'),
 ('sistemas',r'sistemas|informatic|programador|desarrollador|soporte tecnico|\bti\b|datos|software|redes'),
 ('administracion',r'administra|recursos humanos|logistic|secretari|asistente administrativo|almacen|archiv'),
 ('ventas',r'ventas|vendedor|comercial|atencion al cliente|cajer|promotor|asesor de negocios|call center|teleoperador'),
 ('conductores',r'chofer|conductor|operador de maquinaria|operador de equipo|montacarga|motorizado|reparto'),
 ('seguridad',r'vigilan|agente de seguridad|seguridad patrimonial|bombero|resguardo'),
 ('construccion',r'albanil|obra|construcci|arquitect|electricista|gasfiter|soldador|maestro de obra|topograf|operario de construccion'),
 ('agro',r'agronom|agricol|agrari|veterinar|zootecn|forestal|acuicult|pesca'),
 ('gastronomia',r'cocin|chef|mozo|azafat|panader|barista|ayudante de cocina'),
 ('limpieza',r'limpieza|operario de limpieza|mantenimiento|conserje')]
for x in jobs:
    t=a(x['p']+' '+x['q'])
    ks=[k for k,p in CARR if re.search(p,t)]
    if x.pop('km',0) and 'mineria' not in ks: ks.insert(0,'mineria')
    if x['c'] in ('educacion','salud') and x['c'] not in ks and not ks: ks.append(x['c'])
    x['k']=ks[:3]

# Grados que pide cada convocatoria, tal como aparecen en el texto (puede pedir varios)
GRADOS=[('m',r'maestr|magister|doctorad'),
 ('ti',r'titulad|licenciad|titulo (profesional|universitario)|colegiad|habilitad|universitaria - licenciado'),
 ('b',r'bachiller'),
 ('eg',r'egresad[oa]s? (universitari|de la carrera|de las carreras|de universidad)|universitaria completa|egresad[oa]s? en'),
 ('t',r'tecnic[oa]s? (titulad|egresad|completa|en )|instituto|tecnica completa|carrera tecnica|estudios tecnicos|tecnico superior'),
 ('e',r'estudiante|practicante|practicas (pre|profesional)|cursando|ultimos ciclos|universitaria estudiando|tecnica estudiando|universitaria incompleta'),
 ('s',r'secundaria|primaria completa|sin estudios|sin experiencia')]
for x in jobs:
    t=a(' '.join([x['p'],x['q']]+[b for _,b in x.get('d',[])]))
    g=[k for k,p in GRADOS if re.search(p,t)]
    if not g and re.search(r'egresad',t): g=['eg']
    if not g and x.get('e')=='u': g=['ti']
    if not g and x.get('e'): g=[{'s':'s','t':'t','e':'e'}.get(x['e'],'ti')]
    x['g']=g
names=[None]*len(inst)
for k,v in inst.items(): names[v]=k
seen={k:v for k,v in seen.items() if (k.startswith(('ep|','mina|')) and v>=(datetime.date.fromisoformat(TODAY)-datetime.timedelta(days=45)).isoformat()) or (not k.startswith(('ep|','mina|')) and k.split('|')[3]>=TODAY)}
json.dump(seen,open(W+'/seen.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({"gen":TODAY,"inst":names,"logo":[logos.get(n,"") for n in names],"jobs":jobs},open(SITE+'/data.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print(f'convocatorias={len(jobs)} empleosperu={ep} mineras={mn} sin_enlace={dropped} enlaces_rotos={dl} instituciones={len(inst)} con_logo={sum(1 for n in names if logos.get(n))} nuevas_hoy={sum(1 for x in jobs if x["v"]==TODAY)} tam={os.path.getsize(SITE+"/data.json")//1024}KB')
print(sorted(collections.Counter(x['r'] for x in jobs).items()))
