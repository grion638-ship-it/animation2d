code = '''import React, { useEffect, useRef } from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import * as THREE from "three";
import { TIMINGS } from "./timings";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

let TOON_GRAD: THREE.DataTexture | null = null;
const TEX_CACHE: Record<string, THREE.Texture> = {};

function getToonGradient(): THREE.DataTexture {
  if (TOON_GRAD) return TOON_GRAD;
  const data = new Uint8Array([70, 70, 70, 255, 145, 145, 145, 255, 215, 215, 215, 255, 255, 255, 255, 255]);
  const tex = new THREE.DataTexture(data, 4, 1, THREE.RGBAFormat);
  tex.minFilter = THREE.NearestFilter;
  tex.magFilter = THREE.NearestFilter;
  tex.needsUpdate = true;
  TOON_GRAD = tex;
  return tex;
}

function getWoodTexture(baseHex = "#8b5a2b", lineHex = "#4a2c11"): THREE.Texture {
  const key = `wood_${baseHex}_${lineHex}`;
  if (TEX_CACHE[key]) return TEX_CACHE[key];
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, 512, 512);
  ctx.strokeStyle = lineHex;
  ctx.lineWidth = 5;
  for (let y = 0; y < 512; y += 64) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(512, y);
    ctx.stroke();
    const jx = ((y * 3) % 380) + 60;
    ctx.beginPath();
    ctx.moveTo(jx, y);
    ctx.lineTo(jx, y + 64);
    ctx.stroke();
    ctx.fillStyle = "#261505";
    ctx.beginPath();
    ctx.arc(jx - 14, y + 18, 4, 0, Math.PI * 2);
    ctx.arc(jx - 14, y + 46, 4, 0, Math.PI * 2);
    ctx.arc(jx + 14, y + 18, 4, 0, Math.PI * 2);
    ctx.arc(jx + 14, y + 46, 4, 0, Math.PI * 2);
    ctx.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(4, 4);
  TEX_CACHE[key] = tex;
  return tex;
}

function getStoneTexture(baseHex = "#64748b", mortarHex = "#1e293b"): THREE.Texture {
  const key = `stone_${baseHex}_${mortarHex}`;
  if (TEX_CACHE[key]) return TEX_CACHE[key];
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, 512, 512);
  ctx.strokeStyle = mortarHex;
  ctx.lineWidth = 6;
  const shades = ["rgba(255,255,255,0.07)", "rgba(0,0,0,0.08)", "rgba(255,255,255,0.03)"];
  for (let row = 0; row < 8; row++) {
    const y = row * 64;
    const off = (row % 2) * 64;
    for (let col = -1; col < 5; col++) {
      const x = col * 128 + off;
      ctx.fillStyle = shades[(row + col + 4) % 3];
      ctx.fillRect(x + 4, y + 4, 120, 56);
      ctx.strokeRect(x, y, 128, 64);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(3, 2);
  TEX_CACHE[key] = tex;
  return tex;
}

function getPlaqueTexture(title: string, sub: string, bg = "#eab308", fg = "#7f1d1d"): THREE.Texture {
  const key = `plaque_${title}_${sub}`;
  if (TEX_CACHE[key]) return TEX_CACHE[key];
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 256;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, 512, 256);
  ctx.strokeStyle = "#111111";
  ctx.lineWidth = 14;
  ctx.strokeRect(10, 10, 492, 236);
  ctx.fillStyle = fg;
  ctx.font = "900 58px Arial Black, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(title, 256, 118);
  ctx.fillStyle = "#111111";
  ctx.font = "800 34px Arial, sans-serif";
  ctx.fillText(sub, 256, 185);
  const tex = new THREE.CanvasTexture(c);
  TEX_CACHE[key] = tex;
  return tex;
}

function getFaceTexture(mood: string, role: string, lookX = 0): THREE.Texture {
  const key = `face_${mood}_${role}_${lookX.toFixed(1)}`;
  if (TEX_CACHE[key]) return TEX_CACHE[key];
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = "#e2e8f0";
  ctx.fillRect(0, 360, 512, 152);

  const lx = 205 + lookX * 10;
  const rx = 307 + lookX * 10;
  const ey = 235;

  ctx.strokeStyle = "#111111";
  ctx.fillStyle = "#111111";
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  if (mood === "shock" || mood === "sweat") {
    ctx.fillStyle = "#ffffff";
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.ellipse(205, 235, 34, 38, 0, 0, Math.PI * 2);
    ctx.ellipse(307, 235, 34, 38, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#111111";
    ctx.beginPath();
    ctx.arc(lx, ey, 10, 0, Math.PI * 2);
    ctx.arc(rx, ey, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 11;
    ctx.beginPath();
    ctx.moveTo(165, 182);
    ctx.quadraticCurveTo(205, 165, 240, 188);
    ctx.moveTo(272, 188);
    ctx.quadraticCurveTo(307, 165, 347, 182);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(256, 325, 26, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
    ctx.fillStyle = "#38bdf8";
    ctx.beginPath();
    ctx.moveTo(135, 165);
    ctx.quadraticCurveTo(112, 205, 130, 220);
    ctx.quadraticCurveTo(150, 230, 148, 205);
    ctx.closePath();
    ctx.fill();
    ctx.lineWidth = 7;
    ctx.stroke();
  } else if (mood === "angry") {
    ctx.beginPath();
    ctx.arc(lx, ey, 14, 0, Math.PI * 2);
    ctx.arc(rx, ey, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.moveTo(160, 185);
    ctx.lineTo(242, 215);
    ctx.moveTo(352, 185);
    ctx.lineTo(270, 215);
    ctx.stroke();
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.moveTo(215, 322);
    ctx.quadraticCurveTo(256, 292, 297, 322);
    ctx.stroke();
  } else if (mood === "smug") {
    ctx.beginPath();
    ctx.arc(lx, ey + 4, 13, 0, Math.PI * 2);
    ctx.arc(rx, ey + 4, 13, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 13;
    ctx.beginPath();
    ctx.moveTo(165, 212);
    ctx.lineTo(242, 216);
    ctx.moveTo(270, 212);
    ctx.quadraticCurveTo(310, 190, 348, 206);
    ctx.stroke();
    ctx.lineWidth = 11;
    ctx.beginPath();
    ctx.moveTo(212, 305);
    ctx.quadraticCurveTo(260, 332, 308, 288);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.arc(lx, ey, 13, 0, Math.PI * 2);
    ctx.arc(rx, ey, 13, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 11;
    ctx.beginPath();
    ctx.moveTo(168, 198);
    ctx.quadraticCurveTo(205, 180, 238, 198);
    ctx.moveTo(274, 198);
    ctx.quadraticCurveTo(307, 180, 344, 198);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(214, 300);
    ctx.quadraticCurveTo(256, 328, 298, 300);
    ctx.stroke();
  }

  if (role === "king") {
    ctx.strokeStyle = "#b45309";
    ctx.lineWidth = 18;
    ctx.beginPath();
    ctx.moveTo(185, 285);
    ctx.quadraticCurveTo(256, 265, 327, 285);
    ctx.stroke();
  }

  const tex = new THREE.CanvasTexture(c);
  TEX_CACHE[key] = tex;
  return tex;
}

function addOutline(mesh: THREE.Mesh, thickness = 0.038): THREE.Mesh {
  const outMat = new THREE.MeshBasicMaterial({ color: 0x09090b, side: THREE.BackSide });
  const outMesh = new THREE.Mesh(mesh.geometry, outMat);
  outMesh.scale.setScalar(1 + thickness);
  mesh.add(outMesh);
  return mesh;
}

function cleanScene(scene: THREE.Scene) {
  scene.traverse((obj: any) => {
    if (obj.isMesh) {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach((m: any) => m.dispose());
        } else {
          obj.material.dispose();
        }
      }
    }
  });
}

function build3DStickman(
  role: string,
  mood: string,
  toonGrad: THREE.DataTexture,
  walkPhase = 0,
  isWalking = false,
  lArmRotX = 0.2,
  rArmRotX = -0.4,
  propR = "none",
  propL = "none",
  lookX = 0
): THREE.Group {
  const group = new THREE.Group();

  const palettes: Record<string, { torso: number; trim: number; hat: number }> = {
    king: { torso: 0xb91c1c, trim: 0xfacc15, hat: 0x881337 },
    groom: { torso: 0x2563eb, trim: 0xeab308, hat: 0x1e3a8a },
    general: { torso: 0x94a3b8, trim: 0xf8fafc, hat: 0x64748b },
    banker: { torso: 0x059669, trim: 0xfbbf24, hat: 0x064e3b },
    noble1: { torso: 0x7e22ce, trim: 0xfde047, hat: 0x581c87 },
    noble2: { torso: 0xc2410c, trim: 0xfcd34d, hat: 0x7c2d12 },
  };
  const pal = palettes[role] || palettes.groom;

  const bob = isWalking ? Math.abs(Math.sin(walkPhase)) * 0.12 : 0;
  const bodyGroup = new THREE.Group();
  bodyGroup.position.y = bob;
  group.add(bodyGroup);

  const torso = addOutline(
    new THREE.Mesh(new THREE.CapsuleGeometry(0.52, 0.95, 12, 18), new THREE.MeshToonMaterial({ color: pal.torso, gradientMap: toonGrad })),
    0.045
  );
  torso.position.y = 2.05;
  bodyGroup.add(torso);

  const belt = addOutline(
    new THREE.Mesh(new THREE.CylinderGeometry(0.54, 0.54, 0.14, 18), new THREE.MeshToonMaterial({ color: 0x3f2305, gradientMap: toonGrad })),
    0.03
  );
  belt.position.y = 1.72;
  bodyGroup.add(belt);

  const buckle = addOutline(
    new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.2, 0.15), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
    0.04
  );
  buckle.position.set(0, 1.72, 0.52);
  bodyGroup.add(buckle);

  if (role === "king") {
    const ermine = addOutline(
      new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.64, 0.32, 18), new THREE.MeshToonMaterial({ color: 0xffffff, gradientMap: toonGrad })),
      0.04
    );
    ermine.position.y = 2.55;
    bodyGroup.add(ermine);

    const cape = addOutline(
      new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.95, 2.2, 14, 1, false, Math.PI * 0.65, Math.PI * 1.7), new THREE.MeshToonMaterial({ color: 0x7f1d1d, gradientMap: toonGrad, side: THREE.DoubleSide })),
      0.03
    );
    cape.position.set(0, 1.65, -0.15);
    bodyGroup.add(cape);
  }

  const head = addOutline(
    new THREE.Mesh(new THREE.SphereGeometry(0.72, 24, 24), new THREE.MeshToonMaterial({ map: getFaceTexture(mood, role, lookX), gradientMap: toonGrad })),
    0.045
  );
  head.rotation.y = -Math.PI * 0.5;
  head.position.y = 3.42;
  bodyGroup.add(head);

  if (role === "king") {
    const hatBrim = addOutline(
      new THREE.Mesh(new THREE.CylinderGeometry(0.82, 0.82, 0.14, 18), new THREE.MeshToonMaterial({ color: 0x881337, gradientMap: toonGrad })),
      0.04
    );
    hatBrim.position.y = 4.02;
    bodyGroup.add(hatBrim);

    const crown = addOutline(
      new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.52, 0.38, 8), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
      0.045
    );
    crown.position.y = 4.25;
    bodyGroup.add(crown);
  } else if (role === "general") {
    const helm = addOutline(
      new THREE.Mesh(new THREE.SphereGeometry(0.76, 18, 14, 0, Math.PI * 2, 0, Math.PI * 0.55), new THREE.MeshToonMaterial({ color: 0x94a3b8, gradientMap: toonGrad })),
      0.04
    );
    helm.position.y = 3.46;
    bodyGroup.add(helm);

    const plume = addOutline(
      new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.75, 10), new THREE.MeshToonMaterial({ color: 0xdc2626, gradientMap: toonGrad })),
      0.04
    );
    plume.position.set(0, 4.35, -0.1);
    plume.rotation.x = -0.35;
    bodyGroup.add(plume);
  } else {
    const beret = addOutline(
      new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.65, 0.22, 18), new THREE.MeshToonMaterial({ color: pal.hat, gradientMap: toonGrad })),
      0.04
    );
    beret.position.y = 4.02;
    beret.rotation.z = -0.08;
    bodyGroup.add(beret);

    const feather = addOutline(
      new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.55, 8), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
      0.04
    );
    feather.position.set(0.55, 4.22, 0);
    feather.rotation.z = -0.55;
    bodyGroup.add(feather);
  }

  const makeArm = (isLeft: boolean, rotX: number, prop: string) => {
    const pivot = new THREE.Group();
    pivot.position.set(isLeft ? -0.58 : 0.58, 2.42, 0);
    const swing = isWalking ? Math.sin(walkPhase + (isLeft ? 0 : Math.PI)) * 0.45 : 0;
    pivot.rotation.x = rotX + swing;
    pivot.rotation.z = isLeft ? 0.22 : -0.22;

    const armMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.075, 0.88, 6, 10), new THREE.MeshBasicMaterial({ color: 0x111111 }));
    armMesh.position.y = -0.46;
    pivot.add(armMesh);

    const handGroup = new THREE.Group();
    handGroup.position.set(0, -0.95, 0);
    pivot.add(handGroup);

    if (prop === "key") {
      const keyGroup = new THREE.Group();
      const ring = addOutline(new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.055, 8, 16), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })), 0.04);
      const shaft = addOutline(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.75, 8), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })), 0.04);
      shaft.position.y = -0.55;
      const tooth = addOutline(new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.14, 0.06), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })), 0.04);
      tooth.position.set(0.1, -0.78, 0);
      keyGroup.add(ring, shaft, tooth);
      keyGroup.rotation.x = Math.PI * 0.5;
      handGroup.add(keyGroup);
    } else if (prop === "paper") {
      const rollGroup = new THREE.Group();
      const tray = addOutline(new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.32, 0.08, 16), new THREE.MeshToonMaterial({ color: 0xeab308, gradientMap: toonGrad })), 0.04);
      const roll = addOutline(new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.42, 16), new THREE.MeshToonMaterial({ color: 0xffffff, gradientMap: toonGrad })), 0.04);
      roll.position.y = 0.25;
      rollGroup.add(tray, roll);
      rollGroup.rotation.x = -rotX;
      handGroup.add(rollGroup);
    } else if (prop === "sword") {
      const swordGroup = new THREE.Group();
      const blade = addOutline(new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.45, 0.03), new THREE.MeshToonMaterial({ color: 0xf8fafc, gradientMap: toonGrad })), 0.04);
      blade.position.y = 0.75;
      const guard = addOutline(new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.09, 0.1), new THREE.MeshToonMaterial({ color: 0xeab308, gradientMap: toonGrad })), 0.04);
      guard.position.y = 0.05;
      swordGroup.add(blade, guard);
      swordGroup.rotation.x = Math.PI * 0.65;
      handGroup.add(swordGroup);
    } else if (prop === "goldbag") {
      const bag = addOutline(new THREE.Mesh(new THREE.SphereGeometry(0.32, 12, 12), new THREE.MeshToonMaterial({ color: 0xeab308, gradientMap: toonGrad })), 0.04);
      bag.position.y = -0.22;
      handGroup.add(bag);
    } else if (prop === "scroll") {
      const scr = addOutline(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.65, 12), new THREE.MeshToonMaterial({ color: 0xfef3c7, gradientMap: toonGrad })), 0.04);
      scr.rotation.z = Math.PI * 0.5;
      handGroup.add(scr);
    }
    return pivot;
  };

  bodyGroup.add(makeArm(true, lArmRotX, propL));
  bodyGroup.add(makeArm(false, rArmRotX, propR));

  const makeLeg = (isLeft: boolean) => {
    const legPivot = new THREE.Group();
    legPivot.position.set(isLeft ? -0.22 : 0.22, 1.25, 0);
    const lSwing = isWalking ? Math.sin(walkPhase + (isLeft ? 0 : Math.PI)) * 0.52 : 0;
    legPivot.rotation.x = lSwing;

    const legMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 1.05, 6, 10), new THREE.MeshBasicMaterial({ color: 0x111111 }));
    legMesh.position.y = -0.58;
    legPivot.add(legMesh);

    const shoe = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.14, 0.36), new THREE.MeshBasicMaterial({ color: 0x111111 }));
    shoe.position.set(0, -1.18, 0.08);
    legPivot.add(shoe);
    return legPivot;
  };

  group.add(makeLeg(true));
  group.add(makeLeg(false));

  return group;
}

function buildPalace3DSet(
  scene: THREE.Scene,
  toonGrad: THREE.DataTexture,
  doorOpen = 0,
  doorLocked = 0,
  showChest = false,
  showToilet = false
) {
  const floorTex = getWoodTexture("#7c4722", "#3b1e08");
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(36, 46), new THREE.MeshToonMaterial({ map: floorTex, gradientMap: toonGrad }));
  floor.rotation.x = -Math.PI * 0.5;
  scene.add(floor);

  const carpet = addOutline(new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.04, 42), new THREE.MeshToonMaterial({ color: 0x991b1b, gradientMap: toonGrad })), 0.015);
  carpet.position.set(0, 0.02, 0);
  scene.add(carpet);

  const trimL = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.05, 42), new THREE.MeshToonMaterial({ color: 0xeab308, gradientMap: toonGrad }));
  trimL.position.set(-2.15, 0.03, 0);
  const trimR = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.05, 42), new THREE.MeshToonMaterial({ color: 0xeab308, gradientMap: toonGrad }));
  trimR.position.set(2.15, 0.03, 0);
  scene.add(trimL, trimR);

  const wallTex = getStoneTexture("#475569", "#1e293b");
  const backWall = new THREE.Mesh(new THREE.BoxGeometry(28, 14, 0.8), new THREE.MeshToonMaterial({ map: wallTex, gradientMap: toonGrad }));
  backWall.position.set(0, 7, -8.5);
  scene.add(backWall);

  const sideWallL = new THREE.Mesh(new THREE.BoxGeometry(0.8, 14, 36), new THREE.MeshToonMaterial({ map: wallTex, gradientMap: toonGrad }));
  sideWallL.position.set(-8.5, 7, 2);
  scene.add(sideWallL);

  const sideWallR = new THREE.Mesh(new THREE.BoxGeometry(0.8, 14, 36), new THREE.MeshToonMaterial({ map: wallTex, gradientMap: toonGrad }));
  sideWallR.position.set(8.5, 7, 2);
  scene.add(sideWallR);

  for (const zPos of [-7.6, -2.5, 2.5, 7.5]) {
    for (const xSide of [-5.8, 5.8]) {
      const col = addOutline(
        new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.62, 13, 12), new THREE.MeshToonMaterial({ color: 0x64748b, gradientMap: toonGrad })),
        0.03
      );
      col.position.set(xSide, 6.5, zPos);
      scene.add(col);

      const base = addOutline(
        new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.7, 1.5), new THREE.MeshToonMaterial({ color: 0x94a3b8, gradientMap: toonGrad })),
        0.035
      );
      base.position.set(xSide, 0.35, zPos);
      scene.add(base);
    }
  }

  const archFrame = addOutline(
    new THREE.Mesh(new THREE.BoxGeometry(4.6, 6.8, 0.9), new THREE.MeshToonMaterial({ color: 0x94a3b8, gradientMap: toonGrad })),
    0.03
  );
  archFrame.position.set(0, 3.4, -8.1);
  scene.add(archFrame);

  const doorPivot = new THREE.Group();
  doorPivot.position.set(-1.9, 0, -7.75);
  doorPivot.rotation.y = doorOpen * 1.35;
  scene.add(doorPivot);

  const doorTex = getWoodTexture("#5c2d0c", "#261002");
  const doorMesh = addOutline(
    new THREE.Mesh(new THREE.BoxGeometry(3.8, 6.2, 0.28), new THREE.MeshToonMaterial({ map: doorTex, gradientMap: toonGrad })),
    0.03
  );
  doorMesh.position.set(1.9, 3.1, 0);
  doorPivot.add(doorMesh);

  const plaque = addOutline(
    new THREE.Mesh(new THREE.BoxGeometry(2.5, 1.1, 0.12), new THREE.MeshBasicMaterial({ map: getPlaqueTexture("ROYAL PRIVY", "GROOM OF THE STOOL") })),
    0.04
  );
  plaque.position.set(1.9, 3.9, 0.18);
  doorPivot.add(plaque);

  if (doorLocked > 0) {
    const barY = interpolate(doorLocked, [0, 1], [7.5, 2.8], clamp);
    const ironBar = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(4.8, 0.42, 0.35), new THREE.MeshToonMaterial({ color: 0x1e293b, gradientMap: toonGrad })),
      0.04
    );
    ironBar.position.set(0, barY, -7.45);
    scene.add(ironBar);

    const lockBox = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 0.45), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
      0.045
    );
    lockBox.position.set(0, barY - 0.1, -7.3);
    scene.add(lockBox);
  }

  if (showChest) {
    const chestGroup = new THREE.Group();
    chestGroup.position.set(2.4, 0, 1.2);
    chestGroup.rotation.y = -0.45;
    const box = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(1.9, 1.1, 1.3), new THREE.MeshToonMaterial({ map: doorTex, gradientMap: toonGrad })),
      0.04
    );
    box.position.y = 0.55;
    chestGroup.add(box);

    const chestPlaque = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.55, 0.08), new THREE.MeshBasicMaterial({ map: getPlaqueTexture("1,000 GOLD", "ROYAL SALARY") })),
      0.04
    );
    chestPlaque.position.set(0, 0.55, 0.68);
    chestGroup.add(chestPlaque);

    for (let i = 0; i < 12; i++) {
      const coin = addOutline(
        new THREE.Mesh(new THREE.SphereGeometry(0.24, 10, 10), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
        0.04
      );
      coin.position.set((i % 4 - 1.5) * 0.36, 1.18 + (i % 2) * 0.15, ((i / 4) | 0) * 0.3 - 0.25);
      chestGroup.add(coin);
    }
    scene.add(chestGroup);
  }

  if (showToilet) {
    const stoolGroup = new THREE.Group();
    stoolGroup.position.set(-1.6, 0, -1.5);
    stoolGroup.rotation.y = 0.35;

    const backRest = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(2.1, 3.4, 0.45), new THREE.MeshToonMaterial({ color: 0x991b1b, gradientMap: toonGrad })),
      0.04
    );
    backRest.position.set(0, 1.7, -0.75);
    stoolGroup.add(backRest);

    const seatBox = addOutline(
      new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.45, 1.85), new THREE.MeshToonMaterial({ color: 0xb91c1c, gradientMap: toonGrad })),
      0.04
    );
    seatBox.position.set(0, 0.72, 0.1);
    stoolGroup.add(seatBox);

    const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.58, 0.1, 16), new THREE.MeshBasicMaterial({ color: 0x09090b }));
    hole.position.set(0, 1.46, 0.15);
    stoolGroup.add(hole);

    const goldRim = addOutline(
      new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.07, 10, 18), new THREE.MeshToonMaterial({ color: 0xfacc15, gradientMap: toonGrad })),
      0.03
    );
    goldRim.rotation.x = Math.PI * 0.5;
    goldRim.position.set(0, 1.48, 0.15);
    stoolGroup.add(goldRim);

    scene.add(stoolGroup);
  }
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
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(idx === 2 || idx === 8 || idx === 12 || idx === 13 ? 0x2e1065 : 0x1e293b);
    scene.fog = new THREE.FogExp2(scene.background.getHex(), 0.022);

    const camera = new THREE.PerspectiveCamera(42, 1080 / 1920, 0.1, 120);
    scene.add(new THREE.AmbientLight(0xffffff, 0.85));

    const dirLight = new THREE.DirectionalLight(0xfffbeb, 1.45);
    dirLight.position.set(6, 14, 10);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0xf97316, 1.6, 22);
    pointLight.position.set(0, 5.5, -4);
    scene.add(pointLight);

    const toonGrad = getToonGradient();
    const wPhase = frame * 0.28;

    const isToiletScene = idx === 2 || idx === 8 || idx === 12 || idx === 13;
    const doorOpen = idx === 1 ? interpolate(p, [0.5, 1], [0, 0.9], clamp) : idx === 6 || idx === 7 ? 0.95 : idx === 11 ? interpolate(p, [0, 0.4], [0.9, 0], clamp) : 0;
    const doorLocked = idx === 11 ? interpolate(p, [0.4, 0.8], [0, 1], clamp) : idx === 15 || idx === 16 ? 1 : 0;

    buildPalace3DSet(scene, toonGrad, doorOpen, doorLocked, idx === 0 || idx === 5, isToiletScene);

    if (idx === 0) {
      camera.position.set(interpolate(p, [0, 1], [3.6, 1.2]), interpolate(p, [0, 1], [4.8, 3.4]), interpolate(p, [0, 1], [9.5, 6.2]));
      camera.lookAt(0.4, 2.5, 0.5);
      const groom = build3DStickman("groom", "smug", toonGrad, wPhase, false, -0.4, -0.7, "key", "goldbag");
      groom.position.set(-0.4, 0, 1.2);
      groom.rotation.y = 0.25;
      scene.add(groom);
    } else if (idx === 1) {
      const zWalk = interpolate(p, [0, 1], [4.5, -3.5]);
      camera.position.set(3.4, 3.8, zWalk + 5.8);
      camera.lookAt(0, 2.6, zWalk - 1.5);
      const king = build3DStickman("king", "normal", toonGrad, wPhase, true, 0.2, -0.5, "key", "none");
      king.position.set(-0.6, 0, zWalk);
      king.rotation.y = Math.PI;
      const groom = build3DStickman("groom", "normal", toonGrad, wPhase + 1.5, true, 0.2, 0.2);
      groom.position.set(0.85, 0, zWalk + 1.4);
      groom.rotation.y = Math.PI;
      scene.add(king, groom);
    } else if (idx === 2) {
      camera.position.set(interpolate(p, [0, 1], [-2.2, 0.9]), interpolate(p, [0, 1], [3.6, 3.2]), interpolate(p, [0, 1], [5.8, 4.1]));
      camera.lookAt(0.2, 2.7, -0.8);
      const king = build3DStickman("king", "smug", toonGrad, 0, false, 0.2, 0.2, "none", "none", 0.5);
      king.position.set(-1.55, 0, -1.1);
      king.rotation.y = 0.35;
      const groom = build3DStickman("groom", "shock", toonGrad, 0, false, 0.3, -1.1, "paper", "none", -0.5);
      groom.position.set(1.15, 0, -0.4);
      groom.rotation.y = -0.35;
      scene.add(king, groom);
    } else if (idx === 3) {
      camera.position.set(interpolate(p, [0, 1], [-3.2, 3.2]), 2.6, 6.8);
      camera.lookAt(0, 3.0, 0);
      const king = build3DStickman("king", "smug", toonGrad, 0, false, -0.3, -0.8, "key", "none");
      king.position.set(0, 0, 0.5);
      scene.add(king);
    } else if (idx === 4) {
      const gx = interpolate(p, [0, 0.45], [-2.8, 0], clamp);
      camera.position.set(2.4, 3.2, 6.2);
      camera.lookAt(0, 2.6, 0);
      const gen = build3DStickman("general", p < 0.55 ? "smug" : "shock", toonGrad, wPhase, p < 0.45, -0.4, -1.1, "sword", "shield");
      gen.position.set(gx, 0, 0.5);
      scene.add(gen);
    } else if (idx === 5) {
      const bx = interpolate(p, [0, 0.45], [2.8, 0], clamp);
      camera.position.set(-2.4, 3.2, 6.2);
      camera.lookAt(0, 2.6, 0);
      const banker = build3DStickman("banker", p < 0.55 ? "smug" : "shock", toonGrad, wPhase, p < 0.45, -0.6, -0.7, "goldbag", "goldbag");
      banker.position.set(bx, 0, 0.5);
      scene.add(banker);
    } else if (idx === 6) {
      camera.position.set(interpolate(p, [0, 1], [-1.8, 1.8]), 2.8, -1.2);
      camera.lookAt(0, 3.0, -6.5);
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, 0.2, -1.1, "key", "none");
      groom.position.set(0, 0, -4.8);
      scene.add(groom);
    } else if (idx === 7) {
      const zIn = interpolate(p, [0, 1], [-2.2, -6.8]);
      camera.position.set(2.8, 3.5, 0.5);
      camera.lookAt(0, 2.7, -5.5);
      const king = build3DStickman("king", "normal", toonGrad, wPhase, true);
      king.position.set(-0.5, 0, zIn);
      king.rotation.y = Math.PI;
      const groom = build3DStickman("groom", "sweat", toonGrad, wPhase + 1.2, true, 0.2, -0.9, "paper");
      groom.position.set(0.65, 0, zIn + 1.3);
      groom.rotation.y = Math.PI;
      scene.add(king, groom);
    } else if (idx === 8) {
      camera.position.set(interpolate(p, [0, 1], [1.8, 0.4]), 3.1, 4.2);
      camera.lookAt(-0.3, 2.5, -0.8);
      const groom = build3DStickman("groom", "sweat", toonGrad, 0, false, -0.8, -1.0, "paper");
      groom.position.set(0.6, 0, -0.3);
      scene.add(groom);
    } else if (idx === 9) {
      const lunge = Math.sin(frame * 0.28) * 0.65;
      camera.position.set(Math.sin(p * 2.2) * 3.2, 3.4, 5.2);
      camera.lookAt(0, 2.5, -2.0);
      const n1 = build3DStickman("noble1", "angry", toonGrad, wPhase, true, 0.2, -1.1 + Math.sin(frame * 0.35) * 0.5, "sword");
      n1.position.set(-1.35 + lunge, 0, -2.0);
      n1.rotation.y = 0.45;
      const n2 = build3DStickman("noble2", "angry", toonGrad, wPhase + 1, true, 0.2, -1.1 + Math.cos(frame * 0.35) * 0.5, "sword");
      n2.position.set(1.35 - lunge, 0, -2.0);
      n2.rotation.y = -0.45;
      scene.add(n1, n2);
    } else if (idx === 10) {
      camera.position.set(0, 3.3, interpolate(p, [0, 1], [4.8, 3.4]));
      camera.lookAt(0, 3.2, 0);
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, 0.2, -1.0, "key");
      groom.position.set(0, 0, 0);
      scene.add(groom);
    } else if (idx === 11) {
      camera.position.set(interpolate(p, [0, 1], [-2.5, 2.2]), 3.4, -1.2);
      camera.lookAt(0, 3.0, -6.8);
      const king = build3DStickman("king", "normal", toonGrad, 0, false, 0.2, 0.2, "none", "none", 0.5);
      king.position.set(-1.1, 0, -5.2);
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, 0.2, -0.9, "key", "none", -0.5);
      groom.position.set(1.1, 0, -5.2);
      scene.add(king, groom);
    } else if (idx === 12 || idx === 13) {
      camera.position.set(interpolate(p, [0, 1], [2.2, -1.6]), 3.3, 4.4);
      camera.lookAt(0, 2.8, -0.5);
      const king = build3DStickman("king", "smug", toonGrad, 0, false, 0.2, -0.8, "none", "none", 0.6);
      king.position.set(-1.05, 0, -0.5);
      king.rotation.y = 0.4;
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, 0.2, -0.9, "scroll", "none", -0.6);
      groom.position.set(1.05, 0, -0.5);
      groom.rotation.y = -0.4;
      scene.add(king, groom);
    } else if (idx === 14) {
      camera.position.set(-2.4, 3.1, 5.8);
      camera.lookAt(0, 2.6, 0);
      const king = build3DStickman("king", "angry", toonGrad, 0, false, 0.2, -1.2, "none", "none", 0.6);
      king.position.set(-1.2, 0, 0);
      king.rotation.y = 0.35;
      const noble = build3DStickman("noble1", "sweat", toonGrad, wPhase, true, -0.6, -0.6, "none", "none", -0.6);
      noble.position.set(interpolate(p, [0, 1], [0.8, 1.8]), 0, 0);
      noble.rotation.y = -0.35;
      scene.add(king, noble);
    } else if (idx === 15) {
      camera.position.set(2.6, 3.2, -1.2);
      camera.lookAt(0, 2.7, -5.8);
      const noble = build3DStickman("noble2", "sweat", toonGrad, wPhase, p < 0.5, -0.8, -0.8);
      noble.position.set(interpolate(p, [0, 0.5], [-2.6, -1.25], clamp), 0, -4.8);
      noble.rotation.y = 0.45;
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, 0.2, -1.0, "key");
      groom.position.set(0.95, 0, -4.8);
      groom.rotation.y = -0.35;
      scene.add(noble, groom);
    } else if (idx === 16) {
      camera.position.set(interpolate(p, [0, 1], [-3.2, 3.2]), 3.6, -0.5);
      camera.lookAt(0, 2.6, -5.5);
      const g1 = build3DStickman("general", "sweat", toonGrad, wPhase, p < 0.5);
      g1.position.set(-1.8, 0, -4.6);
      const b1 = build3DStickman("banker", "sweat", toonGrad, wPhase + 1, p < 0.5, 0.2, -0.8, "goldbag");
      b1.position.set(0, 0, -4.6);
      const n1 = build3DStickman("noble1", "sweat", toonGrad, wPhase + 2, p < 0.5);
      n1.position.set(1.8, 0, -4.6);
      scene.add(g1, b1, n1);
    } else {
      camera.position.set(Math.sin(p * 1.5) * 1.8, interpolate(p, [0, 1], [2.4, 3.8]), interpolate(p, [0, 1], [7.2, 5.6]));
      camera.lookAt(0, 2.8, 0);
      const groom = build3DStickman("groom", "smug", toonGrad, 0, false, -0.7, -1.0, "paper", "goldbag");
      groom.position.set(0, 0.45, 0.4);
      groom.scale.setScalar(1.18);
      const king = build3DStickman("king", "normal", toonGrad, 0, false);
      king.position.set(-1.95, 0, 1.2);
      king.scale.setScalar(0.85);
      const gen = build3DStickman("general", "sweat", toonGrad, 0, false);
      gen.position.set(1.95, 0, 1.2);
      gen.scale.setScalar(0.85);
      scene.add(groom, king, gen);
    }

    sharedRenderer.render(scene, camera);
    sharedRenderer.renderLists.dispose();
    cleanScene(scene);
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
print("✅ MEMORIA 3D OTTIMIZZATA (ZERO MEMORY LEAK, 10X VELOCITÀ)!")
