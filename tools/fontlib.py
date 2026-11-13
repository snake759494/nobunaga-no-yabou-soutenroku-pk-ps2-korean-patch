"""글꼴(NBX 36번): u32 (오프셋,크기)×3036 표 + 글리프마다 N9GD/TIM2 384B, 픽셀 0x70부터 24x22 4bpp(하위 니블 = 왼쪽).
코드표: ELF 0x2A5A60 u16 정렬 3,023개, 글리프 번호 = 코드표 첨자."""
import struct,numpy as np
from common import CODES_OFF,NGLYPH
GW,GH,PIX=24,22,0x70
def table(b): return [struct.unpack_from('<II',b,8*i) for i in range(3036)]
def get(b,i):
    o=table(b)[i][0]; a=np.frombuffer(b[o+PIX:o+PIX+GW*GH//2],np.uint8)
    return np.stack([a&15,a>>4],1).reshape(GH,GW)
def put(b,i,g,T=None):
    T=T or table(b); o=T[i][0]; lin=np.asarray(g,np.uint8).reshape(-1)
    b[o+PIX:o+PIX+GW*GH//2]=(lin[0::2]|(lin[1::2]<<4)).astype(np.uint8).tobytes()
def codes(e): return list(struct.unpack_from('<%dH'%NGLYPH,e,CODES_OFF))
def set_codes(e,c): struct.pack_into('<%dH'%NGLYPH,e,CODES_OFF,*c)
def sjis_seq(start=0x889F):
    for hi in list(range(0x88,0xA0))+list(range(0xE0,0xFD)):
        for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
            c=hi<<8|lo
            if c>=start: yield c
