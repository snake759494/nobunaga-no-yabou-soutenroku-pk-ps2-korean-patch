import sys,os; sys.path.insert(0,'work/tools')
from common import *
import tim2,relabel
from PIL import Image,ImageDraw
e=elf(); T=toc(e); f=open('work/iso/nbx.bin','rb')
J=[x for x in (l.rstrip(chr(10)).split(chr(9)) for l in open('work/trans/labels.tsv',encoding='utf-8')) if len(x)>=3]
data={}
pairs=[]
for x in J:
    en,k,t=x[:3]; box=tuple(map(int,x[3].split(','))) if len(x)>3 else None
    en,k=int(en),int(k); t=t.replace('|',chr(10))
    if en not in data: a,sz=T[en]; f.seek(a); data[en]=bytearray(f.read(sz))
    before=Image.fromarray(tim2.decode(bytes(data[en]),k)[0],'RGBA')
    import numpy as np
    al=np.asarray(before)[...,3]
    (relabel.redraw_full if en==33 else relabel.relabel)(data[en],k,t,**({'box':box} if box else {}))
    after=Image.fromarray(tim2.decode(bytes(data[en]),k)[0],'RGBA')
    pairs.append((en,k,before,after))
x=y=rh=0; pos=[]
for en,k,b,a in pairs:
    w=(b.width*2)*2+4; hh=b.height*2
    if x+w>1600: x=0;y+=rh+14;rh=0
    pos.append((x,y,en,k,b,a)); x+=w+10; rh=max(rh,hh)
S=Image.new('RGB',(1600,y+rh+14),(60,0,60)); D=ImageDraw.Draw(S)
for x,y,en,k,b,a in pos:
    b2=b.resize((b.width*2,b.height*2)); a2=a.resize((a.width*2,a.height*2))
    S.paste(b2,(x,y+12),b2); S.paste(a2,(x+b2.width+4,y+12),a2); D.text((x,y),'%d:%d'%(en,k),fill=(255,255,0))
for n in range(0,S.height,1000): S.crop((0,n,1600,min(S.height,n+1000))).save('work/shots/sheet/lab%d.png'%(n//1000))
print(S.size)
