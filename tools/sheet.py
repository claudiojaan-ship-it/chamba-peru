import json,sys
from PIL import Image
R=sys.argv[1]; L=json.load(open(R+'/work/logos.json',encoding='utf-8'))
names=[k for k in L if any(w in k for w in sys.argv[3].split('|'))][:40]
cv=Image.new('RGB',(8*170,((len(names)+7)//8)*170),(200,200,200))
for i,k in enumerate(names): cv.paste(Image.open(R+'/site/'+L[k]),((i%8)*170+5,(i//8)*170+5))
cv.save(sys.argv[2]); print(names)
