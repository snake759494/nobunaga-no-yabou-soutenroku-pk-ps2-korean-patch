import struct,sys
f=open(sys.argv[1],'rb')
def rd(l,n): f.seek(l*2048); return f.read(n)
pvd=rd(16,2048); root=pvd[156:190]
def walk(lba,size,path):
    d=rd(lba,size);i=0
    while i<len(d):
        L=d[i]
        if L==0: i=(i//2048+1)*2048; continue
        r=d[i:i+L]; el=struct.unpack('<I',r[2:6])[0]; sz=struct.unpack('<I',r[10:14])[0]; fl=r[25]; nl=r[32]; nm=r[33:33+nl]
        if nm not in (b'\0',b'\1'):
            p=path+'/'+nm.decode('latin1')
            print(f'{el:8d} {sz:11d} {p}')
            if fl&2: walk(el,sz,p)
        i+=L
walk(struct.unpack('<I',root[2:6])[0],struct.unpack('<I',root[10:14])[0],'')
