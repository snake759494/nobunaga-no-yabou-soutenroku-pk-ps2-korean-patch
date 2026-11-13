import sys,re
def runs(d,minc=3):
    i=0;n=len(d);out=[]
    while i<n:
        j=i;c=0
        while j<n-1:
            b=d[j]
            if (0x81<=b<=0x9f or 0xe0<=b<=0xfc) and (0x40<=d[j+1]<=0xfc and d[j+1]!=0x7f): j+=2;c+=1
            elif 0x20<=b<0x7f or b in (0x0a,): j+=1
            elif 0xa1<=b<=0xdf: j+=1
            else: break
        if c>=minc: out.append((i,d[i:j])); i=j
        else: i=max(j,i+1)
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    r=runs(d,int(sys.argv[2]) if len(sys.argv)>2 else 3)
    print(len(r),sum(len(x) for _,x in r))
    for o,s in r[:: max(1,len(r)//int(sys.argv[3] if len(sys.argv)>3 else 40))]:
        print(hex(o),s.decode('cp932','replace')[:60])
