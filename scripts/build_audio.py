from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "staging" / "2026-09-24"
FEED = ROOT / "worldview-weekly.xml"
AUDIO = ROOT / "audio" / "current.txt"
ORIGINAL = STAGE / "build_audio_original.py"
GUID = "worldview-2026-09-24-cepr-datacentres-electricity"
BUILD_DATE = "Thu, 24 Sep 2026 17:30:00 GMT"


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def assemble() -> None:
    feed = FEED.read_text(encoding="utf-8")
    if GUID not in feed:
        fragments = "".join(
            p.read_text(encoding="utf-8")
            for p in sorted(STAGE.glob("feed-*.xml"))
        )
        feed = re.sub(
            r"<lastBuildDate>[^<]*</lastBuildDate>",
            f"<lastBuildDate>{BUILD_DATE}</lastBuildDate>",
            feed,
            count=1,
        )
        marker = f"<lastBuildDate>{BUILD_DATE}</lastBuildDate>"
        if marker not in feed:
            raise SystemExit("Could not update worldview-weekly.xml lastBuildDate")
        feed = feed.replace(marker, marker + "\n\n" + fragments, 1)
        if feed.count("worldview-2026-09-24-") != 12:
            raise SystemExit("Expected exactly 12 Sep 24 reading items")
        FEED.write_text(feed, encoding="utf-8")

    audio = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(STAGE.glob("audio-*.txt"))
    )
    expected = (
        "DATE: 2026-09-24\n"
        "TITLE: Worldview Weekly — September 24, 2026\n"
    )
    if not audio.startswith(expected):
        raise SystemExit("Narration header mismatch")
    AUDIO.write_text(audio, encoding="utf-8")


def run_original_builder() -> None:
    source = ORIGINAL.read_text(encoding="utf-8")
    ns = {
        "__name__": "worldview_original_builder",
        "__file__": str(ROOT / "scripts" / "build_audio.py"),
    }
    exec(compile(source, str(ROOT / "scripts" / "build_audio.py"), "exec"), ns)
    ns["main"]()


def finalize_inputs() -> None:
    # Restore the canonical builder and remove all one-run staging material.
    shutil.copyfile(ORIGINAL, ROOT / "scripts" / "build_audio.py")
    shutil.rmtree(STAGE)

    # Validate the two publication surfaces before recording the source commit.
    import xml.etree.ElementTree as ET
    ET.parse(FEED)
    ET.parse(ROOT / "podcast.xml")
    if not (ROOT / "audio" / "episodes" / "2026-09-24.mp3").exists():
        raise SystemExit("Expected Sep 24 MP3 was not generated")
    if "2026-09-24" not in (ROOT / "podcast.xml").read_text(encoding="utf-8"):
        raise SystemExit("Podcast feed missing Sep 24 episode")

    run("git", "config", "user.name", "github-actions[bot]")
    run(
        "git",
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    run(
        "git",
        "add",
        "worldview-weekly.xml",
        "audio/current.txt",
        "scripts/build_audio.py",
        "staging/2026-09-24",
    )
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
    ).returncode
    if status != 0:
        run("git", "commit", "-m", "Publish Worldview Weekly for 2026-09-24")


def main() -> None:
    assemble()
    run_original_builder()
    finalize_inputs()


if __name__ == "__main__":
    main()
