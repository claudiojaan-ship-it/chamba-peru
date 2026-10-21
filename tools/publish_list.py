# Lista los archivos a publicar: data.json + logos usados que aún no se publicaron.
# Uso: py -P tools/publish_list.py <raiz>          -> imprime JSON (lista de rutas relativas a site/)
#      py -P tools/publish_list.py <raiz> --mark   -> registra esos logos como publicados
import json,sys,os
R=sys.argv[1]; P=R+'/work/published_logos.json'
d=json.load(open(R+'/site/data.json',encoding='utf-8'))
done=set(json.load(open(P,encoding='utf-8'))) if os.path.exists(P) else set()
used=sorted({l for l in d['logo'] if l and os.path.exists(R+'/site/'+l)})
new=[l for l in used if l not in done][:250]
if '--mark' in sys.argv:
    json.dump(sorted(done|set(new)),open(P,'w',encoding='utf-8')); print('marcados',len(new))
else:
    print(json.dumps(['data.json']+new,ensure_ascii=False))
