"""TIM2 4/8bpp 해석·쓰기"""
import struct,numpy as np
from PIL import Image
def info(b,k):
    p=k+16; tot,cs,isz,hs,cc,fmt,mm,ct,it,w,h=struct.unpack_from('<IIIHHBBBBHH',b,p)
    return dict(p=p,tot=tot,cs=cs,isz=isz,hs=hs,cc=cc,ct=ct,it=it,w=w,h=h)
def unswz8(c):
    # CSM1 8bpp 팔레트 순서 보정
    c=c.copy()
    for i in range(0,256,32): c[i+8:i+16],c[i+16:i+24]=c[i+16:i+24].copy(),c[i+8:i+16].copy()
    return c
def clut_src(b,k):
    """CLUT 없는 그림은 바로 앞의 CLUT 있는 TIM2 의 것을 공유"""
    I=info(b,k)
    if I['cs']: return k
    j=k
    while True:
        j=bytes(b).rfind(b'TIM2',0,j)
        if j<0: return None
        if info(b,j)['cs']: return j
def clut_bytes(b,k):
    s=clut_src(b,k); J=info(b,s); q=J['p']+J['hs']+J['isz']
    return q,J['cs'],J
def decode(b,k):
    I=info(b,k); p=I['p']+I['hs']; w,h=I['w'],I['h']
    px=np.frombuffer(b[p:p+I['isz']],np.uint8)
    q,cs,J=clut_bytes(b,k); I['ct']=J['ct'] if not I['cs'] else I['ct']
    cl=np.frombuffer(b[q:q+cs],np.uint8).reshape(-1,4).copy()
    if I['it']==4: idx=np.stack([px&15,px>>4],1).reshape(-1)[:w*h]
    else:
        idx=px[:w*h]
        if len(cl)==256 and not (I['ct']&0x80): cl=unswz8(cl)
    a=cl[idx].reshape(h,w,4).astype(np.uint16); a[...,3]=np.minimum(a[...,3]*2,255)
    return a.astype(np.uint8),I
def to_png(b,k,path): a,I=decode(b,k); Image.fromarray(a,'RGBA').save(path)
