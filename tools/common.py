import os,struct
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W=os.path.join(R,'work')
ISO=os.path.join(R,'Nobunaga no Yabou - Soutenroku with Power-Up Kit (Japan).iso')
ELF_LBA,ELF_SIZE=316,4043264
NBX_LBA,NBX_SIZE=183790,251996160
SEI_LBA,SEI_SIZE=348884,1415168
GUN_LBA,GUN_SIZE=349575,1239040
TOC_OFF=0x2a7370; TOC_N=137
CODES_OFF=0x2a5a60; NGLYPH=3023
def f2v(o): return o-0x800+0x100000
def v2f(v): return v-0x100000+0x800
def rd(p): return open(p,'rb').read()
def elf(): return rd(os.path.join(W,'iso','elf.bin'))
def nbx(): return rd(os.path.join(W,'iso','nbx.bin'))
def toc(e):
    return [struct.unpack_from('<II',e,TOC_OFF+8*i) for i in range(TOC_N)]
def entry(i,e=None,n=None):
    e=e or elf(); a,b=toc(e)[i]
    with open(os.path.join(W,'iso','nbx.bin'),'rb') as f: f.seek(a); return f.read(b)
