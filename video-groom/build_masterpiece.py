import asyncio
import json
import math
import os
import subprocess
import edge_tts

os.makedirs("public/segments", exist_ok=True)

# 18 segmenti narrativi per avere pause naturali e 20 cambi di inquadratura sincronizzati al millisecondo
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

async def generate_voice_segments():
    timings = []
    concat_list = []
    current_time = 0.0

    for idx, text in enumerate(SEGMENTS):
        raw_file = f"public/segments/seg_{idx:02d}_raw.mp3"
        clean_file = f"public/segments/seg_{idx:02d}.wav"
        comm = edge_tts.Communicate(text, VOICE, rate="+2%", pitch="-2Hz")
        await comm.save(raw_file)

        # Filtro audio professionale: rimuove silenzi morti eccessivi e applica EQ caldo da studio
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_file,
            "-af", "equalizer=f=180:width_type=o:width=2:g=2.5,equalizer=f=3500:width_type=o:width=2:g=1.5,acompressor=threshold=-18dB:ratio=2.5:attack=15:release=120,apad=pad_dur=0.14",
            "-ar", "44100", "-ac", "2", clean_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", clean_file
        ]).decode().strip()
        dur = float(out)

        timings.append({
            "index": idx,
            "start": round(current_time, 3),
            "end": round(current_time + dur, 3),
            "duration": round(dur, 3),
            "text": text
        })
        current_time += dur
        concat_list.append(f"file 'segments/seg_{idx:02d}.wav'")

    with open("public/concat.txt", "w") as f:
        f.write("\n".join(concat_list))

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "public/concat.txt",
        "-c:a", "libmp3lame", "-b:a", "192k", "public/voce.mp3"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return timings, current_time

timings, total_duration = asyncio.run(generate_voice_segments())
fps = 60
total_frames = int(math.ceil(total_duration * fps))

print(f"✅ Voce realistica generata! Durata totale: {total_duration:.2f}s ({total_frames} frame a 60 FPS)")

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

timings_json = json.dumps(timings)

story_tsx = f"""import {{ AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile }} from "remotion";
import React from "react";

const TIMINGS = {timings_json};

// TORCIA DA PARETE MEDIEVALE (Montata sulle colonne in pietra, mai sulle finestre!)
const WallTorch = ({{ x, y, scale = 1 }}: {{ x: number; y: number; scale?: number }}) => {{
  const frame = useCurrentFrame();
  const flicker = Math.sin(frame * 0.32 + x) * 0.1 + Math.cos(frame * 0.19) * 0.07;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `scale(${{scale}})` }}>
      <div
        style={{
          position: "absolute",
          left: -160,
          top: -180,
          width: 380,
          height: 380,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,165,45,0.45) 0%, rgba(255,90,0,0) 70%)",
          transform: `scale(${{1 + flicker * 0.4}})`,
        }}
      />
      <svg width="90" height="190" viewBox="0 0 90 190" style={{ overflow: "visible" }}>
        <rect x="25" y="110" width="40" height="16" rx="5" fill="#1e293b" stroke="#0f172a" strokeWidth="6" />
        <polygon points="28,92 62,92 52,175 38,175" fill="#475569" stroke="#0f172a" strokeWidth="7" strokeLinejoin="round" />
        <g transform={{`translate(45, 90) scale(1, ${{1 + flicker}}) translate(-45, -90)`}}>
          <path d="M 45 8 C 74 42, 76 75, 45 92 C 14 75, 16 42, 45 8 Z" fill="#f97316" stroke="#111" strokeWidth="6" />
          <path d="M 45 26 C 62 48, 62 72, 45 84 C 28 72, 28 48, 45 26 Z" fill="#fde047" />
        </g>
      </svg>
    </div>
  );
}};

// PERSONAGGI STORICI ORIGINALI (Ogni personaggio ha volto, barba, capelli e vestiti unici, braccia attaccate perfettamente)
const HistoricalCharacter = ({{
  role,
  expression,
  lookX = 0,
  lookY = 0,
  x = 0,
  y = 0,
  scale = 1,
  flip = false,
  walk = false,
  leftArm = 25,
  rightArm = -25,
  propRight = "none",
  propLeft = "none",
}}: {{
  role: "king" | "groom" | "general" | "banker" | "noble_blonde" | "noble_dark";
  expression: "confident" | "proud" | "nervous" | "shocked" | "furious" | "scheming" | "whisper" | "pleading" | "rejected";
  lookX?: number;
  lookY?: number;
  x?: number;
  y?: number;
  scale?: number;
  flip?: boolean;
  walk?: boolean;
  leftArm?: number;
  rightArm?: number;
  propRight?: "none" | "paper" | "key" | "sword" | "goldbag" | "scroll" | "bell";
  propLeft?: "none" | "shield" | "goldbag" | "ledger";
}}) => {{
  const frame = useCurrentFrame();
  const walkCycle = walk ? Math.sin(frame * 0.22) : 0;
  const bob = walk ? Math.abs(walkCycle) * 16 : Math.sin(frame * 0.07 + x) * 4;
  const legSwing = walk ? walkCycle * 30 : 0;
  const headTilt = Math.sin(frame * 0.04 + x * 0.5) * 2;
  const isBlinking = (frame + Math.abs(x)) % 175 > 169;

  const palette: Record<string, {{ main: string; trim: string; sleeve: string }}> = {{
    king: {{ main: "#881337", trim: "#eab308", sleeve: "#9f1239" }},
    groom: {{ main: "#1e3a8a", trim: "#cbd5e1", sleeve: "#1d4ed8" }},
    general: {{ main: "#475569", trim: "#94a3b8", sleeve: "#64748b" }},
    banker: {{ main: "#064e3b", trim: "#d97706", sleeve: "#047857" }},
    noble_blonde: {{ main: "#581c87", trim: "#facc15", sleeve: "#6b21a8" }},
    noble_dark: {{ main: "#7c2d12", trim: "#f59e0b", sleeve: "#9a3412" }},
  }};
  const colors = palette[role];

  return (
    <div
      style={{
        position: "absolute",
        left: `calc(50% + ${{x}}px)`,
        top: `calc(54% + ${{y - bob}}px)`,
        transform: `translate(-50%, -50%) scale(${{scale}}) scaleX(${{flip ? -1 : 1}})`,
        width: 480,
        height: 820,
        zIndex: 10,
      }}
    >
      <svg viewBox="0 0 480 820" width="100%" height="100%" style={{ overflow: "visible" }}>
        {/* Ombra morbida sul pavimento */}
        <ellipse cx="240" cy="745" rx="105" ry="22" fill="rgba(0,0,0,0.42)" />

        {/* Mantello Reale o Militare */}
        {{(role === "king" || role === "general") && (
          <path
            d="M 115 285 L 65 645 C 155 680, 325 680, 415 645 L 365 285 Z"
            fill={{role === "king" ? "#4c0519" : "#991b1b"}}
            stroke="#111"
            strokeWidth="12"
            strokeLinejoin="round"
          />
        )}}

        {/* GAMBE E CALZATURE STORICHE */}
        <line x1="202" y1="520" x2={{202 - legSwing}} y2="725" stroke="#111" strokeWidth="16" strokeLinecap="round" />
        <line x1="278" y1="520" x2={{278 + legSwing}} y2="725" stroke="#111" strokeWidth="16" strokeLinecap="round" />
        <path d={{`M ${{170 - legSwing}} 725 C ${{170 - legSwing}} 705, ${{222 - legSwing}} 705, ${{222 - legSwing}} 732 L ${{165 - legSwing}} 732 Z`}} fill="#1e293b" stroke="#111" strokeWidth="8" />
        <path d={{`M ${{258 + legSwing}} 725 C ${{258 + legSwing}} 705, ${{310 + legSwing}} 705, ${{310 + legSwing}} 732 L ${{255 + legSwing}} 732 Z`}} fill="#1e293b" stroke="#111" strokeWidth="8" />

        {/* BRACCIO SINISTRO (Attaccato esattamente al perno della spalla 142,315) */}
        <g transform={{`translate(142, 315) rotate(${{leftArm}})`}}>
          <ellipse cx="0" cy="0" rx="28" ry="24" fill={{colors.sleeve}} stroke="#111" strokeWidth="10" />
          <line x1="0" y1="12" x2="-32" y2="145" stroke="#111" strokeWidth="16" strokeLinecap="round" />
          <circle cx="-32" cy="145" r="17" fill="#fff" stroke="#111" strokeWidth="8" />
          {{propLeft === "shield" && (
            <g transform="translate(-85, 85)">
              <path d="M 0 0 L 96 0 L 96 80 C 96 135, 48 168, 48 168 C 48 168, 0 135, 0 80 Z" fill="#eab308" stroke="#111" strokeWidth="10" />
              <path d="M 16 16 L 80 16 L 80 75 C 80 112, 48 142, 48 142 C 48 142, 16 112, 16 75 Z" fill="#991b1b" stroke="#111" strokeWidth="6" />
            </g>
          )}}
          {{propLeft === "goldbag" && (
            <g transform="translate(-75, 115)">
              <path d="M 22 0 L 58 0 L 78 52 C 88 88, -8 88, 2 52 Z" fill="#eab308" stroke="#111" strokeWidth="9" />
              <circle cx="40" cy="52" r="15" fill="#fef08a" stroke="#111" strokeWidth="5" />
            </g>
          )}}
        </g>

        {/* BUSTO STORICO TUDOR */}
        <path
          d="M 138 300 C 138 255, 342 255, 342 300 L 356 525 C 356 542, 124 542, 124 525 Z"
          fill={{colors.main}}
          stroke="#111"
          strokeWidth="12"
          strokeLinejoin="round"
        />
        {/* Ombreggiatura tridimensionale sul busto */}
        <path d="M 290 275 L 310 532 L 350 525 L 336 295 Z" fill="rgba(0,0,0,0.26)" />

        {/* DETTAGLI VESTITI UNICI PER RUOLO */}
        {{role === "king" && (
          <g>
            <rect x="216" y="305" width="48" height="225" fill="#eab308" stroke="#111" strokeWidth="8" />
            <polygon points="240,345 256,365 240,385 224,365" fill="#dc2626" stroke="#111" strokeWidth="5" />
            <polygon points="240,415 256,435 240,455 224,435" fill="#1d4ed8" stroke="#111" strokeWidth="5" />
            {/* Pelliccia di ermellino reale */}
            <path d="M 128 282 Q 240 342 352 282 L 362 348 Q 240 398 118 348 Z" fill="#fff" stroke="#111" strokeWidth="10" />
            <circle cx="165" cy="322" r="5" fill="#111" />
            <circle cx="215" cy="336" r="5" fill="#111" />
            <circle cx="265" cy="336" r="5" fill="#111" />
            <circle cx="315" cy="322" r="5" fill="#111" />
            {/* Catena reale d'oro */}
            <path d="M 155 340 Q 240 405 325 340" stroke="#facc15" strokeWidth="12" fill="none" />
          </g>
        )}}

        {{role === "groom" && (
          <g>
            {/* Tunica trapuntata di corte con colletto bianco Tudor e stemma chiave */}
            <polygon points="195,275 285,275 240,335" fill="#fff" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
            <line x1="240" y1="335" x2="240" y2="532" stroke="#93c5fd" strokeWidth="7" />
            <line x1="185" y1="300" x2="175" y2="525" stroke="#1d4ed8" strokeWidth="6" />
            <line x1="295" y1="300" x2="305" y2="525" stroke="#1d4ed8" strokeWidth="6" />
            <rect x="128" y="460" width="224" height="26" fill="#451a03" stroke="#111" strokeWidth="8" />
            <rect x="220" y="454" width="40" height="38" rx="6" fill="#eab308" stroke="#111" strokeWidth="6" />
          </g>
        )}}

        {{role === "general" && (
          <g>
            <path d="M 148 292 L 332 292 L 315 475 L 240 508 L 165 475 Z" fill="#e2e8f0" stroke="#111" strokeWidth="10" strokeLinejoin="round" />
            <path d="M 240 292 L 315 475 L 240 508 Z" fill="#cbd5e1" />
            <line x1="240" y1="292" x2="240" y2="508" stroke="#334155" strokeWidth="6" />
            <polygon points="240,335 268,370 240,405 212,370" fill="#dc2626" stroke="#111" strokeWidth="6" />
          </g>
        )}}

        {{role === "banker" && (
          <g>
            {/* Pelliccia marrone pregiata ai bordi della veste e catena di monete */}
            <rect x="180" y="285" width="32" height="245" fill="#78350f" stroke="#111" strokeWidth="7" />
            <rect x="268" y="285" width="32" height="245" fill="#78350f" stroke="#111" strokeWidth="7" />
            <circle cx="240" cy="365" r="18" fill="#eab308" stroke="#111" strokeWidth="6" />
            <circle cx="240" cy="425" r="18" fill="#eab308" stroke="#111" strokeWidth="6" />
          </g>
        )}}

        {{(role === "noble_blonde" || role === "noble_dark") && (
          <g>
            <line x1="195" y1="295" x2="185" y2="525" stroke="#eab308" strokeWidth="8" />
            <line x1="285" y1="295" x2="295" y2="525" stroke="#eab308" strokeWidth="8" />
            <ellipse cx="240" cy="288" rx="98" ry="22" fill="#fff" stroke="#111" strokeWidth="9" />
            <path d="M 152 288 Q 175 270 198 288 Q 220 306 242 288 Q 265 270 288 288 Q 310 306 328 288" stroke="#94a3b8" strokeWidth="5" fill="none" />
          </g>
        )}}

        {/* BRACCIO DESTRO (Attaccato esattamente al perno della spalla 338,315) */}
        <g transform={{`translate(338, 315) rotate(${{rightArm}})`}}>
          <ellipse cx="0" cy="0" rx="28" ry="24" fill={{colors.sleeve}} stroke="#111" strokeWidth="10" />
          <line x1="0" y1="12" x2="48" y2="140" stroke="#111" strokeWidth="16" strokeLinecap="round" />
          <circle cx="48" cy="140" r="17" fill="#fff" stroke="#111" strokeWidth="8" />

          {{propRight === "paper" && (
            <g transform={{`translate(15, 105) rotate(${{-rightArm}})`}}>
              <ellipse cx="45" cy="85" rx="62" ry="18" fill="#eab308" stroke="#111" strokeWidth="7" />
              <rect x="6" y="0" width="78" height="82" rx="12" fill="#fff" stroke="#111" strokeWidth="8" />
              <ellipse cx="45" cy="18" rx="18" ry="7" fill="#cbd5e1" stroke="#111" strokeWidth="5" />
              <path d="M 65 45 L 92 115 L 38 105 Z" fill="#fff" stroke="#111" strokeWidth="7" strokeLinejoin="round" />
            </g>
          )}}

          {{propRight === "key" && (
            <g transform="translate(30, 115) rotate(20)">
              <circle cx="24" cy="24" r="24" fill="none" stroke="#eab308" strokeWidth="10" />
              <line x1="24" y1="48" x2="24" y2="145" stroke="#eab308" strokeWidth="12" strokeLinecap="round" />
              <rect x="24" y="110" width="28" height="12" fill="#eab308" stroke="#111" strokeWidth="5" />
              <rect x="24" y="130" width="22" height="12" fill="#eab308" stroke="#111" strokeWidth="5" />
            </g>
          )}}

          {{propRight === "sword" && (
            <g transform="translate(38, -85) rotate(12)">
              <polygon points="14,0 34,0 38,190 10,190" fill="#f1f5f9" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
              <line x1="24" y1="20" x2="24" y2="180" stroke="#94a3b8" strokeWidth="4" />
              <rect x="-16" y="185" width="80" height="18" rx="6" fill="#eab308" stroke="#111" strokeWidth="7" />
              <rect x="15" y="203" width="18" height="36" fill="#78350f" stroke="#111" strokeWidth="6" />
            </g>
          )}}

          {{propRight === "goldbag" && (
            <g transform="translate(12, 105)">
              <path d="M 25 0 L 65 0 L 85 55 C 95 95, -5 95, 5 55 Z" fill="#eab308" stroke="#111" strokeWidth="9" />
              <circle cx="45" cy="55" r="18" fill="#fef08a" stroke="#111" strokeWidth="5" />
            </g>
          )}}

          {{propRight === "scroll" && (
            <g transform="translate(18, 95) rotate(-12)">
              <rect x="0" y="0" width="88" height="112" rx="8" fill="#fef3c7" stroke="#111" strokeWidth="8" />
              <line x1="18" y1="32" x2="70" y2="32" stroke="#111" strokeWidth="6" />
              <line x1="18" y1="56" x2="70" y2="56" stroke="#111" strokeWidth="6" />
              <circle cx="44" cy="84" r="14" fill="#dc2626" stroke="#111" strokeWidth="5" />
            </g>
          )}}

          {{propRight === "bell" && (
            <g transform="translate(22, 110)">
              <path d="M 10 55 L 60 55 L 50 15 C 45 0, 25 0, 20 15 Z" fill="#facc15" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
              <circle cx="35" cy="62" r="9" fill="#eab308" stroke="#111" strokeWidth="5" />
            </g>
          )}}
        </g>

        {/* TESTA E VOLTO UNICO PER OGNI PERSONAGGIO */}
        <g transform={{`translate(240, 172) rotate(${{headTilt}}) translate(-240, -172)`}}>
          <circle cx="240" cy="172" r="124" fill="#ffffff" stroke="#111" strokeWidth="12" />
          <path d="M 122 202 A 124 124 0 0 0 358 202 A 124 100 0 0 1 122 202 Z" fill="#e2e8f0" />

          {/* CAPELLI, ELMI E COPRICAPI DISTINTI */}
          {{role === "king" && (
            <g>
              {/* Capelli e Barba Rossiccia stile Enrico VIII */}
              <path d="M 118 165 C 115 245, 365 245, 362 165 C 350 225, 130 225, 118 165 Z" fill="#b45309" stroke="#111" strokeWidth="9" />
              {/* Cappello Tudor di velluto rosso + Corona Reale */}
              <ellipse cx="240" cy="62" rx="138" ry="34" fill="#881337" stroke="#111" strokeWidth="10" />
              <polygon points="150,65 330,65 342,5 290,38 240,-12 190,38 138,5" fill="#facc15" stroke="#111" strokeWidth="10" strokeLinejoin="round" />
              <circle cx="240" cy="36" r="10" fill="#dc2626" stroke="#111" strokeWidth="4" />
            </g>
          )}}

          {{role === "groom" && (
            <g>
              {/* Capelli castani mossi naturali da giovane cortigiano (senza righe bianche copiate!) */}
              <path
                d="M 114 148 C 118 35, 362 35, 366 148 C 325 95, 265 78, 205 92 C 165 102, 135 118, 114 148 Z"
                fill="#451a03"
                stroke="#111"
                strokeWidth="10"
                strokeLinejoin="round"
              />
            </g>
          )}}

          {{role === "general" && (
            <g>
              {/* Cicatrice da battaglia + Elmo cavaliere con visiera */}
              <line x1="168" y1="125" x2="182" y2="178" stroke="#991b1b" strokeWidth="5" strokeLinecap="round" />
              <path d="M 110 155 C 110 30, 370 30, 370 155 L 342 115 L 138 115 Z" fill="#94a3b8" stroke="#111" strokeWidth="11" strokeLinejoin="round" />
              <path d="M 240 38 C 295 -30, 375 -10, 350 52 C 310 36, 270 40, 240 38 Z" fill="#dc2626" stroke="#111" strokeWidth="9" />
            </g>
          )}}

          {{role === "banker" && (
            <g>
              {/* Cappello mercantile + Occhiali tondi + Pizzetto grigio */}
              <path d="M 122 125 C 135 45, 345 45, 358 125 Z" fill="#064e3b" stroke="#111" strokeWidth="10" />
              <rect x="115" y="95" width="250" height="32" rx="14" fill="#78350f" stroke="#111" strokeWidth="9" />
              <polygon points="222,235 258,235 240,275" fill="#64748b" stroke="#111" strokeWidth="7" strokeLinejoin="round" />
            </g>
          )}}

          {{role === "noble_blonde" && (
            <g>
              {/* Capelli biondi ricci + Berretto piumato viola */}
              <path d="M 116 145 C 125 45, 355 45, 364 145 C 320 98, 160 98, 116 145 Z" fill="#eab308" stroke="#111" strokeWidth="10" />
              <ellipse cx="240" cy="58" rx="128" ry="28" fill="#581c87" stroke="#111" strokeWidth="10" />
              <path d="M 295 45 C 345 -18, 395 5, 355 52" fill="#facc15" stroke="#111" strokeWidth="7" />
            </g>
          )}}

          {{role === "noble_dark" && (
            <g>
              {/* Capelli neri + Barba appuntita Tudor + Berretto rosso */}
              <path d="M 116 145 C 125 45, 355 45, 364 145 C 320 98, 160 98, 116 145 Z" fill="#18181b" stroke="#111" strokeWidth="10" />
              <polygon points="215,230 265,230 240,278" fill="#18181b" stroke="#111" strokeWidth="7" strokeLinejoin="round" />
              <ellipse cx="240" cy="58" rx="128" ry="28" fill="#7c2d12" stroke="#111" strokeWidth="10" />
            </g>
          )}}

          {/* OCCHI CON PUPILLE ESPRESSIVE CHE GUARDANO NELLA DIREZIONE DELLA SCENA */}
          {{isBlinking ? (
            <g>
              <line x1="168" y1="158" x2="212" y2="158" stroke="#111" strokeWidth="9" strokeLinecap="round" />
              <line x1="268" y1="158" x2="312" y2="158" stroke="#111" strokeWidth="9" strokeLinecap="round" />
            </g>
          ) : expression === "shocked" ? (
            <g>
              <circle cx="190" cy="158" r="26" fill="#fff" stroke="#111" strokeWidth="8" />
              <circle cx={{190 + lookX}} cy={{158 + lookY}} r="7" fill="#111" />
              <circle cx="290" cy="158" r="26" fill="#fff" stroke="#111" strokeWidth="8" />
              <circle cx={{290 + lookX}} cy={{158 + lookY}} r="7" fill="#111" />
              <path d="M 162 120 Q 190 105 216 122" stroke="#111" strokeWidth="8" fill="none" strokeLinecap="round" />
              <path d="M 264 122 Q 290 105 318 120" stroke="#111" strokeWidth="8" fill="none" strokeLinecap="round" />
            </g>
          ) : (
            <g>
              <circle cx={{190 + lookX}} cy={{158 + lookY}} r="11" fill="#111" />
              <circle cx={{187 + lookX}} cy={{154 + lookY}} r="3.5" fill="#fff" />
              <circle cx={{290 + lookX}} cy={{158 + lookY}} r="11" fill="#111" />
              <circle cx={{287 + lookX}} cy={{154 + lookY}} r="3.5" fill="#fff" />

              {/* Sopracciglia espressive */}
              {{expression === "furious" && (
                <>
                  <line x1="158" y1="122" x2="216" y2="144" stroke="#111" strokeWidth="11" strokeLinecap="round" />
                  <line x1="322" y1="122" x2="264" y2="144" stroke="#111" strokeWidth="11" strokeLinecap="round" />
                </>
              )}}
              {{expression === "scheming" && (
                <>
                  <line x1="160" y1="132" x2="215" y2="142" stroke="#111" strokeWidth="9" strokeLinecap="round" />
                  <path d="M 265 140 Q 292 118 320 130" stroke="#111" strokeWidth="9" fill="none" strokeLinecap="round" />
                </>
              )}}
              {{(expression === "nervous" || expression === "pleading" || expression === "rejected") && (
                <>
                  <line x1="158" y1="142" x2="214" y2="128" stroke="#111" strokeWidth="9" strokeLinecap="round" />
                  <line x1="266" y1="128" x2="322" y2="142" stroke="#111" strokeWidth="9" strokeLinecap="round" />
                </>
              )}}
              {{(expression === "confident" || expression === "proud" || expression === "whisper") && (
                <>
                  <path d="M 162 132 Q 190 118 216 132" stroke="#111" strokeWidth="8" fill="none" strokeLinecap="round" />
                  <path d="M 264 132 Q 290 118 318 132" stroke="#111" strokeWidth="8" fill="none" strokeLinecap="round" />
                </>
              )}}
            </g>
          )}}

          {/* Occhiali del Banchiere */}
          {{role === "banker" && (
            <g>
              <circle cx="190" cy="158" r="30" fill="none" stroke="#eab308" strokeWidth="7" />
              <circle cx="290" cy="158" r="30" fill="none" stroke="#eab308" strokeWidth="7" />
              <line x1="220" y1="158" x2="260" y2="158" stroke="#eab308" strokeWidth="7" />
            </g>
          )}}

          {/* Baffi per Re e Generale */}
          {{role === "king" && (
            <path d="M 185 192 Q 240 175 295 192" stroke="#b45309" strokeWidth="14" fill="none" strokeLinecap="round" />
          )}}
          {{role === "general" && (
            <path d="M 190 190 Q 240 178 290 190" stroke="#475569" strokeWidth="12" fill="none" strokeLinecap="round" />
          )}}

          {/* Goccia di sudore per tensione */}
          {{(expression === "nervous" || expression === "pleading") && (
            <path d="M 138 105 C 138 105, 116 136, 128 150 C 140 162, 158 150, 146 130 Z" fill="#38bdf8" stroke="#111" strokeWidth="6" />
          )}}

          {/* BOCCHE PULITE ED ESPRESSIVE (ZERO APERTURA CASUALE RIPETITIVA!) */}
          {{expression === "confident" || expression === "proud" ? (
            <path d="M 202 204 Q 240 228 282 198" stroke="#111" strokeWidth="9" fill="none" strokeLinecap="round" />
          ) : expression === "scheming" ? (
            <path d="M 198 208 Q 245 232 288 190" stroke="#111" strokeWidth="10" fill="none" strokeLinecap="round" />
          ) : expression === "shocked" ? (
            <ellipse cx="240" cy="212" rx="16" ry="20" fill="#111" />
          ) : expression === "whisper" ? (
            <ellipse cx="252" cy="210" rx="14" ry="11" fill="#111" />
          ) : expression === "furious" ? (
            <path d="M 198 220 Q 240 192 282 220" stroke="#111" strokeWidth="10" fill="none" strokeLinecap="round" />
          ) : (
            <path d="M 200 212 Q 220 202 240 212 Q 260 222 280 212" stroke="#111" strokeWidth="8" fill="none" strokeLinecap="round" />
          )}}
        </g>
      </svg>
    </div>
  );
}};

// AMBIENTE 1: GRANDE SALA DEL TRONO TUDOR IN PROSPETTIVA 2.5D (Oversize 1680px: ZERO BORDI NERI!)
const GrandThroneRoomSet = ({{ panX = 0, panY = 0, children }}: {{ panX?: number; panY?: number; children?: React.ReactNode }}) => (
  <AbsoluteFill style={{ backgroundColor: "#1e293b", overflow: "hidden" }}>
    <div style={{ position: "absolute", left: -300, top: -180, width: 1680, height: 2280, transform: `translate(${{panX * 0.45}}px, ${{panY * 0.35}}px)` }}>
      <svg width="1680" height="2280" viewBox="0 0 1680 2280">
        <defs>
          <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#334155" />
          </linearGradient>
          <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>
        </defs>

        {/* Parete di fondo in pietra lavorata */}
        <rect width="1680" height="1520" fill="url(#wallGrad)" />
        {{[220, 400, 580, 760, 940, 1120, 1300].map((y, r) => (
          <g key={{y}}>
            <line x1="0" y1={{y}} x2="1680" y2={{y}} stroke="#0f172a" strokeWidth="6" opacity="0.65" />
            {{[200, 520, 840, 1160, 1480].map((x) => (
              <line key={{x}} x1={{x + (r % 2) * 150}} y1={{y - 180}} x2={{x + (r % 2) * 150}} y2={{y}} stroke="#0f172a" strokeWidth="6" opacity="0.65" />
            ))}}
          </g>
        ))}}

        {/* Grandi Vetrate Gotiche Cattedrale (ai lati esterni) */}
        {{[380, 1300].map((cx) => (
          <g key={{cx}}>
            <path d={{`M ${{cx - 115}} 980 L ${{cx - 115}} 420 Q ${{cx}} 230 ${{cx + 115}} 420 L ${{cx + 115}} 980 Z`}} fill="#0284c7" stroke="#0f172a" strokeWidth="18" />
            <path d={{`M ${{cx - 95}} 960 L ${{cx - 95}} 430 Q ${{cx}} 265 ${{cx + 95}} 430 L ${{cx + 95}} 960 Z`}} fill="#38bdf8" opacity="0.75" />
            <line x1={{cx}} y1="265" x2={{cx}} y2="980" stroke="#0f172a" strokeWidth="12" />
            <line x1={{cx - 110}} y1="620" x2={{cx + 110}} y2="620" stroke="#0f172a" strokeWidth="12" />
          </g>
        ))}}

        {/* Colonne Monumentali in Pietra (Le torce sono montate QUI sulle colonne, mai sulle finestre!) */}
        {{[570, 1110].map((px) => (
          <g key={{px}}>
            <rect x={{px - 55}} y="120" width="110" height="1400" fill="#475569" stroke="#0f172a" strokeWidth="12" />
            <rect x={{px - 75}} y="1460" width="150" height="65" rx="8" fill="#64748b" stroke="#0f172a" strokeWidth="10" />
          </g>
        ))}}

        {/* Arazzo Reale Tudor centrale */}
        <polygon points="710,210 970,210 970,860 840,950 710,860" fill="#7f1d1d" stroke="#111" strokeWidth="12" />
        <polygon points="732,235 948,235 948,840 840,918 732,840" fill="none" stroke="#eab308" strokeWidth="8" />
        <circle cx="840" cy="540" r="68" fill="#eab308" stroke="#111" strokeWidth="8" />
        <polygon points="790,430 890,430 905,375 865,400 840,360 815,400 775,375" fill="#eab308" stroke="#111" strokeWidth="6" />

        {/* Pavimento a Scacchi in Prospettiva 3D + Tappeto Reale con Gradini */}
        <rect x="0" y="1520" width="1680" height="760" fill="url(#floorGrad)" stroke="#0f172a" strokeWidth="14" />
        {{[-600, -350, -150, 0, 150, 350, 600].map((offset) => (
          <line key={{offset}} x1={{840 + offset * 0.4}} y1="1520" x2={{840 + offset * 1.9}} y2="2280" stroke="#334155" strokeWidth="6" />
        ))}}
        {{[1620, 1740, 1890, 2070].map((fy) => (
          <line key={{fy}} x1="0" y1={{fy}} x2="1680" y2={{fy}} stroke="#334155" strokeWidth="6" />
        ))}}

        {/* Pedana e Tappeto Rosso Reale */}
        <polygon points="560,1520 1120,1520 1290,2280 390,2280" fill="#991b1b" stroke="#eab308" strokeWidth="16" />
      </svg>

      {/* Torce montate esattamente sulle colonne di pietra */}
      <WallTorch x={{525}} y={{620}} />
      <WallTorch x={{1065}} y={{620}} />
    </div>

    {{children}}
  </AbsoluteFill>
);

// AMBIENTE 2: CAMERA PRIVATA REALE DEL "GROOM OF THE STOOL" (Con letto a baldacchino, libreria, candelabri e Trono-Toilette)
const RoyalPrivyChamberSet = ({{ panX = 0, panY = 0, children }}: {{ panX?: number; panY?: number; children?: React.ReactNode }}) => (
  <AbsoluteFill style={{ backgroundColor: "#2e1065", overflow: "hidden" }}>
    <div style={{ position: "absolute", left: -300, top: -180, width: 1680, height: 2280, transform: `translate(${{panX * 0.45}}px, ${{panY * 0.35}}px)` }}>
      <svg width="1680" height="2280" viewBox="0 0 1680 2280">
        {/* Pareti in boiserie di quercia scura e tappezzeria damascata */}
        <rect width="1680" height="1520" fill="#3b0764" />
        <rect x="0" y="1080" width="1680" height="440" fill="#451a03" stroke="#111" strokeWidth="12" />
        {{[260, 480, 700, 920, 1140, 1360].map((x) => (
          <rect key={{x}} x={{x}} y="1125" width="170" height="350" rx="8" fill="#5c2408" stroke="#290f02" strokeWidth="8" />
        ))}}

        {/* Grande Libreria Reale piena di volumi colorati stile Ricks Clips a destra */}
        <g transform="translate(1050, 380)">
          <rect x="0" y="0" width="360" height="700" fill="#451a03" stroke="#111" strokeWidth="12" />
          {{[140, 310, 480].map((sy, idx) => (
            <g key={{sy}}>
              <rect x="18" y={{sy}} width="324" height="22" fill="#78350f" stroke="#111" strokeWidth="6" />
              {{[35, 75, 115, 160, 200, 245, 285].map((bx, b) => (
                <rect
                  key={{bx}}
                  x={{bx}}
                  y={{sy - 105 + (b % 3) * 12}}
                  width="32"
                  height={{105 - (b % 3) * 12}}
                  fill={{["#ef4444", "#3b82f6", "#eab308", "#10b981", "#a855f7"][(b + idx) % 5]}}
                  stroke="#111"
                  strokeWidth="5"
                />
              ))}}
            </g>
          ))}}
        </g>

        {/* Tende di velluto rosso reale a sinistra */}
        <path d="M 220 180 L 650 180 L 580 1120 L 220 1120 Z" fill="#7f1d1d" stroke="#111" strokeWidth="12" />
        <rect x="200" y="160" width="480" height="32" rx="12" fill="#eab308" stroke="#111" strokeWidth="8" />

        {/* Pavimento in parquet di legno in prospettiva */}
        <rect x="0" y="1520" width="1680" height="760" fill="#290f02" stroke="#111" strokeWidth="14" />
        <ellipse cx="840" cy="1780" rx="480" ry="165" fill="#991b1b" stroke="#eab308" strokeWidth="12" />

        {/* IL "ROYAL CLOSE STOOL" (Il Trono-Gabinetto in velluto cremisi e oro) */}
        <g transform="translate(420, 860)">
          <rect x="35" y="0" width="350" height="440" rx="28" fill="#991b1b" stroke="#111" strokeWidth="12" />
          <rect x="65" y="30" width="290" height="380" rx="18" fill="#7f1d1d" stroke="#eab308" strokeWidth="8" />
          <rect x="10" y="400" width="400" height="220" rx="20" fill="#b91c1c" stroke="#111" strokeWidth="12" />
          <ellipse cx="210" cy="442" rx="102" ry="30" fill="#0f172a" stroke="#eab308" strokeWidth="9" />
        </g>
      </svg>
      <WallTorch x={{820}} y={{360}} scale={{1.05}} />
    </div>
    {{children}}
  </AbsoluteFill>
);

// AMBIENTE 3: CORRIDOIO DEL CASTELLO CON GRANDE PORTA IN QUERCia E COLONNE
const CastleCorridorSet = ({{ panX = 0, locked = false, children }}: {{ panX?: number; locked?: boolean; children?: React.ReactNode }}) => (
  <AbsoluteFill style={{ backgroundColor: "#334155", overflow: "hidden" }}>
    <div style={{ position: "absolute", left: -300, top: -180, width: 1680, height: 2280, transform: `translateX(${{panX * 0.45}}px)` }}>
      <svg width="1680" height="2280" viewBox="0 0 1680 2280">
        <rect width="1680" height="1540" fill="#475569" />
        {{[240, 440, 640, 840, 1040, 1240, 1440].map((y, r) => (
          <line key={{y}} x1="0" y1={{y}} x2="1680" y2={{y}} stroke="#1e293b" strokeWidth="6" />
        ))}}
        <rect x="0" y="1540" width="1680" height="740" fill="#1e293b" stroke="#0f172a" strokeWidth="14" />

        {/* Grande Portale ad Arco della Stanza Segreta */}
        <g transform="translate(440, 460)">
          <path d="M 40 1080 L 40 420 Q 400 40 760 420 L 760 1080 Z" fill="#94a3b8" stroke="#111" strokeWidth="14" />
          <path d="M 95 1080 L 95 450 Q 400 120 705 450 L 705 1080 Z" fill="#78350f" stroke="#111" strokeWidth="14" />
          <line x1="400" y1="280" x2="400" y2="1080" stroke="#111" strokeWidth="10" />
          <rect x="310" y="360" width="180" height="130" fill="#0f172a" stroke="#111" strokeWidth="10" />
          <line x1="370" y1="360" x2="370" y2="490" stroke="#475569" strokeWidth="8" />
          <line x1="430" y1="360" x2="430" y2="490" stroke="#475569" strokeWidth="8" />
          <rect x="200" y="590" width="400" height="115" rx="14" fill="#eab308" stroke="#111" strokeWidth="9" />
          <text x="400" y="642" fill="#111" fontSize="34" fontWeight="900" fontFamily="Arial Black, sans-serif" textAnchor="middle">
            PRIVY CHAMBER
          </text>
          <text x="400" y="684" fill="#991b1b" fontSize="27" fontWeight="900" fontFamily="Arial Black, sans-serif" textAnchor="middle">
            GROOM OF THE STOOL
          </text>

          {{locked && (
            <g>
              <rect x="30" y="730" width="740" height="60" rx="12" fill="#334155" stroke="#111" strokeWidth="12" />
              <rect x="345" y="700" width="110" height="120" rx="18" fill="#eab308" stroke="#111" strokeWidth="10" />
              <circle cx="400" cy="750" r="15" fill="#111" />
            </g>
          )}}
        </g>
      </svg>
      <WallTorch x={{350}} y={{620}} />
      <WallTorch x={{1250}} y={{620}} />
    </div>
    {{children}}
  </AbsoluteFill>
);

// PRIMO PIANO SFOCATO CINEMATOGRAFICO (Come il tavolo/scrivania in primo piano su Ricks Clips)
const ForegroundBlurredTable = ({{ type }}: {{ type: "gold" | "royal_seal" }}) => (
  <div
    style={{
      position: "absolute",
      bottom: -40,
      left: -80,
      right: -80,
      height: 440,
      backgroundColor: "#451a03",
      borderTop: "14px solid #111",
      filter: "blur(3px)",
      zIndex: 25,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    }}
  >
    <div style={{ width: 880, height: 320, backgroundColor: "#7f1d1d", border: "10px solid #eab308", borderRadius: 16 }} />
    {{type === "royal_seal" && (
      <div style={{ position: "absolute", top: -95, fontSize: 0 }}>
        <svg width="260" height="220" viewBox="0 0 260 220">
          <ellipse cx="130" cy="155" rx="115" ry="45" fill="#eab308" stroke="#111" strokeWidth="10" />
          <polygon points="55,145 205,145 220,45 168,85 130,20 92,85 40,45" fill="#facc15" stroke="#111" strokeWidth="10" strokeLinejoin="round" />
        </svg>
      </div>
    )}}
  </div>
);

export const GroomStory: React.FC = () => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const time = frame / fps;

  // Trova il segmento vocale attivo (da 0 a 17) per cambiare scena in perfetto sync con la voce!
  let activeSeg = TIMINGS[TIMINGS.length - 1];
  for (const seg of TIMINGS) {{
    if (time >= seg.start && time < seg.end) {{
      activeSeg = seg;
      break;
    }}
  }}
  const idx = activeSeg.index;
  const localP = Math.max(0, Math.min(1, (time - activeSeg.start) / Math.max(0.01, activeSeg.duration)));

  // Movimento camera fluido e contenuto (MAI fuori dai bordi!)
  const camScale = interpolate(localP, [0, 1], [1.03, 1.13]);
  const camPanX = interpolate(localP, [0, 1], idx % 2 === 0 ? [-28, 28] : [28, -28]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a", overflow: "hidden" }}>
      <Audio src={{staticFile("voce.mp3")}} />

      <AbsoluteFill style={{ transform: `scale(${{camScale}})` }}>
        {/* SHOT 0: "Imagine landing the most powerful, highly paid job in the entire kingdom..." */}
        {{idx === 0 && (
          <GrandThroneRoomSet panX={{camPanX}}>
            <HistoricalCharacter
              role="groom"
              expression={{localP < 0.5 ? "confident" : "proud"}}
              lookX={{interpolate(localP, [0, 0.5, 1], [-5, 5, 0])}}
              x={{0}}
              y={{40}}
              scale={{1.18}}
              leftArm={{interpolate(localP, [0, 1], [25, -40])}}
              rightArm={{interpolate(localP, [0, 1], [-25, 45])}}
              propRight="key"
              propLeft="goldbag"
            />
            <ForegroundBlurredTable type="royal_seal" />
          </GrandThroneRoomSet>
        )}}

        {/* SHOT 1: "...but your only actual duty is..." */}
        {{idx === 1 && (
          <RoyalPrivyChamberSet panX={{camPanX}}>
            <HistoricalCharacter
              role="king"
              expression="proud"
              lookX={{6}}
              x={{-165}}
              y={{105}}
              scale={{1.12}}
              rightArm={{interpolate(localP, [0, 0.5, 1], [-20, -65, -25])}}
              propRight="bell"
            />
            <HistoricalCharacter
              role="groom"
              expression="confident"
              lookX={{-6}}
              x={{205}}
              y={{115}}
              scale={{1.08}}
            />
          </RoyalPrivyChamberSet>
        )}}

        {/* SHOT 2: "...wiping your boss's butt." (Zoom drammatico sulla faccia scioccata del Groom col rotolo reale!) */}
        {{idx === 2 && (
          <RoyalPrivyChamberSet panX={{0}}>
            <HistoricalCharacter
              role="king"
              expression="confident"
              x={{-240}}
              y={{140}}
              scale={{0.98}}
            />
            <HistoricalCharacter
              role="groom"
              expression={{localP < 0.35 ? "nervous" : "shocked"}}
              lookY={{4}}
              x={{140}}
              y={{110}}
              scale={{interpolate(localP, [0, 1], [1.15, 1.32])}}
              rightArm={{interpolate(localP, [0, 1], [-20, -75])}}
              propRight="paper"
            />
          </RoyalPrivyChamberSet>
        )}}

        {/* SHOT 3: "Back in Tudor England," */}
        {{idx === 3 && (
          <GrandThroneRoomSet panX={{camPanX}}>
            <HistoricalCharacter
              role="king"
              expression="proud"
              x={{0}}
              y={{80}}
              scale={{1.22}}
              leftArm={{35}}
              rightArm={{-45}}
              propRight="key"
            />
          </GrandThroneRoomSet>
        )}}

        {/* SHOT 4: "the most coveted role in the royal court wasn't a top general..." */}
        {{idx === 4 && (
          <GrandThroneRoomSet panX={{camPanX}}>
            <HistoricalCharacter
              role="general"
              expression={{localP < 0.6 ? "proud" : "rejected"}}
              lookX={{localP < 0.6 ? 0 : -6}}
              x={{0}}
              y={{105}}
              scale={{1.16}}
              rightArm={{interpolate(localP, [0, 0.5, 1], [-60, -85, -25])}}
              propRight="sword"
              propLeft="shield"
            />
            {{localP > 0.58 && (
              <svg width="460" height="460" viewBox="0 0 460 460" style={{ position: "absolute", left: 310, top: 690, zIndex: 30 }}>
                <line x1="60" y1="60" x2="400" y2="400" stroke="#dc2626" strokeWidth="44" strokeLinecap="round" />
                <line x1="400" y1="60" x2="60" y2="400" stroke="#dc2626" strokeWidth="44" strokeLinecap="round" />
              </svg>
            )}}
          </GrandThroneRoomSet>
        )}}

        {/* SHOT 5: "...or a wealthy banker." */}
        {{idx === 5 && (
          <GrandThroneRoomSet panX={{-camPanX}}>
            <HistoricalCharacter
              role="banker"
              expression={{localP < 0.55 ? "confident" : "rejected"}}
              x={{0}}
              y={{105}}
              scale={{1.16}}
              leftArm={{40}}
              rightArm={{-50}}
              propRight="goldbag"
              propLeft="goldbag"
            />
            {{localP > 0.55 && (
              <svg width="460" height="460" viewBox="0 0 460 460" style={{ position: "absolute", left: 310, top: 690, zIndex: 30 }}>
                <line x1="60" y1="60" x2="400" y2="400" stroke="#dc2626" strokeWidth="44" strokeLinecap="round" />
                <line x1="400" y1="60" x2="60" y2="400" stroke="#dc2626" strokeWidth="44" strokeLinecap="round" />
              </svg>
            )}}
          </GrandThroneRoomSet>
        )}}

        {/* SHOT 6: "It was the Groom of the Stool—" */}
        {{idx === 6 && (
          <CastleCorridorSet panX={{camPanX}}>
            <HistoricalCharacter
              role="groom"
              expression="proud"
              x={{0}}
              y={{135}}
              scale={{1.24}}
              rightArm={{interpolate(localP, [0, 1], [-15, -75])}}
              propRight="key"
            />
          </CastleCorridorSet>
        )}}

        {/* SHOT 7: "the guy officially in charge of the King's toilet time." */}
        {{idx === 7 && (
          <CastleCorridorSet panX={{camPanX}}>
            <HistoricalCharacter
              role="king"
              expression="confident"
              lookX={{5}}
              x={{interpolate(localP, [0, 1], [-240, -150])}}
              y={{145}}
              scale={{1.05}}
              walk
            />
            <HistoricalCharacter
              role="groom"
              expression="nervous"
              lookX={{-5}}
              x={{interpolate(localP, [0, 1], [260, 175])}}
              y={{155}}
              scale={{1.05}}
              walk
              rightArm={{-60}}
              propRight="paper"
            />
          </CastleCorridorSet>
        )}}

        {/* SHOT 8: "It sounds like an absolute punishment," */}
        {{idx === 8 && (
          <RoyalPrivyChamberSet panX={{0}}>
            <HistoricalCharacter
              role="groom"
              expression="nervous"
              lookY={{5}}
              x={{0}}
              y={{125}}
              scale={{1.22}}
              leftArm={{-45}}
              rightArm={{-65}}
              propRight="paper"
            />
          </RoyalPrivyChamberSet>
        )}}

        {/* SHOT 9: "but the richest nobles literally fought each other for this job." (2 nobili diversi che duellano!) */}
        {{idx === 9 && (
          <CastleCorridorSet panX={{-camPanX}}>
            <HistoricalCharacter
              role="noble_blonde"
              expression="furious"
              lookX={{6}}
              x={{-205 + Math.sin(frame * 0.28) * 42}}
              y={{155}}
              scale={{1.06}}
              walk
              rightArm={{-55 + Math.sin(frame * 0.38) * 38}}
              propRight="sword"
            />
            <HistoricalCharacter
              role="noble_dark"
              expression="furious"
              lookX={{6}}
              x={{205 - Math.sin(frame * 0.28) * 42}}
              y={{155}}
              scale={{1.06}}
              flip
              walk
              rightArm={{-55 + Math.cos(frame * 0.38) * 38}}
              propRight="sword"
            />
            <svg
              width="200"
              height="200"
              viewBox="0 0 200 200"
              style={{
                position: "absolute",
                left: 440,
                top: 760,
                zIndex: 25,
                transform: `scale(${{0.75 + Math.abs(Math.sin(frame * 0.4)) * 0.45}}) rotate(${{frame * 5}}deg)`,
              }}
            >
              <polygon points="100,10 122,78 190,100 122,122 100,190 78,122 10,100 78,78" fill="#facc15" stroke="#111" strokeWidth="6" />
            </svg>
          </CastleCorridorSet>
        )}}

        {/* SHOT 10: "Why?" (Primo piano intrigante del Groom che alza il sopracciglio) */}
        {{idx === 10 && (
          <CastleCorridorSet panX={{0}}>
            <HistoricalCharacter
              role="groom"
              expression="scheming"
              lookX={{4}}
              x={{0}}
              y={{160}}
              scale={{1.38}}
              rightArm={{-55}}
              propRight="key"
            />
          </CastleCorridorSet>
        )}}

        {/* SHOT 11: "Because you were locked in a private room with the King every single day." */}
        {{idx === 11 && (
          <CastleCorridorSet panX={{0}} locked={{localP > 0.3}}>
            <HistoricalCharacter role="king" expression="confident" lookX={{5}} x={{-175}} y={{165}} scale={{1.04}} />
            <HistoricalCharacter role="groom" expression="scheming" lookX={{-5}} x={{175}} y={{165}} scale={{1.06}} rightArm={{-50}} propRight="key" />
          </CastleCorridorSet>
        )}}

        {/* SHOT 12: "You became his ultimate confidant." */}
        {{idx === 12 && (
          <RoyalPrivyChamberSet panX={{camPanX}}>
            <HistoricalCharacter role="king" expression="whisper" lookX={{7}} x={{-155}} y={{130}} scale={{1.18}} rightArm={{-55}} />
            <HistoricalCharacter role="groom" expression="confident" lookX={{-7}} x={{175}} y={{135}} scale={{1.18}} rightArm={{-35}} propRight="scroll" />
          </RoyalPrivyChamberSet>
        )}}

        {/* SHOT 13: "You knew all his dark secrets," */}
        {{idx === 13 && (
          <RoyalPrivyChamberSet panX={{-camPanX}}>
            <HistoricalCharacter
              role="groom"
              expression="scheming"
              lookX={{-6}}
              x={{60}}
              y={{140}}
              scale={{1.32}}
              rightArm={{-65}}
              propRight="scroll"
            />
          </RoyalPrivyChamberSet>
        )}}

        {/* SHOT 14: "you knew who he hated," */}
        {{idx === 14 && (
          <GrandThroneRoomSet panX={{camPanX}}>
            <HistoricalCharacter role="king" expression="furious" lookX={{7}} x={{-180}} y={{120}} scale={{1.12}} rightArm={{-70}} />
            <HistoricalCharacter role="noble_blonde" expression="nervous" lookX={{-7}} x={{190}} y={{135}} scale={{1.06}} />
          </GrandThroneRoomSet>
        )}}

        {/* SHOT 15: "and you controlled exactly who got to speak with him." */}
        {{idx === 15 && (
          <CastleCorridorSet panX={{camPanX}} locked>
            <HistoricalCharacter role="noble_dark" expression="pleading" lookX={{6}} x={{-230}} y={{175}} scale={{0.96}} leftArm={{-55}} rightArm={{-60}} />
            <HistoricalCharacter
              role="groom"
              expression="scheming"
              lookX={{-6}}
              x={{165}}
              y={{130}}
              scale={{1.2}}
              rightArm={{interpolate(localP, [0, 1], [-80, -30])}}
              propRight="key"
            />
          </CastleCorridorSet>
        )}}

        {/* SHOT 16: "So, while everyone else was outside begging for power," */}
        {{idx === 16 && (
          <CastleCorridorSet panX={{-camPanX}} locked>
            <HistoricalCharacter role="general" expression="pleading" lookX={{5}} x={{-220}} y={{165}} scale={{0.98}} leftArm={{-50}} />
            <HistoricalCharacter role="banker" expression="pleading" lookX={{-5}} x={{220}} y={{165}} scale={{0.98}} flip rightArm={{-60}} propRight="goldbag" />
          </CastleCorridorSet>
        )}}

        {/* SHOT 17: "the guy holding the royal toilet paper was actually secretly running the country." */}
        {{idx === 17 && (
          <GrandThroneRoomSet panX={{0}}>
            <svg width="1080" height="1920" style={{ position: "absolute", top: 0, left: 0, zIndex: 20 }}>
              <line x1="540" y1="180" x2="225" y2="1120" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
              <line x1="540" y1="180" x2="855" y2="1120" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
            </svg>
            <HistoricalCharacter
              role="groom"
              expression="scheming"
              lookY={{2}}
              x={{0}}
              y={{65}}
              scale={{interpolate(localP, [0, 1], [1.24, 1.36])}}
              leftArm={{45}}
              rightArm={{-65}}
              propRight="paper"
              propLeft="goldbag"
            />
            <HistoricalCharacter role="king" expression="confident" x={{-310}} y={{250}} scale={{0.82}} />
            <HistoricalCharacter role="general" expression="pleading" x={{310}} y={{250}} scale={{0.82}} flip />
          </GrandThroneRoomSet>
        )}}
      </AbsoluteFill>

      {/* Vignettatura cinematografica morbida */}
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle, rgba(0,0,0,0) 60%, rgba(0,0,0,0.52) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
}};
"""

with open("src/GroomStory.tsx", "w") as f:
    f.write(story_tsx)

print("✅ Tutte le 18 scene dinamiche + sfondi 2.5D oversize + personaggi storici unici sono pronti!")
