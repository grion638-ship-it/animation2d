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

async def prep_audio():
    timings, concat_lines, t = [], [], 0.0
    for i, txt in enumerate(SEGMENTS):
        raw, wav = f"public/segments/seg_{i:02d}_raw.mp3", f"public/segments/seg_{i:02d}.wav"
        if not os.path.exists(wav):
            await edge_tts.Communicate(txt, "en-US-AndrewMultilingualNeural", rate="+2%", pitch="-2Hz").save(raw)
            subprocess.run([
                "ffmpeg", "-y", "-i", raw,
                "-af", "equalizer=f=180:width_type=o:width=2:g=2.5,equalizer=f=3500:width_type=o:width=2:g=1.5,acompressor=threshold=-18dB:ratio=2.5:attack=15:release=120,apad=pad_dur=0.12",
                "-ar", "44100", "-ac", "2", wav
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", wav
        ]).decode().strip())
        timings.append({"index": i, "start": round(t, 3), "end": round(t + dur, 3), "duration": round(dur, 3)})
        t += dur
        concat_lines.append(f"file 'segments/seg_{i:02d}.wav'")
    open("public/concat.txt", "w").write("\n".join(concat_lines))
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "public/concat.txt",
        "-c:a", "libmp3lame", "-b:a", "192k", "public/voce.mp3"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return timings, t

timings, total_dur = asyncio.run(prep_audio())
fps = 60
total_frames = int(math.ceil(total_dur * fps))

open("src/Root.tsx", "w").write(f'''import React from "react";
import {{ Composition }} from "remotion";
import {{ GroomStory }} from "./GroomStory";

export const RemotionRoot: React.FC = () => (
  <Composition id="GroomStory" component={{GroomStory}} durationInFrames={{{total_frames}}} fps={{{fps}}} width={{1080}} height={{1920}} />
);
''')

tsx = """import React from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

const TIMINGS = __TIMINGS__;

const Dust = ({ color = "#fde047" }: { color?: string }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 18 }}>
      {Array.from({ length: 28 }).map((_, i) => {
        const x = ((i * 97) + Math.sin(frame * 0.02 + i) * 55 + frame * (0.3 + (i % 3) * 0.15)) % 1080;
        const y = ((i * 131) - frame * (0.5 + (i % 4) * 0.2) + 19200) % 1920;
        const s = 4 + (i % 5) * 2.2;
        return (
          <div key={i} style={{
            position: "absolute", left: x, top: y, width: s, height: s, borderRadius: "50%",
            backgroundColor: color, opacity: 0.28 + 0.42 * Math.abs(Math.sin(frame * 0.04 + i)),
            boxShadow: `0 0 ${s * 2}px ${color}`
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

const Sconce = ({ x, y, scale = 1 }: { x: number; y: number; scale?: number }) => {
  const frame = useCurrentFrame();
  const f = Math.sin(frame * 0.34 + x) * 0.12 + Math.cos(frame * 0.21) * 0.08;
  const sw = Math.sin(frame * 0.19 + x) * 6;
  const sp1 = (frame * 3.2 + x) % 90;
  const sp2 = (frame * 2.4 + x + 45) % 90;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `scale(${scale})` }}>
      <div style={{
        position: "absolute", left: -180, top: -200, width: 420, height: 420, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(251,146,60,0.44) 0%, rgba(234,88,12,0.14) 45%, transparent 72%)",
        transform: `scale(${1 + f * 0.45})`
      }} />
      <svg width="100" height="210" viewBox="0 0 100 210" style={{ overflow: "visible" }}>
        <rect x="30" y="105" width="40" height="75" rx="6" fill="#1e293b" stroke="#09090b" strokeWidth="6" />
        <polygon points="28,95 72,95 58,155 42,155" fill="#475569" stroke="#09090b" strokeWidth="7" />
        <rect x="22" y="84" width="56" height="14" rx="5" fill="#eab308" stroke="#09090b" strokeWidth="6" />
        <g transform={`translate(50,84) scale(1,${1 + f}) translate(-50,-84)`}>
          <path d={`M ${50 + sw} 5 C 82 40, 80 78, 50 90 C 20 78, 18 40, ${50 + sw} 5 Z`} fill="#ea580c" stroke="#09090b" strokeWidth="6" />
          <path d={`M ${50 + sw * 0.6} 22 C 70 48, 68 74, 50 84 C 32 74, 30 48, ${50 + sw * 0.6} 22 Z`} fill="#facc15" />
          <ellipse cx="50" cy="68" rx="9" ry="14" fill="#ffffff" opacity="0.85" />
        </g>
        <circle cx={42 + Math.sin(frame * 0.2) * 10} cy={75 - sp1} r={3.5 * (1 - sp1 / 90)} fill="#fde047" />
        <circle cx={58 + Math.cos(frame * 0.25) * 10} cy={75 - sp2} r={3 * (1 - sp2 / 90)} fill="#fb923c" />
      </svg>
    </div>
  );
};

const Guard = ({ x, y, flip = false }: { x: number; y: number; flip?: boolean }) => {
  const frame = useCurrentFrame();
  const br = Math.sin(frame * 0.06 + x) * 2.2;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%,-100%) scale(0.66) scaleX(${flip ? -1 : 1})`, width: 260, height: 520 }}>
      <svg viewBox="0 0 260 520" width="100%" height="100%" style={{ overflow: "visible" }}>
        <ellipse cx="130" cy="495" rx="65" ry="14" fill="rgba(0,0,0,0.4)" />
        <line x1="110" y1="340" x2="108" y2="490" stroke="#09090b" strokeWidth="14" strokeLinecap="round" />
        <line x1="150" y1="340" x2="152" y2="490" stroke="#09090b" strokeWidth="14" strokeLinecap="round" />
        <ellipse cx="100" cy="493" rx="20" ry="9" fill="#1e293b" stroke="#09090b" strokeWidth="5" />
        <ellipse cx="160" cy="493" rx="20" ry="9" fill="#1e293b" stroke="#09090b" strokeWidth="5" />
        <g transform={`translate(0,${-br})`}>
          <path d="M 80 200 L 180 200 L 190 350 L 70 350 Z" fill="#7f1d1d" stroke="#09090b" strokeWidth="9" />
          <rect x="118" y="200" width="24" height="150" fill="#eab308" stroke="#09090b" strokeWidth="5" />
          <circle cx="130" cy="125" r="62" fill="#e2e8f0" stroke="#09090b" strokeWidth="9" />
          <path d="M 62 120 C 65 40, 195 40, 198 120 Z" fill="#475569" stroke="#09090b" strokeWidth="9" />
          <rect x="52" y="112" width="156" height="14" rx="6" fill="#64748b" stroke="#09090b" strokeWidth="6" />
          <g transform={`translate(200,260) rotate(${Math.sin(frame * 0.04 + x) * 1.5})`}>
            <line x1="0" y1="-240" x2="0" y2="230" stroke="#78350f" strokeWidth="10" />
            <path d="M 0 -240 L 0 -150 L 48 -195 Z" fill="#cbd5e1" stroke="#09090b" strokeWidth="7" />
          </g>
        </g>
      </svg>
    </div>
  );
};

const Actor = ({
  role, emotion, x = 0, y = 0, scale = 1, flip = false, walk = false,
  lookX = 0, lookY = 0, lArm = 22, rArm = -22, propR = "none", propL = "none"
}: {
  role: "king" | "groom" | "general" | "banker" | "noble1" | "noble2";
  emotion: "confident" | "proud" | "nervous" | "shocked" | "furious" | "scheming" | "whisper" | "pleading" | "rejected";
  x?: number; y?: number; scale?: number; flip?: boolean; walk?: boolean;
  lookX?: number; lookY?: number; lArm?: number; rArm?: number; propR?: string; propL?: string;
}) => {
  const frame = useCurrentFrame();
  const ws = 0.22;

  const getLeg = (isL: boolean) => {
    const hx = isL ? 210 : 270;
    if (!walk) return { hx, hy: 492, kx: hx + (isL ? -4 : 4), ky: 596, ax: hx + (isL ? -7 : 7), ay: 700, fd: 0 };
    const ph = frame * ws + (isL ? 0 : Math.PI);
    const hy = 492 - Math.abs(Math.cos(frame * ws)) * 8;
    const tr = Math.sin(ph) * 0.42;
    const cr = tr - Math.max(0.05, -Math.cos(ph) * 0.52 + 0.34);
    const kx = hx + Math.sin(tr) * 104;
    const ky = hy + Math.cos(tr) * 104;
    const ax = kx + Math.sin(cr) * 104;
    const ay = Math.min(700, ky + Math.cos(cr) * 104);
    return { hx, hy, kx, ky, ax, ay, fd: (cr * 180) / Math.PI * 0.45 };
  };

  const ll = getLeg(true), rl = getLeg(false);
  const breathY = walk ? -Math.abs(Math.cos(frame * ws)) * 6 : Math.sin(frame * 0.065 + x) * 1.8;
  const tilt = Math.sin(frame * 0.045 + x * 0.3) * 1.8;
  const blink = (frame + Math.abs(Math.round(x))) % 180 > 174;
  const swing = walk ? Math.sin(frame * ws) * 24 : 0;

  const pal: Record<string, { t: string; c: string; tr: string; s: string; h: string }> = {
    king: { t: "#881337", c: "#7f1d1d", tr: "#facc15", s: "#9f1239", h: "#fef2f2" },
    groom: { t: "#1e3a8a", c: "#1e40af", tr: "#eab308", s: "#2563eb", h: "#1e293b" },
    general: { t: "#475569", c: "#991b1b", tr: "#cbd5e1", s: "#64748b", h: "#0f172a" },
    banker: { t: "#064e3b", c: "#065f46", tr: "#f59e0b", s: "#047857", h: "#1c1917" },
    noble1: { t: "#581c87", c: "#6b21a8", tr: "#fde047", s: "#7e22ce", h: "#1e1b4b" },
    noble2: { t: "#7c2d12", c: "#9a3412", tr: "#fbbf24", s: "#b45309", h: "#27272a" },
  };
  const c = pal[role];

  return (
    <div style={{
      position: "absolute", left: `calc(50% + ${x}px)`, top: `calc(54% + ${y}px)`,
      transform: `translate(-50%,-50%) scale(${scale}) scaleX(${flip ? -1 : 1})`,
      width: 480, height: 820, zIndex: 12
    }}>
      <svg viewBox="0 0 480 820" width="100%" height="100%" style={{ overflow: "visible" }}>
        <ellipse cx="240" cy="714" rx="108" ry="20" fill="rgba(0,0,0,0.45)" />
        {(role === "king" || role === "general" || role === "noble1") && (
          <g transform={`translate(0,${breathY})`}>
            <path d="M 118 280 L 68 655 C 145 685, 335 685, 412 655 L 362 280 Z" fill={c.c} stroke="#09090b" strokeWidth="11" />
            <path d="M 145 310 L 115 645 M 335 310 L 365 645" stroke="rgba(0,0,0,0.28)" strokeWidth="8" strokeLinecap="round" />
          </g>
        )}
        {[ll, rl].map((lg, idx) => (
          <g key={idx}>
            <line x1={lg.hx} y1={lg.hy} x2={lg.kx} y2={lg.ky} stroke={c.h} strokeWidth="22" strokeLinecap="round" />
            <line x1={lg.hx} y1={lg.hy} x2={lg.kx} y2={lg.ky} stroke="#09090b" strokeWidth="16" strokeLinecap="round" />
            <circle cx={lg.kx} cy={lg.ky} r="10" fill="#1e293b" stroke="#09090b" strokeWidth="5" />
            <line x1={lg.kx} y1={lg.ky} x2={lg.ax} y2={lg.ay} stroke="#09090b" strokeWidth="15" strokeLinecap="round" />
            <g transform={`translate(${lg.ax},${lg.ay}) rotate(${lg.fd})`}>
              <path d={idx === 0 ? "M -34 10 C -36 -6,-8 -10,14 -4 L 18 14 L -32 14 Z" : "M -14 -4 C 8 -10,36 -6,34 10 L 32 14 L -18 14 Z"} fill="#1c1917" stroke="#09090b" strokeWidth="6" />
              <rect x={idx === 0 ? -14 : -2} y="-3" width="14" height="9" rx="2" fill="#eab308" stroke="#09090b" strokeWidth="3.5" />
            </g>
          </g>
        ))}

        <g transform={`translate(0,${breathY})`}>
          <g transform={`translate(138,308) rotate(${lArm + swing})`}>
            <ellipse cx="0" cy="10" rx="30" ry="26" fill={c.s} stroke="#09090b" strokeWidth="9" />
            <path d="M -12 -6 L -12 24 M 8 -6 L 8 24" stroke={c.tr} strokeWidth="5" strokeLinecap="round" />
            <line x1="0" y1="22" x2="-18" y2="92" stroke={c.s} strokeWidth="24" strokeLinecap="round" />
            <line x1="0" y1="22" x2="-18" y2="92" stroke="#09090b" strokeWidth="15" strokeLinecap="round" />
            <g transform="translate(-18,92) rotate(18)">
              <circle cx="0" cy="0" r="9" fill="#09090b" />
              <line x1="0" y1="0" x2="-14" y2="68" stroke="#09090b" strokeWidth="14" strokeLinecap="round" />
              <g transform="translate(-14,68)">
                <circle cx="0" cy="0" r="15" fill="#f8fafc" stroke="#09090b" strokeWidth="7" />
                {propL === "shield" && (
                  <g transform="translate(-52,-35)">
                    <path d="M 0 0 L 104 0 L 104 85 C 104 142,52 175,52 175 C 52 175,0 142,0 85 Z" fill="#eab308" stroke="#09090b" strokeWidth="10" />
                    <path d="M 16 16 L 88 16 L 88 80 C 88 120,52 148,52 148 C 52 148,16 120,16 80 Z" fill="#991b1b" stroke="#09090b" strokeWidth="6" />
                    <polygon points="52,42 68,78 52,114 36,78" fill="#fde047" stroke="#09090b" strokeWidth="4" />
                  </g>
                )}
                {propL === "goldbag" && (
                  <g transform="translate(-42,8)">
                    <path d="M 24 0 L 58 0 L 78 55 C 88 92,-6 92,4 55 Z" fill="#eab308" stroke="#09090b" strokeWidth="8" />
                    <circle cx="41" cy="54" r="16" fill="#fef08a" stroke="#09090b" strokeWidth="5" />
                  </g>
                )}
              </g>
            </g>
          </g>

          <path d="M 134 292 C 134 248,346 248,346 292 L 362 512 C 362 532,118 532,118 512 Z" fill={c.t} stroke="#09090b" strokeWidth="12" />
          <path d="M 285 268 L 308 524 L 356 514 L 340 288 Z" fill="rgba(0,0,0,0.28)" />
          <path d="M 168 355 Q 175 435 162 515 M 312 355 Q 305 435 318 515" stroke="rgba(0,0,0,0.22)" strokeWidth="6" fill="none" strokeLinecap="round" />

          {role === "king" && (
            <g>
              <polygon points="195,280 285,280 296,522 184,522" fill="#eab308" stroke="#09090b" strokeWidth="8" />
              {[345, 395, 445].map((gy) => <polygon key={gy} points={`240,${gy - 14} 254,${gy} 240,${gy + 14} 226,${gy}`} fill="#dc2626" stroke="#09090b" strokeWidth="4" />)}
              <path d="M 122 276 Q 240 338 358 276 L 368 344 Q 240 396 112 344 Z" fill="#ffffff" stroke="#09090b" strokeWidth="10" />
              {[155, 195, 240, 285, 325].map((ex) => <ellipse key={ex} cx={ex} cy="322" rx="4" ry="7" fill="#09090b" />)}
              <rect x="122" y="462" width="236" height="26" rx="6" fill="#facc15" stroke="#09090b" strokeWidth="8" />
            </g>
          )}
          {role === "groom" && (
            <g>
              <polygon points="192,268 288,268 240,332" fill="#f8fafc" stroke="#09090b" strokeWidth="8" />
              <line x1="240" y1="332" x2="240" y2="522" stroke="#eab308" strokeWidth="8" />
              <line x1="182" y1="292" x2="168" y2="518" stroke="#eab308" strokeWidth="6" />
              <line x1="298" y1="292" x2="312" y2="518" stroke="#eab308" strokeWidth="6" />
              <rect x="122" y="458" width="236" height="26" rx="5" fill="#451a03" stroke="#09090b" strokeWidth="8" />
              <rect x="218" y="452" width="44" height="38" rx="6" fill="#eab308" stroke="#09090b" strokeWidth="6" />
            </g>
          )}
          {role === "general" && (
            <g>
              <path d="M 142 282 L 338 282 L 320 472 L 240 508 L 160 472 Z" fill="#e2e8f0" stroke="#09090b" strokeWidth="10" />
              <path d="M 240 282 L 338 282 L 320 472 L 240 508 Z" fill="#94a3b8" />
              <polygon points="240,330 270,368 240,406 210,368" fill="#eab308" stroke="#09090b" strokeWidth="6" />
            </g>
          )}
          {role === "banker" && (
            <g>
              <rect x="172" y="275" width="36" height="248" fill="#78350f" stroke="#09090b" strokeWidth="8" />
              <rect x="272" y="275" width="36" height="248" fill="#78350f" stroke="#09090b" strokeWidth="8" />
              <path d="M 162 315 Q 240 385 318 315" stroke="#facc15" strokeWidth="10" fill="none" />
              <circle cx="240" cy="368" r="18" fill="#eab308" stroke="#09090b" strokeWidth="6" />
            </g>
          )}
          {(role === "noble1" || role === "noble2") && (
            <g>
              <line x1="192" y1="285" x2="180" y2="520" stroke={c.tr} strokeWidth="9" />
              <line x1="288" y1="285" x2="300" y2="520" stroke={c.tr} strokeWidth="9" />
              <ellipse cx="240" cy="282" rx="102" ry="23" fill="#ffffff" stroke="#09090b" strokeWidth="9" />
              <path d="M 148 282 Q 172 264 196 282 Q 220 300 244 282 Q 268 264 292 282 Q 316 300 332 282" stroke="#94a3b8" strokeWidth="5" fill="none" />
            </g>
          )}

          <g transform={`translate(342,308) rotate(${rArm - swing})`}>
            <ellipse cx="0" cy="10" rx="30" ry="26" fill={c.s} stroke="#09090b" strokeWidth="9" />
            <path d="M -8 -6 L -8 24 M 12 -6 L 12 24" stroke={c.tr} strokeWidth="5" strokeLinecap="round" />
            <line x1="0" y1="22" x2="22" y2="92" stroke={c.s} strokeWidth="24" strokeLinecap="round" />
            <line x1="0" y1="22" x2="22" y2="92" stroke="#09090b" strokeWidth="15" strokeLinecap="round" />
            <g transform="translate(22,92) rotate(-18)">
              <circle cx="0" cy="0" r="9" fill="#09090b" />
              <line x1="0" y1="0" x2="24" y2="66" stroke="#09090b" strokeWidth="14" strokeLinecap="round" />
              <g transform="translate(24,66)">
                <circle cx="0" cy="0" r="15" fill="#f8fafc" stroke="#09090b" strokeWidth="7" />
                {propR === "paper" && (
                  <g transform={`translate(-22,12) rotate(${-(rArm - swing - 18)})`}>
                    <ellipse cx="48" cy="88" rx="64" ry="18" fill="#eab308" stroke="#09090b" strokeWidth="7" />
                    <rect x="8" y="0" width="80" height="84" rx="12" fill="#ffffff" stroke="#09090b" strokeWidth="8" />
                    <ellipse cx="48" cy="18" rx="19" ry="7" fill="#cbd5e1" stroke="#09090b" strokeWidth="5" />
                    <path d="M 68 45 L 96 118 L 38 106 Z" fill="#ffffff" stroke="#09090b" strokeWidth="7" />
                  </g>
                )}
                {propR === "key" && (
                  <g transform="translate(6,12) rotate(18)">
                    <circle cx="24" cy="24" r="24" fill="none" stroke="#eab308" strokeWidth="10" />
                    <line x1="24" y1="48" x2="24" y2="148" stroke="#eab308" strokeWidth="12" strokeLinecap="round" />
                    <rect x="24" y="112" width="30" height="12" fill="#eab308" stroke="#09090b" strokeWidth="5" />
                    <rect x="24" y="132" width="22" height="12" fill="#eab308" stroke="#09090b" strokeWidth="5" />
                  </g>
                )}
                {propR === "sword" && (
                  <g transform="translate(10,-195) rotate(14)">
                    <polygon points="14,0 34,0 38,195 10,195" fill="#f8fafc" stroke="#09090b" strokeWidth="8" />
                    <rect x="-18" y="190" width="84" height="18" rx="6" fill="#eab308" stroke="#09090b" strokeWidth="7" />
                    <rect x="15" y="208" width="18" height="36" fill="#78350f" stroke="#09090b" strokeWidth="6" />
                  </g>
                )}
                {propR === "goldbag" && (
                  <g transform="translate(-25,12)">
                    <path d="M 25 0 L 65 0 L 85 55 C 95 95,-5 95,5 55 Z" fill="#eab308" stroke="#09090b" strokeWidth="9" />
                    <circle cx="45" cy="55" r="18" fill="#fef08a" stroke="#09090b" strokeWidth="5" />
                  </g>
                )}
                {propR === "scroll" && (
                  <g transform="translate(-10,10) rotate(-14)">
                    <rect x="0" y="0" width="90" height="114" rx="8" fill="#fef3c7" stroke="#09090b" strokeWidth="8" />
                    <line x1="18" y1="32" x2="72" y2="32" stroke="#09090b" strokeWidth="6" />
                    <line x1="18" y1="56" x2="72" y2="56" stroke="#09090b" strokeWidth="6" />
                    <circle cx="45" cy="85" r="15" fill="#dc2626" stroke="#09090b" strokeWidth="5" />
                  </g>
                )}
                {propR === "bell" && (
                  <g transform="translate(-12,12)">
                    <path d="M 8 56 L 62 56 L 52 14 C 46 0,24 0,18 14 Z" fill="#facc15" stroke="#09090b" strokeWidth="8" />
                    <circle cx="35" cy="63" r="9" fill="#eab308" stroke="#09090b" strokeWidth="5" />
                  </g>
                )}
              </g>
            </g>
          </g>

          <g transform={`translate(240,168) rotate(${tilt}) translate(-240,-168)`}>
            <rect x="216" y="255" width="48" height="36" rx="10" fill="#e2e8f0" stroke="#09090b" strokeWidth="9" />
            <ellipse cx="114" cy="175" rx="16" ry="24" fill="#ffffff" stroke="#09090b" strokeWidth="10" />
            <ellipse cx="366" cy="175" rx="16" ry="24" fill="#ffffff" stroke="#09090b" strokeWidth="10" />
            <circle cx="240" cy="168" r="124" fill="#ffffff" stroke="#09090b" strokeWidth="12" />
            <path d="M 122 198 A 124 124 0 0 0 358 198 A 124 98 0 0 1 122 198 Z" fill="#cbd5e1" />

            {role === "king" && (
              <g>
                <path d="M 122 168 C 118 262,362 262,358 168 C 342 224,295 238,240 238 C 185 238,138 224,122 168 Z" fill="#b45309" stroke="#09090b" strokeWidth="9" />
                <ellipse cx="240" cy="60" rx="142" ry="34" fill="#881337" stroke="#09090b" strokeWidth="10" />
                <polygon points="148,64 332,64 345,4 292,38 240,-14 188,38 135,4" fill="#facc15" stroke="#09090b" strokeWidth="10" />
                <circle cx="240" cy="34" r="10" fill="#dc2626" stroke="#09090b" strokeWidth="4" />
              </g>
            )}
            {role === "groom" && (
              <g>
                <path d="M 114 152 C 112 42,368 42,366 152 C 338 98,285 84,225 94 C 175 102,138 122,114 152 Z" fill="#3f2305" stroke="#09090b" strokeWidth="10" />
                <ellipse cx="245" cy="56" rx="115" ry="24" fill="#1e3a8a" stroke="#09090b" strokeWidth="9" transform="rotate(-6,245,56)" />
                <path d="M 310 42 C 355 -15,395 10,352 50" fill="#facc15" stroke="#09090b" strokeWidth="7" />
              </g>
            )}
            {role === "general" && (
              <g>
                <line x1="168" y1="128" x2="184" y2="182" stroke="#991b1b" strokeWidth="5.5" strokeLinecap="round" />
                <path d="M 110 154 C 110 28,370 28,370 154 L 340 114 L 140 114 Z" fill="#94a3b8" stroke="#09090b" strokeWidth="11" />
                <path d="M 240 36 C 295 -32,378 -12,352 52 C 312 36,272 40,240 36 Z" fill="#dc2626" stroke="#09090b" strokeWidth="9" />
              </g>
            )}
            {role === "banker" && (
              <g>
                <path d="M 120 124 C 135 42,345 42,360 124 Z" fill="#064e3b" stroke="#09090b" strokeWidth="10" />
                <rect x="112" y="94" width="256" height="32" rx="14" fill="#78350f" stroke="#09090b" strokeWidth="9" />
                <polygon points="222,226 258,226 240,268" fill="#64748b" stroke="#09090b" strokeWidth="7" />
              </g>
            )}
            {role === "noble1" && (
              <g>
                <path d="M 116 146 C 125 45,355 45,364 146 C 320 98,160 98,116 146 Z" fill="#eab308" stroke="#09090b" strokeWidth="10" />
                <ellipse cx="240" cy="58" rx="128" ry="28" fill="#581c87" stroke="#09090b" strokeWidth="10" />
                <path d="M 295 45 C 345 -18,395 5,355 52" fill="#fde047" stroke="#09090b" strokeWidth="7" />
              </g>
            )}
            {role === "noble2" && (
              <g>
                <path d="M 116 146 C 125 45,355 45,364 146 C 320 98,160 98,116 146 Z" fill="#18181b" stroke="#09090b" strokeWidth="10" />
                <polygon points="216,225 264,225 240,272" fill="#18181b" stroke="#09090b" strokeWidth="7" />
                <ellipse cx="240" cy="58" rx="128" ry="28" fill="#7c2d12" stroke="#09090b" strokeWidth="10" />
              </g>
            )}

            {blink ? (
              <g>
                <path d="M 164 156 Q 192 168 220 156" stroke="#09090b" strokeWidth="9" fill="none" />
                <path d="M 260 156 Q 288 168 316 156" stroke="#09090b" strokeWidth="9" fill="none" />
              </g>
            ) : (
              <g>
                <ellipse cx="192" cy="156" rx="24" ry={emotion === "shocked" ? 27 : 20} fill="#ffffff" stroke="#09090b" strokeWidth="7" />
                <circle cx={192 + lookX} cy={156 + lookY} r={emotion === "shocked" ? 8 : 11} fill="#09090b" />
                <circle cx={188 + lookX} cy={151 + lookY} r="3.8" fill="#ffffff" />
                <ellipse cx="288" cy="156" rx="24" ry={emotion === "shocked" ? 27 : 20} fill="#ffffff" stroke="#09090b" strokeWidth="7" />
                <circle cx={288 + lookX} cy={156 + lookY} r={emotion === "shocked" ? 8 : 11} fill="#09090b" />
                <circle cx={284 + lookX} cy={151 + lookY} r="3.8" fill="#ffffff" />
                {emotion === "furious" ? (
                  <>
                    <line x1="158" y1="118" x2="220" y2="138" stroke="#09090b" strokeWidth="11" strokeLinecap="round" />
                    <line x1="322" y1="118" x2="260" y2="138" stroke="#09090b" strokeWidth="11" strokeLinecap="round" />
                  </>
                ) : emotion === "scheming" ? (
                  <>
                    <line x1="162" y1="128" x2="218" y2="136" stroke="#09090b" strokeWidth="9.5" strokeLinecap="round" />
                    <path d="M 262 134 Q 290 110 320 124" stroke="#09090b" strokeWidth="9.5" fill="none" strokeLinecap="round" />
                  </>
                ) : (emotion === "nervous" || emotion === "pleading" || emotion === "rejected") ? (
                  <>
                    <line x1="158" y1="136" x2="216" y2="122" stroke="#09090b" strokeWidth="9" strokeLinecap="round" />
                    <line x1="264" y1="122" x2="322" y2="136" stroke="#09090b" strokeWidth="9" strokeLinecap="round" />
                  </>
                ) : (
                  <>
                    <path d="M 162 124 Q 192 108 220 124" stroke="#09090b" strokeWidth="8.5" fill="none" strokeLinecap="round" />
                    <path d="M 260 124 Q 288 108 318 124" stroke="#09090b" strokeWidth="8.5" fill="none" strokeLinecap="round" />
                  </>
                )}
              </g>
            )}

            <path d="M 240 152 L 233 182 L 246 185" stroke="#09090b" strokeWidth="6.5" fill="none" strokeLinecap="round" />
            {role === "banker" && (
              <g>
                <circle cx="192" cy="156" r="28" fill="none" stroke="#eab308" strokeWidth="6.5" />
                <circle cx="288" cy="156" r="28" fill="none" stroke="#eab308" strokeWidth="6.5" />
                <line x1="220" y1="156" x2="260" y2="156" stroke="#eab308" strokeWidth="6.5" />
              </g>
            )}
            {role === "king" && <path d="M 188 196 Q 240 180 292 196" stroke="#b45309" strokeWidth="13" fill="none" strokeLinecap="round" />}
            {role === "general" && <path d="M 192 195 Q 240 182 288 195" stroke="#475569" strokeWidth="11" fill="none" strokeLinecap="round" />}
            {(emotion === "nervous" || emotion === "pleading") && (
              <g transform={`translate(0,${(frame % 45) * 0.35})`}>
                <path d="M 136 104 C 136 104,116 132,128 146 C 140 158,156 146,144 126 Z" fill="#38bdf8" stroke="#09090b" strokeWidth="5.5" />
              </g>
            )}

            {emotion === "confident" || emotion === "proud" ? (
              <path d="M 206 206 Q 240 226 278 200" stroke="#09090b" strokeWidth="8.5" fill="none" strokeLinecap="round" />
            ) : emotion === "scheming" ? (
              <path d="M 202 210 Q 244 230 286 194" stroke="#09090b" strokeWidth="9" fill="none" strokeLinecap="round" />
            ) : emotion === "furious" || emotion === "rejected" || emotion === "shocked" ? (
              <path d="M 206 218 Q 240 196 274 218" stroke="#09090b" strokeWidth="9" fill="none" strokeLinecap="round" />
            ) : (
              <path d="M 202 212 Q 222 202 240 212 Q 258 222 278 212" stroke="#09090b" strokeWidth="8" fill="none" strokeLinecap="round" />
            )}
          </g>
        </g>
      </svg>
    </div>
  );
};

const Pedestal = ({ focus = false, press = false }: { focus?: boolean; press?: boolean }) => {
  const frame = useCurrentFrame();
  const hy = press ? interpolate(frame % 55, [0, 25, 55], [-90, 8, -90]) : -250;
  return (
    <div style={{
      position: "absolute", bottom: -30, left: "50%", transform: "translateX(-50%)",
      width: 1120, height: 520, filter: focus ? "blur(0px)" : "blur(7px)", zIndex: 26
    }}>
      <svg viewBox="0 0 1120 520" width="100%" height="100%">
        <polygon points="90,150 1030,150 1120,520 0,520" fill="#451a03" stroke="#09090b" strokeWidth="12" />
        <polygon points="160,180 960,180 1030,490 90,490" fill="#065f46" stroke="#eab308" strokeWidth="10" />
        <ellipse cx="560" cy="240" rx="230" ry="70" fill="#991b1b" stroke="#eab308" strokeWidth="10" />
        <polygon points="440,225 680,225 700,95 615,150 560,65 505,150 420,95" fill="#facc15" stroke="#09090b" strokeWidth="11" />
        <rect x="310" y="330" width="500" height="110" rx="12" fill="#eab308" stroke="#09090b" strokeWidth="9" />
        <text x="560" y="395" fill="#7f1d1d" fontSize="54" fontWeight="900" fontFamily="Arial Black" textAnchor="middle">ROYAL POWER</text>
        {press && (
          <g transform={`translate(0,${hy})`}>
            <line x1="980" y1="-40" x2="610" y2="115" stroke="#1e3a8a" strokeWidth="58" strokeLinecap="round" />
            <line x1="980" y1="-40" x2="610" y2="115" stroke="#09090b" strokeWidth="14" strokeLinecap="round" />
            <circle cx="595" cy="120" r="46" fill="#f8fafc" stroke="#09090b" strokeWidth="10" />
          </g>
        )}
      </svg>
    </div>
  );
};

const ThroneRoom = ({ camX = 0, camY = 0, guards = true, children }: { camX?: number; camY?: number; guards?: boolean; children?: React.ReactNode }) => {
  const frame = useCurrentFrame();
  const cloud = (frame * 0.45) % 450;
  const sw = Math.sin(frame * 0.035) * 2.5;
  const bw = Math.sin(frame * 0.05) * 3;
  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.15}px,${camY * 0.1}px,0)`, background: "linear-gradient(180deg,#0284c7 0%,#38bdf8 55%,#bae6fd 100%)" }}>
        <svg width="2400" height="1100" viewBox="0 0 2400 1100">
          {[300, 850, 1400, 1950].map((cx, i) => (
            <g key={i} transform={`translate(${(cx + cloud) % 2200},${260 + (i % 2) * 110})`} opacity="0.85">
              <ellipse cx="0" cy="0" rx="140" ry="48" fill="#ffffff" />
              <ellipse cx="65" cy="-18" rx="95" ry="45" fill="#ffffff" />
            </g>
          ))}
        </svg>
      </div>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.42}px,${camY * 0.3}px,0)` }}>
        <svg width="2400" height="2240" viewBox="0 0 2400 2240">
          <path fillRule="evenodd" d="M 0 0 H 2400 V 1480 H 0 Z M 560 940 L 560 390 Q 685 210 810 390 L 810 940 Z M 1590 940 L 1590 390 Q 1715 210 1840 390 L 1840 940 Z" fill="#334155" stroke="#09090b" strokeWidth="14" />
          {[200, 380, 560, 740, 920, 1100, 1280].map((y) => <line key={y} x1="0" y1={y} x2="2400" y2={y} stroke="#1e293b" strokeWidth="6" />)}
          {[685, 1715].map((wx) => (
            <g key={wx}>
              <line x1={wx} y1="225" x2={wx} y2="940" stroke="#09090b" strokeWidth="14" />
              <line x1={wx - 125} y1="580" x2={wx + 125} y2="580" stroke="#09090b" strokeWidth="14" />
            </g>
          ))}
          <g transform={`translate(1200,180) rotate(${bw * 0.4}) translate(-1200,-180)`}>
            <polygon points="1055,187 1345,187 1345,860 1200,960 1055,860" fill="#7f1d1d" stroke="#09090b" strokeWidth="12" />
            <polygon points="1080,212 1320,212 1320,840 1200,925 1080,840" fill="none" stroke="#eab308" strokeWidth="7" />
            <circle cx="1200" cy="520" r="74" fill="#eab308" stroke="#09090b" strokeWidth="8" />
          </g>
          <rect x="0" y="1480" width="2400" height="760" fill="#1e293b" stroke="#09090b" strokeWidth="14" />
          {[-900, -600, -350, -150, 0, 150, 350, 600, 900].map((off) => <line key={off} x1={1200 + off * 0.45} y1="1480" x2={1200 + off * 1.85} y2="2240" stroke="#0f172a" strokeWidth="7" />)}
          <polygon points="900,1480 1500,1480 1720,2240 680,2240" fill="#991b1b" stroke="#eab308" strokeWidth="16" />
        </svg>
      </div>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.72}px,${camY * 0.55}px,0)` }}>
        <svg width="2400" height="2240" viewBox="0 0 2400 2240">
          {[910, 1490].map((px) => (
            <g key={px}>
              <rect x={px - 58} y="80" width="116" height="1420" fill="#475569" stroke="#09090b" strokeWidth="12" />
              <rect x={px - 80} y="1445" width="160" height="65" rx="8" fill="#64748b" stroke="#09090b" strokeWidth="10" />
            </g>
          ))}
          <g transform={`translate(1200,60) rotate(${sw}) translate(-1200,-60)`}>
            <line x1="1200" y1="0" x2="1200" y2="210" stroke="#09090b" strokeWidth="12" />
            <ellipse cx="1200" cy="230" rx="190" ry="38" fill="none" stroke="#eab308" strokeWidth="14" />
            {[1030, 1110, 1200, 1290, 1370].map((cx) => (
              <g key={cx}>
                <rect x={cx - 8} y="185" width="16" height="36" fill="#fefce8" stroke="#09090b" strokeWidth="4" />
                <ellipse cx={cx} cy="172" rx="8" ry="14" fill="#facc15" />
              </g>
            ))}
          </g>
        </svg>
        <Sconce x={860} y={590} />
        <Sconce x={1440} y={590} />
        {guards && <><Guard x={995} y={1495} /><Guard x={1405} y={1495} flip /></>}
      </div>
      <AbsoluteFill style={{ transform: `translate3d(${camX}px,${camY}px,0)`, zIndex: 12 }}>{children}</AbsoluteFill>
      <Dust />
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 1.45}px,${camY * 1.15}px,0)`, filter: "blur(6px)", pointerEvents: "none", zIndex: 24 }}>
        <div style={{ position: "absolute", left: 490, top: 0, width: 130, height: 2240, backgroundColor: "#0f172a", opacity: 0.72 }} />
        <div style={{ position: "absolute", left: 1780, top: 0, width: 130, height: 2240, backgroundColor: "#0f172a", opacity: 0.72 }} />
      </div>
    </AbsoluteFill>
  );
};

const PrivyRoom = ({ camX = 0, camY = 0, children }: { camX?: number; camY?: number; children?: React.ReactNode }) => {
  const frame = useCurrentFrame();
  const dr = Math.sin(frame * 0.045) * 8;
  return (
    <AbsoluteFill style={{ backgroundColor: "#1e1b4b", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.38}px,${camY * 0.25}px,0)` }}>
        <svg width="2400" height="2240" viewBox="0 0 2400 2240">
          <rect width="2400" height="1480" fill="#311042" />
          <rect x="0" y="1020" width="2400" height="460" fill="#451a03" stroke="#09090b" strokeWidth="12" />
          {[450, 700, 950, 1200, 1450, 1700, 1950].map((px) => <rect key={px} x={px - 95} y="1065" width="190" height="370" rx="8" fill="#5c2408" stroke="#290f02" strokeWidth="8" />)}
          <g transform="translate(1390,340)">
            <rect x="0" y="0" width="390" height="680" fill="#290f02" stroke="#09090b" strokeWidth="12" />
            {[150, 320, 490].map((sy, r) => (
              <g key={sy}>
                <rect x="18" y={sy} width="354" height="22" fill="#78350f" stroke="#09090b" strokeWidth="6" />
                {[32, 72, 114, 156, 198, 242, 286, 324].map((bx, b) => (
                  <rect key={bx} x={bx} y={sy - 110 + ((b + r) % 3) * 14} width="34" height={110 - ((b + r) % 3) * 14} fill={["#dc2626", "#2563eb", "#eab308", "#059669", "#9333ea"][(b + r) % 5]} stroke="#09090b" strokeWidth="5" />
                ))}
              </g>
            ))}
          </g>
          <rect x="0" y="1480" width="2400" height="760" fill="#290f02" stroke="#09090b" strokeWidth="14" />
          <ellipse cx="1200" cy="1760" rx="520" ry="175" fill="#7f1d1d" stroke="#eab308" strokeWidth="14" />
        </svg>
      </div>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.68}px,${camY * 0.5}px,0)` }}>
        <svg width="2400" height="2240" viewBox="0 0 2400 2240">
          <path d={`M 620 150 L 1060 150 L ${990 + dr} 1180 L ${620 - dr * 0.5} 1180 Z`} fill="#881337" stroke="#09090b" strokeWidth="12" />
          <rect x="590" y="135" width="500" height="30" rx="12" fill="#eab308" stroke="#09090b" strokeWidth="8" />
          <g transform="translate(830,830)">
            <rect x="35" y="0" width="350" height="440" rx="28" fill="#991b1b" stroke="#09090b" strokeWidth="12" />
            <rect x="65" y="30" width="290" height="380" rx="18" fill="#7f1d1d" stroke="#eab308" strokeWidth="8" />
            <rect x="10" y="400" width="400" height="220" rx="20" fill="#b91c1c" stroke="#09090b" strokeWidth="12" />
            <ellipse cx="210" cy="442" rx="104" ry="32" fill="#09090b" stroke="#eab308" strokeWidth="9" />
          </g>
        </svg>
        <Sconce x={1180} y={360} scale={1.05} />
      </div>
      <AbsoluteFill style={{ transform: `translate3d(${camX}px,${camY}px,0)`, zIndex: 12 }}>{children}</AbsoluteFill>
      <Dust color="#fbbf24" />
    </AbsoluteFill>
  );
};

const Corridor = ({ camX = 0, camY = 0, openP = 0, lockP = 0, children }: { camX?: number; camY?: number; openP?: number; lockP?: number; children?: React.ReactNode }) => {
  const ds = interpolate(openP, [0, 1], [1, 0.35]);
  const by = interpolate(lockP, [0, 1], [-220, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: "#1e293b", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: -660, top: -160, width: 2400, height: 2240, transform: `translate3d(${camX * 0.5}px,${camY * 0.35}px,0)` }}>
        <svg width="2400" height="2240" viewBox="0 0 2400 2240">
          <rect width="2400" height="1500" fill="#475569" />
          {[220, 420, 620, 820, 1020, 1220, 1420].map((y) => <line key={y} x1="0" y1={y} x2="2400" y2={y} stroke="#1e293b" strokeWidth="6" />)}
          <rect x="0" y="1500" width="2400" height="740" fill="#1e293b" stroke="#09090b" strokeWidth="14" />
          <g transform="translate(800,420)">
            <path d="M 40 1080 L 40 420 Q 400 40 760 420 L 760 1080 Z" fill="#94a3b8" stroke="#09090b" strokeWidth="14" />
            <path d="M 95 1080 L 95 450 Q 400 120 705 450 L 705 1080 Z" fill="#f59e0b" />
            <g transform={`translate(95,0) scale(${ds},1) translate(-95,0)`}>
              <path d="M 95 1080 L 95 450 Q 400 120 705 450 L 705 1080 Z" fill="#78350f" stroke="#09090b" strokeWidth="14" />
              <line x1="400" y1="280" x2="400" y2="1080" stroke="#09090b" strokeWidth="10" />
              <rect x="310" y="360" width="180" height="130" fill="#0f172a" stroke="#09090b" strokeWidth="10" />
              <rect x="200" y="590" width="400" height="115" rx="14" fill="#eab308" stroke="#09090b" strokeWidth="9" />
              <text x="400" y="642" fill="#09090b" fontSize="34" fontWeight="900" fontFamily="Arial Black" textAnchor="middle">PRIVY CHAMBER</text>
              <text x="400" y="684" fill="#991b1b" fontSize="27" fontWeight="900" fontFamily="Arial Black" textAnchor="middle">GROOM OF THE STOOL</text>
            </g>
            {lockP > 0 && (
              <g transform={`translate(0,${by})`}>
                <rect x="30" y="730" width="740" height="60" rx="12" fill="#334155" stroke="#09090b" strokeWidth="12" />
                <rect x="345" y="700" width="110" height="120" rx="18" fill="#eab308" stroke="#09090b" strokeWidth="10" />
                <circle cx="400" cy="750" r="15" fill="#09090b" />
              </g>
            )}
          </g>
        </svg>
        <Sconce x={710} y={580} />
        <Sconce x={1610} y={580} />
      </div>
      <AbsoluteFill style={{ transform: `translate3d(${camX}px,${camY}px,0)`, zIndex: 12 }}>{children}</AbsoluteFill>
      <Dust />
    </AbsoluteFill>
  );
};

export const GroomStory: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;

  let seg = TIMINGS[TIMINGS.length - 1];
  for (const s of TIMINGS) {
    if (time >= s.start && time < s.end) { seg = s; break; }
  }
  const idx = seg.index;
  const p = Math.max(0, Math.min(1, (time - seg.start) / Math.max(0.01, seg.duration)));
  const sub = p < 0.52 ? 0 : 1;

  const camX = interpolate(p, [0, 1], idx % 2 === 0 ? [-75, 75] : [75, -75]);
  const camY = interpolate(p, [0, 1], sub === 0 ? [12, -12] : [-12, 12]);
  const zoom = interpolate(p, [0, 0.52, 0.53, 1], [1.02, 1.11, 1.16, 1.24]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#09090b", overflow: "hidden" }}>
      <Audio src={staticFile("voce.mp3")} />
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        {idx === 0 && (
          <>
            <ThroneRoom camX={camX} camY={camY}>
              <div style={{ filter: sub === 0 ? "blur(7px)" : "blur(0px)" }}>
                <Actor role="groom" emotion={sub === 0 ? "confident" : "proud"} lookX={sub === 0 ? -5 : 4} x={0} y={65} scale={sub === 0 ? 1.05 : 1.22} walk={sub === 0} lArm={interpolate(p, [0, 1], [25, -42])} rArm={interpolate(p, [0, 1], [-25, -58])} propR="key" propL="goldbag" />
              </div>
            </ThroneRoom>
            <Pedestal focus={sub === 0} press={sub === 0} />
          </>
        )}
        {idx === 1 && (
          <PrivyRoom camX={camX} camY={camY}>
            <Actor role="king" emotion="proud" lookX={7} x={-175} y={95} scale={1.1} rArm={interpolate(p, [0, 0.5, 1], [-20, -68, -30])} propR="bell" />
            <Actor role="groom" emotion="confident" lookX={-7} x={195} y={105} scale={1.08} walk={p < 0.45} />
          </PrivyRoom>
        )}
        {idx === 2 && (
          <PrivyRoom camX={camX * 0.6} camY={camY}>
            {sub === 0 ? (
              <>
                <Actor role="king" emotion="confident" lookX={6} x={-195} y={110} scale={1.04} />
                <Actor role="groom" emotion="nervous" lookX={-6} x={165} y={110} scale={1.16} rArm={-58} propR="paper" />
              </>
            ) : (
              <Actor role="groom" emotion="shocked" lookY={5} x={30} y={155} scale={1.38} rArm={-72} propR="paper" />
            )}
          </PrivyRoom>
        )}
        {idx === 3 && (
          <ThroneRoom camX={camX} camY={camY}>
            <Actor role="king" emotion="proud" lookX={interpolate(p, [0, 1], [-6, 6])} x={0} y={80} scale={1.2} lArm={32} rArm={-52} propR="key" />
          </ThroneRoom>
        )}
        {idx === 4 && (
          <ThroneRoom camX={camX} camY={camY}>
            <Actor role="general" emotion={p < 0.55 ? "proud" : "rejected"} x={interpolate(p, [0, 0.55, 1], [-80, 0, -40])} y={95} scale={1.15} walk={p < 0.5} rArm={-65} propR="sword" propL="shield" />
            {p > 0.56 && (
              <svg width="440" height="440" viewBox="0 0 440 440" style={{ position: "absolute", left: 320, top: 680, zIndex: 30 }}>
                <line x1="55" y1="55" x2="385" y2="385" stroke="#dc2626" strokeWidth="42" strokeLinecap="round" />
                <line x1="385" y1="55" x2="55" y2="385" stroke="#dc2626" strokeWidth="42" strokeLinecap="round" />
              </svg>
            )}
          </ThroneRoom>
        )}
        {idx === 5 && (
          <ThroneRoom camX={-camX} camY={camY}>
            <Actor role="banker" emotion={p < 0.55 ? "confident" : "rejected"} x={interpolate(p, [0, 0.55, 1], [80, 0, 40])} y={95} scale={1.15} walk={p < 0.5} lArm={42} rArm={-52} propR="goldbag" propL="goldbag" />
            {p > 0.56 && (
              <svg width="440" height="440" viewBox="0 0 440 440" style={{ position: "absolute", left: 320, top: 680, zIndex: 30 }}>
                <line x1="55" y1="55" x2="385" y2="385" stroke="#dc2626" strokeWidth="42" strokeLinecap="round" />
                <line x1="385" y1="55" x2="55" y2="385" stroke="#dc2626" strokeWidth="42" strokeLinecap="round" />
              </svg>
            )}
          </ThroneRoom>
        )}
        {idx === 6 && (
          <Corridor camX={camX} camY={camY} openP={interpolate(p, [0.3, 1], [0, 0.65], { extrapolateLeft: "clamp" })}>
            <Actor role="groom" emotion="proud" x={0} y={115} scale={1.24} rArm={interpolate(p, [0, 1], [-18, -72])} propR="key" />
          </Corridor>
        )}
        {idx === 7 && (
          <Corridor camX={camX} camY={camY} openP={0.75}>
            <Actor role="king" emotion="confident" lookX={6} x={interpolate(p, [0, 1], [-270, -145])} y={115} scale={1.06} walk />
            <Actor role="groom" emotion="nervous" lookX={-6} x={interpolate(p, [0, 1], [280, 165])} y={120} scale={1.06} walk rArm={-58} propR="paper" />
          </Corridor>
        )}
        {idx === 8 && (
          <PrivyRoom camX={camX} camY={camY}>
            <Actor role="groom" emotion="nervous" lookY={5} x={0} y={125} scale={1.26} lArm={-42} rArm={-64} propR="paper" />
          </PrivyRoom>
        )}
        {idx === 9 && (
          <Corridor camX={-camX} camY={camY}>
            <Actor role="noble1" emotion="furious" lookX={7} x={-205 + Math.sin(frame * 0.26) * 48} y={115} scale={1.06} walk rArm={-55 + Math.sin(frame * 0.36) * 38} propR="sword" />
            <Actor role="noble2" emotion="furious" lookX={7} x={205 - Math.sin(frame * 0.26) * 48} y={115} scale={1.06} flip walk rArm={-55 + Math.cos(frame * 0.36) * 38} propR="sword" />
            <svg width="190" height="190" viewBox="0 0 190 190" style={{ position: "absolute", left: 445, top: 740, zIndex: 25, transform: `scale(${0.7 + Math.abs(Math.sin(frame * 0.42)) * 0.45}) rotate(${frame * 5}deg)` }}>
              <polygon points="95,10 116,74 180,95 116,116 95,180 74,116 10,95 74,74" fill="#fde047" stroke="#09090b" strokeWidth="6" />
            </svg>
          </Corridor>
        )}
        {idx === 10 && (
          <Corridor camX={0} camY={0}>
            <Actor role="groom" emotion="scheming" lookX={5} x={0} y={155} scale={1.38} rArm={-58} propR="key" />
          </Corridor>
        )}
        {idx === 11 && (
          <Corridor camX={camX * 0.5} camY={camY} openP={interpolate(p, [0, 0.35], [0.6, 0], { extrapolateRight: "clamp" })} lockP={interpolate(p, [0.35, 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
            <Actor role="king" emotion="confident" lookX={6} x={-175} y={118} scale={1.05} />
            <Actor role="groom" emotion="scheming" lookX={-6} x={175} y={118} scale={1.06} rArm={-52} propR="key" />
          </Corridor>
        )}
        {idx === 12 && (
          <PrivyRoom camX={camX} camY={camY}>
            <Actor role="king" emotion="whisper" lookX={8} x={-155} y={125} scale={1.18} rArm={-58} />
            <Actor role="groom" emotion="confident" lookX={-8} x={175} y={125} scale={1.18} rArm={-38} propR="scroll" />
          </PrivyRoom>
        )}
        {idx === 13 && (
          <PrivyRoom camX={-camX} camY={camY}>
            <Actor role="groom" emotion="scheming" lookX={-6} x={40} y={145} scale={1.34} rArm={-66} propR="scroll" />
          </PrivyRoom>
        )}
        {idx === 14 && (
          <ThroneRoom camX={camX} camY={camY}>
            <Actor role="king" emotion="furious" lookX={8} x={-180} y={100} scale={1.14} rArm={-72} />
            <Actor role="noble1" emotion="nervous" lookX={-8} x={190} y={108} scale={1.08} />
          </ThroneRoom>
        )}
        {idx === 15 && (
          <Corridor camX={camX} camY={camY} lockP={1}>
            <Actor role="noble2" emotion="pleading" lookX={7} x={interpolate(p, [0, 1], [-270, -210])} y={120} scale={0.98} walk={p < 0.5} lArm={-52} rArm={-60} />
            <Actor role="groom" emotion="scheming" lookX={-7} x={165} y={115} scale={1.2} rArm={interpolate(p, [0, 1], [-78, -28])} propR="key" />
          </Corridor>
        )}
        {idx === 16 && (
          <Corridor camX={-camX} camY={camY} lockP={1}>
            <Actor role="general" emotion="pleading" lookX={6} x={-215} y={118} scale={1.0} lArm={-52} />
            <Actor role="banker" emotion="pleading" lookX={-6} x={215} y={118} scale={1.0} flip rArm={-62} propR="goldbag" />
          </Corridor>
        )}
        {idx === 17 && (
          <ThroneRoom camX={camX * 0.45} camY={camY} guards={false}>
            <svg width="1080" height="1920" style={{ position: "absolute", top: 0, left: 0, zIndex: 20 }}>
              <line x1="540" y1="180" x2="225" y2="1120" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
              <line x1="540" y1="180" x2="855" y2="1120" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
            </svg>
            <Actor role="groom" emotion="scheming" lookY={2} x={0} y={55} scale={interpolate(p, [0, 1], [1.24, 1.36])} lArm={44} rArm={-66} propR="paper" propL="goldbag" />
            <Actor role="king" emotion="confident" x={-310} y={210} scale={0.82} />
            <Actor role="general" emotion="pleading" x={310} y={210} scale={0.82} flip />
          </ThroneRoom>
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(0,0,0,0) 58%, rgba(0,0,0,0.52) 100%)", pointerEvents: "none", zIndex: 30 }} />
    </AbsoluteFill>
  );
};
"""

open("src/GroomStory.tsx", "w").write(tsx.replace("__TIMINGS__", json.dumps(timings)))
print(f"✅ CODICE ULTRA 2.5D PRONTO ({total_frames} frame a 60 FPS, PNG Lossless + CRF 14)!")
