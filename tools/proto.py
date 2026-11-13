import sys,os; sys.path.insert(0,os.path.dirname(__file__))
from common import *; import fontlib,glyph,isopatch,struct
e=bytearray(elf()); T=toc(e); b=bytearray(entry(36,e))
menu={0x2c2ea0:'이전 기록에서 시작한다',0x2c2ec0:'새로 게임을 시작한다',0x2c2ee0:'직접 무장을 작성한다',0x2c2f00:'게임 설명을 본다'}
chars=sorted(set(''.join(menu.values()))-{' '})
cl=fontlib.codes(e); k0=cl.index(0x889F); seq=fontlib.sjis_seq(); enc={}
for i,ch in enumerate(chars):
    c=next(seq); cl[k0+i]=c; enc[ch]=c; fontlib.put(b,k0+i,glyph.glyph(ch))
# 나머지 슬롯 코드도 정렬 유지(남은 슬롯 = 이후 코드)
for j in range(k0+len(chars),len(cl)): cl[j]=next(seq)
fontlib.set_codes(e,cl)
for o,s in menu.items():
    bs=b''.join(struct.pack('>H',enc[ch]) if ch!=' ' else b' ' for ch in s)+b'\0'
    n=len(e[o:o+64].split(b'\0')[0]); cap=n
    while e[o+cap]==0 and cap<64: cap+=1
    assert len(bs)<=cap,(s,len(bs),cap); e[o:o+len(bs)]=bs; e[o+len(bs):o+cap]=bytes(cap-len(bs))
iso=os.path.join(W,'build.iso'); isopatch.ensure_copy(iso)
isopatch.write(iso,ELF_LBA,bytes(e)); isopatch.write(iso,NBX_LBA,bytes(b),T[36][0]); print('ok',len(chars))
