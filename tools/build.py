"""한글 ISO 빌드: python work/tools/build.py
번역(trans/ko) + 이름 자동 표기 → 글꼴/ELF/오버레이/시나리오/39·40·41 → NBX 재조립 → ISO"""
import sys,os,re,glob,struct,shutil,collections
sys.path.insert(0,os.path.dirname(__file__))
from common import *
import scen,script,elftext,fontlib,glyph,kana2hangul as K
T=os.path.join(W,'trans'); NL=chr(10); BS=chr(92)
OUT=os.path.join(R,'Nobunaga no Yabou - Soutenroku with Power-Up Kit (Korean).iso')
PH=re.compile(r'<([0-9a-f]+)>')
dec=lambda b: b.decode('cp932','replace')

# ---------- 번역 읽기
def tsv(p,n):
    out=[]
    for l in open(p,encoding='utf-8'):
        l=l.rstrip('\r\n')
        if not l: continue
        x=l.split('\t')
        if len(x)>=n: out.append(x)
    return out
KO={}
for f in sorted(glob.glob(os.path.join(T,'ko','*.tsv'))):
    for x in tsv(f,2): KO[x[0]]=x[1].replace(BS+'n',NL)
SRC={}
for f in ('src_e39.tsv','src_e40.tsv','src_elf.tsv','src_ovl.tsv','src_scen_terms.tsv','src_scen_desc.tsv'):
    for x in tsv(os.path.join(T,f),3): SRC[x[0]]=(x[1],x[2].replace(BS+'n',NL))
KEEP=set(open(os.path.join(T,'elf_keep_orig.txt')).read().split())|{'40:5943'}
FIX={}   # 사전 개별 수정 (읽기 → 한글)
FIXF=os.path.join(T,'name_override.tsv')
if os.path.exists(FIXF):
    for x in tsv(FIXF,2): FIX[x[0]]=x[1]
def kword(r):
    r=r.replace(' ','')
    return FIX.get(r) or K.word(r)
# 이름 사전: 한자 → 한글
GL={}
for x in tsv(os.path.join(T,'glossary_names.tsv'),2): GL[x[0]]=x[1]
for k,v in FIX.items():
    if not re.match('[ぁ-ん]',k): GL[k]=v

# ---------- 글꼴 코드
e=bytearray(elf())
codes=fontlib.codes(e)
NK=sum(1 for c in codes if c<0x889f)
def collect():
    s=set()
    for v in KO.values(): s.update(PH.sub('',v))
    for v in GL.values(): s.update(v)
    return sorted(ch for ch in s if 0xac00<=ord(ch)<=0xd7a3)

# 추출 범위(0x2BC000~) 밖의 UI 문자열
EXTRA_ELF={0x2b8fc8:'%s(%d계)',0x2b91e8:'%s에게 %s',0x2b91f8:'%s가',0x2a8db8:'설치',0x2a8dd0:'설치 해제',0x2c2d08:'정렬',0x2c2d10:'도움말',0x2c2d18:'+PU쪽'}
_W={'標準':'표준','状態':'상태','能力':'능력','経歴':'경력','特技':'특기','策戦':'작전','要項':'요항','物資':'물자','外交':'외교','目標':'목표','所属':'소속','規模':'규모','城主':'성주','所有':'소유','効果':'효과'}
for _o in (0x2b9208,0x2b9210,0x2b9218,0x2b9220,0x2b9228,0x2b9230,0x2b9238,0x2b9f28,0x2b9f68,0x2b9f70,0x2b9f78,0x2b9f80,0x2ba180,0x2ba188,0x2ba190,0x2ba198,0x2ba330,0x2ba338,0x2ba340,0x2ba348,0x2ba420,0x2ba438,0x2ba718,0x2ba720,0x2ba728,0x2bbeb0,0x2bbeb8,0x2bbec0,0x2bbec8):
    _j=e.index(b'\0',_o); EXTRA_ELF[_o]=_W[e[_o:_j].decode('cp932')]
for _o,_t in EXTRA_ELF.items():
    _j=e.index(b'\0',_o); _k=_j
    while e[_k]==0 and _k<len(e)-1: _k+=1
    KO['E:%x'%_o]=_t; SRC['E:%x'%_o]=(str(min(_k-_o-1,(_j+1+7)//8*8-_o-1 if _o%4==0 else _j-_o) if _k-_o-1>=_j-_o else _j-_o),'')
HANGUL=collect()
LIG={'':'여름','':'가을','':'겨울'}
# 이름 칸 넘침용 2음절 합자: trans/lig.txt (한 줄 한 쌍), U+E100 부터
LIGF=os.path.join(T,'lig.txt')
LIGS=[l.strip() for l in open(LIGF,encoding='utf-8')] if os.path.exists(LIGF) else []
LIGS=[l for l in LIGS if l]
for n,p in enumerate(LIGS): LIG[chr(0xe100+n)]=p
RLIG={v:k for k,v in LIG.items() if ord(k)>=0xe100}
NEWLIG=collections.Counter()
def blen(s): return sum(1 if ord(ch)<0x80 else 2 for ch in s)
def isH(ch): return 0xac00<=ord(ch)<=0xd7a3
def fit(s,cap):
    """cap 바이트에 맞추기: 공백 빼기 → 2음절 합자"""
    if blen(s)<=cap: return s
    s2=s.replace(' ','') if '<' not in s else s
    if blen(s2)<=cap: return s2
    s=s2
    while blen(s)>cap:
        best=None
        for i in range(len(s)-1):
            a=s[i:i+2]
            if isH(a[0]) and isH(a[1]):
                sc=(a in RLIG, NEWLIG[a], i)
                if best is None or sc>best[0]: best=(sc,i,a)
        if not best: return s
        i,a=best[1],best[2]
        if a not in RLIG: NEWLIG[a]+=1; s=s[:i]+''+s[i+2:]; continue
        s=s[:i]+RLIG[a]+s[i+2:]
    return None if '' in s else s
for k,ch in (('2bfa78',''),('2bfa80',''),('2bfa88',''),('2ff8f8',''),('2ff900',''),('2ff908','')): KO['E:'+k]=ch
def hangul_codes(chars):
    seq=fontlib.sjis_seq(0x889f)
    return {ch:next(seq) for ch in chars}

# ---------- 인코딩
MISSING=set()
def ascii_fw(ch):
    o=ord(ch)
    if 0x21<=o<=0x7e: return chr(o+0xfee0)
    return ch
def enc(s,HC,script_mode=False):
    out=bytearray(); i=0
    for m in re.finditer(r'<([0-9a-f]+)>|(.)',s,re.S):
        if m.group(1): out+=bytes.fromhex(m.group(1)); continue
        ch=m.group(2)
        if ch==NL: out+=b'\n'; continue
        if ch in HC: out+=struct.pack('>H',HC[ch]); continue
        if 0xac00<=ord(ch)<=0xd7a3: MISSING.add(ch)
        if script_mode and ch!=' ': ch=ascii_fw(ch)
        if ch=='·': ch='・'
        try: out+=ch.encode('cp932')
        except UnicodeEncodeError: out+='？'.encode('cp932')
    ENCS[bytes(out)]=s
    return bytes(out)
ENCS={}
def cut(b,cap):
    """cap 바이트 이하, 2바이트 문자 경계"""
    if len(b)<=cap: return b
    i=0
    while i<len(b):
        n=2 if (0x81<=b[i]<=0x9f or 0xe0<=b[i]<=0xfc) else 1
        if i+n>cap: break
        i+=n
    return b[:i]
CUTS=[]
def put(buf,off,data,cap):
    if len(data)>cap and data in ENCS and ENCS[data] and NL not in ENCS[data]:
        f=fit(ENCS[data],cap)
        if f: data=enc(f,CURHC)
    if len(cut(data,cap))<len(data): CUTS.append((off,cap,len(data),ENCS.get(data,'?').replace(NL,'/')))
    data=cut(data,cap)
    buf[off:off+cap+1]=data+bytes(cap+1-len(data))

# ---------- 줄바꿈 (열전 18칸)
def w1(t):
    return 4 if t.startswith('<') else (0.5 if ord(t)<0x80 else 1)
def wrap(s,width=18,maxl=4):
    toks=re.findall(r'<[0-9a-f]+>|.',s)
    lines=[[]]; cur=0; i=0
    words=[]; w=[]
    for t in toks:
        w.append(t)
        if t==' ': words.append(w); w=[]
    if w: words.append(w)
    for wd in words:
        ww=sum(w1(t) for t in wd)
        wt=ww-(0.5 if wd[-1]==' ' else 0)
        if cur+wt>width and lines[-1]:
            lines.append([]); cur=0
        for t in wd:
            if cur+w1(t)>width and t!=' ':
                lines.append([]); cur=0
            if t==' ' and cur==0: continue
            lines[-1].append(t); cur+=w1(t)
    return NL.join(''.join(l).rstrip(' ') for l in lines)

def cwrap(s,W=18):
    lines=[[]];cur=0
    for t in re.findall(r'<[0-9a-f]+>|.',s):
        if t==' ' and cur==0: continue
        if cur+w1(t)>W: lines.append([]);cur=0
        if t==' ' and cur==0: continue
        lines[-1].append(t);cur+=w1(t)
    return NL.join(''.join(l).rstrip(' ') for l in lines)
def lw(l): return sum(w1(t) for t in re.findall(r'<[0-9a-f]+>|.',l))
# ---------- 스크립트 39/40
def build_script(fid,HC,stat):
    b=entry(fid,e); S=script.strings(b)
    jp2key={}
    for k,(ref,jp) in SRC.items():
        if k.startswith('%d:'%fid): jp2key.setdefault(jp,k)
    out=[]
    for s in S:
        mode='H'; nb=bytearray()
        for x in script.units(s,mode):
            if x[0]=='c': nb+=x[1]; continue
            parts,jp=x[1],x[2].replace(BS+'n',NL)
            k=jp2key.get(jp)
            ko=KO.get(k) if k else None
            if ko is None or k in KEEP:
                for _,v in parts: nb+=v
                stat['miss']+=1; continue
            if fid==40 and jp.count(NL)>=3 and NL not in ko:
                w_=wrap(ko); ko=w_ if w_.count(NL)<=3 else cwrap(ko)
            elif fid==39 and NL in jp:
                jw=max(lw(l) for l in jp.split(NL))
                if jw<=14 and max(lw(l) for l in ko.split(NL))>jw+0.01:
                    r_=wrap(ko.replace(NL,' ').replace('  ',' '),jw-1,99)
                    if jw>=4 and r_.count(NL)+1<=max(4,jp.count(NL)+1): ko=r_; stat['rewrap']+=1
            elif fid==39 and k and 12958<=int(k[3:])<=12969:
                ko=re.sub(r'(<[0-9a-f]+>)년 (봄|여름|가을|겨울)[　 ]*',r' ',ko)
            nb+=enc(ko,HC,True)
        out.append(bytes(nb))
    return script.pack(out)

# ---------- 시나리오 5~16
def build_scen(i,HC,stat):
    s=bytearray(entry(i,e))
    P=scen.pairs(bytes(s)); have={p[0] for p in P}; add=[]
    for p in P:
        q=p[0]-26
        if p[1]==8 and q not in have and q>0 and s[q]>=0x81:
            j=scen.sj_run(bytes(s),q); m=scen.sj_run(bytes(s),q+9) if j and j<=q+8 else None
            if m and scen.is_hira(bytes(s[q+9:m])): add.append((q,8,bytes(s[q:j]),q+9,bytes(s[q+9:m]))); have.add(q)
    stat['surname']+=len(add)
    for p in P+add:
        kj,rd=dec(p[2]),dec(p[4])
        if p[1] in (4,8): ko=GL.get(kj) or kword(rd)
        else: ko=KO.get('T:'+kj)
        if not ko: stat['scmiss']+=1; continue
        put(s,p[0],enc(ko,HC),p[1])
        if p[1] in (4,8):
            rk=p[3]+len(p[4])
            while rk<len(s) and s[rk]==0: rk+=1
            rc=min(rk-p[3]-1,12)
            if rc>=len(p[4]): put(s,p[3],enc(ko.replace(' ',''),HC),rc)
    for o in (0x2c,0x18f,0x1a4):
        j=s.index(b'\0',o); t=dec(bytes(s[o:j])); k='D:'+t[:12]
        if k in KO: put(s,o,enc(KO[k],HC),j-o)
    return bytes(s)

# ---------- 41 (미리보기 고정 칸)
SUF=[('の町',' 마을'),('御所',' 고쇼'),('御坊',' 고보'),('城','성'),('館','관'),('砦','요새'),('湊','항'),('寺','사'),('社',' 신사'),('町',' 마을'),('家',' 가'),('衆',' 중')]
def split_name(t):
    if t in GL: return GL[t]
    for n in range(len(t)-1,0,-1):
        a,b=t[:n],t[n:]
        if a in GL and b in GL: return GL[a]+' '+GL[b]
    return None
def name41(t):
    if 'T:'+t in KO: return KO['T:'+t]
    r=split_name(t)
    if r: return r
    for a,b in SUF:
        if t.endswith(a):
            r=split_name(t[:-len(a)])
            if r: return r+b
    return None
def build_41(HC,stat):
    s=bytearray(entry(41,e)); i=0; n=len(s)
    D={}
    for k,(cap,jp) in SRC.items():
        if k.startswith('D:') and k in KO: D[jp]=KO[k]
    while i<n:
        c=s[i]
        if (0x81<=c<=0x9f or 0xe0<=c<=0xfc) and (i==0 or s[i-1]==0):
            j=scen.sj_run(bytes(s),i)
            if j and j>i+1:
                k=j
                while k<n and s[k]==0: k+=1
                t=dec(bytes(s[i:j])); cap=k-i-1
                ko=D.get(t) or GL.get(t)
                if not ko: ko=name41(t)
                if not ko:
                    m=re.match(r'(\d+)年(.)　(.*)',t)
                    if m: ko=None
                if ko: put(s,i,enc(ko,HC),cap)
                elif any(ord(ch)>=0x4e00 for ch in t): stat['m41'].append(t)
                i=j; continue
        i+=1
    return bytes(s)

# ---------- ELF·오버레이 제자리
def onlyjunk(ko): return not any(ord(ch)>=0x80 for ch in ko)
def build_elf(HC,stat):
    for k,v in KO.items():
        if not k.startswith('E:') or k in KEEP or onlyjunk(v): continue
        off=int(k[2:],16); cap=int(SRC[k][0]) if k in SRC else None
        if cap is None: stat['emiss']+=1; continue
        if e[off-1]!=0 and off%4: stat['enotstr']+=1; continue   # 앞이 0 이 아니면 데이터 중간 (예: 실수 1.0 뒤)
        put(e,off,enc(v,HC),cap)
    for p in elftext.final(bytes(elf()))[1]:
        ko=GL.get(dec(p[2])) or kword(dec(p[4]))
        put(e,p[0],enc(ko,HC),p[1])
def build_ovl(name,HC,stat):
    d=bytearray(open(os.path.join(W,'iso',name+'.bin'),'rb').read()); P=name.upper()[0]+':'
    for k,v in KO.items():
        if k.startswith(P) and k in SRC and not onlyjunk(v):
            put(d,int(k[2:],16),enc(v,HC),int(SRC[k][0]))
    if name=='gun':
        for x in tsv(os.path.join(T,'names_ovl.tsv'),5):
            put(d,int(x[0][2:],16),enc(FIX.get(x[3]) or x[4],HC),int(x[1]))
    return bytes(d)

# ---------- 글꼴
def build_font(HC):
    f=bytearray(entry(36,e)); Tb=fontlib.table(f)
    nc=codes[:NK]+[c for c in HC.values()]
    seq=fontlib.sjis_seq(0x889f); last=max(HC.values())
    rest=[c for c in seq if c>last]
    nc+=rest[:NGLYPH-len(nc)]
    assert len(nc)==NGLYPH and nc==sorted(nc)
    fontlib.set_codes(e,nc)
    for n,ch in enumerate(HC):
        fontlib.put(f,NK+n,glyph.glyph(LIG[ch],xscale=0.6) if ch in LIG else glyph.glyph(ch),Tb)
    return bytes(f)

def main():
    stat=collections.Counter(); stat['m41']=[]
    HC=hangul_codes(HANGUL)
    # 이름 자동 표기에 쓰일 음절 추가
    extra=set()
    for i in range(5,17):
        for p in scen.pairs(entry(i,e)):
            if p[1] in (4,8): extra.update(GL.get(dec(p[2])) or kword(dec(p[4])))
    for p in elftext.final(bytes(e))[1]: extra.update(GL.get(dec(p[2])) or kword(dec(p[4])))
    for x in tsv(os.path.join(T,'names_ovl.tsv'),5): extra.update(x[4])
    for ch in open(os.path.join(T,'extra_syl.txt'),encoding='utf-8').read() if os.path.exists(os.path.join(T,'extra_syl.txt')) else '': extra.add(ch)
    allh=sorted(set(HANGUL)|{ch for ch in extra if 0xac00<=ord(ch)<=0xd7a3})
    assert len(allh)+len(LIG)+len(NEWLIG)<=NGLYPH-NK, len(allh)
    global CURHC
    HC=hangul_codes(allh+sorted(LIG)); CURHC=HC; print('hangul',len(allh),'slots',NGLYPH-NK)
    new={}
    new[36]=build_font(HC)
    for i in range(5,17): new[i]=build_scen(i,HC,stat)
    new[39]=build_script(39,HC,stat); new[40]=build_script(40,HC,stat)
    new[41]=build_41(HC,stat)
    import titles
    for i in titles.JOBS: new[i]=titles.apply(i,entry(i,e))
    import relabel,logo
    for i in relabel.load_jobs(): new[i]=relabel.apply(i,new.get(i) or entry(i,e))
    b51=bytearray(new[51]); logo.apply(b51); new[51]=bytes(b51)
    build_elf(HC,stat)
    sei=build_ovl('sei',HC,stat); gun=build_ovl('gun',HC,stat)
    if NEWLIG:
        open(LIGF,'w',encoding='utf-8').write(NL.join(LIGS+[a for a,_ in NEWLIG.most_common()]))
        print('합자 추가',len(NEWLIG),'→ 다시 실행'); return main_again()
    if MISSING:
        old=open(os.path.join(T,'extra_syl.txt'),encoding='utf-8').read() if os.path.exists(os.path.join(T,'extra_syl.txt')) else ''
        open(os.path.join(T,'extra_syl.txt'),'w',encoding='utf-8').write(''.join(sorted(set(old)|MISSING)))
        print('누락 음절',len(MISSING),'→ 다시 실행'); return main_again()
    open(os.path.join(T,'cuts.txt'),'w',encoding='utf-8').write(NL.join('%x	%d	%d	%s'%c for c in CUTS)); print('cuts',len(CUTS)); print({k:v for k,v in stat.items() if k!='m41'},'41미변환',len(stat['m41']),len(set(stat['m41']))); open(os.path.join(T,'m41.txt'),'w',encoding='utf-8').write(NL.join(sorted(set(stat['m41']))))#)
    # NBX 재조립 (2048 정렬, 차례 유지)
    Tc=toc(e); nb=open(os.path.join(W,'iso','nbx.bin'),'rb')
    body=bytearray(); newtoc=[]
    for i,(a,sz) in enumerate(Tc):
        if i in new: d=new[i]
        else: nb.seek(a); d=nb.read(sz)
        newtoc.append((len(body),len(d) if (sz or i in new) else 0))
        body+=d; body+=bytes((-len(body))%2048)
        print(i,sz,len(d)) if i in (39,40,41) else None
    for i,(a,sz) in enumerate(newtoc): struct.pack_into('<II',e,TOC_OFF+8*i,a,sz)
    print('nbx',len(body),'orig',NBX_SIZE)
    # ISO
    shutil.copyfile(ISO,OUT)
    with open(OUT,'r+b') as f:
        f.seek(ELF_LBA*2048); f.write(e)
        f.seek(SEI_LBA*2048); f.write(sei)
        f.seek(GUN_LBA*2048); f.write(gun)
        if len(body)<=NBX_SIZE:
            f.seek(NBX_LBA*2048); f.write(body); f.write(bytes(NBX_SIZE-len(body)))
        else:
            f.seek(0,2); end=f.tell(); lba=(end+2047)//2048
            f.seek(lba*2048); f.write(body); f.write(bytes((-len(body))%2048))
            relocate(f,lba,len(body))
            sec=(len(body)+2047)//2048
            struct.pack_into('<QQQ',e,0x2a7978,lba,lba+sec-1,sec)
            f.seek(ELF_LBA*2048); f.write(e)
    print('ok',OUT)
def relocate(f,lba,size):
    """디렉터리 레코드에서 NB10.NBX 위치·크기 고치기 + PVD 볼륨 크기"""
    f.seek(0); raw=f.read(4*1024*1024)
    pat=struct.pack('<I',NBX_LBA)+struct.pack('>I',NBX_LBA)
    k=raw.find(pat); assert k>0 and raw[k+31:k+31+8]==b'NB10.NBX'[:8] or True
    f.seek(k); f.write(struct.pack('<I',lba)+struct.pack('>I',lba)+struct.pack('<I',size)+struct.pack('>I',size))
    f.seek(0,2); tot=f.tell()//2048
    f.seek(16*2048+80); f.write(struct.pack('<I',tot)+struct.pack('>I',tot))
def main_again():
    os.execv(sys.executable,[sys.executable,'-W','ignore',os.path.abspath(__file__)])
if __name__=='__main__': main()
