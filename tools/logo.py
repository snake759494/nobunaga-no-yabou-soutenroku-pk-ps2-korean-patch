"""타이틀 로고(51번 848 + 231360) 한글화: 두 장을 이어 붙여 로고 지우고 다시 그림"""
import sys,os,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__))
import tim2,imgpatch
from PIL import Image,ImageDraw,ImageFont
A,B=848,231360
SERIF=imgpatch.SERIF; GOTH=imgpatch.GOTH
def render(text,font,px,S=3):
    f=ImageFont.truetype(font,px*S)
    t=Image.new('L',(len(text)*px*S*2+40,px*S*3)); ImageDraw.Draw(t).text((0,0),text,font=f,fill=255)
    g=t.crop(t.getbbox()); return g
def place(canvas,g,box,S=3):
    x0,y0,x1,y1=box; W,H=x1-x0,y1-y0
    g=g.resize((W*S,H*S),Image.LANCZOS).resize((W,H),Image.LANCZOS)
    a=np.zeros(canvas,np.float32); a[y0:y1,x0:x1]=np.asarray(g,np.float32)/255; return a
def comp(rgb,a,top,bot,outline,ow,glow=None,gw=0):
    ys=np.nonzero(a.max(1)>0.1)[0]; y0,y1=ys.min(),ys.max()
    t=((np.arange(rgb.shape[0])-y0)/max(1,y1-y0)).clip(0,1)[:,None,None]
    col=np.array(top,np.float32)*(1-t)+np.array(bot,np.float32)*t
    o=cv2.dilate(a,np.ones((ow*2+1,ow*2+1),np.float32))
    if glow is not None:
        gl=cv2.GaussianBlur(cv2.dilate(a,np.ones((gw,gw),np.float32)),(0,0),gw/2)*0.9
        rgb=rgb*(1-gl[...,None])+np.array(glow,np.float32)*gl[...,None]
    rgb=rgb*(1-o[...,None])+np.array(outline,np.float32)*o[...,None]
    rgb=rgb*(1-a[...,None])+col*a[...,None]
    return rgb
def apply(b):
    ra,Ia=tim2.decode(bytes(b),A); rb,Ib=tim2.decode(bytes(b),B)
    rgb=np.concatenate([ra[...,:3],rb[...,:3]],1).copy(); al=np.concatenate([ra[...,3],rb[...,3]],1)
    H,W=rgb.shape[:2]
    f=rgb.astype(np.float32); L=f@np.array([0.3,0.59,0.11],np.float32)
    bg=cv2.medianBlur(rgb,31).astype(np.float32)@np.array([0.3,0.59,0.11],np.float32)
    m=((np.abs(L-bg)>18)|(f[...,2]-f[...,1]>25)).astype(np.uint8)
    reg=np.zeros_like(m); reg[28:345,80:640]=1; m&=reg
    m=cv2.dilate(m,np.ones((7,7),np.uint8))
    clean=cv2.inpaint(rgb,m,9,cv2.INPAINT_TELEA).astype(np.float32)
    mm=cv2.GaussianBlur(m.astype(np.float32),(0,0),6)[...,None]; clean=clean*(1-0.45*mm)
    # 1) 노부나가의 야망
    a=place((H,W),render('노부나가의 야망',SERIF,60),(92,40,632,140))
    out=comp(clean,a,(250,250,255),(150,155,175),(5,5,10),3,glow=(60,80,210),gw=9)
    # 2) 창천록
    a=place((H,W),render('창 천 록',SERIF,48),(220,150,450,210))
    out=comp(out,a,(240,240,245),(160,160,170),(5,5,10),2,glow=(60,80,210),gw=7)
    # 3) with
    a=place((H,W),render('with',SERIF,20),(300,222,360,244))
    out=comp(out,a,(230,230,230),(190,190,190),(5,5,10),1)
    # 4) 파워업 키트 (검은 글자 흰 테두리)
    a=place((H,W),render('파워업 키트',GOTH,44),(150,250,500,302))
    out=comp(out,a,(15,15,20),(10,10,15),(235,235,240),2)
    # 밑줄
    cv2.line(out,(148,322),(500,322),(235,235,240),3); cv2.line(out,(148,322),(500,322),(15,15,20),1)
    out=out.clip(0,255).astype(np.uint8)
    imgpatch.encode(b,A,Ia,np.ascontiguousarray(out[:,:512]),np.ascontiguousarray(al[:,:512]))
    imgpatch.encode(b,B,Ib,np.ascontiguousarray(out[:,512:]),np.ascontiguousarray(al[:,512:]))
if __name__=='__main__':
    from common import *
    e=elf(); a,sz=toc(e)[51]; f=open(os.path.join(W,'iso','nbx.bin'),'rb'); f.seek(a); d=bytearray(f.read(sz))
    apply(d)
    ra=tim2.decode(bytes(d),A)[0]; rb=tim2.decode(bytes(d),B)[0]
    Image.fromarray(np.concatenate([ra,rb],1)).save(os.path.join(W,'shots','sheet','logo2.png'))
