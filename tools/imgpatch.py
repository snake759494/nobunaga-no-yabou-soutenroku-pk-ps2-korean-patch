"""제목 그림(TIM2) 일본어 글자 지우고 한글 그리기"""
import sys,os,struct,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__))
from common import R
import tim2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
SERIF=os.path.join(R,'SeoulHangangEB.ttf')
GOTH=os.path.join(R,'NanumSquareNeo-dEb.ttf')

def text_mask(rgb,box):
    x0,y0,x1,y1=box; r,g,b=[rgb[...,i].astype(int) for i in range(3)]
    m=((r>120)&(g>100)&(r>b+25))|((r+g+b)>520)
    out=np.zeros(m.shape,np.uint8); out[y0:y1,x0:x1]=m[y0:y1,x0:x1]
    return cv2.dilate(out,np.ones((5,5),np.uint8))
def gold_text(size,text,px,font=SERIF,top=(255,240,170),bot=(200,150,60),shadow=(20,12,0),xs=1.0):
    W,H=size; S=3
    f=ImageFont.truetype(font,px*S)
    tmp=Image.new('L',(W*S*2,H*S*2)); d=ImageDraw.Draw(tmp); d.text((0,0),text,font=f,fill=255)
    bb=tmp.getbbox(); g=tmp.crop(bb)
    gw=int(g.width*xs)
    if gw>W*S: gw=W*S
    g=g.resize((gw,g.height),Image.LANCZOS)
    if g.height>H*S: g=g.resize((g.width,H*S),Image.LANCZOS)
    m=Image.new('L',(W*S,H*S)); m.paste(g,((W*S-g.width)//2,(H*S-g.height)//2))
    m=m.resize((W,H),Image.LANCZOS)
    a=np.asarray(m,np.float32)/255
    ys,_=np.nonzero(a>0.1)
    t=np.zeros((H,1))
    if len(ys): t=((np.arange(H)-ys.min())/max(1,ys.max()-ys.min())).clip(0,1)[:,None]
    col=np.array(top)[None,None,:]*(1-t[...,None])+np.array(bot)[None,None,:]*t[...,None]
    sh=cv2.GaussianBlur(cv2.dilate(a,np.ones((3,3))),(3,3),0)
    sh=np.roll(np.roll(sh,1,0),1,1)
    return a,col,sh,np.array(shadow,np.float32)
def patch(b,k,box,text,px,clear=True,**kw):
    """b: bytearray, k: TIM2 위치, box: (x0,y0,x1,y1) 글자 영역"""
    rgba,I=tim2.decode(bytes(b),k); rgb=rgba[...,:3].copy()
    if clear:
        m=text_mask(rgb,box); rgb=cv2.inpaint(rgb,m,4,cv2.INPAINT_TELEA)
    if not text: encode(b,k,I,rgb,rgba[...,3]); return
    x0,y0,x1,y1=box; a,col,sh,shc=gold_text((x1-x0,y1-y0),text,px,**kw)
    reg=rgb[y0:y1,x0:x1].astype(np.float32)
    reg=reg*(1-sh[...,None]*0.85)+shc*(sh[...,None]*0.85)
    reg=reg*(1-a[...,None])+col*a[...,None]
    rgb[y0:y1,x0:x1]=reg.clip(0,255).astype(np.uint8)
    encode(b,k,I,rgb,rgba[...,3])
def encode(b,k,I,rgb,alpha):
    p=I['p']+I['hs']; w,h=I['w'],I['h']
    q,cs,_=tim2.clut_bytes(b,k); cl=np.frombuffer(bytes(b[q:q+cs]),np.uint8).reshape(-1,4).copy()
    pal=tim2.unswz8(cl) if (I['it']==5 and len(cl)==256 and not (I['ct']&0x80)) else cl
    pa=pal[:,3].astype(int)*2
    pc=pal[:,:3].astype(np.float32)
    flat=rgb.reshape(-1,3).astype(np.float32); al=alpha.reshape(-1).astype(int)
    o,_=tim2.decode(bytes(b),k); o=o.reshape(-1,4).astype(int)
    if I['it']==5: oidx=np.frombuffer(bytes(b[p:p+w*h]),np.uint8).astype(np.int64)
    else:
        pk=np.frombuffer(bytes(b[p:p+w*h//2]),np.uint8); oidx=np.stack([pk&15,pk>>4],1).reshape(-1).astype(np.int64)
    same=(np.abs(o[:,:3]-flat).max(1)<1)&(np.abs(o[:,3]-al)<2)
    idx=np.zeros(len(flat),np.int64)
    for s in range(0,len(flat),8192):
        d=((flat[s:s+8192,None,:]-pc[None])**2).sum(2)+((al[s:s+8192,None]-pa[None])**2)*4
        idx[s:s+8192]=d.argmin(1)
    if I['it']==5:
        if pal is not cl:  # 팔레트 순서 되돌리기(대칭)
            perm=np.arange(256)
            for i in range(0,256,32): perm[i+8:i+16],perm[i+16:i+24]=np.arange(i+16,i+24),np.arange(i+8,i+16)
            idx=perm[idx]
        idx=np.where(same,oidx,idx)
        b[p:p+w*h]=idx.astype(np.uint8).tobytes()
    else:
        idx=np.where(same,oidx,idx); ii=idx.astype(np.uint8); b[p:p+w*h//2]=(ii[0::2]|(ii[1::2]<<4)).tobytes()
def show(b,k,path): Image.fromarray(tim2.decode(bytes(b),k)[0],'RGBA').save(path)
