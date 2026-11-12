code = '''import React, { useEffect, useRef } from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import * as THREE from "three";
import { TIMINGS } from "./timings";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

const TEX_CACHE: Record<string, THREE.CanvasTexture> = {};

// TEXTURE PAVIMENTI E MURI 3D AD ALTA RISOLUZIONE (1024x1024)
function getEnvTexture(type: "wood" | "stone" | "grass" | "carpet" | "books"): THREE.CanvasTexture {
  if (TEX_CACHE[type]) return TEX_CACHE[type];
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 1024;
  const ctx = c.getContext("2d")!;

  if (type === "wood") {
    ctx.fillStyle = "#8b5a2b";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let y = 0; y < 1024; y += 128) {
      ctx.fillStyle = (y / 128) % 2 === 0 ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.05)";
      ctx.fillRect(0, y, 1024, 128);
      ctx.strokeStyle = "#3b1e08";
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1024, y);
      ctx.stroke();
      const jx = ((y * 5) % 700) + 120;
      ctx.beginPath();
      ctx.moveTo(jx, y);
      ctx.lineTo(jx, y + 128);
      ctx.stroke();
    }
  } else if (type === "stone") {
    ctx.fillStyle = "#64748b";
    ctx.fillRect(0, 0, 1024, 1024);
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 10;
    for (let r = 0; r < 8; r++) {
      const y = r * 128;
      const off = (r % 2) * 128;
      for (let col = -1; col < 5; col++) {
        const x = col * 256 + off;
        ctx.fillStyle = (r + col) % 2 === 0 ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
        ctx.fillRect(x + 6, y + 6, 244, 116);
        ctx.strokeRect(x, y, 256, 128);
      }
    }
  } else if (type === "grass") {
    ctx.fillStyle = "#4ade80";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let i = 0; i < 600; i++) {
      ctx.fillStyle = i % 2 === 0 ? "#22c55e" : "#16a34a";
      const gx = (i * 73) % 1024;
      const gy = (i * 137) % 1024;
      ctx.fillRect(gx, gy, 8, 22);
    }
  } else if (type === "books") {
    ctx.fillStyle = "#290f02";
    ctx.fillRect(0, 0, 1024, 1024);
    const colors = ["#ef4444", "#3b82f6", "#eab308", "#10b981", "#a855f7", "#f97316"];
    for (let row = 0; row < 4; row++) {
      const sy = row * 256 + 220;
      ctx.fillStyle = "#78350f";
      ctx.fillRect(0, sy, 1024, 36);
      for (let bx = 24; bx < 980; bx += 68) {
        const bh = 155 + ((bx + row * 19) % 45);
        ctx.fillStyle = colors[(bx + row) % colors.length];
        ctx.fillRect(bx, sy - bh, 56, bh);
        ctx.strokeStyle = "#111111";
        ctx.lineWidth = 6;
        ctx.strokeRect(bx, sy - bh, 56, bh);
      }
    }
  }

  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  if (type !== "books") tex.repeat.set(4, 4);
  TEX_CACHE[type] = tex;
  return tex;
}

function getSignTexture(title: string, sub: string, bg = "#fef3c7", fg = "#991b1b"): THREE.CanvasTexture {
  const key = `sign_${title}_${sub}`;
  if (TEX_CACHE[key]) return TEX_CACHE[key];
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 512;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, 1024, 512);
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 22;
  ctx.strokeRect(18, 18, 988, 476);
  ctx.strokeStyle = "#eab308";
  ctx.lineWidth = 10;
  ctx.strokeRect(42, 42, 940, 428);
  ctx.fillStyle = fg;
  ctx.font = "900 104px Arial Black, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(title, 512, 235);
  ctx.fillStyle = "#111111";
  ctx.font = "800 62px Arial, sans-serif";
  ctx.fillText(sub, 512, 365);
  const tex = new THREE.CanvasTexture(c);
  TEX_CACHE[key] = tex;
  return tex;
}

// DISEGNATORE PERSONAGGIO 2.5D AD ALTISSIMA DEFINIZIONE (1024x1280) COME IN RICKS CLIPS
// Zero deformazione sferica, elmi e vestiti perfetti, braccia/gambe nere articolate!
function renderCharacterCanvas(
  role: string,
  mood: string,
  walkPhase: number,
  isWalking: boolean,
  lArmDeg: number,
  rArmDeg: number,
  propR: string,
  propL: string,
  lookX: number
): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 1280;
  const ctx = c.getContext("2d")!;
  ctx.clearRect(0, 0, 1024, 1280);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  const cx = 512;
  const bob = isWalking ? Math.abs(Math.sin(walkPhase)) * 18 : 0;
  const lSwing = isWalking ? Math.sin(walkPhase) * 55 : 0;
  const rSwing = isWalking ? -Math.sin(walkPhase) * 55 : 0;
  const lKnee = isWalking ? Math.max(0, Math.cos(walkPhase) * 30) : 0;
  const rKnee = isWalking ? Math.max(0, -Math.cos(walkPhase) * 30) : 0;

  // MANTELLO POSTERIORE (Re e Generale)
  if (role === "king" || role === "general") {
    ctx.fillStyle = role === "king" ? "#7f1d1d" : "#b91c1c";
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 18;
    ctx.beginPath();
    ctx.moveTo(cx - 145, 520 - bob);
    ctx.lineTo(cx - 210, 1060);
    ctx.quadraticCurveTo(cx, 1110, cx + 210, 1060);
    ctx.lineTo(cx + 145, 520 - bob);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  // GAMBE STICKMAN SPESSE CON GINOCCHIO FLESSO E SCARPE (Come in Ricks Clips e9NoHjAXYIY e QlDPMzGmYac)
  const drawLeg = (hipX: number, swing: number, knee: number) => {
    const footX = hipX + swing;
    const footY = 1190 - knee * 0.5;
    const ctrlX = hipX + swing * 0.5 + (swing >= 0 ? 22 : -22);
    const ctrlY = 1010;
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 26;
    ctx.beginPath();
    ctx.moveTo(hipX, 860 - bob);
    ctx.quadraticCurveTo(ctrlX, ctrlY, footX, footY);
    ctx.stroke();

    ctx.fillStyle = "#1e293b";
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.ellipse(footX + (swing >= 0 ? 12 : -12), footY + 8, 38, 18, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  };

  drawLeg(cx - 55, lSwing, lKnee);
  drawLeg(cx + 55, rSwing, rKnee);

  // FUNZIONE BRACCIA E OGGETTI
  const drawArm = (isLeft: boolean, deg: number, prop: string) => {
    ctx.save();
    ctx.translate(isLeft ? cx - 135 : cx + 135, 580 - bob);
    const armWave = isWalking ? Math.sin(walkPhase + (isLeft ? 0 : Math.PI)) * 18 : 0;
    ctx.rotate(((deg + armWave) * Math.PI) / 180);

    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 24;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(isLeft ? -55 : 55, 95, isLeft ? -42 : 42, 215);
    ctx.stroke();

    // Mano nera arrotondata (NIENTE PALLINI BIANCHI STACCATI!)
    const hx = isLeft ? -42 : 42;
    const hy = 215;
    ctx.fillStyle = "#111111";
    ctx.beginPath();
    ctx.arc(hx, hy, 22, 0, Math.PI * 2);
    ctx.fill();

    ctx.translate(hx, hy);
    ctx.rotate((-(deg + armWave) * Math.PI) / 180);

    if (prop === "key") {
      ctx.fillStyle = "#facc15";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 10;
      ctx.beginPath();
      ctx.arc(25, 10, 34, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#78350f";
      ctx.beginPath();
      ctx.arc(25, 10, 14, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#facc15";
      ctx.fillRect(15, 42, 20, 115);
      ctx.strokeRect(15, 42, 20, 115);
      ctx.fillRect(35, 110, 32, 18);
      ctx.strokeRect(35, 110, 32, 18);
      ctx.fillRect(35, 136, 26, 18);
      ctx.strokeRect(35, 136, 26, 18);
    } else if (prop === "paper") {
      // Cuscino reale d'oro + Rotolo di Carta Igienica Reale nitido
      ctx.fillStyle = "#eab308";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 10;
      ctx.beginPath();
      ctx.ellipse(30, 65, 85, 24, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.roundRect(-22, -45, 104, 105, 18);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#cbd5e1";
      ctx.beginPath();
      ctx.ellipse(30, -22, 26, 10, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.moveTo(65, 10);
      ctx.lineTo(105, 95);
      ctx.lineTo(35, 82);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    } else if (prop === "sword") {
      ctx.save();
      ctx.rotate(-0.35);
      ctx.fillStyle = "#f8fafc";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 10;
      ctx.beginPath();
      ctx.moveTo(-16, 0);
      ctx.lineTo(0, -260);
      ctx.lineTo(16, 0);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#eab308";
      ctx.fillRect(-52, -12, 104, 24);
      ctx.strokeRect(-52, -12, 104, 24);
      ctx.restore();
    } else if (prop === "shield") {
      ctx.fillStyle = "#eab308";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 12;
      ctx.beginPath();
      ctx.moveTo(-70, -65);
      ctx.lineTo(70, -65);
      ctx.lineTo(70, 35);
      ctx.quadraticCurveTo(0, 125, -70, 35);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#991b1b";
      ctx.beginPath();
      ctx.moveTo(-48, -42);
      ctx.lineTo(48, -42);
      ctx.lineTo(48, 25);
      ctx.quadraticCurveTo(0, 92, -48, 25);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    } else if (prop === "goldbag") {
      ctx.fillStyle = "#eab308";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 10;
      ctx.beginPath();
      ctx.arc(0, 35, 58, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#78350f";
      ctx.font = "900 54px Arial Black";
      ctx.textAlign = "center";
      ctx.fillText("$", 0, 54);
    } else if (prop === "scroll") {
      ctx.fillStyle = "#fef3c7";
      ctx.strokeStyle = "#111111";
      ctx.lineWidth = 10;
      ctx.fillRect(-35, -45, 115, 145);
      ctx.strokeRect(-35, -45, 115, 145);
      ctx.fillStyle = "#dc2626";
      ctx.beginPath();
      ctx.arc(22, 55, 20, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
    ctx.restore();
  };

  drawArm(true, lArmDeg, propL);

  // CORPO CAPSULA 2.5D CON CEL-SHADING E VESTITI STORICI DETTAGLIATI
  const bodyColors: Record<string, { main: string; shade: string }> = {
    king: { main: "#b91c1c", shade: "#7f1d1d" },
    groom: { main: "#2563eb", shade: "#1d4ed8" },
    general: { main: "#94a3b8", shade: "#64748b" },
    banker: { main: "#059669", shade: "#047857" },
    noble1: { main: "#7e22ce", shade: "#581c87" },
    noble2: { main: "#ea580c", shade: "#9a3412" },
  };
  const bc = bodyColors[role] || bodyColors.groom;

  ctx.fillStyle = bc.main;
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 18;
  ctx.beginPath();
  ctx.roundRect(cx - 135, 485 - bob, 270, 395, 115);
  ctx.fill();
  ctx.stroke();

  // Luce cel-shaded a sinistra e ombra a destra (Stile Ricks Clips)
  ctx.strokeStyle = "rgba(255,255,255,0.32)";
  ctx.lineWidth = 16;
  ctx.beginPath();
  ctx.moveTo(cx - 98, 540 - bob);
  ctx.lineTo(cx - 98, 810 - bob);
  ctx.stroke();

  // DETTAGLI ABITO PER OGNI RUOLO
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 12;
  if (role === "king") {
    // Fascia dorata reale con rubini + pelliccia d'ermellino
    ctx.fillStyle = "#facc15";
    ctx.fillRect(cx - 34, 500 - bob, 68, 365);
    ctx.strokeRect(cx - 34, 500 - bob, 68, 365);
    ctx.fillStyle = "#dc2626";
    ctx.beginPath();
    ctx.arc(cx, 620 - bob, 14, 0, Math.PI * 2);
    ctx.arc(cx, 710 - bob, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.moveTo(cx - 142, 505 - bob);
    ctx.quadraticCurveTo(cx, 585 - bob, cx + 142, 505 - bob);
    ctx.lineTo(cx + 148, 585 - bob);
    ctx.quadraticCurveTo(cx, 655 - bob, cx - 148, 585 - bob);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    for (const dx of [-85, -42, 0, 42, 85]) {
      ctx.fillStyle = "#111111";
      ctx.beginPath();
      ctx.arc(cx + dx, 565 - bob, 6, 0, Math.PI * 2);
      ctx.fill();
    }
  } else if (role === "groom") {
    // Colletto di corte bianco + bottoni d'oro + cintura con fibbia
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.moveTo(cx - 52, 490 - bob);
    ctx.lineTo(cx + 52, 490 - bob);
    ctx.lineTo(cx, 575 - bob);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.strokeStyle = "#eab308";
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.moveTo(cx, 575 - bob);
    ctx.lineTo(cx, 865 - bob);
    ctx.stroke();

    ctx.strokeStyle = "#111111";
    ctx.fillStyle = "#451a03";
    ctx.fillRect(cx - 132, 755 - bob, 264, 42);
    ctx.strokeRect(cx - 132, 755 - bob, 264, 42);
    ctx.fillStyle = "#facc15";
    ctx.fillRect(cx - 28, 747 - bob, 56, 58);
    ctx.strokeRect(cx - 28, 747 - bob, 56, 58);
  } else if (role === "general") {
    // Corazza d'acciaio con stemma d'oro (Niente più grigio piatto!)
    ctx.fillStyle = "#e2e8f0";
    ctx.beginPath();
    ctx.moveTo(cx - 115, 515 - bob);
    ctx.lineTo(cx + 115, 515 - bob);
    ctx.lineTo(cx + 95, 785 - bob);
    ctx.lineTo(cx, 835 - bob);
    ctx.lineTo(cx - 95, 785 - bob);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#eab308";
    ctx.beginPath();
    ctx.moveTo(cx, 595 - bob);
    ctx.lineTo(cx + 38, 650 - bob);
    ctx.lineTo(cx, 705 - bob);
    ctx.lineTo(cx - 38, 650 - bob);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else {
    // Ricami d'oro e gorgiera bianca Tudor per Banchiere e Nobili
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.moveTo(cx - 58, 515 - bob);
    ctx.lineTo(cx - 68, 855 - bob);
    ctx.moveTo(cx + 58, 515 - bob);
    ctx.lineTo(cx + 68, 855 - bob);
    ctx.stroke();

    ctx.strokeStyle = "#111111";
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.ellipse(cx, 502 - bob, 138, 30, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  drawArm(false, rArmDeg, propR);

  // TESTA ROTONDA PERFETTA STILE RICKS CLIPS (Con ombra sul mento, capelli e cappelli sopra le sopracciglia!)
  const hy = 315 - bob;
  ctx.fillStyle = "#ffffff";
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 18;
  ctx.beginPath();
  ctx.arc(cx, hy, 185, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Ombra grigia morbida sotto il mento
  ctx.fillStyle = "#e2e8f0";
  ctx.beginPath();
  ctx.arc(cx, hy, 176, 0.25, Math.PI - 0.25);
  ctx.quadraticCurveTo(cx, hy + 115, cx - 170, hy + 42);
  ctx.fill();

  // OCCHI, SOPRACCIGLIA ED ESPRESSIONI NITIDE (Sempre ben visibili sotto i cappelli!)
  const lx = cx - 64 + lookX * 14;
  const rx = cx + 64 + lookX * 14;
  const ey = hy + 8;

  ctx.fillStyle = "#111111";
  ctx.strokeStyle = "#111111";

  if (mood === "shock" || mood === "sweat") {
    ctx.fillStyle = "#ffffff";
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.ellipse(cx - 64, ey, 36, 42, 0, 0, Math.PI * 2);
    ctx.ellipse(cx + 64, ey, 36, 42, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#111111";
    ctx.beginPath();
    ctx.arc(lx, ey, 11, 0, Math.PI * 2);
    ctx.arc(rx, ey, 11, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = 13;
    ctx.beginPath();
    ctx.moveTo(cx - 105, ey - 58);
    ctx.quadraticCurveTo(cx - 64, ey - 78, cx - 26, ey - 52);
    ctx.moveTo(cx + 26, ey - 52);
    ctx.quadraticCurveTo(cx + 64, ey - 78, cx + 105, ey - 58);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx - 38, hy + 92);
    ctx.quadraticCurveTo(cx, hy + 62, cx + 38, hy + 92);
    ctx.stroke();

    // Goccia di sudore azzurra
    ctx.fillStyle = "#38bdf8";
    ctx.lineWidth = 9;
    ctx.beginPath();
    ctx.moveTo(cx - 142, hy - 55);
    ctx.quadraticCurveTo(cx - 168, hy - 12, cx - 145, hy + 4);
    ctx.quadraticCurveTo(cx - 122, hy + 12, cx - 128, hy - 18);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else if (mood === "angry") {
    ctx.beginPath();
    ctx.arc(lx, ey + 6, 16, 0, Math.PI * 2);
    ctx.arc(rx, ey + 6, 16, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = 16;
    ctx.beginPath();
    ctx.moveTo(cx - 112, ey - 42);
    ctx.lineTo(cx - 22, ey - 12);
    ctx.moveTo(cx + 112, ey - 42);
    ctx.lineTo(cx + 22, ey - 12);
    ctx.stroke();

    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.moveTo(cx - 42, hy + 92);
    ctx.quadraticCurveTo(cx, hy + 64, cx + 42, hy + 92);
    ctx.stroke();
  } else if (mood === "smug") {
    ctx.beginPath();
    ctx.arc(lx, ey + 6, 15, 0, Math.PI * 2);
    ctx.arc(rx, ey + 6, 15, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = 15;
    ctx.beginPath();
    ctx.moveTo(cx - 108, ey - 16);
    ctx.lineTo(cx - 22, ey - 12);
    ctx.moveTo(cx + 22, ey - 14);
    ctx.quadraticCurveTo(cx + 68, ey - 42, cx + 112, ey - 22);
    ctx.stroke();

    ctx.lineWidth = 13;
    ctx.beginPath();
    ctx.moveTo(cx - 42, hy + 78);
    ctx.quadraticCurveTo(cx + 8, hy + 108, cx + 56, hy + 62);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.arc(lx, ey, 15, 0, Math.PI * 2);
    ctx.arc(rx, ey, 15, 0, Math.PI * 2);
    ctx.fill();

    ctx.lineWidth = 13;
    ctx.beginPath();
    ctx.moveTo(cx - 102, ey - 36);
    ctx.quadraticCurveTo(cx - 64, ey - 54, cx - 26, ey - 36);
    ctx.moveTo(cx + 26, ey - 36);
    ctx.quadraticCurveTo(cx + 64, ey - 54, cx + 102, ey - 36);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx - 42, hy + 76);
    ctx.quadraticCurveTo(cx, hy + 104, cx + 42, hy + 76);
    ctx.stroke();
  }

  // CAPELLI, CORONE ED ELMI (Posizionati sopra la fronte, MAI sopra gli occhi!)
  ctx.lineWidth = 14;
  if (role === "king") {
    // Baffi e barba curata Tudor + Corona Reale con gemme
    ctx.strokeStyle = "#b45309";
    ctx.lineWidth = 18;
    ctx.beginPath();
    ctx.moveTo(cx - 65, hy + 56);
    ctx.quadraticCurveTo(cx, hy + 38, cx + 65, hy + 56);
    ctx.stroke();

    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 14;
    ctx.fillStyle = "#881337";
    ctx.beginPath();
    ctx.ellipse(cx, hy - 148, 205, 42, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#facc15";
    ctx.beginPath();
    ctx.moveTo(cx - 135, hy - 142);
    ctx.lineTo(cx - 152, hy - 235);
    ctx.lineTo(cx - 72, hy - 185);
    ctx.lineTo(cx, hy - 255);
    ctx.lineTo(cx + 72, hy - 185);
    ctx.lineTo(cx + 152, hy - 235);
    ctx.lineTo(cx + 135, hy - 142);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#dc2626";
    ctx.beginPath();
    ctx.arc(cx, hy - 182, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  } else if (role === "groom") {
    // Ciuffo di capelli castani + Berretto Tudor blu con piuma dorata
    ctx.fillStyle = "#451a03";
    ctx.beginPath();
    ctx.arc(cx, hy, 185, Math.PI * 1.12, Math.PI * 1.88);
    ctx.quadraticCurveTo(cx, hy - 95, cx - 165, hy - 68);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#1e3a8a";
    ctx.beginPath();
    ctx.ellipse(cx + 8, hy - 155, 175, 36, -0.06, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#facc15";
    ctx.beginPath();
    ctx.moveTo(cx + 95, hy - 172);
    ctx.quadraticCurveTo(cx + 185, hy - 255, cx + 215, hy - 175);
    ctx.quadraticCurveTo(cx + 155, hy - 155, cx + 95, hy - 172);
    ctx.fill();
    ctx.stroke();
  } else if (role === "general") {
    // Elmo da Cavaliere con visiera ALZATA sopra le sopracciglia + Piuma Rossa
    ctx.fillStyle = "#94a3b8";
    ctx.beginPath();
    ctx.arc(cx, hy - 25, 182, Math.PI * 1.08, Math.PI * 1.92);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#cbd5e1";
    ctx.fillRect(cx - 175, hy - 102, 350, 28);
    ctx.strokeRect(cx - 175, hy - 102, 350, 28);

    ctx.fillStyle = "#dc2626";
    ctx.beginPath();
    ctx.moveTo(cx, hy - 205);
    ctx.quadraticCurveTo(cx + 115, hy - 295, cx + 145, hy - 195);
    ctx.quadraticCurveTo(cx + 65, hy - 185, cx, hy - 205);
    ctx.fill();
    ctx.stroke();
  } else {
    // Cappello Tudor di velluto per Banchiere e Nobili
    ctx.fillStyle = role === "banker" ? "#064e3b" : role === "noble1" ? "#581c87" : "#7c2d12";
    ctx.beginPath();
    ctx.ellipse(cx, hy - 152, 185, 38, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  const tex = new THREE.CanvasTexture(c);
  tex.needsUpdate = true;
  return tex;
}

// AGGIUNGE UN PERSONAGGIO 2.5D NEL MONDO 3D CHE GUARDA SEMPRE LA CAMERA E PROIETTA OMBRA 3D
function spawnRicksActor3D(
  scene: THREE.Scene,
  camera: THREE.Camera,
  role: string,
  mood: string,
  x: number,
  z: number,
  walkPhase: number,
  isWalking: boolean,
  lArmDeg = 22,
  rArmDeg = -22,
  propR = "none",
  propL = "none",
  lookX = 0,
  scale = 1
): THREE.Texture {
  const tex = renderCharacterCanvas(role, mood, walkPhase, isWalking, lArmDeg, rArmDeg, propR, propL, lookX);

  const h = 4.6 * scale;
  const w = h * (1024 / 1280);
  const geo = new THREE.PlaneGeometry(w, h);
  const mat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    alphaTest: 0.08,
    side: THREE.DoubleSide,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(x, h * 0.48, z);

  // Orienta il personaggio verso la telecamera sull'asse orizzontale (Così non si vede mai di schiena o deformato!)
  const dx = camera.position.x - x;
  const dz = camera.position.z - z;
  mesh.rotation.y = Math.atan2(dx, dz);
  scene.add(mesh);

  // Ombra morbida sul pavimento 3D
  const shadowGeo = new THREE.CircleGeometry(0.85 * scale, 24);
  const shadowMat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35 });
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI * 0.5;
  shadow.position.set(x, 0.03, z);
  scene.add(shadow);

  return tex;
}

// COSTRUISCE I 5 AMBIENTI 3D DISTINTI (Cortile Esterno, Sala del Trono, Tesoreria/Guerra, Corridoio, Camera Privata)
function build3DWorld(
  scene: THREE.Scene,
  envType: "courtyard" | "throne" | "treasury" | "corridor" | "privy",
  doorOpen = 0,
  doorLocked = 0
) {
  if (envType === "courtyard") {
    // CORTILE ESTERNO SOLEGGIATO DEL CASTELLO CON CIELO, NUVOLE 3D, ALBERI 3D E FORZIERE D'ORO
    scene.background = new THREE.Color(0x38bdf8);
    scene.fog = new THREE.FogExp2(0x38bdf8, 0.015);

    const grass = new THREE.Mesh(
      new THREE.PlaneGeometry(60, 60),
      new THREE.MeshLambertMaterial({ map: getEnvTexture("grass") })
    );
    grass.rotation.x = -Math.PI * 0.5;
    scene.add(grass);

    // Vialetto imperiale in pietra e tappeto rosso
    const path = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.06, 40), new THREE.MeshLambertMaterial({ color: 0x991b1b }));
    path.position.set(0, 0.03, 0);
    scene.add(path);

    // Mura merlate del Castello Tudor sullo sfondo
    const castleWall = new THREE.Mesh(
      new THREE.BoxGeometry(34, 11, 2),
      new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") })
    );
    castleWall.position.set(0, 5.5, -12);
    scene.add(castleWall);

    for (const tx of [-11, 11]) {
      const tower = new THREE.Mesh(
        new THREE.CylinderGeometry(3.2, 3.5, 16, 16),
        new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") })
      );
      tower.position.set(tx, 8, -11);
      scene.add(tower);

      const roof = new THREE.Mesh(new THREE.ConeGeometry(3.8, 4.5, 16), new THREE.MeshLambertMaterial({ color: 0x1e3a8a }));
      roof.position.set(tx, 18.2, -11);
      scene.add(roof);
    }

    // Alberi 3D nel parco reale (Come in QlDPMzGmYac)
    for (const [ax, az] of [[-6.5, -4], [6.5, -4], [-7.5, 3], [7.5, 3]]) {
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.5, 2.8, 10), new THREE.MeshLambertMaterial({ color: 0x5c2d0c }));
      trunk.position.set(ax, 1.4, az);
      const leaves = new THREE.Mesh(new THREE.SphereGeometry(1.85, 14, 14), new THREE.MeshLambertMaterial({ color: 0x16a34a }));
      leaves.position.set(ax, 3.6, az);
      scene.add(trunk, leaves);
    }

    // Nuvole 3D bianche nel cielo
    for (const [cx, cy, cz] of [[-8, 14, -18], [7, 15, -16], [0, 16, -22]]) {
      const cloud = new THREE.Mesh(new THREE.SphereGeometry(2.4, 12, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      cloud.scale.set(2.2, 0.65, 1);
      cloud.position.set(cx, cy, cz);
      scene.add(cloud);
    }

    // Forziere del Tesoro Reale pieno di monete d'oro
    const chest = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.2, 1.4), new THREE.MeshLambertMaterial({ color: 0x78350f }));
    chest.position.set(2.2, 0.6, 1.5);
    chest.rotation.y = -0.4;
    scene.add(chest);

    const sign = new THREE.Mesh(
      new THREE.PlaneGeometry(1.8, 0.85),
      new THREE.MeshBasicMaterial({ map: getSignTexture("1,000 GOLD", "ROYAL SALARY", "#eab308", "#7f1d1d") })
    );
    sign.position.set(1.92, 0.65, 2.15);
    sign.rotation.y = -0.4;
    scene.add(sign);

    for (let i = 0; i < 18; i++) {
      const coin = new THREE.Mesh(new THREE.SphereGeometry(0.26, 10, 10), new THREE.MeshLambertMaterial({ color: 0xfacc15 }));
      coin.position.set(2.2 + (i % 4 - 1.5) * 0.38, 1.3 + (i % 3) * 0.18, 1.5 + ((i / 4) | 0) * 0.25 - 0.3);
      scene.add(coin);
    }
  } else if (envType === "throne") {
    // GRANDE SALA DEL TRONO LUMINOSA CON VETRATE, COLONNE, QUADRI E TRONO REALE
    scene.background = new THREE.Color(0x334155);
    scene.fog = new THREE.FogExp2(0x334155, 0.018);

    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshLambertMaterial({ map: getEnvTexture("wood") }));
    floor.rotation.x = -Math.PI * 0.5;
    scene.add(floor);

    const carpet = new THREE.Mesh(new THREE.BoxGeometry(5.2, 0.05, 36), new THREE.MeshLambertMaterial({ color: 0x991b1b }));
    carpet.position.set(0, 0.03, 0);
    scene.add(carpet);

    const backWall = new THREE.Mesh(new THREE.BoxGeometry(30, 16, 0.8), new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") }));
    backWall.position.set(0, 8, -9);
    scene.add(backWall);

    // Grandi Finestre luminose che danno sul cielo azzurro esterno
    for (const wx of [-6.5, 6.5]) {
      const win = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 7.5), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
      win.position.set(wx, 6.8, -8.55);
      scene.add(win);
    }

    // Grande Trono Reale Tudor al centro su pedana dorata
    const dais = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.55, 4.2), new THREE.MeshLambertMaterial({ color: 0xeab308 }));
    dais.position.set(0, 0.28, -6.2);
    scene.add(dais);

    const throneBack = new THREE.Mesh(new THREE.BoxGeometry(2.8, 5.2, 0.5), new THREE.MeshLambertMaterial({ color: 0x7f1d1d }));
    throneBack.position.set(0, 3.1, -7.2);
    scene.add(throneBack);
  } else if (envType === "treasury") {
    // SALA DEL TESORO E DELLA GUERRA CON QUADRI E MONTAGNE D'ORO
    scene.background = new THREE.Color(0x1e293b);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshLambertMaterial({ map: getEnvTexture("wood") }));
    floor.rotation.x = -Math.PI * 0.5;
    scene.add(floor);

    const wall = new THREE.Mesh(new THREE.BoxGeometry(30, 16, 0.8), new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") }));
    wall.position.set(0, 8, -8);
    scene.add(wall);

    const banner = new THREE.Mesh(
      new THREE.PlaneGeometry(5.2, 2.4),
      new THREE.MeshBasicMaterial({ map: getSignTexture("ROYAL COURT", "TUDOR ENGLAND", "#fef3c7", "#1e3a8a") })
    );
    banner.position.set(0, 6.8, -7.5);
    scene.add(banner);
  } else if (envType === "corridor") {
    // GALLERIA DEL PALAZZO CON PORTA REALE CHE SI APRE VERSO LA STANZA ILLUMINATA
    scene.background = new THREE.Color(0x334155);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 50), new THREE.MeshLambertMaterial({ map: getEnvTexture("wood") }));
    floor.rotation.x = -Math.PI * 0.5;
    scene.add(floor);

    const carpet = new THREE.Mesh(new THREE.BoxGeometry(4.8, 0.05, 46), new THREE.MeshLambertMaterial({ color: 0x991b1b }));
    carpet.position.set(0, 0.03, 0);
    scene.add(carpet);

    const wallL = new THREE.Mesh(new THREE.BoxGeometry(9, 15, 0.8), new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") }));
    wallL.position.set(-6.6, 7.5, -7.5);
    const wallR = new THREE.Mesh(new THREE.BoxGeometry(9, 15, 0.8), new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") }));
    wallR.position.set(6.6, 7.5, -7.5);
    const wallTop = new THREE.Mesh(new THREE.BoxGeometry(5, 8, 0.8), new THREE.MeshLambertMaterial({ map: getEnvTexture("stone") }));
    wallTop.position.set(0, 11, -7.5);
    scene.add(wallL, wallR, wallTop);

    // Stanza interna illuminata visibile oltre la porta aperta
    const innerRoom = new THREE.Mesh(new THREE.BoxGeometry(6, 8, 0.5), new THREE.MeshBasicMaterial({ color: 0xf59e0b }));
    innerRoom.position.set(0, 4, -9.2);
    scene.add(innerRoom);

    const doorPivot = new THREE.Group();
    doorPivot.position.set(-2.1, 0, -7.2);
    doorPivot.rotation.y = doorOpen * 1.45;
    scene.add(doorPivot);

    const door = new THREE.Mesh(new THREE.BoxGeometry(4.2, 7.0, 0.28), new THREE.MeshLambertMaterial({ color: 0x5c2d0c }));
    door.position.set(2.1, 3.5, 0);
    doorPivot.add(door);

    const sign = new THREE.Mesh(
      new THREE.PlaneGeometry(3.1, 1.45),
      new THREE.MeshBasicMaterial({ map: getSignTexture("ROYAL PRIVY", "GROOM OF THE STOOL", "#eab308", "#7f1d1d") })
    );
    sign.position.set(2.1, 4.4, 0.18);
    doorPivot.add(sign);

    if (doorLocked > 0) {
      const barY = interpolate(doorLocked, [0, 1], [8.2, 3.2], clamp);
      const bar = new THREE.Mesh(new THREE.BoxGeometry(5.4, 0.45, 0.35), new THREE.MeshLambertMaterial({ color: 0x1e293b }));
      bar.position.set(0, barY, -6.9);
      const lock = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.95, 0.45), new THREE.MeshLambertMaterial({ color: 0xfacc15 }));
      lock.position.set(0, barY - 0.1, -6.75);
      scene.add(bar, lock);
    }
  } else if (envType === "privy") {
    // STANZA PRIVATA DEL RE CON LIBRERIE 3D, QUADRI, TAPPETO E TRONO-GABINETTO IN VELLUTO
    scene.background = new THREE.Color(0x3b0764);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(36, 36), new THREE.MeshLambertMaterial({ map: getEnvTexture("wood") }));
    floor.rotation.x = -Math.PI * 0.5;
    scene.add(floor);

    const rug = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, 0.05, 32), new THREE.MeshLambertMaterial({ color: 0x991b1b }));
    rug.position.set(0, 0.03, -0.5);
    scene.add(rug);

    const backWall = new THREE.Mesh(new THREE.BoxGeometry(28, 15, 0.8), new THREE.MeshLambertMaterial({ color: 0x4c1d95 }));
    backWall.position.set(0, 7.5, -7.5);
    scene.add(backWall);

    // Grande Libreria 3D piena di libri colorati a destra
    const bookcase = new THREE.Mesh(new THREE.BoxGeometry(4.6, 7.5, 0.9), new THREE.MeshLambertMaterial({ map: getEnvTexture("books") }));
    bookcase.position.set(4.2, 3.75, -6.8);
    scene.add(bookcase);

    // IL TRONO-GABINETTO ("ROYAL CLOSE STOOL")
    const stoolGroup = new THREE.Group();
    stoolGroup.position.set(-1.9, 0, -1.6);
    stoolGroup.rotation.y = 0.28;

    const back = new THREE.Mesh(new THREE.BoxGeometry(2.3, 3.8, 0.45), new THREE.MeshLambertMaterial({ color: 0x991b1b }));
    back.position.set(0, 1.9, -0.8);
    const box = new THREE.Mesh(new THREE.BoxGeometry(2.3, 1.5, 1.9), new THREE.MeshLambertMaterial({ color: 0xb91c1c }));
    box.position.set(0, 0.75, 0.1);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.65, 0.09, 12, 24), new THREE.MeshLambertMaterial({ color: 0xfacc15 }));
    rim.rotation.x = Math.PI * 0.5;
    rim.position.set(0, 1.54, 0.15);
    const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 0.08, 24), new THREE.MeshBasicMaterial({ color: 0x09090b }));
    hole.position.set(0, 1.51, 0.15);
    stoolGroup.add(back, box, rim, hole);
    scene.add(stoolGroup);
  }
}

function cleanScene(scene: THREE.Scene) {
  scene.traverse((obj: any) => {
    if (obj.isMesh) {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m: any) => m.dispose());
        else obj.material.dispose();
      }
    }
  });
}

let sharedRenderer: THREE.WebGLRenderer | null = null;

export const GroomStory: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const time = frame / fps;

  let seg: any = TIMINGS[TIMINGS.length - 1];
  for (const s of TIMINGS) {
    if (time >= s.start && time < s.end) {
      seg = s;
      break;
    }
  }
  const idx = seg.index;
  const p = Math.max(0, Math.min(1, (time - seg.start) / Math.max(0.01, seg.duration)));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (!sharedRenderer) {
      sharedRenderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        powerPreference: "high-performance",
        preserveDrawingBuffer: true,
      });
      sharedRenderer.setSize(1080, 1920, false);
      sharedRenderer.toneMapping = THREE.ACESFilmicToneMapping;
      sharedRenderer.toneMappingExposure = 1.12;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1080 / 1920, 0.1, 150);

    // Illuminazione 3D da Studio Cinematografico
    const hemi = new THREE.HemisphereLight(0xffffff, 0x334155, 1.05);
    scene.add(hemi);
    const sun = new THREE.DirectionalLight(0xfffbeb, 1.35);
    sun.position.set(8, 18, 12);
    scene.add(sun);

    const wPhase = frame * 0.28;
    const dynamicTextures: THREE.Texture[] = [];

    // 18 SCENE CON INQUADRATURE AMPIE E NITIDE (Nessun personaggio tagliato a metà o di schiena!)
    if (idx === 0) {
      build3DWorld(scene, "courtyard");
      camera.position.set(interpolate(p, [0, 1], [3.2, 0.8]), interpolate(p, [0, 1], [4.2, 3.0]), interpolate(p, [0, 1], [11.5, 8.2]));
      camera.lookAt(0.4, 2.2, 0.8);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "groom", "smug", -0.6, 1.2, wPhase, false, -30, -55, "key", "goldbag", 0.3));
    } else if (idx === 1) {
      build3DWorld(scene, "corridor", interpolate(p, [0.45, 1], [0, 0.9], clamp));
      const zWalk = interpolate(p, [0, 1], [2.5, -3.2]);
      camera.position.set(2.4, 3.1, zWalk + 7.8);
      camera.lookAt(0, 2.3, zWalk - 1.5);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "normal", -1.15, zWalk, wPhase, true, 20, -45, "key", "none", 0.3),
        spawnRicksActor3D(scene, camera, "groom", "normal", 1.15, zWalk + 0.8, wPhase + 1.5, true, 20, 20, "none", "none", -0.3)
      );
    } else if (idx === 2) {
      build3DWorld(scene, "privy");
      camera.position.set(interpolate(p, [0, 1], [-1.5, 1.2]), 2.9, interpolate(p, [0, 1], [8.6, 6.8]));
      camera.lookAt(0, 2.3, -1.0);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "smug", -1.65, -1.1, 0, false, 20, 20, "none", "none", 0.5),
        spawnRicksActor3D(scene, camera, "groom", "shock", 1.35, -0.6, 0, false, 25, -62, "paper", "none", -0.5)
      );
    } else if (idx === 3) {
      build3DWorld(scene, "throne");
      camera.position.set(interpolate(p, [0, 1], [-2.8, 2.8]), 2.8, 8.8);
      camera.lookAt(0, 2.4, 0);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "king", "smug", 0, 0.5, 0, false, -25, -55, "key", "none", 0));
    } else if (idx === 4) {
      build3DWorld(scene, "treasury");
      const gx = interpolate(p, [0, 0.45], [-2.8, 0], clamp);
      camera.position.set(1.8, 2.9, 8.5);
      camera.lookAt(0, 2.3, 0);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "general", p < 0.55 ? "smug" : "shock", gx, 0.5, wPhase, p < 0.45, -35, -55, "sword", "shield", 0));
    } else if (idx === 5) {
      build3DWorld(scene, "courtyard");
      const bx = interpolate(p, [0, 0.45], [-2.8, -0.5], clamp);
      camera.position.set(-1.6, 2.9, 8.5);
      camera.lookAt(0.4, 2.3, 0.8);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "banker", p < 0.55 ? "smug" : "shock", bx, 0.8, wPhase, p < 0.45, -45, -55, "goldbag", "goldbag", 0.3));
    } else if (idx === 6) {
      build3DWorld(scene, "corridor", interpolate(p, [0.2, 1], [0, 0.85], clamp));
      camera.position.set(interpolate(p, [0, 1], [-1.6, 1.6]), 2.8, 1.8);
      camera.lookAt(0, 2.4, -5.5);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "groom", "smug", 0, -3.5, 0, false, 20, -60, "key", "none", 0));
    } else if (idx === 7) {
      build3DWorld(scene, "corridor", 0.95);
      const zIn = interpolate(p, [0, 1], [-1.5, -5.8]);
      camera.position.set(2.2, 3.1, 2.8);
      camera.lookAt(0, 2.4, -5.5);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "normal", -1.1, zIn, wPhase, true, 20, 20, "none", "none", 0.2),
        spawnRicksActor3D(scene, camera, "groom", "sweat", 1.1, zIn + 0.9, wPhase + 1.2, true, 20, -58, "paper", "none", -0.2)
      );
    } else if (idx === 8) {
      build3DWorld(scene, "privy");
      camera.position.set(interpolate(p, [0, 1], [1.8, -0.6]), 2.9, 7.4);
      camera.lookAt(-0.2, 2.3, -0.8);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "groom", "sweat", 0.8, -0.4, 0, false, -45, -62, "paper", "none", -0.4));
    } else if (idx === 9) {
      build3DWorld(scene, "courtyard");
      const lunge = Math.sin(frame * 0.26) * 0.65;
      camera.position.set(Math.sin(p * 2) * 2.5, 3.1, 8.8);
      camera.lookAt(0, 2.3, 0);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "noble1", "angry", -1.55 + lunge, 0.4, wPhase, true, 20, -60 + Math.sin(frame * 0.35) * 28, "sword", "none", 0.5),
        spawnRicksActor3D(scene, camera, "noble2", "angry", 1.55 - lunge, 0.4, wPhase + 1, true, 20, -60 + Math.cos(frame * 0.35) * 28, "sword", "none", -0.5)
      );
    } else if (idx === 10) {
      build3DWorld(scene, "throne");
      camera.position.set(0, 2.8, interpolate(p, [0, 1], [7.8, 6.2]));
      camera.lookAt(0, 2.5, 0);
      dynamicTextures.push(spawnRicksActor3D(scene, camera, "groom", "smug", 0, 0, 0, false, 20, -58, "key", "none", 0.3));
    } else if (idx === 11) {
      build3DWorld(scene, "corridor", interpolate(p, [0, 0.35], [0.85, 0], clamp), interpolate(p, [0.35, 0.75], [0, 1], clamp));
      camera.position.set(interpolate(p, [0, 1], [-2.2, 2.2]), 3.0, 1.8);
      camera.lookAt(0, 2.5, -5.5);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "normal", -1.35, -4.2, 0, false, 20, 20, "none", "none", 0.4),
        spawnRicksActor3D(scene, camera, "groom", "smug", 1.35, -4.2, 0, false, 20, -55, "key", "none", -0.4)
      );
    } else if (idx === 12 || idx === 13) {
      build3DWorld(scene, "privy");
      camera.position.set(interpolate(p, [0, 1], [2.2, -1.8]), 2.9, 7.6);
      camera.lookAt(0, 2.4, -0.5);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "smug", -1.3, -0.5, 0, false, 20, -45, "none", "none", 0.5),
        spawnRicksActor3D(scene, camera, "groom", "smug", 1.3, -0.5, 0, false, 20, -58, "scroll", "none", -0.5)
      );
    } else if (idx === 14) {
      build3DWorld(scene, "throne");
      camera.position.set(-2.2, 2.9, 8.4);
      camera.lookAt(0, 2.4, 0);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "king", "angry", -1.4, 0, 0, false, 20, -68, "none", "none", 0.5),
        spawnRicksActor3D(scene, camera, "noble1", "sweat", interpolate(p, [0, 1], [0.9, 1.9]), 0, wPhase, true, -45, -45, "none", "none", -0.5)
      );
    } else if (idx === 15) {
      build3DWorld(scene, "corridor", 0, 1);
      camera.position.set(2.2, 2.9, 1.8);
      camera.lookAt(0, 2.4, -5.0);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "noble2", "sweat", interpolate(p, [0, 0.55], [-2.6, -1.35], clamp), -3.8, wPhase, p < 0.55, -50, -50, "none", "none", 0.5),
        spawnRicksActor3D(scene, camera, "groom", "smug", 1.25, -3.8, 0, false, 20, -58, "key", "none", -0.5)
      );
    } else if (idx === 16) {
      build3DWorld(scene, "corridor", 0, 1);
      camera.position.set(interpolate(p, [0, 1], [-2.8, 2.8]), 3.2, 2.5);
      camera.lookAt(0, 2.4, -4.5);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "general", "sweat", -1.95, -3.8, wPhase, p < 0.5),
        spawnRicksActor3D(scene, camera, "banker", "sweat", 0, -3.8, wPhase + 1, p < 0.5, 20, -55, "goldbag"),
        spawnRicksActor3D(scene, camera, "noble1", "sweat", 1.95, -3.8, wPhase + 2, p < 0.5)
      );
    } else {
      build3DWorld(scene, "throne");
      camera.position.set(Math.sin(p * 1.5) * 2.0, interpolate(p, [0, 1], [2.6, 3.6]), interpolate(p, [0, 1], [9.2, 7.6]));
      camera.lookAt(0, 2.5, 0);
      dynamicTextures.push(
        spawnRicksActor3D(scene, camera, "groom", "smug", 0, 0.2, 0, false, -45, -60, "paper", "goldbag", 0, 1.15),
        spawnRicksActor3D(scene, camera, "king", "normal", -2.2, 1.2, 0, false, 20, 20, "none", "none", 0, 0.82),
        spawnRicksActor3D(scene, camera, "general", "sweat", 2.2, 1.2, 0, false, 20, 20, "none", "none", 0, 0.82)
      );
    }

    sharedRenderer.render(scene, camera);
    sharedRenderer.renderLists.dispose();
    cleanScene(scene);
    dynamicTextures.forEach((t) => t.dispose());
  }, [frame, idx, p]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#09090b" }}>
      <Audio src={staticFile("voce.mp3")} />
      <canvas ref={canvasRef} width={1080} height={1920} style={{ width: "100%", height: "100%" }} />
    </AbsoluteFill>
  );
};
'''
open("src/GroomStory.tsx", "w").write(code)
print("✅ MOTORE IBRIDO 3D WORLD + 2.5D HIGH-RES RICKS CLIPS INSTALLATO!")
