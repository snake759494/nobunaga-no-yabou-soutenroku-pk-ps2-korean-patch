"""ELF 문자열 추출: 0x2BC000~0x304000, 사전 쌍(한자 8/16칸 + 읽기)은 따로."""
import sys,os,struct,collections
sys.path.insert(0,os.path.dirname(__file__))
from common import *
import scen,mips
LO,HI=0x2bc000,0x304000
DICT_RANGES=[(0x2c3750,0x2e1600),(0x2e8358,0x2ea920),(0x2f6d60,0x2f70a0),(0x2fa910,0x2fc500),(0x2ffa70,0x301660)]
def in_dict(o): return any(a<=o<b for a,b in DICT_RANGES)
def valid(b):
    try: t=b.decode('cp932')
    except: return None
    if not any(ord(ch)>=0x3000 for ch in t): return None
    if any(ord(ch)<0x20 and ch not in '\n' for ch in t): return None
    return t
def cstr(e,o):
    j=e.index(b'\0',o); return e[o:j]
def ptr_pairs(e):
    """(kanji_off, cap, kanji, kana_off, kana): 데이터의 u32 쌍 (한자 포인터, 히라가나 포인터)"""
    out={}; lo,hi=f2v(LO),f2v(HI)
    for k in range(0x2a0000,len(e)-7,4):
        a,b=struct.unpack_from('<II',e,k)
        if lo<=a<hi and lo<=b<hi and in_dict(v2f(a)) and e[v2f(a)-1]==0 and e[v2f(b)-1]==0:
            ka=cstr(e,v2f(a)); kb=cstr(e,v2f(b))
            if ka and scen.is_hira(kb) and not scen.is_hira(ka) and valid(ka):
                o=v2f(a); k2=o+len(ka)
                while k2<HI and e[k2]==0: k2+=1
                cap=min(k2-o-1,((o+len(ka)+1+7)//8*8)-o-1)
                out.setdefault(o,(o,cap,ka,v2f(b),kb))
    return sorted(out.values())
def refs_all(e):
    ptr=collections.Counter()
    for k in range(0x2a0000,len(e)-3,4):
        v=struct.unpack_from('<I',e,k)[0]
        if f2v(LO)<=v<f2v(HI): ptr[v]+=1
    code=collections.Counter(); regs={}
    for a in range(0x100000,0x100000+0x2a0000,4):
        x=struct.unpack_from('<I',e,v2f(a))[0]
        if x>>26==0xf: regs[(x>>16)&31]=((x&0xffff)<<16,a)
        elif (x>>26) in (9,0x19):
            rs=(x>>21)&31
            if rs in regs and a-regs[rs][1]<80:
                imm=x&0xffff; imm-=0x10000 if imm&0x8000 else 0
                t=(regs[rs][0]+imm)&0xffffffff
                if f2v(LO)<=t<f2v(HI): code[t]+=1
    return ptr,code
def extract(e):
    ptr,code=refs_all(e)
    dict_pairs=ptr_pairs(e)
    dset=set()
    for p in dict_pairs: dset.add(p[0]); dset.add(p[3])
    out=[]; i=LO
    while i<HI:
        if e[i]!=0 and e[i-1]==0 and i not in dset:
            j=e.index(b'\0',i); t=valid(e[i:j])
            if t is not None:
                k=j
                while k<HI and e[k]==0: k+=1
                va=f2v(i); r=ptr[va]+code[va]
                cap_nz=k-i-1
                cap=min(cap_nz,((j+1+7)//8*8)-i-1) if i%4==0 else j-i
                cap=max(cap,j-i)
                out.append(dict(off=i,len=j-i,cap=cap,capnz=cap_nz,ptr=ptr[va],code=code[va],jp=t))
                i=j; continue
        i+=1
    return out,dict_pairs
if __name__=='__main__':
    e=elf(); S,D=extract(e)
    print(len(S),len(D),sum(1 for s in S if s['ptr'] or s['code']))
    with open(os.path.join(W,'trans','elf_src.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
        for s in S: f.write('%x\t%d\t%d\t%d\t%s\n'%(s['off'],s['cap'],s['ptr'],s['code'],s['jp'].replace(chr(10),chr(92)+'n')))
    with open(os.path.join(W,'trans','elf_dict.tsv'),'w',encoding='utf-8',newline=chr(10)) as f:
        for p in D: f.write('%x\t%d\t%s\t%s\n'%(p[0],p[1],p[2].decode('cp932','replace'),p[4].decode('cp932','replace')))

import re as _re
def is_text(t,ref):
    fw=sum(1 for ch in t if ord(ch)>=0x2000 and not (0xff61<=ord(ch)<=0xff9f))
    hk=sum(1 for ch in t if 0xff61<=ord(ch)<=0xff9f)
    asc=[ch for ch in t if ord(ch)<0x80]
    if fw==0: return False
    if ref: return True
    if hk: return False
    if any(ch in ';<=>?@[]^`{|}~' or ord(ch)==0x5c for ch in asc) and fw<3: return False
    if len(t.encode('cp932'))<=3 and asc: return False
    return True
def final(e):
    S,D=extract(e)
    return [s for s in S if is_text(s['jp'],s['ptr'] or s['code'])],D
