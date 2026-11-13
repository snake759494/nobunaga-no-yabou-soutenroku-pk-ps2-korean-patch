import struct,sys,capstone
ELF='work/iso/elf.bin'
E=open(ELF,'rb').read()
def f2v(o): return o-0x800+0x100000
def v2f(v): return v-0x100000+0x800
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS64+capstone.CS_MODE_LITTLE_ENDIAN)
def w(v): return struct.unpack_from('<I',E,v2f(v))[0]
def dis(v,n=40):
    for k in range(n):
        a=v+4*k; x=w(a); r=list(md.disasm(struct.pack('<I',x),a))
        print('%08x %08x  %s'%(a,x,(r[0].mnemonic+' '+r[0].op_str) if r else '?'))
TEXT_END=0x100000+0x3da200
def refs(target):
    """lui/addiu|ori|lw 쌍으로 target 주소 참조 찾기 (간이)"""
    out=[]; hi=(target+0x8000)>>16; lo=target&0xffff
    for a in range(0x100000,0x100000+0x2a0000,4):
        x=w(a)
        if x>>26==0xf and x&0xffff==hi:
            rt=(x>>16)&31
            for b in range(a+4,a+40,4):
                y=w(b); op=y>>26
                if ((y>>21)&31)==rt and (y&0xffff)==lo and op in (9,0xd,0x23,0x24,0x25,0x2b,0x28,0x29,0x20,0x21,0x1e,0x1f,0x37,0x3f,0x31,0x39):
                    out.append(a); break
    return out
def calls(target):
    j=(3<<26)|((target>>2)&0x3ffffff)
    return [a for a in range(0x100000,0x100000+0x2a0000,4) if w(a)==j]
def funcstart(a):
    while a>0x100000:
        x=w(a-4)
        if x==0x03e00008: return a+4 if w(a)==0 else a+4
        a-=4
        y=w(a)
        if (y>>16)==0x27bd and (y&0x8000): return a
    return a
if __name__=='__main__':
    c=sys.argv[1]
    if c=='dis': dis(int(sys.argv[2],16),int(sys.argv[3]) if len(sys.argv)>3 else 40)
    elif c=='refs': print([hex(x) for x in refs(int(sys.argv[2],16))])
    elif c=='calls': print([hex(x) for x in calls(int(sys.argv[2],16))])
    elif c=='fs': print(hex(funcstart(int(sys.argv[2],16))))
