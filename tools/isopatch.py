"""ISO 제자리 패치 보조"""
import os,shutil,struct
from common import *
def ensure_copy(dst):
    if not os.path.exists(dst) or os.path.getsize(dst)!=os.path.getsize(ISO):
        shutil.copyfile(ISO,dst)
def write(iso,lba,data,off=0):
    with open(iso,'r+b') as f: f.seek(lba*2048+off); f.write(data)
