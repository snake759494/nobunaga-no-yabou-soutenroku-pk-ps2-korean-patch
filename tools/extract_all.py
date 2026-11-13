"""모든 번역 원문 추출 → work/trans/
names_auto.tsv : 읽기 기반 자동 이름 (kind, 한자, 읽기, 한글)
glossary.tsv   : 번역자용 용어집 (한자 \t 한글)
src_*.tsv      : 번역 단위 (key \t cap \t jp)
"""
import sys,os,collections,json
sys.path.insert(0,os.path.dirname(__file__))
from common import *
import scen,script,elftext,kana2hangul as K
T=os.path.join(W,'trans'); os.makedirs(T,exist_ok=True)
e=elf(); d=lambda b: b.decode('cp932','replace')
SC=list(range(5,17))
# ---- 시나리오 쌍
cat_of=lambda cap,off: {4:'region',8:'name',10:'post'}.get(cap,'x12')
auto={}; full={}; manual={}   # 한자 → (읽기,한글)
for i in SC:
    s=entry(i,e); P=scen.pairs(s)
    for k,p in enumerate(P):
        kj,rd=d(p[2]),d(p[4])
        if p[1] in (4,8):
            auto.setdefault((kj,rd),K.word(rd))
            if k+1<len(P) and P[k+1][0]-p[0]==26 and P[k+1][1]==8:
                q=P[k+1]; full.setdefault(kj+d(q[2]),(rd+' '+d(q[4]),K.word(rd)+' '+K.word(d(q[4]))))
        else:
            manual.setdefault((kj,rd),p[1])
# ELF 사전
_,D=elftext.final(e)
for p in D: auto.setdefault((d(p[2]),d(p[4])),K.word(d(p[4])))
with open(os.path.join(T,'names_auto.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for (kj,rd),ko in sorted(auto.items()): f.write(f'{kj}\t{rd}\t{ko}\n')
# 용어집: 이름(한자→한글). 같은 한자에 읽기가 여럿이면 첫 것
gl=collections.OrderedDict()
for kj,(rd,ko) in sorted(full.items()): gl.setdefault(kj,ko)
for (kj,rd),ko in sorted(auto.items(),key=lambda x:-len(x[0][0])): gl.setdefault(kj,ko)
with open(os.path.join(T,'glossary_names.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for k,v in gl.items(): f.write(f'{k}\t{v}\n')
with open(os.path.join(T,'src_scen_terms.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for (kj,rd),cap in sorted(manual.items()): f.write(f'T:{kj}\t{cap}\t{kj}（{rd}）\n')
# ---- 시나리오 개요 문장 (헤더 0x2c 이후 / 0x18f 이후)
with open(os.path.join(T,'src_scen_desc.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    seen=set()
    for i in SC:
        s=entry(i,e)
        for o in (0x2c,0x18f,0x1a4):
            j=s.index(b'\0',o); t=d(s[o:j])
            k=j
            while s[k]==0: k+=1
            if t not in seen: seen.add(t); f.write(f'D:{t[:12]}\t{j-o}\t{t}\n')
# ---- ELF / 오버레이
S,_=elftext.final(e)
with open(os.path.join(T,'src_elf.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for x in S:
        t=x['jp']
        if t.endswith('\n') or ('%' in t and ':' in t): continue   # 디버그 출력
        f.write('E:%x\t%d\t%s\n'%(x['off'],x['cap'],t.replace('\n','\n')))
# ---- 39/40
for fid in (39,40):
    S=script.strings(entry(fid,e)); seen=collections.OrderedDict()
    for si,s in enumerate(S):
        for x in script.units(s):
            if x[0]=='u': seen.setdefault(x[2],[]).append(si)
    with open(os.path.join(T,f'src_e{fid}.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
        for n,(jp,L) in enumerate(seen.items()): f.write(f'{fid}:{n}\t{L[0]}\t{jp}\n')
    print(fid,len(seen))
print('auto',len(auto),'full',len(full),'manual',len(manual))
# ---- 오버레이 (파일오프셋 0 = 0x198A000), 디버그 출력 제외
def ovl_strings(d,lo):
    out=[]; i=lo
    while i<len(d):
        if d[i] and d[i-1]==0:
            j=d.find(bytes(1),i)
            if j<0: break
            t=elftext.valid(d[i:j])
            if t and i%4==0 and elftext.is_text(t,False) and not t.endswith('\n') and '%' not in t and '->' not in t and '[' not in t:
                k=j
                while k<len(d) and d[k]==0: k+=1
                cap=min(k-i-1,((j+1+7)//8*8)-i-1) if i%4==0 else j-i
                out.append((i,max(cap,j-i),t)); i=j; continue
        i+=1
    return out
with open(os.path.join(T,'src_ovl.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for n,lo in (('sei',0x1535d0),('gun',0x1261c0)):
        d=open(os.path.join(W,'iso',n+'.bin'),'rb').read()
        for o,cap,t in ovl_strings(d,lo): f.write('%s:%x\t%d\t%s\n'%(n.upper()[0],o,cap,t))
# ---- 오버레이 공주 이름 사전 (8바이트 칸: 한자, 읽기, 한자…)
def slot_dict(d,lo,hi):
    sl=[]
    for o in range(lo,hi,8):
        t=d[o:o+8].split(bytes(1))[0]
        sl.append((o,t))
    res=[]; cur=None
    for k,(o,t) in enumerate(sl):
        if not t: continue
        if scen.is_hira(t): cur=t; continue
        nxt=sl[k+1][1] if k+1<len(sl) else b''
        r=nxt if scen.is_hira(nxt) else cur
        if r and elftext.valid(t): res.append((o,7,t,r))
    return res
GD=slot_dict(open(os.path.join(W,'iso','gun.bin'),'rb').read(),0x12aaa8,0x12c800)
with open(os.path.join(T,'names_ovl.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
    for o,cap,t,r in GD: f.write('G:%x\t%d\t%s\t%s\t%s\n'%(o,cap,t.decode("cp932","replace"),r.decode("cp932","replace"),K.word(r.decode("cp932","replace"))))
gdo=set(o for o,*_ in GD)
L=[l for l in open(os.path.join(T,'src_ovl.tsv'),encoding='utf-8') if not (l.startswith('G:') and int(l.split('\t')[0][2:],16) in gdo)]
open(os.path.join(T,'src_ovl.tsv'),'w',encoding='utf-8',newline=chr(10)).writelines(L)
