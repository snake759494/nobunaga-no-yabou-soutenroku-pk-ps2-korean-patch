"""한글 글리프 그리기: 흰 획(AA) + 1px 어두운 테두리, 22x22 칸(24 폭 중 22)."""
import numpy as np,os
from PIL import Image,ImageDraw,ImageFont
from common import R
FONT=os.path.join(R,'NanumSquareNeo-dEb.ttf')
SS=4
_f={}
def font(px,path=FONT):
    k=(px,path)
    if k not in _f: _f[k]=ImageFont.truetype(path,px*SS)
    return _f[k]
def cover(text,px=20,xscale=1.0,cw=22,ch=22,dy=0,path=FONT):
    f=font(px,path); W,H=cw*SS,ch*SS
    tmp=Image.new('L',(W*3,H*2),0); d=ImageDraw.Draw(tmp)
    d.text((0,0),text,font=f,fill=255)
    bb=tmp.getbbox()
    if not bb: return np.zeros((ch,cw))
    g=tmp.crop(bb)
    w=max(1,int(round(g.width*xscale)))
    if w>W-2*SS: w=W-2*SS
    g=g.resize((w,g.height),Image.LANCZOS)
    im=Image.new('L',(W,H),0)
    # 가로 가운데, 세로는 글꼴 기준선 기준(한자와 같은 높이): ascent 기준 중앙
    asc,desc=f.getmetrics()
    x=(W-w)//2
    y=bb[1]+ (H-(asc+desc))//2 + dy*SS
    im.paste(g,(x,y))
    a=np.asarray(im.resize((cw,ch),Image.BOX),np.float32)/255.0
    return a
def to4(a,outline=3):
    fill=np.clip(np.round(a*15),0,15)
    m=a>0.35
    dil=m.copy()
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            dil|=np.roll(np.roll(m,dy,0),dx,1)
    v=np.where(dil&(fill<outline),outline,fill)
    v=np.where((a>0.05)&(v<2),2,v)
    return v.astype(np.uint8)
def glyph(text,**kw):
    a=cover(text,**kw); g=np.zeros((22,24),np.uint8); g[:, :22]=to4(a); return g
