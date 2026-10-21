# Lista los enlaces únicos de convocatorias vigentes (uno por línea, saltos LF)
import json,sys,datetime
ROOT=sys.argv[1]; hoy=datetime.date.today().isoformat()
d=json.load(open(ROOT+'/work/dl/jobs.json',encoding='utf-8'))
u={(j.get(f'Enlace {k}') or '').strip() for j in d if (j.get('Fecha Máxima') or '')>=hoy for k in range(1,7)}
open(ROOT+'/work/urls.txt','w',encoding='utf-8',newline='\n').write('\n'.join(sorted(x for x in u if x.startswith('http'))))
print(len([x for x in u if x.startswith('http')]))
