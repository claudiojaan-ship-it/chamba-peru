# Descarga y normaliza logos de instituciones (cache en work/logos_raw, salida en site/logos)
import json,sys,os,re,hashlib,collections,unicodedata,urllib.request,io
from PIL import Image
ROOT=sys.argv[1]; W=ROOT+'/work'; OUT=ROOT+'/site/logos'; os.makedirs(OUT,exist_ok=True); os.makedirs(W+'/logos_raw',exist_ok=True)
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130"}
d=json.load(open(W+'/dl/jobs.json',encoding='utf-8'))
def sl(s): return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFD',s).encode('ascii','ignore').decode().lower()).strip('-')[:60]
over=json.load(open(ROOT+'/tools/logo_overrides.json',encoding='utf-8')) if os.path.exists(ROOT+'/tools/logo_overrides.json') else {}
m=collections.defaultdict(collections.Counter)
for j in d:
    if (j.get('Fecha Máxima') or '')<'2026-01-01': continue
    m[re.sub(r'\s+',' ',j['Institución']).strip().upper()][(j.get('Logo de convocatoria') or '').strip()]+=1
# Empresas de Empleos Perú (bolsa del MTPE): usan el logo que subieron a la plataforma
if os.path.exists(W+'/dl/empleosperu.json'):
    for j in json.load(open(W+'/dl/empleosperu.json',encoding='utf-8')):
        lg=j.get('companyLogo') or {}; nm=re.sub(r'\s+',' ',j.get('companyName') or '').strip().upper()
        if nm and lg.get('url') and 'plataforma empleos peru' not in (lg.get('displayName') or '').lower() and nm not in m:
            m[nm][ "https://mtpe-candidatos.empleosperu.gob.pe/api/attachments"+lg['url'] ]+=1
res={}; miss=[]
for inst,c in m.items():
    url=over.get(inst) or c.most_common(1)[0][0]
    bad=not url or 'referencial' in url or ('MINISTERIO-DE-TRABAJO-Y-PROMOCION' in url and 'TRABAJO' not in inst)
    if bad and inst not in over: miss.append(inst); continue
    raw=W+'/logos_raw/'+hashlib.sha1(url.encode()).hexdigest()
    try:
        if not os.path.exists(raw):
            open(raw,'wb').write(urllib.request.urlopen(urllib.request.Request(url,headers=H),timeout=30).read())
        im=Image.open(raw); im.load()
        if im.mode in ('P','LA','RGBA') or 'transparency' in im.info:
            im=im.convert('RGBA'); bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im); im=bg
        im=im.convert('RGB'); im.thumbnail((160,160),Image.LANCZOS)
        cv=Image.new('RGB',(160,160),(255,255,255)); cv.paste(im,((160-im.width)//2,(160-im.height)//2))
        fn=sl(inst)+'.jpg'; cv.save(OUT+'/'+fn,'JPEG',quality=84,optimize=True); res[inst]='logos/'+fn
    except Exception as e:
        miss.append(inst)
json.dump(res,open(W+'/logos.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
open(W+'/logos_missing.txt','w',encoding='utf-8').write('\n'.join(sorted(miss)))
print('logos',len(res),'faltan',len(miss))
