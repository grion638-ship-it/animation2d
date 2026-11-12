import asyncio, json, math, os, subprocess, edge_tts

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

async def main():
    timings, lines, t = [], [], 0.0
    for i, txt in enumerate(SEGMENTS):
        raw = f"public/segments/seg_{i:02d}_raw.mp3"
        wav = f"public/segments/seg_{i:02d}.wav"
        if not os.path.exists(wav):
            await edge_tts.Communicate(
                txt, "en-US-AndrewMultilingualNeural", rate="+2%", pitch="-2Hz"
            ).save(raw)
            af_filter = (
                "equalizer=f=180:width_type=o:width=2:g=2.5,"
                "equalizer=f=3500:width_type=o:width=2:g=1.5,"
                "acompressor=threshold=-18dB:ratio=2.5:attack=15:release=120,"
                "apad=pad_dur=0.12"
            )
            subprocess.run(
                ["ffmpeg", "-y", "-i", raw, "-af", af_filter, "-ar", "44100", "-ac", "2", wav],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", wav
        ]).decode().strip())
        timings.append({
            "index": i, "start": round(t, 3),
            "end": round(t + dur, 3), "duration": round(dur, 3)
        })
        t += dur
        lines.append(f"file 'segments/seg_{i:02d}.wav'")
    open("public/concat.txt", "w").write("\n".join(lines))
    if not os.path.exists("public/voce.mp3"):
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "public/concat.txt",
            "-c:a", "libmp3lame", "-b:a", "192k", "public/voce.mp3"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    frames = int(math.ceil(t * 60))
    open("src/timings.ts", "w").write(f"export const TIMINGS = {json.dumps(timings)};\n")
    open("src/Root.tsx", "w").write(
        'import React from "react";\n'
        'import { Composition } from "remotion";\n'
        'import { GroomStory } from "./GroomStory";\n'
        f'export const RemotionRoot: React.FC = () => (<Composition id="GroomStory" component={{GroomStory}} durationInFrames={{{frames}}} fps={{60}} width={{1080}} height={{1920}} />);\n'
    )
    print(f"AUDIO_OK: {frames} frame a 60 FPS")

asyncio.run(main())
