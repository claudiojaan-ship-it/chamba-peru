# Vuelve a probar (codificando bien la URL) solo los enlaces que dieron 404/400/410.
# Los que no respondieron (000, 403, 503) se mantienen: suelen ser webs que bloquean visitas automáticas.
import sys,urllib.parse,subprocess
from concurrent.futures import ThreadPoolExecutor
rows=[l.rstrip('\n').split('\t',1) for l in open(sys.argv[1],encoding='utf-8') if '\t' in l]
bad=[(c,u) for c,u in rows if c in ('404','400','410')]
def check(item):
    c,u=item
    q=urllib.parse.quote(u,safe=":/?=&%#~+,;@!$'()*[]")
    r=subprocess.run(["curl","-s","-g","-o","/dev/null","-L","--connect-timeout","8","--max-time","20","-k","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130","-w","%{http_code}","-r","0-2000",q],capture_output=True,text=True).stdout
    return f"{r}\t{u}\n"
with ThreadPoolExecutor(16) as ex: out=list(ex.map(check,bad))
open(sys.argv[2],'w',encoding='utf-8').write(''.join(out))
print('revisados de nuevo',len(bad))
