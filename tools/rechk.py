import sys,urllib.parse,subprocess
bad=[l.rstrip('\n').split('\t') for l in open(sys.argv[1],encoding='utf-8') if not l.startswith(('200','206'))]
out=open(sys.argv[2],'w',encoding='utf-8')
for c,u in bad:
    q=urllib.parse.quote(u,safe=":/?=&%#~+,;@!$'()*[]")
    r=subprocess.run(["curl","-s","-g","-o","/dev/null","-L","--max-time","30","-k","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130","-w","%{http_code}","-r","0-2000",q],capture_output=True,text=True).stdout
    out.write(f"{r}\t{u}\n")
