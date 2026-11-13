import struct
ELF='work/iso/elf.bin'
def toc(e=None):
    e=e or open(ELF,'rb').read()
    o=0x2a7460-0x80
    while True:
        a,b=struct.unpack('<II',e[o-8:o])
        if a%2048 or b==0 or b>300000000: break
        o-=8
    st=o; ents=[]
    while True:
        a,b=struct.unpack('<II',e[o:o+8])
        if a%2048 or b==0 or a>251996160: break
        ents.append((a,b)); o+=8
    return st,ents
if __name__=='__main__':
    import collections
    st,ents=toc(); print(hex(st),len(ents),hex(st+8*len(ents)))
    d=open('work/iso/nbx.bin','rb').read()
    c=collections.Counter()
    for i,(a,b) in enumerate(ents):
        m=d[a:a+4]; c[m]+=1
    print(c.most_common(40))
    for i,(a,b) in enumerate(ents[:30]): print(i,a//2048,b,d[a:a+16].hex(' '))
