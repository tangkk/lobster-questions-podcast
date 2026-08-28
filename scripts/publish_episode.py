#!/usr/bin/env python3
import argparse,datetime as dt,os,xml.etree.ElementTree as ET
from email.utils import format_datetime

def client(endpoint):
 import boto3
 from botocore.config import Config
 return boto3.client('s3',endpoint_url=endpoint,aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(s3={'addressing_style':'path'}))
def main():
 ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd'); ET.register_namespace('atom','http://www.w3.org/2005/Atom')
 p=argparse.ArgumentParser(); p.add_argument('--feed',default='feed.xml'); p.add_argument('--audio',required=True); p.add_argument('--slug',required=True); p.add_argument('--title',required=True); p.add_argument('--description',required=True); p.add_argument('--duration',required=True); p.add_argument('--prefix',required=True); a=p.parse_args()
 for v in ['R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY','R2_ENDPOINT','R2_BUCKET','R2_PUBLIC_URL']:
  if not os.environ.get(v): raise SystemExit('Missing '+v)
 t=ET.parse(a.feed); ch=t.getroot().find('channel');
 if any((i.findtext('guid') or '')==a.slug for i in ch.findall('item')): raise SystemExit('GUID already exists')
 key=f"{a.prefix.rstrip('/')}/{a.slug}.mp3"; c=client(os.environ['R2_ENDPOINT'].strip('"'))
 try: c.head_object(Bucket=os.environ['R2_BUCKET'],Key=key); raise SystemExit('R2 object already exists')
 except Exception as e:
  if isinstance(e,SystemExit): raise
  r=getattr(e,'response',{}) or {}; status=r.get('ResponseMetadata',{}).get('HTTPStatusCode'); code=str(r.get('Error',{}).get('Code',''))
  if status!=404 and code not in {'404','NoSuchKey','NotFound'}: raise
 size=os.path.getsize(a.audio); c.upload_file(a.audio,os.environ['R2_BUCKET'],key,ExtraArgs={'ContentType':'audio/mpeg'})
 item=ET.Element('item'); ET.SubElement(item,'title').text=a.title; ET.SubElement(item,'description').text=a.description; ET.SubElement(item,'pubDate').text=format_datetime(dt.datetime.now(dt.timezone.utc)); ET.SubElement(item,'guid',{'isPermaLink':'false'}).text=a.slug; ET.SubElement(item,'enclosure',{'url':os.environ['R2_PUBLIC_URL'].rstrip('/')+'/'+key,'length':str(size),'type':'audio/mpeg'}); ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text=a.duration; ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text='false'
 first=ch.find('item'); ch.insert(list(ch).index(first),item) if first is not None else ch.append(item); lb=ch.find('lastBuildDate');
 if lb is not None: lb.text=format_datetime(dt.datetime.now(dt.timezone.utc))
 t.write(a.feed,encoding='utf-8',xml_declaration=True)
if __name__=='__main__': main()
