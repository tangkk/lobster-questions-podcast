#!/usr/bin/env python3
import argparse
import pathlib
import subprocess
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def fetch(url, retries=20, delay=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "lobster-publish-verifier/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception as e:
            last = e
            if i + 1 < retries:
                time.sleep(delay)
    raise SystemExit(f"Failed to fetch {url}: {last}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--bytes", type=int, required=True)
    p.add_argument("--duration", required=True)
    a = p.parse_args()

    audio = fetch(a.url)
    if len(audio) != a.bytes:
        raise SystemExit(f"Public MP3 size mismatch: {len(audio)} != {a.bytes}")

    with tempfile.TemporaryDirectory() as td:
        mp3 = pathlib.Path(td) / "episode.mp3"
        mp3.write_bytes(audio)
        seconds = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(mp3)
        ], text=True).strip())
        s = round(seconds)
        actual = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
        if actual != a.duration:
            raise SystemExit(f"Public MP3 duration mismatch: {actual} != {a.duration}")

    feed_url = f"https://raw.githubusercontent.com/{a.repo}/main/feed.xml"
    feed = fetch(feed_url)
    root = ET.fromstring(feed)
    channel = root.find("channel")
    if channel is None:
        raise SystemExit("Live RSS channel missing")
    items = [i for i in channel.findall("item") if i.findtext("guid") == a.slug]
    if len(items) != 1:
        raise SystemExit(f"Live RSS expected one GUID {a.slug}, got {len(items)}")
    item = items[0]
    enclosure = item.find("enclosure")
    if enclosure is None:
        raise SystemExit("Live RSS enclosure missing")
    if enclosure.attrib.get("url") != a.url:
        raise SystemExit("Live RSS enclosure URL mismatch")
    if int(enclosure.attrib.get("length", "-1")) != a.bytes:
        raise SystemExit("Live RSS enclosure length mismatch")
    duration = item.findtext(f"{{{ITUNES}}}duration")
    if duration != a.duration:
        raise SystemExit(f"Live RSS duration mismatch: {duration} != {a.duration}")
    print(f"Verified public release: {a.slug}")


if __name__ == "__main__":
    main()
