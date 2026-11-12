import asyncio
import json
import math
import os
import subprocess
import edge_tts

os.makedirs("public/segments", exist_ok=True)

SEGMENTS = [
    "Imagine landing the most powerful, highly paid job in the entire kingdom...",
    "but your only actual duty is...",
    "wiping your boss's butt.",
    "Back in Tudor England,",
    "the most coveted role in the royal court wasn't a top general...",
    "or a wealthy banker.",
    "It was the Groom of the Stool—",
    "the guy officially in charge of the King's toilet time.",
    "It sounds like an absolute punishment,",
    "but the richest nobles literally fought each other for this job.",
    "Why?",
    "Because you were locked in a private room with the King every single day.",
    "You became his ultimate confidant.",
    "You knew all his dark secrets,",
    "you knew who he hated,",
    "and you controlled exactly who got to speak with him.",
    "So, while everyone else was outside begging for power,",
    "the guy holding the royal toilet paper was actually secretly running the country."
]

VOICE = "en-US-AndrewMultilingualNeural"

async def build_audio():
    timings = []
    concat_lines = []
    t_cursor = 0.0

    for idx, text in enumerate(SEGMENTS):
        raw_mp3 = f"public/segments/seg_{idx:02d}_raw.mp3"
        clean_wav = f"public/segments/seg_{idx:02d}.wav"

        if not os.path.exists(clean_wav):
            comm = edge_tts.Communicate(text, VOICE, rate="+2%", pitch="-2Hz")
            await comm.save(raw_mp3)
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_mp3,
                "-af", "equalizer=f=180:width_type=o:width=2:g=2.5,equalizer=f=3500:width_type=o:width=2:g=1.5,acompressor=threshold=-18dB:ratio=2.5:attack=15:release=120,apad=pad_dur=0.12",
                "-ar", "44100", "-ac", "2", clean_wav
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", clean_wav
        ]).decode().strip()
        dur = float(out)

        timings.append({
            "index": idx,
            "start": round(t_cursor, 3),
            "end": round(t_cursor + dur, 3),
            "duration": round(dur, 3)
        })
        t_cursor += dur
        concat_lines.append(f"file 'segments/seg_{idx:02d}.wav'")

    with open("public/concat.txt", "w") as f:
        f.write("\n".join(concat_lines))

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "public/concat.txt",
        "-c:a", "libmp3lame", "-b:a", "192k", "public/voce.mp3"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return timings, t_cursor

timings, total_dur = asyncio.run(build_audio())
fps = 60
total_frames = int(math.ceil(total_dur * fps))

with open("src/timings.ts", "w") as f:
    f.write(f"export const TIMINGS = {json.dumps(timings, indent=2)};\n")

with open("src/Root.tsx", "w") as f:
    f.write(f"""import {{ Composition }} from "remotion";
import {{ GroomStory }} from "./GroomStory";

export const RemotionRoot: React.FC = () => {{
  return (
    <Composition
      id="GroomStory"
      component={{GroomStory}}
      durationInFrames={{{total_frames}}}
      fps={{{fps}}}
      width={{1080}}
      height={{1920}}
    />
  );
}};
""")

print(f"✅ Audio e sincronizzazione pronti: {total_dur:.2f}s ({total_frames} frame a 60 FPS)")
