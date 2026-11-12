import subprocess
import math

# Legge la durata esatta dell'audio per sincronizzare tutte le 10 scene al millesimo di secondo
try:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", "public/voce.mp3"
    ]).decode().strip()
    duration_sec = float(out)
except Exception:
    duration_sec = 39.5

fps = 60
total_frames = int(math.ceil(duration_sec * fps))

root_code = f"""import {{ Composition }} from "remotion";
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
"""

with open("src/Root.tsx", "w") as f:
    f.write(root_code)

story_code = """import { AbsoluteFill, Audio, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import React from "react";

// TORCIA MEDIEVALE ANIMATA (Fiamma viva + bagliore caldo)
const Torch = ({ x, y, scale = 1 }: { x: number; y: number; scale?: number }) => {
  const frame = useCurrentFrame();
  const flicker = Math.sin(frame * 0.35 + x) * 0.12 + Math.cos(frame * 0.22) * 0.08;
  const flameH = 1 + flicker;

  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `scale(${scale})` }}>
      {/* Alone di luce calda */}
      <div
        style={{
          position: "absolute",
          left: -140,
          top: -160,
          width: 340,
          height: 340,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,160,40,0.42) 0%, rgba(255,100,0,0) 70%)",
          transform: `scale(${1 + flicker * 0.5})`,
          pointerEvents: "none",
        }}
      />
      <svg width="80" height="180" viewBox="0 0 80 180" style={{ overflow: "visible" }}>
        {/* Supporto in ferro */}
        <rect x="28" y="95" width="24" height="14" rx="4" fill="#334155" stroke="#111" strokeWidth="5" />
        <polygon points="22,85 58,85 48,165 32,165" fill="#475569" stroke="#111" strokeWidth="6" strokeLinejoin="round" />
        {/* Fiamma esterna */}
        <g transform={`translate(40, 82) scale(1, ${flameH}) translate(-40, -82)`}>
          <path
            d="M 40 10 C 65 40, 68 70, 40 85 C 12 70, 15 40, 40 10 Z"
            fill="#f97316"
            stroke="#111"
            strokeWidth="5"
          />
          <path
            d="M 40 28 C 55 48, 55 68, 40 78 C 25 68, 25 48, 40 28 Z"
            fill="#facc15"
          />
        </g>
      </svg>
    </div>
  );
};

// STENDARDO REALE TUDOR (Disegnato in SVG puro, zero font mancanti)
const RoyalBanner = ({ x, y, color = "#991b1b" }: { x: number; y: number; color?: string }) => {
  const frame = useCurrentFrame();
  const sway = Math.sin(frame * 0.05 + x) * 2;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `rotate(${sway}deg)`, transformOrigin: "top center" }}>
      <svg width="200" height="420" viewBox="0 0 200 420">
        <rect x="10" y="0" width="180" height="16" rx="8" fill="#eab308" stroke="#111" strokeWidth="6" />
        <polygon points="20,16 180,16 180,340 100,400 20,340" fill={color} stroke="#111" strokeWidth="8" strokeLinejoin="round" />
        <polygon points="35,30 165,30 165,325 100,375 35,325" fill="none" stroke="#eab308" strokeWidth="5" />
        {/* Stemma Corona + Giglio Reale in SVG */}
        <polygon points="60,190 140,190 150,140 120,165 100,130 80,165 50,140" fill="#eab308" stroke="#111" strokeWidth="5" strokeLinejoin="round" />
        <circle cx="100" cy="245" r="22" fill="#eab308" stroke="#111" strokeWidth="5" />
      </svg>
    </div>
  );
};

// PERSONAGGIO RICKS CLIPS VERSIONE STORICA MEDIEVALE COMPLETA
const TudorCharacter = ({
  role,
  mood,
  x = 0,
  y = 0,
  scale = 1,
  flip = false,
  walk = false,
  talking = false,
  leftArmAngle = 20,
  rightArmAngle = -20,
  propRight = "none",
  propLeft = "none",
}: {
  role: "king" | "groom" | "general" | "banker" | "noble1" | "noble2" | "peasant";
  mood: "happy" | "proud" | "sweat" | "shock" | "angry" | "smirk" | "whisper" | "beg";
  x?: number;
  y?: number;
  scale?: number;
  flip?: boolean;
  walk?: boolean;
  talking?: boolean;
  leftArmAngle?: number;
  rightArmAngle?: number;
  propRight?: "none" | "paper" | "key" | "sword" | "goldbag" | "scroll" | "scepter";
  propLeft?: "none" | "shield" | "goldbag";
}) => {
  const frame = useCurrentFrame();

  // Movimento fluido del respiro o della camminata a 60 fps
  const bob = walk ? Math.abs(Math.sin(frame * 0.18)) * 18 : Math.sin(frame * 0.08 + x) * 5;
  const legSwing = walk ? Math.sin(frame * 0.18) * 32 : 0;
  const headTilt = Math.sin(frame * 0.05 + x) * 2.5;

  // Battito di ciglia naturale ogni 3 secondi
  const isBlinking = frame % 190 > 182;

  // Bocca animata se il personaggio sta parlando
  const talkOpen = talking ? Math.abs(Math.sin(frame * 0.35)) * 16 : 0;

  // Colori abiti storici
  const tunicColors: Record<string, string> = {
    king: "#991b1b",
    groom: "#1e40af",
    general: "#64748b",
    banker: "#065f46",
    noble1: "#581c87",
    noble2: "#7c2d12",
    peasant: "#78716c",
  };
  const bodyColor = tunicColors[role] || "#1e40af";

  return (
    <div
      style={{
        position: "absolute",
        left: `calc(50% + ${x}px)`,
        top: `calc(54% + ${y - bob}px)`,
        transform: `translate(-50%, -50%) scale(${scale}) scaleX(${flip ? -1 : 1})`,
        width: 460,
        height: 800,
      }}
    >
      <svg viewBox="0 0 460 800" width="100%" height="100%" style={{ overflow: "visible" }}>
        {/* OMBRA A TERRA */}
        <ellipse cx="230" cy="730" rx="95" ry="18" fill="rgba(0,0,0,0.35)" />

        {/* MANTELLO POSTERIORE (Re e Generale) */}
        {(role === "king" || role === "general") && (
          <path
            d="M 115 290 L 75 620 C 150 650, 310 650, 385 620 L 345 290 Z"
            fill={role === "king" ? "#7f1d1d" : "#b91c1c"}
            stroke="#111"
            strokeWidth="12"
            strokeLinejoin="round"
          />
        )}

        {/* GAMBE STICKMAN CON STIVALI MEDIEVALI */}
        <line x1="195" y1="510" x2={195 - legSwing} y2="715" stroke="#111" strokeWidth="16" strokeLinecap="round" />
        <line x1="265" y1="510" x2={265 + legSwing} y2="715" stroke="#111" strokeWidth="16" strokeLinecap="round" />
        <ellipse cx={180 - legSwing} cy="720" rx="26" ry="12" fill="#27272a" stroke="#111" strokeWidth="6" />
        <ellipse cx={280 + legSwing} cy="720" rx="26" ry="12" fill="#27272a" stroke="#111" strokeWidth="6" />

        {/* BRACCIO SINISTRO ARTICOLATO */}
        <g transform={`translate(140, 325) rotate(${leftArmAngle})`}>
          {/* Manica a sbuffo Tudor */}
          <ellipse cx="0" cy="18" rx="28" ry="32" fill={role === "groom" ? "#fff" : bodyColor} stroke="#111" strokeWidth="10" />
          <line x1="0" y1="35" x2="-35" y2="145" stroke="#111" strokeWidth="15" strokeLinecap="round" />
          <circle cx="-35" cy="145" r="16" fill="#111" />
          {propLeft === "shield" && (
            <g transform="translate(-85, 80)">
              <path d="M 0 0 L 90 0 L 90 75 C 90 125, 45 155, 45 155 C 45 155, 0 125, 0 75 Z" fill="#eab308" stroke="#111" strokeWidth="9" />
              <path d="M 15 15 L 75 15 L 75 70 C 75 105, 45 130, 45 130 C 45 130, 15 105, 15 70 Z" fill="#991b1b" stroke="#111" strokeWidth="5" />
            </g>
          )}
          {propLeft === "goldbag" && (
            <g transform="translate(-80, 110)">
              <path d="M 25 0 L 55 0 L 75 45 C 85 80, 5 80, 15 45 Z" fill="#eab308" stroke="#111" strokeWidth="8" />
              <circle cx="40" cy="48" r="14" fill="#fef08a" stroke="#111" strokeWidth="4" />
            </g>
          )}
        </g>

        {/* CORPO CON VESTITI STORICI DETTAGLIATI */}
        <path
          d="M 135 305 C 135 260, 325 260, 325 305 L 338 515 C 338 532, 122 532, 122 515 Z"
          fill={bodyColor}
          stroke="#111"
          strokeWidth="12"
          strokeLinejoin="round"
        />
        {/* Ombra laterale stile Ricks Clips */}
        <path d="M 280 280 L 298 520 L 332 515 L 320 300 Z" fill="rgba(0,0,0,0.24)" />

        {/* DETTAGLI SPECIFICI PER RUOLO STORICO */}
        {role === "king" && (
          <g>
            {/* Fascia centrale reale dorata con gemme */}
            <rect x="208" y="310" width="44" height="210" fill="#eab308" stroke="#111" strokeWidth="8" />
            <circle cx="230" cy="365" r="9" fill="#dc2626" stroke="#111" strokeWidth="4" />
            <circle cx="230" cy="425" r="9" fill="#1d4ed8" stroke="#111" strokeWidth="4" />
            {/* Mantellina d'ermellino bianco a code nere */}
            <path d="M 130 288 Q 230 340 330 288 L 338 345 Q 230 390 122 345 Z" fill="#ffffff" stroke="#111" strokeWidth="10" />
            <circle cx="165" cy="322" r="5" fill="#111" />
            <circle cx="205" cy="335" r="5" fill="#111" />
            <circle cx="255" cy="335" r="5" fill="#111" />
            <circle cx="295" cy="322" r="5" fill="#111" />
            {/* Cintura reale */}
            <rect x="125" y="455" width="210" height="24" fill="#eab308" stroke="#111" strokeWidth="8" />
          </g>
        )}

        {role === "general" && (
          <g>
            {/* Corazza in acciaio con riflessi */}
            <path d="M 145 295 L 315 295 L 300 465 L 230 495 L 160 465 Z" fill="#cbd5e1" stroke="#111" strokeWidth="10" strokeLinejoin="round" />
            <line x1="230" y1="295" x2="230" y2="495" stroke="#475569" strokeWidth="6" />
            {/* Spallacci d'armatura */}
            <ellipse cx="135" cy="310" rx="38" ry="24" fill="#94a3b8" stroke="#111" strokeWidth="9" />
            <ellipse cx="325" cy="310" rx="38" ry="24" fill="#94a3b8" stroke="#111" strokeWidth="9" />
            {/* Stemma sul petto */}
            <polygon points="230,335 255,365 230,395 205,365" fill="#eab308" stroke="#111" strokeWidth="5" />
          </g>
        )}

        {(role === "banker" || role === "noble1" || role === "noble2") && (
          <g>
            {/* Ricami verticali dorati Tudor */}
            <line x1="190" y1="295" x2="180" y2="515" stroke="#eab308" strokeWidth="8" />
            <line x1="270" y1="295" x2="280" y2="515" stroke="#eab308" strokeWidth="8" />
            {/* Bottoni d'oro */}
            {[335, 375, 415, 455].map((cy) => (
              <circle key={cy} cx="230" cy={cy} r="7" fill="#eab308" stroke="#111" strokeWidth="4" />
            ))}
            {/* Gorgiera bianca plissettata Tudor (Ruff collar) */}
            <ellipse cx="230" cy="292" rx="95" ry="22" fill="#ffffff" stroke="#111" strokeWidth="9" />
            <path d="M 145 292 Q 165 275 185 292 Q 205 309 225 292 Q 245 275 265 292 Q 285 309 315 292" stroke="#94a3b8" strokeWidth="5" fill="none" />
          </g>
        )}

        {role === "groom" && (
          <g>
            {/* Colletto camicia medievale bianca con laccio, ZERO cravatta e ZERO badge moderno */}
            <polygon points="185,280 275,280 230,345" fill="#ffffff" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
            <line x1="215" y1="310" x2="245" y2="325" stroke="#111" strokeWidth="5" />
            <line x1="245" y1="310" x2="215" y2="325" stroke="#111" strokeWidth="5" />
            {/* Bordo dorato della tunica di corte e cintura in cuoio */}
            <line x1="230" y1="345" x2="230" y2="518" stroke="#eab308" strokeWidth="8" />
            <rect x="126" y="455" width="208" height="24" fill="#451a03" stroke="#111" strokeWidth="8" />
            <rect x="212" y="450" width="36" height="34" fill="#eab308" stroke="#111" strokeWidth="6" />
          </g>
        )}

        {role === "peasant" && (
          <g>
            <rect x="128" y="460" width="204" height="20" fill="#451a03" stroke="#111" strokeWidth="7" />
            <rect x="165" y="365" width="42" height="42" fill="#57534e" stroke="#111" strokeWidth="6" />
          </g>
        )}

        {/* BRACCIO DESTRO ARTICOLATO + OGGETTI IN MANO */}
        <g transform={`translate(320, 325) rotate(${rightArmAngle})`}>
          <ellipse cx="0" cy="18" rx="28" ry="32" fill={role === "groom" ? "#fff" : bodyColor} stroke="#111" strokeWidth="10" />
          <line x1="0" y1="35" x2="55" y2="135" stroke="#111" strokeWidth="15" strokeLinecap="round" />
          <circle cx="55" cy="135" r="16" fill="#111" />

          {/* Rotolo di Carta Reale Dorata */}
          {propRight === "paper" && (
            <g transform="translate(20, 95) rotate(${-rightArmAngle})">
              <rect x="0" y="0" width="88" height="92" rx="14" fill="#ffffff" stroke="#111" strokeWidth="9" />
              <ellipse cx="44" cy="20" rx="20" ry="8" fill="#cbd5e1" stroke="#111" strokeWidth="6" />
              <path d="M 70 50 L 98 128 L 35 115 Z" fill="#ffffff" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
            </g>
          )}

          {/* Grande Chiave Medievale in Ferro e Oro */}
          {propRight === "key" && (
            <g transform="translate(35, 110) rotate(25)">
              <circle cx="25" cy="25" r="24" fill="none" stroke="#eab308" strokeWidth="10" />
              <line x1="25" y1="49" x2="25" y2="145" stroke="#eab308" strokeWidth="12" strokeLinecap="round" />
              <rect x="25" y="110" width="28" height="12" fill="#eab308" stroke="#111" strokeWidth="5" />
              <rect x="25" y="130" width="22" height="12" fill="#eab308" stroke="#111" strokeWidth="5" />
            </g>
          )}

          {/* Spada Medievale */}
          {propRight === "sword" && (
            <g transform="translate(45, -75) rotate(15)">
              <polygon points="15,0 35,0 38,185 12,185" fill="#e2e8f0" stroke="#111" strokeWidth="8" strokeLinejoin="round" />
              <line x1="25" y1="20" x2="25" y2="175" stroke="#94a3b8" strokeWidth="4" />
              <rect x="-15" y="180" width="80" height="18" rx="6" fill="#eab308" stroke="#111" strokeWidth="7" />
              <rect x="16" y="198" width="18" height="36" fill="#78350f" stroke="#111" strokeWidth="6" />
              <circle cx="25" cy="240" r="14" fill="#eab308" stroke="#111" strokeWidth="6" />
            </g>
          )}

          {/* Sacco di Monete d'Oro */}
          {propRight === "goldbag" && (
            <g transform="translate(15, 95)">
              <path d="M 25 0 L 65 0 L 85 55 C 95 95, -5 95, 5 55 Z" fill="#eab308" stroke="#111" strokeWidth="9" />
              <circle cx="45" cy="55" r="18" fill="#fef08a" stroke="#111" strokeWidth="5" />
            </g>
          )}

          {/* Pergamena dei Segreti Reali */}
          {propRight === "scroll" && (
            <g transform="translate(20, 85) rotate(-15)">
              <rect x="0" y="0" width="85" height="110" rx="8" fill="#fef3c7" stroke="#111" strokeWidth="8" />
              <line x1="18" y1="30" x2="67" y2="30" stroke="#111" strokeWidth="6" />
              <line x1="18" y1="55" x2="67" y2="55" stroke="#111" strokeWidth="6" />
              <circle cx="42" cy="82" r="14" fill="#dc2626" stroke="#111" strokeWidth="5" />
            </g>
          )}
        </g>

        {/* TESTA GRANDE ROTONDA STILE RICKS CLIPS CON LEGGERA INCLINAZIONE DINAMICA */}
        <g transform={`translate(230, 175) rotate(${headTilt}) translate(-230, -175)`}>
          <circle cx="230" cy="175" r="125" fill="#ffffff" stroke="#111" strokeWidth="12" />
          {/* Ombra grigia sotto il mento */}
          <path d="M 112 205 A 125 125 0 0 0 348 205 A 125 102 0 0 1 112 205 Z" fill="#e2e8f0" />

          {/* CAPIGLIATURA E COPRICAPI STORICI */}
          {role === "general" ? (
            <g>
              {/* Elmo da Cavaliere con Piuma Rossa */}
              <path d="M 102 165 C 102 35, 358 35, 358 165 L 335 125 L 125 125 Z" fill="#94a3b8" stroke="#111" strokeWidth="11" strokeLinejoin="round" />
              <path d="M 230 45 C 280 -25, 360 -10, 340 55 C 300 40, 260 45, 230 45 Z" fill="#dc2626" stroke="#111" strokeWidth="9" />
            </g>
          ) : (
            <g>
              {/* Capelli stile Ricks Clips con riflessi */}
              <path
                d="M 105 155 C 110 35, 350 35, 355 155 C 310 95, 165 95, 105 155 Z"
                fill={role === "king" ? "#71717a" : role === "banker" ? "#57534e" : "#27272a"}
                stroke="#111"
                strokeWidth="10"
                strokeLinejoin="round"
              />
              <path d="M 160 78 Q 235 60 315 95" stroke="#e4e4e7" strokeWidth="5" fill="none" strokeLinecap="round" />
              <path d="M 145 98 Q 225 80 330 118" stroke="#e4e4e7" strokeWidth="4" fill="none" strokeLinecap="round" />
            </g>
          )}

          {/* Corona del Re */}
          {role === "king" && (
            <g transform="translate(135, -35)">
              <polygon
                points="15,85 175,85 190,15 135,52 95,0 55,52 0,15"
                fill="#facc15"
                stroke="#111"
                strokeWidth="11"
                strokeLinejoin="round"
              />
              <circle cx="95" cy="52" r="11" fill="#dc2626" stroke="#111" strokeWidth="5" />
              <circle cx="48" cy="60" r="8" fill="#2563eb" stroke="#111" strokeWidth="4" />
              <circle cx="142" cy="60" r="8" fill="#16a34a" stroke="#111" strokeWidth="4" />
            </g>
          )}

          {/* Cappello di velluto Tudor con piuma per Nobili e Banchiere */}
          {(role === "noble1" || role === "noble2" || role === "banker") && (
            <g transform="translate(115, 10)">
              <ellipse cx="115" cy="48" rx="125" ry="28" fill={bodyColor} stroke="#111" strokeWidth="10" />
              <path d="M 175 35 C 225 -25, 275 0, 240 45" fill="#fef08a" stroke="#111" strokeWidth="7" />
            </g>
          )}

          {/* OCCHI E SOPRACCIGLIA (con battito di ciglia automatico) */}
          {isBlinking ? (
            <g>
              <line x1="155" y1="162" x2="205" y2="162" stroke="#111" strokeWidth="10" strokeLinecap="round" />
              <line x1="255" y1="162" x2="305" y2="162" stroke="#111" strokeWidth="10" strokeLinecap="round" />
            </g>
          ) : (
            <g>
              {mood === "happy" || mood === "proud" ? (
                <>
                  <path d="M 155 130 Q 180 112 205 130" stroke="#111" strokeWidth="9" fill="none" strokeLinecap="round" />
                  <path d="M 255 130 Q 280 112 305 130" stroke="#111" strokeWidth="9" fill="none" strokeLinecap="round" />
                  <path d="M 160 165 Q 180 140 200 165" stroke="#111" strokeWidth="10" fill="none" strokeLinecap="round" />
                  <path d="M 260 165 Q 280 140 300 165" stroke="#111" strokeWidth="10" fill="none" strokeLinecap="round" />
                </>
              ) : mood === "shock" ? (
                <>
                  <circle cx="182" cy="160" r="28" fill="#fff" stroke="#111" strokeWidth="8" />
                  <circle cx="182" cy="160" r="7" fill="#111" />
                  <circle cx="278" cy="160" r="28" fill="#fff" stroke="#111" strokeWidth="8" />
                  <circle cx="278" cy="160" r="7" fill="#111" />
                </>
              ) : mood === "angry" ? (
                <>
                  <line x1="148" y1="125" x2="208" y2="150" stroke="#111" strokeWidth="11" strokeLinecap="round" />
                  <line x1="312" y1="125" x2="252" y2="150" stroke="#111" strokeWidth="11" strokeLinecap="round" />
                  <circle cx="180" cy="165" r="10" fill="#111" />
                  <circle cx="280" cy="165" r="10" fill="#111" />
                </>
              ) : mood === "smirk" || mood === "whisper" ? (
                <>
                  <line x1="152" y1="138" x2="205" y2="148" stroke="#111" strokeWidth="9" strokeLinecap="round" />
                  <line x1="255" y1="148" x2="308" y2="130" stroke="#111" strokeWidth="9" strokeLinecap="round" />
                  <circle cx="180" cy="165" r="10" fill="#111" />
                  <circle cx="280" cy="165" r="10" fill="#111" />
                </>
              ) : (
                <>
                  {/* Sweat / Beg */}
                  <line x1="152" y1="145" x2="205" y2="138" stroke="#111" strokeWidth="10" strokeLinecap="round" />
                  <line x1="255" y1="138" x2="308" y2="145" stroke="#111" strokeWidth="10" strokeLinecap="round" />
                  <circle cx="180" cy="165" r="9" fill="#111" />
                  <circle cx="280" cy="165" r="9" fill="#111" />
                </>
              )}
            </g>
          )}

          {/* GOCCIA DI SUDORE AZZURRA */}
          {(mood === "sweat" || mood === "beg") && (
            <g>
              <path d="M 132 105 C 132 105, 108 138, 122 152 C 135 164, 155 152, 142 130 Z" fill="#38bdf8" stroke="#111" strokeWidth="6" />
              <ellipse cx="129" cy="138" rx="4" ry="7" fill="#fff" />
            </g>
          )}

          {/* BOCCA DINAMICA (Denti a griglia Ricks Clips + Lip-sync) */}
          {talking && talkOpen > 4 ? (
            <ellipse cx="230" cy="212" rx="28" ry={12 + talkOpen} fill="#7f1d1d" stroke="#111" strokeWidth="8" />
          ) : mood === "smirk" ? (
            <path d="M 188 208 Q 230 232 275 192" stroke="#111" strokeWidth="10" fill="none" strokeLinecap="round" />
          ) : mood === "shock" || mood === "whisper" ? (
            <ellipse cx="230" cy="215" rx="20" ry="16" fill="#111" />
          ) : (
            <g>
              <rect x="188" y="192" width="84" height="44" rx="15" fill="#fff" stroke="#111" strokeWidth="9" />
              <line x1="188" y1="214" x2="272" y2="214" stroke="#111" strokeWidth="6" />
              <line x1="210" y1="192" x2="210" y2="236" stroke="#111" strokeWidth="6" />
              <line x1="230" y1="192" x2="230" y2="236" stroke="#111" strokeWidth="6" />
              <line x1="250" y1="192" x2="250" y2="236" stroke="#111" strokeWidth="6" />
            </g>
          )}
        </g>
      </svg>
    </div>
  );
};

// SFONDO 1: SALA DEL TRONO MEDIEVALE (Archi in pietra, vetrate, tappeto rosso, torce)
const CastleThroneRoomBg = ({ panX = 0 }: { panX?: number }) => (
  <AbsoluteFill style={{ backgroundColor: "#334155", transform: `translateX(${panX * 0.4}px)` }}>
    {/* Muro in blocchi di pietra medievale */}
    <svg width="1200" height="1920" viewBox="0 0 1200 1920" style={{ position: "absolute", left: -60 }}>
      <rect width="1200" height="1400" fill="#475569" />
      {[180, 360, 540, 720, 900, 1080, 1260].map((y, idx) => (
        <g key={y}>
          <line x1="0" y1={y} x2="1200" y2={y} stroke="#1e293b" strokeWidth="8" />
          {[150, 450, 750, 1050].map((x) => (
            <line key={x} x1={x + (idx % 2) * 140} y1={y - 180} x2={x + (idx % 2) * 140} y2={y} stroke="#1e293b" strokeWidth="8" />
          ))}
        </g>
      ))}
      {/* Grandi finestre ad arco gotico */}
      {[220, 880].map((cx) => (
        <g key={cx}>
          <path d={`M ${cx - 110} 780 L ${cx - 110} 320 Q ${cx} 160 ${cx + 110} 320 L ${cx + 110} 780 Z`} fill="#0ea5e9" stroke="#111" strokeWidth="14" />
          <path d={`M ${cx - 110} 520 L ${cx + 110} 520 M ${cx} 220 L ${cx} 780`} stroke="#111" strokeWidth="10" />
        </g>
      ))}
    </svg>
    <RoyalBanner x={440} y={140} color="#991b1b" />
    <Torch x={80} y={480} />
    <Torch x={940} y={480} />
    {/* Pavimento in pietra e tappeto reale rosso */}
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: 550, backgroundColor: "#1e293b", borderTop: "14px solid #0f172a" }}>
      <div style={{ margin: "0 auto", width: 580, height: "100%", backgroundColor: "#991b1b", borderLeft: "18px solid #eab308", borderRight: "18px solid #eab308" }} />
    </div>
  </AbsoluteFill>
);

// SFONDO 2: STANZA PRIVATA DEL "ROYAL STOOL" (Velluto, candele, Trono-Gabinetto Tudor)
const RoyalPrivyRoomBg = ({ panX = 0, doorClosed = true }: { panX?: number; doorClosed?: boolean }) => (
  <AbsoluteFill style={{ backgroundColor: "#3b0764", transform: `translateX(${panX * 0.4}px)` }}>
    {/* Pareti tappezzate reali scure */}
    <div style={{ width: "100%", height: 1380, background: "linear-gradient(180deg, #2e1065 0%, #4c1d95 100%)", borderBottom: "14px solid #111" }} />
    <RoyalBanner x={120} y={180} color="#7f1d1d" />
    <RoyalBanner x={760} y={180} color="#7f1d1d" />
    <Torch x={490} y={240} scale={1.1} />

    {/* Pavimento in legno scuro */}
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: 540, backgroundColor: "#451a03", borderTop: "14px solid #111" }} />

    {/* IL "CLOSE STOOL" (Il Trono-Gabinetto Reale in velluto rosso e oro) */}
    <div style={{ position: "absolute", left: 140, top: 680 }}>
      <svg width="420" height="650" viewBox="0 0 420 650">
        {/* Schienale alto reale */}
        <rect x="40" y="20" width="340" height="420" rx="30" fill="#991b1b" stroke="#111" strokeWidth="12" />
        <rect x="65" y="45" width="290" height="370" rx="20" fill="#7f1d1d" stroke="#eab308" strokeWidth="8" />
        {/* Seduta a cassa di velluto con ouverture */}
        <rect x="20" y="400" width="380" height="210" rx="18" fill="#b91c1c" stroke="#111" strokeWidth="12" />
        <ellipse cx="210" cy="435" rx="95" ry="28" fill="#111" stroke="#eab308" strokeWidth="8" />
        {/* Borchie d'oro */}
        {[70, 140, 210, 280, 350].map((cx) => (
          <circle key={cx} cx={cx} cy="500" r="10" fill="#eab308" stroke="#111" strokeWidth="4" />
        ))}
      </svg>
    </div>
  </AbsoluteFill>
);

// SFONDO 3: CORRIDOIO IN PIETRA CON GRANDE PORTA AD ARCO IN LEGNO E FERRO
const CastleCorridorDoorBg = ({ panX = 0, locked = false }: { panX?: number; locked?: boolean }) => (
  <AbsoluteFill style={{ backgroundColor: "#475569", transform: `translateX(${panX * 0.4}px)` }}>
    {/* Muro di pietra */}
    <div style={{ width: "100%", height: 1400, backgroundColor: "#64748b", borderBottom: "14px solid #111" }} />
    {/* Pavimento lastricato */}
    <div style={{ position: "absolute", bottom: 0, width: "100%", height: 520, backgroundColor: "#334155", borderTop: "14px solid #111" }} />

    {/* Grande Porta Medievale ad Arco */}
    <div style={{ position: "absolute", left: 140, top: 340 }}>
      <svg width="800" height="1080" viewBox="0 0 800 1080">
        {/* Cornice in pietra ad arco */}
        <path d="M 40 1060 L 40 420 Q 400 40 760 420 L 760 1060 Z" fill="#94a3b8" stroke="#111" strokeWidth="14" />
        {/* Porta in legno massiccio */}
        <path d="M 95 1060 L 95 450 Q 400 120 705 450 L 705 1060 Z" fill="#78350f" stroke="#111" strokeWidth="14" />
        <line x1="400" y1="280" x2="400" y2="1060" stroke="#111" strokeWidth="10" />
        {/* Bandelle in ferro battuto */}
        <rect x="105" y="520" width="240" height="28" rx="8" fill="#1e293b" stroke="#111" strokeWidth="6" />
        <rect x="455" y="520" width="240" height="28" rx="8" fill="#1e293b" stroke="#111" strokeWidth="6" />
        <rect x="105" y="820" width="240" height="28" rx="8" fill="#1e293b" stroke="#111" strokeWidth="6" />
        <rect x="455" y="820" width="240" height="28" rx="8" fill="#1e293b" stroke="#111" strokeWidth="6" />
        {/* Grata di spionaggio */}
        <rect x="310" y="360" width="180" height="130" fill="#0f172a" stroke="#111" strokeWidth="10" />
        <line x1="370" y1="360" x2="370" y2="490" stroke="#475569" strokeWidth="8" />
        <line x1="430" y1="360" x2="430" y2="490" stroke="#475569" strokeWidth="8" />
        {/* Targa Reale d'Oro */}
        <rect x="210" y="610" width="380" height="110" rx="14" fill="#eab308" stroke="#111" strokeWidth="9" />
        <text x="400" y="660" fill="#111" fontSize="34" fontWeight="900" fontFamily="Arial Black, sans-serif" textAnchor="middle">
          ROYAL CHAMBER
        </text>
        <text x="400" y="700" fill="#991b1b" fontSize="28" fontWeight="900" fontFamily="Arial Black, sans-serif" textAnchor="middle">
          GROOM OF THE STOOL
        </text>

        {/* Sbarra di blocco pesante quando si chiudono dentro */}
        {locked && (
          <g>
            <rect x="40" y="720" width="720" height="58" rx="12" fill="#334155" stroke="#111" strokeWidth="12" />
            <rect x="350" y="695" width="100" height="110" rx="16" fill="#eab308" stroke="#111" strokeWidth="10" />
            <circle cx="400" cy="745" r="14" fill="#111" />
          </g>
        )}
      </svg>
    </div>
    <Torch x={70} y={460} />
    <Torch x={930} y={460} />
  </AbsoluteFill>
);

export const GroomStory: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Progresso normalizzato da 0.0 a 1.0 lungo tutto l'audio
  const p = frame / durationInFrames;

  // Suddivisione in 10 scene fluide sincronizzate con la storia
  let sceneIndex = 1;
  let localP = 0;
  const cuts = [0.0, 0.09, 0.20, 0.30, 0.39, 0.52, 0.64, 0.74, 0.83, 0.91, 1.01];
  for (let i = 0; i < cuts.length - 1; i++) {
    if (p >= cuts[i] && p < cuts[i + 1]) {
      sceneIndex = i + 1;
      localP = (p - cuts[i]) / (cuts[i + 1] - cuts[i]);
      break;
    }
  }

  // Zoom cinematografico continuo + Pan fluido della telecamera su ogni scena
  const camScale = interpolate(localP, [0, 1], [1.02, 1.16]);
  const camPanX = interpolate(localP, [0, 1], [-35, 35]);

  // Effetto transizione Whip-Pan morbida nei primi 8 frame di ogni cambio scena
  const whipOffset = interpolate(localP, [0, 0.08], [160, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a", overflow: "hidden" }}>
      <Audio src={staticFile("voce.mp3")} />

      <AbsoluteFill
        style={{
          transform: `scale(${camScale}) translateX(${camPanX + whipOffset}px)`,
        }}
      >
        {/* SCENA 1: "Imagine landing the most powerful, highly paid job in the entire kingdom..." */}
        {sceneIndex === 1 && (
          <CastleThroneRoomBg panX={camPanX}>
            {/* Raggio di luce dorata divina dal soffitto */}
            <div
              style={{
                position: "absolute",
                left: 240,
                top: 0,
                width: 600,
                height: 1920,
                background: "linear-gradient(180deg, rgba(250,204,21,0.38) 0%, rgba(250,204,21,0.05) 100%)",
              }}
            />
            <TudorCharacter
              role="groom"
              mood="proud"
              x={0}
              y={110}
              scale={1.18}
              talking
              leftArmAngle={interpolate(localP, [0, 1], [25, -45])}
              rightArmAngle={interpolate(localP, [0, 1], [-25, 45])}
              propRight="key"
              propLeft="goldbag"
            />
          </CastleThroneRoomBg>
        )}

        {/* SCENA 2: "...but your only actual duty is... wiping your boss's butt." */}
        {sceneIndex === 2 && (
          <RoyalPrivyRoomBg panX={camPanX}>
            <TudorCharacter
              role="king"
              mood="happy"
              x={-175}
              y={95}
              scale={1.08}
              talking
              rightArmAngle={-30}
            />
            <TudorCharacter
              role="groom"
              mood={localP < 0.45 ? "sweat" : "shock"}
              x={215}
              y={125}
              scale={1.08}
              rightArmAngle={interpolate(localP, [0, 0.5, 1], [-15, -75, -55])}
              propRight="paper"
            />
          </RoyalPrivyRoomBg>
        )}

        {/* SCENA 3: "Back in Tudor England, the most coveted role wasn't a top general..." */}
        {sceneIndex === 3 && (
          <CastleThroneRoomBg panX={camPanX}>
            <TudorCharacter
              role="general"
              mood={localP < 0.6 ? "proud" : "shock"}
              x={interpolate(localP, [0, 0.65, 1], [0, 0, -120])}
              y={115}
              scale={1.15}
              talking={localP < 0.6}
              rightArmAngle={interpolate(localP, [0, 0.5, 1], [-55, -80, -20])}
              propRight="sword"
              propLeft="shield"
            />
            {/* Grande X Rossa Reale che scarta il Generale */}
            {localP > 0.55 && (
              <svg width="500" height="500" viewBox="0 0 500 500" style={{ position: "absolute", left: 290, top: 680 }}>
                <line x1="60" y1="60" x2="440" y2="440" stroke="#dc2626" strokeWidth="48" strokeLinecap="round" />
                <line x1="440" y1="60" x2="60" y2="440" stroke="#dc2626" strokeWidth="48" strokeLinecap="round" />
              </svg>
            )}
          </CastleThroneRoomBg>
        )}

        {/* SCENA 4: "...or a wealthy banker." */}
        {sceneIndex === 4 && (
          <CastleThroneRoomBg panX={-camPanX}>
            <TudorCharacter
              role="banker"
              mood={localP < 0.6 ? "happy" : "shock"}
              x={interpolate(localP, [0, 0.65, 1], [0, 0, 120])}
              y={115}
              scale={1.15}
              talking={localP < 0.6}
              leftArmAngle={35}
              rightArmAngle={-45}
              propRight="goldbag"
              propLeft="goldbag"
            />
            {localP > 0.55 && (
              <svg width="500" height="500" viewBox="0 0 500 500" style={{ position: "absolute", left: 290, top: 680 }}>
                <line x1="60" y1="60" x2="440" y2="440" stroke="#dc2626" strokeWidth="48" strokeLinecap="round" />
                <line x1="440" y1="60" x2="60" y2="440" stroke="#dc2626" strokeWidth="48" strokeLinecap="round" />
              </svg>
            )}
          </CastleThroneRoomBg>
        )}

        {/* SCENA 5: "It was the Groom of the Stool, the guy officially in charge of the King's toilet time." */}
        {sceneIndex === 5 && (
          <CastleCorridorDoorBg panX={camPanX}>
            <TudorCharacter
              role="king"
              mood="happy"
              x={interpolate(localP, [0, 1], [-260, -155])}
              y={150}
              scale={1.04}
              walk
              talking
              rightArmAngle={-35}
            />
            <TudorCharacter
              role="groom"
              mood="sweat"
              x={interpolate(localP, [0, 1], [270, 175])}
              y={165}
              scale={1.04}
              walk
              rightArmAngle={-60}
              propRight="paper"
            />
          </CastleCorridorDoorBg>
        )}

        {/* SCENA 6: "It sounds like an absolute punishment, but the richest nobles literally fought each other for this job." */}
        {sceneIndex === 6 && (
          <CastleCorridorDoorBg panX={-camPanX}>
            {/* Duello animato con le spade tra due Nobili Tudor */}
            <TudorCharacter
              role="noble1"
              mood="angry"
              x={-210 + Math.sin(frame * 0.25) * 45}
              y={160}
              scale={1.05}
              walk
              rightArmAngle={-55 + Math.sin(frame * 0.35) * 40}
              propRight="sword"
            />
            <TudorCharacter
              role="noble2"
              mood="angry"
              x={210 - Math.sin(frame * 0.25) * 45}
              y={160}
              scale={1.05}
              flip
              walk
              rightArmAngle={-55 + Math.cos(frame * 0.35) * 40}
              propRight="sword"
            />
            {/* Scintille dell'incrocio delle spade al centro */}
            <svg
              width="220"
              height="220"
              viewBox="0 0 220 220"
              style={{
                position: "absolute",
                left: 430,
                top: 760,
                transform: `scale(${0.8 + Math.abs(Math.sin(frame * 0.4)) * 0.5}) rotate(${frame * 6}deg)`,
              }}
            >
              <polygon points="110,10 130,85 205,110 130,135 110,210 90,135 15,110 90,85" fill="#facc15" stroke="#111" strokeWidth="6" />
            </svg>
          </CastleCorridorDoorBg>
        )}

        {/* SCENA 7: "Why? Because you were locked in a private room with the King every single day." */}
        {sceneIndex === 7 && (
          <CastleCorridorDoorBg panX={0} locked={localP > 0.25}>
            <TudorCharacter
              role="king"
              mood="happy"
              x={-180}
              y={170}
              scale={1.02}
              talking
            />
            <TudorCharacter
              role="groom"
              mood="smirk"
              x={180}
              y={170}
              scale={1.05}
              rightArmAngle={-55}
              propRight="key"
            />
          </CastleCorridorDoorBg>
        )}

        {/* SCENA 8: "You became his ultimate confidant. You knew all his dark secrets..." */}
        {sceneIndex === 8 && (
          <RoyalPrivyRoomBg panX={camPanX}>
            {/* Primo piano del Re che sussurra segreti al Groom */}
            <TudorCharacter
              role="king"
              mood="whisper"
              x={-165}
              y={130}
              scale={1.22}
              talking
              rightArmAngle={-65}
            />
            <TudorCharacter
              role="groom"
              mood="smirk"
              x={185}
              y={135}
              scale={1.22}
              rightArmAngle={-45}
              propRight="scroll"
            />
          </RoyalPrivyRoomBg>
        )}

        {/* SCENA 9: "...you knew who he hated, and you controlled exactly who got to speak with him." */}
        {sceneIndex === 9 && (
          <CastleCorridorDoorBg panX={camPanX} locked>
            {/* Il Groom comanda chi entra mentre il nobile e il generale implorano */}
            <TudorCharacter
              role="noble1"
              mood="beg"
              x={-260}
              y={190}
              scale={0.95}
              leftArmAngle={-50}
              rightArmAngle={-60}
            />
            <TudorCharacter
              role="groom"
              mood="smirk"
              x={170}
              y={130}
              scale={1.18}
              talking
              rightArmAngle={interpolate(localP, [0, 1], [-80, -25])}
              propRight="scroll"
            />
          </CastleCorridorDoorBg>
        )}

        {/* SCENA 10: "So, while everyone else was outside begging for power, the guy holding the royal toilet paper was actually secretly running the country." */}
        {sceneIndex === 10 && (
          <CastleThroneRoomBg panX={0}>
            {/* Fili da burattinaio dorati dall'alto */}
            <svg width="1080" height="1920" style={{ position: "absolute", top: 0, left: 0 }}>
              <line x1="540" y1="150" x2="220" y2="1150" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
              <line x1="540" y1="150" x2="860" y2="1150" stroke="#facc15" strokeWidth="6" strokeDasharray="14,10" />
            </svg>
            {/* Il Groom gigante al centro come vero padrone del Regno, Re e Nobile più piccoli ai lati */}
            <TudorCharacter
              role="groom"
              mood="smirk"
              x={0}
              y={65}
              scale={interpolate(localP, [0, 1], [1.25, 1.38])}
              talking
              leftArmAngle={45}
              rightArmAngle={-65}
              propRight="paper"
              propLeft="goldbag"
            />
            <TudorCharacter
              role="king"
              mood="happy"
              x={-310}
              y={260}
              scale={0.82}
            />
            <TudorCharacter
              role="general"
              mood="beg"
              x={310}
              y={260}
              scale={0.82}
              flip
            />
          </CastleThroneRoomBg>
        )}
      </AbsoluteFill>

      {/* Vignettatura cinematografica morbida */}
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle, rgba(0,0,0,0) 62%, rgba(0,0,0,0.48) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
"""

with open("src/GroomStory.tsx", "w") as f:
    f.write(story_code)

print(f"✅ File generati con successo! Durata: {duration_sec:.2f}s ({total_frames} frame a {fps} FPS).")
