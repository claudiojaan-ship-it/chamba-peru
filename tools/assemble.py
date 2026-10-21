# Inserta los créditos de fotos en la plantilla y escribe site/chamba-peru.html y site/index.html
import sys
R=sys.argv[1]
t=open(R+'/tools/template.html',encoding='utf-8').read()
p=open(R+'/tools/photos.js',encoding='utf-8').read()
html=t.replace('/*PHOTOS*/',p)
for name in ('chamba-peru.html','index.html'):
    open(R+'/site/'+name,'w',encoding='utf-8',newline='\n').write(html)
