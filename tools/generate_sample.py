import asyncio
import os
import re
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import qrcode


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "audio"
SEGMENTS = ROOT / "build" / "segments"

TRACK_NAME = "U01_Section-A_1b_The-Changing-World"

TURNS = [
    (
        "Li Rui",
        "zh-CN-YunxiNeural",
        "Hello, George.",
        "-4%",
        "+1Hz",
    ),
    (
        "George",
        "en-US-BrianNeural",
        "Hi, Li Rui. Guess what? My father, Bob, and I are going to visit your hometown. "
        "Could you be our guide?",
        "-5%",
        "+0Hz",
    ),
    (
        "Li Rui",
        "zh-CN-YunxiNeural",
        "Sure! I'd love to!",
        "-4%",
        "+1Hz",
    ),
    (
        "George",
        "en-US-BrianNeural",
        "Wonderful! You know, my father's last visit was about twenty years ago. "
        "He became a good friend of your grandfather.",
        "-5%",
        "+0Hz",
    ),
    (
        "Li Rui",
        "zh-CN-YunxiNeural",
        "Grandpa will be so happy. They haven't seen each other for ages!",
        "-4%",
        "+1Hz",
    ),
    (
        "George",
        "en-US-BrianNeural",
        "Yes, and my father really wants to see how the place has changed since he last visited.",
        "-5%",
        "+0Hz",
    ),
]


async def synthesize_turn(index, voice, text, rate, pitch):
    target = SEGMENTS / f"{index:02d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(target))
    return target


async def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    SEGMENTS.mkdir(parents=True, exist_ok=True)

    paths = []
    for index, (_, voice, text, rate, pitch) in enumerate(TURNS, start=1):
        paths.append(await synthesize_turn(index, voice, text, rate, pitch))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    silence_specs = {
        "start": 0.70,
        "turn": 0.56,
        "end": 0.90,
    }
    silence_paths = {}
    for name, duration in silence_specs.items():
        target = SEGMENTS / f"silence-{name}.mp3"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                str(duration),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "96k",
                str(target),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        silence_paths[name] = target

    ordered = [silence_paths["start"]]
    for index, path in enumerate(paths):
        ordered.append(path)
        if index < len(paths) - 1:
            ordered.append(silence_paths["turn"])
    ordered.append(silence_paths["end"])

    concat_file = SEGMENTS / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in ordered),
        encoding="utf-8",
    )
    mp3_path = OUTPUT / f"{TRACK_NAME}.mp3"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "96k",
            "-metadata",
            "title=Unit 1 Section A 1b - The Changing World",
            "-metadata",
            "album=Grade 9 English Listening",
            "-metadata",
            "artist=Li Rui and George",
            str(mp3_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    public_url = os.environ.get("PUBLIC_URL")
    if public_url:
        qr_dir = ROOT / "deliverables"
        qr_dir.mkdir(parents=True, exist_ok=True)
        site_qr_dir = ROOT / "docs" / "assets" / "images"
        site_qr_dir.mkdir(parents=True, exist_ok=True)
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=4)
        qr.add_data(public_url)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="#10233f", back_color="white")
        qr_image.save(qr_dir / f"{TRACK_NAME}_QR.png")
        qr_image.save(site_qr_dir / f"{TRACK_NAME}_QR.png")

    probe = subprocess.run(
        [ffmpeg, "-i", str(mp3_path)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    duration = re.search(r"Duration: ([0-9:.]+)", probe.stderr)
    print(f"Generated: {mp3_path}")
    print(f"Duration: {duration.group(1) if duration else 'unknown'}")


if __name__ == "__main__":
    asyncio.run(main())
