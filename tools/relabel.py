"""작은 라벨·버튼 그림 일괄 한글화: 그림 전체에서 글자 픽셀을 찾아 지우고 같은 색감으로 한글을 다시 그린다."""
import sys,os,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__))
import tim2,imgpatch
from PIL import Image,ImageDraw,ImageFont
SERIF=imgpatch.SERIF
def lum(a): return a[...,0]*0.3+a[...,1]*0.59+a[...,2]*0.11
def find_mask(rgb,alpha,box=None):
    f=rgb.astype(np.float32); h,w=alpha.shape
    bg=cv2.medianBlur(rgb,9).astype(np.float32)
    L=lum(f); Lb=lum(bg)
    m=(L-Lb>28)|((np.abs(f-bg).max(2)>70))
    g=(rgb[...,1]>180)&(rgb[...,0]<120)&(rgb[...,2]<120)
    m&=~g; m&=alpha>40
    if box:
        x0,y0,x1,y1=box; b=np.zeros_like(m); b[y0:y1,x0:x1]=True; m&=b
    else:
        b=np.zeros_like(m); q=max(1,h//7); b[q:h-q,q:w-q]=True; m&=b
    m=m.astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m,8)
    keep=np.zeros_like(m)
    for i in range(1,n):
        if st[i,4]>=3: keep[lab==i]=1
    return keep
def draw(rgb,alpha,box,text,col_top,col_bot,outc,font=SERIF,vertical=False,stroke=1):
    x0,y0,x1,y1=box; W,H=x1-x0,y1-y0; S=4
    if W<4 or H<4: return rgb
    f=ImageFont.truetype(font,int(H*S*1.1))
    tmp=Image.new('L',(len(text)*H*S*3+50,H*S*8)); d=ImageDraw.Draw(tmp)
    d.multiline_text((0,0),text,font=f,fill=255,spacing=int(H*S*0.05),align='center')
    bb=tmp.getbbox()
    if not bb: return rgb
    g=tmp.crop(bb)
    nh=int(H*S*0.92); nw=int(g.width*nh/g.height)
    if nw>W*S: nw=W*S
    g=g.resize((nw,nh),Image.LANCZOS)
    M=Image.new('L',(W*S,H*S)); M.paste(g,((W*S-nw)//2,(H*S-nh)//2))
    a=np.asarray(M.resize((W,H),Image.LANCZOS),np.float32)/255
    t=np.linspace(0,1,H)[:,None,None]
    col=np.array(col_top,np.float32)*(1-t)+np.array(col_bot,np.float32)*t
    o=cv2.dilate(a,np.ones((3,3),np.float32)) if stroke else a*0
    reg=rgb[y0:y1,x0:x1].astype(np.float32)
    reg=reg*(1-o[...,None])+np.array(outc,np.float32)*o[...,None]
    reg=reg*(1-a[...,None])+col*a[...,None]
    rgb=rgb.copy(); rgb[y0:y1,x0:x1]=reg.clip(0,255).astype(np.uint8)
    return rgb
def relabel(b,k,text,box=None,font=SERIF,vertical=False,pad=1,colors=None):
    dbox=None
    if box and len(box)==8: box,dbox=tuple(box[:4]),tuple(box[4:])
    rgba,I=tim2.decode(bytes(b),k); rgb=rgba[...,:3].copy(); al=rgba[...,3]; h,w=al.shape
    m=find_mask(rgb,al,box)
    ys,xs=np.nonzero(m)
    if len(ys)==0: return False
    tb=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
    L=lum(rgb.astype(np.float32))
    core=m.astype(bool)&(L>=np.percentile(L[m>0],75))
    cy=(tb[1]+tb[3])/2
    up=core.copy(); up[int(cy):]=False; dn=core.copy(); dn[:int(cy)]=False
    ct=rgb[up].mean(0) if up.any() else rgb[core].mean(0)
    cb=rgb[dn].mean(0) if dn.any() else ct
    md=cv2.dilate(m,np.ones((3,3),np.uint8))
    ring=(md>0)&(m==0)
    dark=rgb[(md>0)&(L<np.percentile(L[md>0],25))]
    outc=dark.mean(0) if len(dark) else (0,0,0)
    if colors: ct,cb,outc=colors
    lt=ct[0]*0.3+ct[1]*0.59+ct[2]*0.11
    if box and lt<170:
        k_=190/max(lt,1); ct=np.minimum(np.array(ct)*k_,255); cb=ct
    im=cv2.dilate(m,np.ones((3,3),np.uint8),iterations=pad)
    if box:
        im=np.zeros_like(m); im[box[1]:box[3],box[0]:box[2]]=1
    clean=cv2.inpaint(rgb,im,5,cv2.INPAINT_TELEA)
    al=cv2.inpaint(np.ascontiguousarray(al),im,5,cv2.INPAINT_TELEA)
    # 그릴 영역: 글자 범위를 그림 안쪽으로 조금 넓힘
    x0,y0,x1,y1=tb
    if box: bx0,by0,bx1,by1=box
    else:
        g=(rgb[...,1]>180)&(rgb[...,0]<120)&(rgb[...,2]<120)
        cols=np.nonzero(g.sum(0)>h*0.3)[0]
        bx1=cols.min() if len(cols) else w; bx0,by0,by1=0,0,h
    cxm=(x0+x1)/2; need=len(text.replace(' ','').replace('\n',''))
    hw=max((x1-x0)/2, min((x1-x0)/2+(y1-y0)*0.6, cxm-bx0-2, bx1-2-cxm))
    if need<=len(text) and (x1-x0)>=hw*2*0.9: hw=(x1-x0)/2
    X0=int(max(bx0+1,cxm-hw)); X1=int(min(bx1-1,cxm+hw))
    if vertical: X0,X1=x0,x1
    if box:
        X0,X1=bx0,bx1; bh=by1-by0; y0=int(by0+bh*0.08); y1=int(by1-bh*0.08)
    if dbox: X0,y0,X1,y1=dbox
    out=draw(clean,al,(X0,y0,X1,y1),text,ct,cb,outc,font,vertical)
    ch=np.abs(out.astype(int)-clean.astype(int)).sum(2)>0
    al=al.copy(); al[ch]=np.maximum(al[ch],rgba[...,3].max())
    imgpatch.encode(b,k,I,out,al); return True
def full_arrays(rgba,text,font=SERIF):
    rgb=rgba[...,:3].astype(np.float32); al=rgba[...,3]; h,w=al.shape
    m=al>100; ys,xs=np.nonzero(m)
    x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
    L=lum(rgb); hi=m&(L>np.percentile(L[m],35))&(L<np.percentile(L[m],80)); lo=m&(L<np.percentile(L[m],15))
    cy=(y0+y1)//2
    def mean(mm,default): return rgb[mm].mean(0) if mm.any() else default
    up=hi.copy(); up[cy:]=False; dn=hi.copy(); dn[:cy]=False
    ct=mean(up,rgb[hi].mean(0)); cb=mean(dn,ct); oc=mean(lo,np.zeros(3))
    W,H=x1-x0,y1-y0; S=4
    f=ImageFont.truetype(font,int(H*S))
    tmp=Image.new('L',(len(text)*H*S*2+50,H*S*3)); d=ImageDraw.Draw(tmp); d.text((0,0),text,font=f,fill=255)
    g=tmp.crop(tmp.getbbox())
    nh=int(H*S*0.86); nw=int(g.width*nh/g.height); nw=min(nw,W*S)
    g=g.resize((nw,nh),Image.LANCZOS)
    M=Image.new('L',(W*S,H*S)); M.paste(g,((W*S-nw)//2,(H*S-nh)//2))
    a=np.asarray(M.resize((W,H),Image.LANCZOS),np.float32)/255
    o=cv2.dilate(a,np.ones((5,5),np.float32)); o=np.maximum(o,np.roll(np.roll(o,2,0),2,1)*0.8)
    t=np.linspace(0,1,H)[:,None,None]
    col=np.array(ct)*(1-t)+np.array(cb)*t
    out=np.zeros((h,w,3),np.float32); A=np.zeros((h,w),np.float32)
    reg=np.array(oc)[None,None,:]*np.ones((H,W,1))
    reg=reg*(1-a[...,None])+col*a[...,None]
    out[y0:y1,x0:x1]=reg; A[y0:y1,x0:x1]=np.maximum(o,a)*255
    return out.clip(0,255).astype(np.uint8),A.astype(np.uint8)
def redraw_full(b,k,text,font=SERIF):
    """투명 배경 글자 그림: 원래 글자 색(위/아래)·테두리 색을 뽑아 새로 그림"""
    rgba,I=tim2.decode(bytes(b),k); out,A=full_arrays(rgba,text,font)
    imgpatch.encode(b,k,I,out,A); return True
def redraw_pair(b,kt,kb,text,font=SERIF):
    """위·아래 반쪽 두 장으로 나뉜 글자 그림"""
    t,It=tim2.decode(bytes(b),kt); u,Ib=tim2.decode(bytes(b),kb)
    out,A=full_arrays(np.concatenate([t,u],0),text,font); h=t.shape[0]
    imgpatch.encode(b,kt,It,np.ascontiguousarray(out[:h]),np.ascontiguousarray(A[:h]))
    imgpatch.encode(b,kb,Ib,np.ascontiguousarray(out[h:]),np.ascontiguousarray(A[h:]))
def load_jobs():
    p=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'trans','labels.tsv'); J={}
    for l in open(p,encoding='utf-8'):
        x=l.rstrip('\n').split('\t')
        if len(x)<3: continue
        box=tuple(map(int,x[3].split(','))) if len(x)>3 else None
        J.setdefault(int(x[0]),[]).append((int(x[1]),x[2].replace('|','\n'),box))
    return J
def apply(i,data):
    J=load_jobs()
    if i not in J: return data
    b=bytearray(data)
    for k,t,box in J[i]:
        if i==33: redraw_full(b,k,t)
        elif (i==34 and k==108864) or i==46 or (i==81 and 788000<k<790000): cell(b,k,box,t,imgpatch.SERIF if i==46 else None)
        elif t.startswith('PAIR:'): redraw_pair(b,k,box[0],t[5:])
        else: relabel(b,k,t,**({'box':box} if box else {}))
    return bytes(b)
def cell(b,k,box,text,font=None):
    """아주 작은 아이콘 칸: 바탕을 칸의 어두운 색으로 채우고 한 글자"""
    rgba,I=tim2.decode(bytes(b),k); rgb=rgba[...,:3].copy(); al=rgba[...,3]
    x0,y0,x1,y1=box; c=rgb[y0:y1,x0:x1].astype(np.float32); L=lum(c)
    bg=np.median(c[L<=np.percentile(L,40)],0); fg=c[L>=np.percentile(L,85)].mean(0)
    lf=fg@np.array([0.3,0.59,0.11])
    if lf<200: fg=np.minimum(fg*(215/max(lf,1)),255)
    rgb[y0:y1,x0:x1]=bg.astype(np.uint8)
    out=draw(rgb,al,(x0,y0,x1,y1),text,fg,fg*0.85,(0,0,0),font or imgpatch.GOTH,False,stroke=0)
    imgpatch.encode(b,k,I,out,al)
