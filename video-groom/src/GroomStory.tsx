import React, { useEffect, useRef } from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import * as THREE from "three";
import { TIMINGS } from "./timings";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

interface HumanRig {
  root: THREE.Group;
  pelvis: THREE.Group;
  torso: THREE.Group;
  head: THREE.Group;
  browL: THREE.Mesh;
  browR: THREE.Mesh;
  eyelidL: THREE.Mesh;
  eyelidR: THREE.Mesh;
  pupilL: THREE.Group;
  pupilR: THREE.Group;
  lowerJaw: THREE.Group;
  mouthOpenMesh: THREE.Mesh;
  shL: THREE.Group;
  elbL: THREE.Group;
  shR: THREE.Group;
  elbR: THREE.Group;
  hipL: THREE.Group;
  kneeL: THREE.Group;
  hipR: THREE.Group;
  kneeR: THREE.Group;
  sweatDrop: THREE.Mesh;
  propsR: Record<string, THREE.Object3D>;
  propsL: Record<string, THREE.Object3D>;
}

interface WorldCache {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  actors: Record<string, HumanRig>;
  doorPivot: THREE.Group;
  ironBar: THREE.Group;
  chestGroup: THREE.Group;
  stoolGroup: THREE.Group;
  smokeParticles: THREE.Mesh[];
  torchFlames: THREE.Mesh[];
  torchLights: THREE.PointLight[];
}

let CACHE: WorldCache | null = null;

function makePBRTexture(type: "stone" | "wood" | "marble" | "velvet" | "goldSign" | "privySign"): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 1024;
  const ctx = c.getContext("2d")!;

  if (type === "stone") {
    ctx.fillStyle = "#334155";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let r = 0; r < 8; r++) {
      const y = r * 128;
      const off = (r % 2) * 128;
      for (let col = -1; col < 5; col++) {
        const x = col * 256 + off;
        const grad = ctx.createLinearGradient(x, y, x + 256, y + 128);
        grad.addColorStop(0, (r + col) % 2 === 0 ? "#475569" : "#3b495e");
        grad.addColorStop(1, "#1e293b");
        ctx.fillStyle = grad;
        ctx.fillRect(x + 8, y + 8, 240, 112);
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 12;
        ctx.strokeRect(x, y, 256, 128);
      }
    }
  } else if (type === "wood") {
    ctx.fillStyle = "#5c2e0e";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let y = 0; y < 1024; y += 64) {
      ctx.fillStyle = (y / 64) % 2 === 0 ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.08)";
      ctx.fillRect(0, y, 1024, 64);
      ctx.strokeStyle = "#261002";
      ctx.lineWidth = 7;
      ctx.strokeRect(0, y, 1024, 64);
    }
  } else if (type === "marble") {
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let r = 0; r < 4; r++) {
      for (let col = 0; col < 4; col++) {
        ctx.fillStyle = (r + col) % 2 === 0 ? "#1e293b" : "#0f172a";
        ctx.fillRect(col * 256, r * 256, 256, 256);
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 5;
        ctx.strokeRect(col * 256, r * 256, 256, 256);
      }
    }
  } else if (type === "velvet") {
    ctx.fillStyle = "#7f1d1d";
    ctx.fillRect(0, 0, 1024, 1024);
    ctx.fillStyle = "#facc15";
    ctx.fillRect(42, 0, 38, 1024);
    ctx.fillRect(944, 0, 38, 1024);
  } else {
    ctx.fillStyle = "#eab308";
    ctx.fillRect(0, 0, 1024, 1024);
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 28;
    ctx.strokeRect(24, 24, 976, 976);
    ctx.fillStyle = "#7f1d1d";
    ctx.font = "900 128px Arial Black, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(type === "goldSign" ? "1,000 GOLD" : "ROYAL PRIVY", 512, 435);
    ctx.fillStyle = "#111111";
    ctx.font = "800 80px Arial, sans-serif";
    ctx.fillText(type === "goldSign" ? "DAILY SALARY" : "GROOM OF THE STOOL", 512, 635);
  }

  const tex = new THREE.CanvasTexture(c);
  if (type === "stone" || type === "wood" || type === "marble") {
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(4, 4);
  }
  return tex;
}

// COSTRUISCE UN ATTORE 3D CON LIP-SYNC, PALPEBRE ANIMATE, OCCHI RIFLETTENTI E ABITI SCOLPITI
function createCinemaHuman3D(role: string): HumanRig {
  const root = new THREE.Group();
  const pelvis = new THREE.Group();
  pelvis.position.y = 1.94;
  root.add(pelvis);

  const torso = new THREE.Group();
  pelvis.add(torso);

  const skinMat = new THREE.MeshPhysicalMaterial({
    color: 0xf3c1a2,
    roughness: 0.36,
    metalness: 0.02,
    clearcoat: 0.24,
    clearcoatRoughness: 0.3,
    sheen: 0.45,
    sheenColor: new THREE.Color(0xff9478),
  });

  const cfg: Record<string, { tunic: number; vest: number; pants: number; hair: number; cape?: number; armor?: boolean }> = {
    king: { tunic: 0x991b1b, vest: 0xb91c1c, pants: 0x3b0764, hair: 0xb45309, cape: 0x7f1d1d },
    groom: { tunic: 0x1d4ed8, vest: 0x1e3a8a, pants: 0x0f172a, hair: 0x3b1e08 },
    general: { tunic: 0x475569, vest: 0x94a3b8, pants: 0x1e293b, hair: 0x18181b, cape: 0x991b1b, armor: true },
    banker: { tunic: 0x047857, vest: 0x065f46, pants: 0x064e3b, hair: 0x52525b },
    noble1: { tunic: 0x6b21a8, vest: 0x581c87, pants: 0x1e1b4b, hair: 0xd97706 },
    noble2: { tunic: 0x9a3412, vest: 0x7c2d12, pants: 0x27272a, hair: 0x18181b },
  };
  const c = cfg[role] || cfg.groom;

  const clothMat = new THREE.MeshPhysicalMaterial({ color: c.tunic, roughness: 0.55, sheen: 0.5 });
  const vestMat = new THREE.MeshPhysicalMaterial({ color: c.vest, roughness: 0.48, sheen: 0.6 });
  const pantsMat = new THREE.MeshStandardMaterial({ color: c.pants, roughness: 0.7 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.18, metalness: 0.92 });
  const steelMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.15, metalness: 0.94 });
  const leatherMat = new THREE.MeshStandardMaterial({ color: 0x241205, roughness: 0.35, metalness: 0.15 });
  const hairMat = new THREE.MeshStandardMaterial({ color: c.hair, roughness: 0.65 });
  const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.4 });

  // BUSTO SCOLPITO CON DOPPIO STRATO D'ABITO E BOTTONI D'ORO
  const chestMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.47, 0.58, 24, 32), c.armor ? steelMat : clothMat);
  chestMesh.scale.set(1.14, 1.0, 0.78);
  chestMesh.position.y = 0.68;
  chestMesh.castShadow = true;
  chestMesh.receiveShadow = true;
  torso.add(chestMesh);

  const vestOverlay = new THREE.Mesh(new THREE.CylinderGeometry(0.49, 0.46, 0.72, 24), c.armor ? steelMat : vestMat);
  vestOverlay.scale.set(1.06, 1.0, 0.76);
  vestOverlay.position.y = 0.62;
  torso.add(vestOverlay);

  for (let b = 0; b < 4; b++) {
    const btn = new THREE.Mesh(new THREE.SphereGeometry(0.032, 12, 12), goldMat);
    btn.position.set(0, 0.42 + b * 0.16, 0.38);
    torso.add(btn);
  }

  const hipsMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.44, 0.26, 20, 24), pantsMat);
  hipsMesh.scale.set(1.06, 1.0, 0.76);
  hipsMesh.position.y = 0.1;
  torso.add(hipsMesh);

  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.065, 14, 28), whiteMat);
  collar.rotation.x = Math.PI * 0.5;
  collar.position.set(0, 1.18, 0.02);
  torso.add(collar);

  const belt = new THREE.Mesh(new THREE.CylinderGeometry(0.49, 0.49, 0.12, 24), leatherMat);
  belt.scale.set(1.03, 1, 0.75);
  belt.position.y = 0.18;
  torso.add(belt);

  const buckle = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.16, 0.08), goldMat);
  buckle.position.set(0, 0.18, 0.37);
  torso.add(buckle);

  if (role === "king") {
    const ermine = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.16, 18, 32), whiteMat);
    ermine.rotation.x = Math.PI * 0.5;
    ermine.scale.set(1.12, 0.84, 1.0);
    ermine.position.y = 1.1;
    torso.add(ermine);

    const chain = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.048, 14, 28), goldMat);
    chain.rotation.x = Math.PI * 0.35;
    chain.position.set(0, 0.88, 0.19);
    torso.add(chain);
  }

  if (c.cape) {
    const cape = new THREE.Mesh(
      new THREE.CylinderGeometry(0.48, 0.9, 2.18, 28, 1, false, Math.PI * 0.65, Math.PI * 1.7),
      new THREE.MeshPhysicalMaterial({ color: c.cape, roughness: 0.6, side: THREE.DoubleSide })
    );
    cape.position.set(0, 0.18, -0.19);
    cape.castShadow = true;
    torso.add(cape);
  }

  // COLLO E TESTA UMANA 3D CON MASCELLA, BOCCA ANIMATA (LIP-SYNC) E PALPEBRE (BLINK)
  const neck = new THREE.Mesh(new THREE.CapsuleGeometry(0.165, 0.25, 18, 24), skinMat);
  neck.position.y = 1.32;
  torso.add(neck);

  const head = new THREE.Group();
  head.position.y = 1.72;
  torso.add(head);

  const cranium = new THREE.Mesh(new THREE.SphereGeometry(0.41, 36, 36), skinMat);
  cranium.scale.set(0.94, 1.08, 0.98);
  cranium.castShadow = true;
  head.add(cranium);

  const lowerJaw = new THREE.Group();
  lowerJaw.position.set(0, -0.1, 0.05);
  head.add(lowerJaw);

  const jawMesh = new THREE.Mesh(new THREE.SphereGeometry(0.34, 32, 32), skinMat);
  jawMesh.scale.set(0.95, 0.88, 0.96);
  lowerJaw.add(jawMesh);

  for (const side of [-1, 1]) {
    const cheek = new THREE.Mesh(new THREE.SphereGeometry(0.145, 20, 20), skinMat);
    cheek.scale.set(1.12, 0.78, 0.92);
    cheek.position.set(side * 0.21, -0.05, 0.26);
    head.add(cheek);

    const ear = new THREE.Mesh(new THREE.CapsuleGeometry(0.055, 0.085, 14, 18), skinMat);
    ear.position.set(side * 0.38, -0.02, 0.02);
    ear.rotation.z = side * 0.15;
    head.add(ear);
  }

  // Naso 3D anatomico con narici
  const noseBridge = new THREE.Mesh(new THREE.CapsuleGeometry(0.048, 0.14, 14, 18), skinMat);
  noseBridge.position.set(0, 0.02, 0.39);
  noseBridge.rotation.x = -0.32;
  const noseTip = new THREE.Mesh(new THREE.SphereGeometry(0.064, 20, 20), skinMat);
  noseTip.position.set(0, -0.05, 0.44);
  head.add(noseBridge, noseTip);

  // Occhi 3D con Riflesso Cornea + Palpebre mobili per il Battito Cigliare
  const makeEye = (xPos: number) => {
    const eg = new THREE.Group();
    eg.position.set(xPos, 0.08, 0.34);
    const sclera = new THREE.Mesh(
      new THREE.SphereGeometry(0.078, 24, 24),
      new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.05, clearcoat: 1.0 })
    );
    const pupilGrp = new THREE.Group();
    const iris = new THREE.Mesh(
      new THREE.SphereGeometry(0.043, 18, 18),
      new THREE.MeshStandardMaterial({ color: role === "king" || role === "noble1" ? 0x2563eb : 0x3b1e08, roughness: 0.15 })
    );
    iris.position.z = 0.052;
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.023, 14, 14), new THREE.MeshBasicMaterial({ color: 0x050505 }));
    pupil.position.z = 0.071;
    const specDot = new THREE.Mesh(new THREE.SphereGeometry(0.009, 10, 10), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    specDot.position.set(0.015, 0.015, 0.078);
    pupilGrp.add(iris, pupil, specDot);

    const eyelid = new THREE.Mesh(
      new THREE.SphereGeometry(0.084, 20, 16, 0, Math.PI * 2, 0, Math.PI * 0.52),
      skinMat
    );
    eyelid.rotation.x = -0.38;
    eg.add(sclera, pupilGrp, eyelid);
    head.add(eg);
    return { eyelid, pupilGrp };
  };
  const eyeLeft = makeEye(-0.15);
  const eyeRight = makeEye(0.15);

  const browGeo = new THREE.CapsuleGeometry(0.028, 0.12, 12, 16);
  const browL = new THREE.Mesh(browGeo, hairMat);
  browL.rotation.z = Math.PI * 0.5;
  browL.position.set(-0.15, 0.21, 0.37);
  const browR = new THREE.Mesh(browGeo, hairMat);
  browR.rotation.z = Math.PI * 0.5;
  browR.position.set(0.15, 0.21, 0.37);
  head.add(browL, browR);

  // Bocca 3D con cavità orale, labbra e denti per il Lip-Sync!
  const lipMat = new THREE.MeshStandardMaterial({ color: 0xb85d50, roughness: 0.4 });
  const upperLip = new THREE.Mesh(new THREE.CapsuleGeometry(0.026, 0.13, 12, 16), lipMat);
  upperLip.rotation.z = Math.PI * 0.5;
  upperLip.position.set(0, -0.16, 0.37);
  head.add(upperLip);

  const mouthOpenMesh = new THREE.Mesh(
    new THREE.SphereGeometry(0.075, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0x3b0a0a })
  );
  mouthOpenMesh.scale.set(1.2, 0.15, 0.6);
  mouthOpenMesh.position.set(0, -0.18, 0.35);
  head.add(mouthOpenMesh);

  const teeth = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.025, 0.04), whiteMat);
  teeth.position.set(0, -0.16, 0.36);
  head.add(teeth);

  const sweatDrop = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 14, 14),
    new THREE.MeshPhysicalMaterial({ color: 0x38bdf8, roughness: 0.08, transmission: 0.6, clearcoat: 1 })
  );
  sweatDrop.scale.set(0.8, 1.4, 0.8);
  sweatDrop.position.set(-0.34, 0.18, 0.28);
  sweatDrop.visible = false;
  head.add(sweatDrop);

  // Capelli Volumetrici + Corone / Elmi / Berretti Tudor
  const hairBase = new THREE.Mesh(new THREE.SphereGeometry(0.43, 28, 24, 0, Math.PI * 2, 0, Math.PI * 0.58), hairMat);
  hairBase.position.set(0, 0.05, -0.02);
  hairBase.rotation.x = -0.22;
  head.add(hairBase);

  for (const hx of [-0.19, -0.06, 0.06, 0.19]) {
    const lock = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.18, 12, 16), hairMat);
    lock.rotation.z = 1.25;
    lock.position.set(hx, 0.33, 0.26);
    head.add(lock);
  }

  if (role === "king") {
    const beard = new THREE.Mesh(new THREE.SphereGeometry(0.36, 24, 20), hairMat);
    beard.scale.set(1.02, 0.78, 0.95);
    beard.position.set(0, -0.13, 0.09);
    lowerJaw.add(beard);

    const mustacheL = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.14, 10, 12), hairMat);
    mustacheL.rotation.z = 1.4;
    mustacheL.position.set(-0.09, -0.13, 0.39);
    const mustacheR = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.14, 10, 12), hairMat);
    mustacheR.rotation.z = -1.4;
    mustacheR.position.set(0.09, -0.13, 0.39);
    head.add(mustacheL, mustacheR);

    const crownBase = new THREE.Mesh(new THREE.CylinderGeometry(0.39, 0.35, 0.22, 24), goldMat);
    crownBase.position.set(0, 0.48, 0);
    head.add(crownBase);
    for (let i = 0; i < 8; i++) {
      const ang = (i / 8) * Math.PI * 2;
      const spike = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.18, 12), goldMat);
      spike.position.set(Math.sin(ang) * 0.36, 0.64, Math.cos(ang) * 0.36);
      head.add(spike);
    }
  } else if (role === "general") {
    const helm = new THREE.Mesh(new THREE.SphereGeometry(0.45, 24, 20, 0, Math.PI * 2, 0, Math.PI * 0.48), steelMat);
    helm.position.set(0, 0.08, 0);
    const plume = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.36, 12, 16), new THREE.MeshStandardMaterial({ color: 0xdc2626 }));
    plume.rotation.x = -0.45;
    plume.position.set(0, 0.62, -0.08);
    head.add(helm, plume);
  } else {
    const beret = new THREE.Mesh(new THREE.CylinderGeometry(0.46, 0.38, 0.14, 24), clothMat);
    beret.position.set(0, 0.44, 0);
    beret.rotation.z = -0.08;
    const feather = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.38, 12), goldMat);
    feather.position.set(0.34, 0.56, 0);
    feather.rotation.z = -0.5;
    head.add(beret, feather);
  }

  const buildArm = (isLeft: boolean) => {
    const sh = new THREE.Group();
    sh.position.set(isLeft ? -0.56 : 0.56, 1.04, 0);
    torso.add(sh);

    const shoulderCap = new THREE.Mesh(new THREE.SphereGeometry(0.165, 18, 18), c.armor ? steelMat : vestMat);
    sh.add(shoulderCap);

    const upper = new THREE.Mesh(new THREE.CapsuleGeometry(0.125, 0.42, 16, 20), c.armor ? steelMat : clothMat);
    upper.position.y = -0.26;
    upper.castShadow = true;
    sh.add(upper);

    const elb = new THREE.Group();
    elb.position.y = -0.52;
    sh.add(elb);

    const fore = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.38, 16, 20), skinMat);
    fore.position.y = -0.24;
    fore.castShadow = true;
    elb.add(fore);

    const hand = new THREE.Group();
    hand.position.y = -0.5;
    elb.add(hand);

    const palm = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 16), skinMat);
    palm.scale.set(0.85, 1.15, 1.0);
    hand.add(palm);

    for (let f = -1.5; f <= 1.5; f += 1) {
      const finger = new THREE.Mesh(new THREE.CapsuleGeometry(0.018, 0.075, 8, 10), skinMat);
      finger.position.set(0, -0.09, f * 0.025);
      hand.add(finger);
    }

    const props: Record<string, THREE.Object3D> = {};

    const keyGrp = new THREE.Group();
    const kRing = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.04, 12, 24), goldMat);
    const kShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.62, 12), goldMat);
    kShaft.position.y = -0.44;
    const kTeeth = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.14, 0.04), goldMat);
    kTeeth.position.set(0.08, -0.62, 0);
    keyGrp.add(kRing, kShaft, kTeeth);
    keyGrp.rotation.x = Math.PI * 0.5;
    keyGrp.visible = false;
    hand.add(keyGrp);
    props["key"] = keyGrp;

    const paperGrp = new THREE.Group();
    const tray = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.28, 0.05, 24), goldMat);
    const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.36, 24), whiteMat);
    roll.position.y = 0.2;
    paperGrp.add(tray, roll);
    paperGrp.position.set(0, -0.08, 0.18);
    paperGrp.visible = false;
    hand.add(paperGrp);
    props["paper"] = paperGrp;

    const swordGrp = new THREE.Group();
    const blade = new THREE.Mesh(new THREE.BoxGeometry(0.04, 1.38, 0.1), steelMat);
    blade.position.y = 0.72;
    const hilt = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.1, 0.4), goldMat);
    hilt.position.y = 0.05;
    swordGrp.add(blade, hilt);
    swordGrp.rotation.x = Math.PI * 0.55;
    swordGrp.visible = false;
    hand.add(swordGrp);
    props["sword"] = swordGrp;

    const bagGrp = new THREE.Mesh(new THREE.SphereGeometry(0.26, 20, 20), goldMat);
    bagGrp.position.y = -0.18;
    bagGrp.visible = false;
    hand.add(bagGrp);
    props["goldbag"] = bagGrp;

    const scrollGrp = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.08, 0.56, 16),
      new THREE.MeshStandardMaterial({ color: 0xfef3c7, roughness: 0.55 })
    );
    scrollGrp.rotation.z = Math.PI * 0.5;
    scrollGrp.position.set(0, -0.1, 0.16);
    scrollGrp.visible = false;
    hand.add(scrollGrp);
    props["scroll"] = scrollGrp;

    return { sh, elb, props };
  };

  const armL = buildArm(true);
  const armR = buildArm(false);

  const buildLeg = (isLeft: boolean) => {
    const hip = new THREE.Group();
    hip.position.set(isLeft ? -0.24 : 0.24, 0, 0);
    pelvis.add(hip);

    const thigh = new THREE.Mesh(new THREE.CapsuleGeometry(0.165, 0.62, 16, 20), pantsMat);
    thigh.position.y = -0.44;
    thigh.castShadow = true;
    hip.add(thigh);

    const knee = new THREE.Group();
    knee.position.y = -0.88;
    hip.add(knee);

    const calf = new THREE.Mesh(new THREE.CapsuleGeometry(0.135, 0.62, 16, 20), pantsMat);
    calf.position.y = -0.43;
    calf.castShadow = true;
    knee.add(calf);

    const shoe = new THREE.Mesh(new THREE.CapsuleGeometry(0.135, 0.25, 14, 18), leatherMat);
    shoe.rotation.x = Math.PI * 0.5;
    shoe.position.set(0, -0.92, 0.09);
    shoe.castShadow = true;
    knee.add(shoe);

    return { hip, knee };
  };

  const legL = buildLeg(true);
  const legR = buildLeg(false);

  return {
    root,
    pelvis,
    torso,
    head,
    browL,
    browR,
    eyelidL: eyeLeft.eyelid,
    eyelidR: eyeRight.eyelid,
    pupilL: eyeLeft.pupilGrp,
    pupilR: eyeRight.pupilGrp,
    lowerJaw,
    mouthOpenMesh,
    shL: armL.sh,
    elbL: armL.elb,
    shR: armR.sh,
    elbR: armR.elb,
    hipL: legL.hip,
    kneeL: legL.knee,
    hipR: legR.hip,
    kneeR: legR.knee,
    sweatDrop,
    propsR: armR.props,
    propsL: armL.props,
  };
}

function poseHumanRig(
  rig: HumanRig,
  visible: boolean,
  frame = 0,
  isSpeaking = false,
  x = 0,
  z = 0,
  rotY = 0,
  walkPhase = 0,
  isWalking = false,
  mood: "normal" | "smug" | "shock" | "angry" | "sweat" = "normal",
  shLDeg = 12,
  elbLDeg = -18,
  shRDeg = 12,
  elbRDeg = -18,
  propR = "none",
  propL = "none",
  headYaw = 0,
  headPitch = 0
) {
  rig.root.visible = visible;
  if (!visible) return;

  rig.root.position.set(x, 0, z);
  rig.root.rotation.y = rotY;

  // Respiro naturale + Camminata fluida
  const breath = Math.sin(frame * 0.08) * 0.015;
  const bob = isWalking ? Math.abs(Math.sin(walkPhase)) * 0.09 : breath;
  rig.pelvis.position.y = 1.94 + bob;
  rig.torso.rotation.y = isWalking ? Math.sin(walkPhase) * 0.09 : Math.sin(frame * 0.05) * 0.02;

  if (isWalking) {
    rig.hipL.rotation.x = Math.sin(walkPhase) * 0.55;
    rig.kneeL.rotation.x = Math.max(0, -Math.cos(walkPhase) * 0.65);
    rig.hipR.rotation.x = Math.sin(walkPhase + Math.PI) * 0.55;
    rig.kneeR.rotation.x = Math.max(0, -Math.cos(walkPhase + Math.PI) * 0.65);
  } else {
    rig.hipL.rotation.x = 0;
    rig.kneeL.rotation.x = 0;
    rig.hipR.rotation.x = 0;
    rig.kneeR.rotation.x = 0;
  }

  const armWave = isWalking ? Math.sin(walkPhase) * 0.38 : Math.sin(frame * 0.07) * 0.03;
  rig.shL.rotation.x = (shLDeg * Math.PI) / 180 - armWave;
  rig.elbL.rotation.x = (elbLDeg * Math.PI) / 180;
  rig.shR.rotation.x = (shRDeg * Math.PI) / 180 + armWave;
  rig.elbR.rotation.x = (elbRDeg * Math.PI) / 180;

  Object.keys(rig.propsR).forEach((k) => (rig.propsR[k].visible = k === propR));
  Object.keys(rig.propsL).forEach((k) => (rig.propsL[k].visible = k === propL));

  // Micro-movimento organico della testa + Battito delle palpebre (Blink ogni ~2.5 secondi)
  rig.head.rotation.y = headYaw + Math.sin(frame * 0.06) * 0.03;
  rig.head.rotation.x = headPitch + Math.cos(frame * 0.05) * 0.02;
  rig.sweatDrop.visible = mood === "sweat" || mood === "shock";

  const blinkCycle = frame % 145;
  const isBlinking = blinkCycle > 138;
  const lidAngle = isBlinking ? 0.35 : mood === "smug" ? -0.18 : mood === "shock" ? -0.58 : -0.38;
  rig.eyelidL.rotation.x = lidAngle;
  rig.eyelidR.rotation.x = lidAngle;

  // Movimento pupille
  const eyeShift = Math.sin(frame * 0.04) * 0.04;
  rig.pupilL.rotation.y = eyeShift;
  rig.pupilR.rotation.y = eyeShift;

  // Lip-Sync 3D quando il personaggio parla o reagisce
  const talkWave = isSpeaking ? Math.abs(Math.sin(frame * 0.42) * Math.cos(frame * 0.27)) : 0;
  const mouthOpen = mood === "shock" ? 0.85 : talkWave;

  rig.lowerJaw.position.y = -0.1 - mouthOpen * 0.045;
  rig.mouthOpenMesh.scale.y = 0.15 + mouthOpen * 0.95;

  if (mood === "angry") {
    rig.browL.rotation.z = Math.PI * 0.5 - 0.32;
    rig.browR.rotation.z = Math.PI * 0.5 + 0.32;
    rig.browL.position.y = 0.19;
    rig.browR.position.y = 0.19;
  } else if (mood === "shock" || mood === "sweat") {
    rig.browL.rotation.z = Math.PI * 0.5 + 0.24;
    rig.browR.rotation.z = Math.PI * 0.5 - 0.24;
    rig.browL.position.y = 0.25;
    rig.browR.position.y = 0.25;
  } else if (mood === "smug") {
    rig.browL.rotation.z = Math.PI * 0.5 - 0.12;
    rig.browR.rotation.z = Math.PI * 0.5 + 0.26;
    rig.browL.position.y = 0.2;
    rig.browR.position.y = 0.24;
  } else {
    rig.browL.rotation.z = Math.PI * 0.5;
    rig.browR.rotation.z = Math.PI * 0.5;
    rig.browL.position.y = 0.21;
    rig.browR.position.y = 0.21;
  }
}

function initWorld(canvas: HTMLCanvasElement): WorldCache {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    powerPreference: "high-performance",
    preserveDrawingBuffer: true,
  });
  renderer.setSize(1080, 1920, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0f172a);
  scene.fog = new THREE.FogExp2(0x0f172a, 0.015);

  const pmrem = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  envScene.background = new THREE.Color(0x334155);
  const l1 = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 16), new THREE.MeshBasicMaterial({ color: 0xfffbeb }));
  l1.position.set(15, 25, 15);
  const l2 = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 16), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
  l2.position.set(-15, 15, -10);
  envScene.add(l1, l2);
  scene.environment = pmrem.fromScene(envScene).texture;

  const camera = new THREE.PerspectiveCamera(34, 1080 / 1920, 0.1, 140);

  const hemi = new THREE.HemisphereLight(0xfffbeb, 0x1e293b, 0.9);
  scene.add(hemi);

  const keyLight = new THREE.SpotLight(0xfff7ed, 2.9);
  keyLight.position.set(7, 16, 10);
  keyLight.angle = Math.PI * 0.38;
  keyLight.penumbra = 0.65;
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width = 1024;
  keyLight.shadow.mapSize.height = 1024;
  keyLight.shadow.bias = -0.0004;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.35);
  rimLight.position.set(-8, 10, -6);
  scene.add(rimLight);

  const stoneTex = makePBRTexture("stone");
  const stoneMat = new THREE.MeshStandardMaterial({ map: stoneTex, bumpMap: stoneTex, bumpScale: 0.045, roughness: 0.72 });
  const woodTex = makePBRTexture("wood");
  const woodMat = new THREE.MeshStandardMaterial({ map: woodTex, bumpMap: woodTex, bumpScale: 0.03, roughness: 0.52 });
  const marbleTex = makePBRTexture("marble");
  const marbleMat = new THREE.MeshStandardMaterial({ map: marbleTex, bumpMap: marbleTex, bumpScale: 0.015, roughness: 0.18, metalness: 0.18 });
  const velvetTex = makePBRTexture("velvet");
  const velvetMat = new THREE.MeshStandardMaterial({ map: velvetTex, bumpMap: velvetTex, bumpScale: 0.02, roughness: 0.72 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.18, metalness: 0.92 });

  const marbleFloor = new THREE.Mesh(new THREE.PlaneGeometry(44, 54), marbleMat);
  marbleFloor.rotation.x = -Math.PI * 0.5;
  marbleFloor.receiveShadow = true;
  scene.add(marbleFloor);

  const carpet = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.04, 48), velvetMat);
  carpet.position.set(0, 0.02, 0);
  carpet.receiveShadow = true;
  scene.add(carpet);

  const wallL = new THREE.Mesh(new THREE.BoxGeometry(10, 16, 1.2), stoneMat);
  wallL.position.set(-7.2, 8, -7.8);
  wallL.receiveShadow = true;
  const wallR = new THREE.Mesh(new THREE.BoxGeometry(10, 16, 1.2), stoneMat);
  wallR.position.set(7.2, 8, -7.8);
  wallR.receiveShadow = true;
  const wallTop = new THREE.Mesh(new THREE.BoxGeometry(5, 8.5, 1.2), stoneMat);
  wallTop.position.set(0, 11.8, -7.8);
  scene.add(wallL, wallR, wallTop);

  const torchLights: THREE.PointLight[] = [];
  const torchFlames: THREE.Mesh[] = [];
  const flameMat = new THREE.MeshBasicMaterial({ color: 0xfacc15 });

  for (const zPos of [-6.8, -1.5, 3.8]) {
    for (const xSide of [-5.2, 5.2]) {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.52, 0.58, 14, 24), stoneMat);
      col.position.set(xSide, 7, zPos);
      col.castShadow = true;
      col.receiveShadow = true;
      const base = new THREE.Mesh(new THREE.BoxGeometry(1.45, 0.65, 1.45), goldMat);
      base.position.set(xSide, 0.32, zPos);
      scene.add(col, base);

      if (zPos < 2) {
        const sconceX = xSide > 0 ? xSide - 0.55 : xSide + 0.55;
        const holder = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.45, 12), goldMat);
        holder.position.set(sconceX, 4.4, zPos);
        holder.rotation.x = Math.PI;
        const flame = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.42, 12), flameMat);
        flame.position.set(sconceX, 4.75, zPos);
        scene.add(holder, flame);
        torchFlames.push(flame);

        const pl = new THREE.PointLight(0xf97316, 1.55, 15);
        pl.position.set(sconceX, 4.8, zPos + 0.3);
        scene.add(pl);
        torchLights.push(pl);
      }
    }
  }

  const bookcase = new THREE.Group();
  bookcase.position.set(3.8, 0, -6.9);
  const bcFrame = new THREE.Mesh(new THREE.BoxGeometry(3.2, 6.2, 0.7), woodMat);
  bcFrame.position.y = 3.1;
  bookcase.add(bcFrame);
  const bookColors = [0xdc2626, 0x2563eb, 0xeab308, 0x059669, 0x9333ea];
  for (let row = 0; row < 4; row++) {
    for (let b = 0; b < 8; b++) {
      const book = new THREE.Mesh(
        new THREE.BoxGeometry(0.28, 0.85, 0.55),
        new THREE.MeshStandardMaterial({ color: bookColors[(row + b) % bookColors.length], roughness: 0.5 })
      );
      book.position.set(-1.15 + b * 0.33, 1.2 + row * 1.35, 0.12);
      bookcase.add(book);
    }
  }
  scene.add(bookcase);

  const doorPivot = new THREE.Group();
  doorPivot.position.set(-2.1, 0, -7.35);
  scene.add(doorPivot);

  const doorMesh = new THREE.Mesh(new THREE.BoxGeometry(4.2, 7.4, 0.32), woodMat);
  doorMesh.position.set(2.1, 3.7, 0);
  doorMesh.castShadow = true;
  doorPivot.add(doorMesh);

  const doorSign = new THREE.Mesh(
    new THREE.BoxGeometry(2.8, 1.35, 0.08),
    new THREE.MeshStandardMaterial({ map: makePBRTexture("privySign"), roughness: 0.3, metalness: 0.5 })
  );
  doorSign.position.set(2.1, 4.5, 0.2);
  doorPivot.add(doorSign);

  const ironBar = new THREE.Group();
  const barMesh = new THREE.Mesh(
    new THREE.BoxGeometry(5.2, 0.38, 0.32),
    new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.25 })
  );
  const lockMesh = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.85, 0.44), goldMat);
  ironBar.add(barMesh, lockMesh);
  ironBar.position.set(0, 3.2, -7.0);
  ironBar.visible = false;
  scene.add(ironBar);

  const chestGroup = new THREE.Group();
  chestGroup.position.set(1.85, 0, 1.2);
  chestGroup.rotation.y = -0.45;
  const cBox = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.05, 1.25), woodMat);
  cBox.position.y = 0.52;
  cBox.castShadow = true;
  const cSign = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, 0.65, 0.06),
    new THREE.MeshStandardMaterial({ map: makePBRTexture("goldSign"), roughness: 0.3 })
  );
  cSign.position.set(0, 0.55, 0.64);
  chestGroup.add(cBox, cSign);
  for (let i = 0; i < 16; i++) {
    const ingot = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.08, 16), goldMat);
    ingot.position.set((i % 4 - 1.5) * 0.34, 1.08 + (i % 3) * 0.09, ((i / 4) | 0) * 0.24 - 0.3);
    chestGroup.add(ingot);
  }
  scene.add(chestGroup);

  const stoolGroup = new THREE.Group();
  stoolGroup.position.set(-1.35, 0, -2.2);
  stoolGroup.rotation.y = 0.38;
  const sBack = new THREE.Mesh(new THREE.BoxGeometry(2.1, 3.5, 0.42), velvetMat);
  sBack.position.set(0, 1.75, -0.75);
  sBack.castShadow = true;
  const sSeat = new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.35, 1.85), velvetMat);
  sSeat.position.set(0, 0.68, 0.1);
  sSeat.castShadow = true;
  const sRim = new THREE.Mesh(new THREE.TorusGeometry(0.58, 0.08, 14, 28), goldMat);
  sRim.rotation.x = Math.PI * 0.5;
  sRim.position.set(0, 1.38, 0.18);
  const sHole = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.08, 24), new THREE.MeshBasicMaterial({ color: 0x050505 }));
  sHole.position.set(0, 1.35, 0.18);
  stoolGroup.add(sBack, sSeat, sRim, sHole);
  scene.add(stoolGroup);

  const smokeParticles: THREE.Mesh[] = [];
  const smokeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.28, roughness: 1.0 });
  for (let i = 0; i < 18; i++) {
    const sm = new THREE.Mesh(new THREE.SphereGeometry(0.35 + (i % 4) * 0.15, 14, 14), smokeMat);
    sm.visible = false;
    scene.add(sm);
    smokeParticles.push(sm);
  }

  const actors: Record<string, HumanRig> = {
    king: createCinemaHuman3D("king"),
    groom: createCinemaHuman3D("groom"),
    general: createCinemaHuman3D("general"),
    banker: createCinemaHuman3D("banker"),
    noble1: createCinemaHuman3D("noble1"),
    noble2: createCinemaHuman3D("noble2"),
  };
  Object.values(actors).forEach((a) => scene.add(a.root));

  return {
    renderer,
    scene,
    camera,
    actors,
    doorPivot,
    ironBar,
    chestGroup,
    stoolGroup,
    smokeParticles,
    torchFlames,
    torchLights,
  };
}

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
    if (!CACHE || CACHE.renderer.domElement !== canvas) {
      if (CACHE) CACHE.renderer.dispose();
      CACHE = initWorld(canvas);
    }

    const { renderer, scene, camera, actors, doorPivot, ironBar, chestGroup, stoolGroup, smokeParticles, torchFlames, torchLights } = CACHE;

    Object.values(actors).forEach((a) => (a.root.visible = false));
    chestGroup.visible = false;
    stoolGroup.visible = false;
    ironBar.visible = false;
    doorPivot.rotation.y = 0;
    smokeParticles.forEach((s) => (s.visible = false));

    torchLights.forEach((tl, i) => {
      tl.intensity = 1.45 + Math.sin(frame * 0.32 + i) * 0.28;
    });
    torchFlames.forEach((tf, i) => {
      tf.scale.set(1, 1 + Math.sin(frame * 0.35 + i) * 0.18, 1);
    });

    const wPhase = frame * 0.26;
    const sub = p < 0.52 ? 0 : 1;

    if (idx === 0) {
      chestGroup.visible = true;
      if (sub === 0) {
        camera.position.set(interpolate(p, [0, 0.52], [2.2, 1.4]), 2.2, interpolate(p, [0, 0.52], [4.0, 3.1]));
        camera.lookAt(0.6, 1.8, 1.0);
      } else {
        camera.position.set(interpolate(p, [0.52, 1], [-0.7, 0.35]), 3.25, interpolate(p, [0.52, 1], [3.3, 2.6]));
        camera.lookAt(-0.25, 3.15, 0.8);
      }
      poseHumanRig(actors.groom, true, frame, true, -0.35, 0.8, 0.22, wPhase, false, "smug", -35, -45, -45, -55, "key", "goldbag", 0.15, -0.05);
    } else if (idx === 1) {
      doorPivot.rotation.y = interpolate(p, [0.45, 1], [0, 1.35], clamp);
      const zWalk = interpolate(p, [0, 1], [2.2, -3.4]);
      camera.position.set(2.2, 3.1, zWalk + 4.8);
      camera.lookAt(0, 2.7, zWalk - 1.2);
      poseHumanRig(actors.king, true, frame, true, -0.65, zWalk, Math.PI, wPhase, true, "normal", 15, -20, -35, -40, "key", "none", 0.2, 0);
      poseHumanRig(actors.groom, true, frame, false, 0.65, zWalk + 1.1, Math.PI, wPhase + 1.5, true, "normal", 15, -20, 15, -20, "none", "none", -0.2, 0);
    } else if (idx === 2) {
      stoolGroup.visible = true;
      if (sub === 0) {
        camera.position.set(1.4, 3.1, 1.8);
        camera.lookAt(-0.8, 2.6, -1.6);
      } else {
        camera.position.set(-0.5, 3.35, 1.3);
        camera.lookAt(0.75, 3.15, -0.8);
      }
      poseHumanRig(actors.king, true, frame, sub === 0, -1.2, -1.6, 0.35, 0, false, "smug", 15, -25, -40, -35, "none", "none", 0.25, 0);
      poseHumanRig(actors.groom, true, frame, sub === 1, 0.85, -0.8, -0.35, 0, false, "shock", 20, -30, -55, -65, "paper", "none", -0.25, 0.08);
    } else if (idx === 3) {
      camera.position.set(interpolate(p, [0, 1], [-1.6, 1.6]), 3.15, 3.8);
      camera.lookAt(0, 3.05, 0.5);
      poseHumanRig(actors.king, true, frame, true, 0, 0.5, 0, 0, false, "smug", -25, -35, -50, -45, "key", "none", interpolate(p, [0, 1], [-0.2, 0.2]), 0);
    } else if (idx === 4) {
      const gx = interpolate(p, [0, 0.45], [-2.2, 0], clamp);
      camera.position.set(1.3, 3.2, 3.8);
      camera.lookAt(0, 2.95, 0.5);
      poseHumanRig(actors.general, true, frame, true, gx, 0.5, 0.15, wPhase, p < 0.45, p < 0.55 ? "smug" : "shock", -25, -35, -65, -45, "sword", "none", 0.1, 0);
    } else if (idx === 5) {
      chestGroup.visible = true;
      const bx = interpolate(p, [0, 0.45], [-2.0, -0.4], clamp);
      camera.position.set(-1.3, 3.1, 4.0);
      camera.lookAt(0.2, 2.85, 0.8);
      poseHumanRig(actors.banker, true, frame, true, bx, 0.8, -0.15, wPhase, p < 0.45, p < 0.55 ? "smug" : "shock", -45, -50, -50, -55, "goldbag", "goldbag", -0.1, 0);
    } else if (idx === 6) {
      doorPivot.rotation.y = interpolate(p, [0.2, 1], [0, 1.25], clamp);
      camera.position.set(interpolate(p, [0, 1], [-1.0, 1.0]), 3.25, -2.1);
      camera.lookAt(0, 3.15, -4.8);
      poseHumanRig(actors.groom, true, frame, true, 0, -4.8, 0, 0, false, "smug", 15, -20, -55, -55, "key", "none", 0.1, 0);
    } else if (idx === 7) {
      doorPivot.rotation.y = 1.4;
      const zIn = interpolate(p, [0, 1], [-2.8, -8.2]);
      camera.position.set(2.1, 3.4, -0.5);
      camera.lookAt(0, 2.8, -6.5);
      poseHumanRig(actors.king, true, frame, false, -0.55, zIn, Math.PI, wPhase, true, "normal", 15, -20, 15, -20);
      poseHumanRig(actors.groom, true, frame, true, 0.65, zIn + 1.2, Math.PI, wPhase + 1.4, true, "sweat", 15, -20, -50, -60, "paper", "none");
    } else if (idx === 8) {
      stoolGroup.visible = true;
      smokeParticles.forEach((sm, i) => {
        sm.visible = true;
        const cycle = (frame * 0.04 + i * 0.5) % 3.5;
        sm.position.set(-1.35 + Math.sin(frame * 0.08 + i) * 0.45, 1.4 + cycle * 0.85, -2.1 + Math.cos(frame * 0.07 + i) * 0.35);
        sm.scale.setScalar(0.6 + cycle * 0.45);
      });
      camera.position.set(interpolate(p, [0, 1], [1.5, 0.35]), 3.15, 2.4);
      camera.lookAt(-0.2, 2.9, -1.1);
      poseHumanRig(actors.groom, true, frame, true, 0.65, -0.9, -0.25, 0, false, "sweat", -45, -55, -55, -65, "paper", "none", -0.35, 0.1);
    } else if (idx === 9) {
      const lunge = Math.sin(frame * 0.26) * 0.55;
      camera.position.set(Math.sin(p * 2.2) * 2.4, 3.2, 3.2);
      camera.lookAt(0, 2.8, -2.2);
      poseHumanRig(actors.noble1, true, frame, true, -1.15 + lunge, -2.2, 0.48, wPhase, true, "angry", 20, -30, -65 + Math.sin(frame * 0.38) * 35, -35, "sword", "none", 0.3, 0);
      poseHumanRig(actors.noble2, true, frame, true, 1.15 - lunge, -2.2, -0.48, wPhase + 1, true, "angry", 20, -30, -65 + Math.cos(frame * 0.38) * 35, -35, "sword", "none", -0.3, 0);
    } else if (idx === 10) {
      camera.position.set(0.18, 3.38, interpolate(p, [0, 1], [2.6, 1.95]));
      camera.lookAt(0, 3.28, 0);
      poseHumanRig(actors.groom, true, frame, true, 0, 0, 0, 0, false, "smug", 15, -20, -55, -60, "key", "none", 0.12, -0.05);
    } else if (idx === 11) {
      doorPivot.rotation.y = interpolate(p, [0, 0.35], [1.2, 0], clamp);
      ironBar.visible = p > 0.32;
      ironBar.position.y = interpolate(p, [0.32, 0.72], [7.5, 3.2], clamp);
      camera.position.set(interpolate(p, [0, 1], [-1.8, 1.8]), 3.3, -1.5);
      camera.lookAt(0, 3.1, -5.8);
      poseHumanRig(actors.king, true, frame, false, -0.95, -5.2, 0.25, 0, false, "normal", 15, -20, 15, -20, "none", "none", 0.25, 0);
      poseHumanRig(actors.groom, true, frame, true, 0.95, -5.2, -0.25, 0, false, "smug", 15, -20, -50, -55, "key", "none", -0.25, 0);
    } else if (idx === 12 || idx === 13) {
      stoolGroup.visible = true;
      if (idx === 12) {
        camera.position.set(1.25, 3.35, 1.25);
        camera.lookAt(-0.75, 3.15, -0.8);
      } else {
        camera.position.set(-1.1, 3.35, 1.25);
        camera.lookAt(0.75, 3.15, -0.8);
      }
      poseHumanRig(actors.king, true, frame, idx === 12, -0.85, -0.8, 0.42, 0, false, "smug", 15, -20, -45, -50, "none", "none", 0.3, 0);
      poseHumanRig(actors.groom, true, frame, idx === 13, 0.85, -0.8, -0.42, 0, false, "smug", 15, -20, -55, -60, "scroll", "none", -0.3, 0);
    } else if (idx === 14) {
      camera.position.set(-1.5, 3.2, 3.6);
      camera.lookAt(0, 2.95, 0);
      poseHumanRig(actors.king, true, frame, true, -0.95, 0, 0.35, 0, false, "angry", 15, -20, -75, -20, "none", "none", 0.35, 0);
      poseHumanRig(actors.noble1, true, frame, false, interpolate(p, [0, 1], [0.7, 1.65]), 0, -0.35, wPhase, true, "sweat", -45, -50, -45, -50, "none", "none", -0.35, 0);
    } else if (idx === 15) {
      ironBar.visible = true;
      ironBar.position.y = 3.2;
      camera.position.set(1.5, 3.2, -1.9);
      camera.lookAt(0, 2.95, -5.2);
      poseHumanRig(actors.noble2, true, frame, false, interpolate(p, [0, 0.55], [-2.1, -1.05], clamp), -4.8, 0.45, wPhase, p < 0.55, "sweat", -45, -55, -45, -55, "none", "none", 0.3, 0);
      poseHumanRig(actors.groom, true, frame, true, 0.85, -4.8, -0.35, 0, false, "smug", 15, -20, -55, -55, "key", "none", -0.3, 0);
    } else if (idx === 16) {
      ironBar.visible = true;
      ironBar.position.y = 3.2;
      camera.position.set(interpolate(p, [0, 1], [-2.2, 2.2]), 3.5, -0.8);
      camera.lookAt(0, 2.8, -5.2);
      poseHumanRig(actors.general, true, frame, false, -1.45, -4.8, 0.15, wPhase, p < 0.5, "sweat", -35, -45, -35, -45);
      poseHumanRig(actors.banker, true, frame, true, 0, -4.6, 0, wPhase + 1, p < 0.5, "sweat", 15, -20, -50, -55, "goldbag", "none");
      poseHumanRig(actors.noble1, true, frame, false, 1.45, -4.8, -0.15, wPhase + 2, p < 0.5, "sweat", -35, -45, -35, -45);
    } else {
      chestGroup.visible = true;
      camera.position.set(Math.sin(p * 1.6) * 1.3, interpolate(p, [0, 1], [2.8, 3.3]), interpolate(p, [0, 1], [4.3, 3.2]));
      camera.lookAt(0, 3.05, 0.4);
      poseHumanRig(actors.groom, true, frame, true, 0, 0.6, 0, 0, false, "smug", -45, -50, -55, -60, "paper", "goldbag", 0, -0.05);
      poseHumanRig(actors.king, true, frame, false, -1.55, -0.8, 0.25, 0, false, "normal", 15, -20, 15, -20);
      poseHumanRig(actors.general, true, frame, false, 1.55, -0.8, -0.25, 0, false, "sweat", 15, -20, 15, -20);
    }

    renderer.render(scene, camera);
  }, [frame, idx, p]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#09090b" }}>
      <Audio src={staticFile("voce.mp3")} />
      <canvas ref={canvasRef} width={1080} height={1920} style={{ width: "100%", height: "100%" }} />
      {/* Vignettatura e Contrasto Cinematografico */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        background: "radial-gradient(circle at 50% 45%, transparent 58%, rgba(5,5,12,0.55) 100%)"
      }} />
    </AbsoluteFill>
  );
};
