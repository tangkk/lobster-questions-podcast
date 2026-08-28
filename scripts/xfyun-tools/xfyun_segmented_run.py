#!/usr/bin/env python3
import argparse,os,re,subprocess,tempfile
from xfyun_super_official_run import load_profile,run_once
SENTENCE=re.compile(r'(?<=[。！？!?])')
def split_text(text,max_chars=420):
 out=[]
 for p in [x.strip() for x in re.split(r'\n\s*\n+',text.strip()) if x.strip()]:
  if len(p)<=max_chars: out.append(p); continue
  buf=''
  for s in [x.strip() for x in SENTENCE.split(p) if x.strip()]:
   if buf and len(buf)+len(s)>max_chars: out.append(buf); buf=s
   else: buf+=s
  if buf: out.append(buf)
 return out
def main():
 a=argparse.ArgumentParser(); a.add_argument('--text-file',required=True); a.add_argument('--out',required=True); a.add_argument('--profile',default='default'); a.add_argument('--pause-ms',type=int,default=350); a.add_argument('--max-chars',type=int,default=420); x=a.parse_args(); p=load_profile(x.profile); segs=split_text(open(x.text_file,encoding='utf-8').read(),x.max_chars); os.makedirs(os.path.dirname(x.out) or '.',exist_ok=True)
 with tempfile.TemporaryDirectory() as d:
  parts=[]
  for i,s in enumerate(segs): path=os.path.join(d,f'{i:03d}.mp3'); run_once(p.get('ws_url','wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'),path,p.get('voice','x6_lingyuyan_pro'),s,p.get('speed',50),p.get('volume',52),p.get('pitch',50)); parts.append(path)
  sil=os.path.join(d,'silence.mp3'); subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t',str(x.pause_ms/1000),'-q:a','9',sil],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); lst=os.path.join(d,'concat.txt')
  with open(lst,'w') as f:
   for i,z in enumerate(parts): f.write("file '%s'\n"%z); f.write("file '%s'\n"%sil) if i<len(parts)-1 else None
  subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',lst,'-c:a','libmp3lame','-ar','24000','-ac','1',x.out],check=True)
if __name__=='__main__': main()
