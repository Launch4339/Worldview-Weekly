from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "audio" / "current.txt"
EPISODES = ROOT / "audio" / "episodes"
PODCAST = ROOT / "podcast.xml"
VOICE = os.environ.get("KOKORO_VOICE", "af_heart")
SPEED = float(os.environ.get("KOKORO_SPEED", "1.0"))
BASE = "https://raw.githubusercontent.com/Launch4339/Worldview-Weekly/main"


def parse_script(text: str):
    date_m = re.search(r"^DATE:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M)
    title_m = re.search(r"^TITLE:\s*(.+?)\s*$", text, re.M)
    if not date_m:
        raise SystemExit("audio/current.txt must contain DATE: YYYY-MM-DD")
    date = date_m.group(1)
    title = title_m.group(1).strip() if title_m else f"Worldview Weekly — {date}"
    body = re.sub(r"^(DATE|TITLE):.*$", "", text, flags=re.M).strip()
    if not body:
        raise SystemExit("audio/current.txt contains no narration body")
    return date, title, body


def synthesize(text: str, wav_path: Path):
    pipeline = KPipeline(lang_code="a")
    chunks = []
    silence = np.zeros(int(24000 * 0.35), dtype=np.float32)
    for _gs, _ps, audio in pipeline(text, voice=VOICE, speed=SPEED, split_pattern=r"\n+"):
        if audio is None:
            continue
        chunks.append(np.asarray(audio, dtype=np.float32))
        chunks.append(silence)
    if not chunks:
        raise SystemExit("Kokoro produced no audio")
    merged = np.concatenate(chunks)
    sf.write(wav_path, merged, 24000, subtype="PCM_16")


def make_mp3(wav_path: Path, mp3_path: Path):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
        "-ar", "24000", "-ac", "1", "-b:a", "64k", str(mp3_path)
    ], check=True)


def build_feed(current_date: str, current_title: str, description: str):
    files = sorted(EPISODES.glob("*.mp3"), reverse=True)
    for old in files[8:]:
        old.unlink()
    files = files[:8]

    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for f in files:
        date = f.stem
        try:
            dt = datetime.strptime(date, "%Y-%m-%d").replace(hour=17, tzinfo=timezone.utc)
            pub = format_datetime(dt)
        except ValueError:
            pub = now
        title = current_title if date == current_date else f"Worldview Weekly — {date}"
        desc = description if date == current_date else "A previous Worldview Weekly audio edition."
        url = f"{BASE}/audio/episodes/{f.name}"
        items.append(f"""    <item>\n      <title>{escape(title)}</title>\n      <description>{escape(desc)}</description>\n      <pubDate>{pub}</pubDate>\n      <guid isPermaLink=\"false\">worldview-weekly-{date}</guid>\n      <enclosure url=\"{escape(url)}\" length=\"{f.stat().st_size}\" type=\"audio/mpeg\" />\n    </item>""")

    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\" xmlns:itunes=\"http://www.itunes.com/dtds/podcast-1.0.dtd\">\n  <channel>\n    <title>Worldview Weekly Audio</title>\n    <link>https://github.com/Launch4339/Worldview-Weekly</link>\n    <description>A low-noise weekly global counterweight to The Economist, synthesized for listening.</description>\n    <language>en-us</language>\n    <itunes:author>Worldview Weekly</itunes:author>\n    <itunes:explicit>false</itunes:explicit>\n    <lastBuildDate>{now}</lastBuildDate>\n{chr(10).join(items)}\n  </channel>\n</rss>\n"""
    PODCAST.write_text(xml, encoding="utf-8")


def main():
    text = SCRIPT.read_text(encoding="utf-8")
    date, title, body = parse_script(text)
    EPISODES.mkdir(parents=True, exist_ok=True)
    mp3 = EPISODES / f"{date}.mp3"
    if not mp3.exists():
        wav = EPISODES / f"{date}.wav"
        synthesize(body, wav)
        make_mp3(wav, mp3)
        wav.unlink(missing_ok=True)
    clean = re.sub(r"\s+", " ", body)
    desc = clean[:700] + ("…" if len(clean) > 700 else "")
    build_feed(date, title, desc)


if __name__ == "__main__":
    main()
