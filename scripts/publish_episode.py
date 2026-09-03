#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import xml.etree.ElementTree as ET
from email.utils import format_datetime

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"


def client(endpoint):
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(s3={"addressing_style": "path"}),
    )


def set_text(parent, tag, text, attrs=None):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag, attrs or {})
    elif attrs:
        node.attrib.clear()
        node.attrib.update(attrs)
    node.text = text
    return node


def upsert_episode(feed, url, size, slug, title, description, duration):
    tree = ET.parse(feed)
    channel = tree.getroot().find("channel")
    if channel is None:
        raise SystemExit("RSS channel missing")
    matches = [i for i in channel.findall("item") if i.findtext("guid") == slug]
    if len(matches) > 1:
        raise SystemExit(f"Duplicate RSS GUID already present: {slug}")

    now = dt.datetime.now(dt.timezone.utc)
    if matches:
        item = matches[0]
    else:
        item = ET.Element("item")
        first = channel.find("item")
        channel.insert(list(channel).index(first), item) if first is not None else channel.append(item)
        set_text(item, "pubDate", format_datetime(now))

    set_text(item, "title", title)
    set_text(item, "description", description)
    if item.find("pubDate") is None:
        set_text(item, "pubDate", format_datetime(now))
    set_text(item, "guid", slug, {"isPermaLink": "false"})
    set_text(item, "enclosure", None, {"url": url, "length": str(size), "type": "audio/mpeg"})
    set_text(item, f"{{{ITUNES}}}duration", duration)
    set_text(item, f"{{{ITUNES}}}episodeType", "full")
    set_text(item, f"{{{ITUNES}}}explicit", "false")
    set_text(channel, "lastBuildDate", format_datetime(now))
    tree.write(feed, encoding="utf-8", xml_declaration=True)


def main():
    ET.register_namespace("itunes", ITUNES)
    ET.register_namespace("atom", ATOM)
    p = argparse.ArgumentParser()
    p.add_argument("--feed", default="feed.xml")
    p.add_argument("--audio", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--duration", required=True)
    p.add_argument("--prefix", required=True)
    a = p.parse_args()

    for v in ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT", "R2_BUCKET", "R2_PUBLIC_URL"]:
        if not os.environ.get(v):
            raise SystemExit("Missing " + v)
    if not os.path.isfile(a.audio) or os.path.getsize(a.audio) <= 0:
        raise SystemExit("Audio missing or empty")

    key = f"{a.prefix.rstrip('/')}/{a.slug}.mp3"
    url = f"{os.environ['R2_PUBLIC_URL'].rstrip('/')}/{key}"
    size = os.path.getsize(a.audio)
    c = client(os.environ["R2_ENDPOINT"].strip('"'))
    # Canonical key is intentionally replaceable so reruns are safe and idempotent.
    c.upload_file(a.audio, os.environ["R2_BUCKET"], key, ExtraArgs={"ContentType": "audio/mpeg"})
    upsert_episode(a.feed, url, size, a.slug, a.title, a.description, a.duration)
    print(url)


if __name__ == "__main__":
    main()
