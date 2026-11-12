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
  upperLip: THREE.Mesh;
  lowerJaw: THREE.Group;
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

// GENERATORE TEXTURE PBR + BUMP MAP (Crea vero rilievo 3D su pietra, legno, marmo e velluto)
function makePBRTexture(type: "stone" | "wood" | "marble" | "velvet" | "goldSign" | "privySign"): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 1024;
  const ctx = c.getContext("2d")!;

  if (type === "stone") {
    ctx.fillStyle = "#475569";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let r = 0; r < 8; r++) {
      const y = r * 128;
      const off = (r % 2) * 128;
      for (let col = -1; col < 5; col++) {
        const x = col * 256 + off;
        ctx.fillStyle = (r + col) % 2 === 0 ? "#566782" : "#3d4b61";
        ctx.fillRect(x + 10, y + 10, 236, 108);
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 14;
        ctx.strokeRect(x, y, 256, 128);
      }
    }
  } else if (type === "wood") {
    ctx.fillStyle = "#6e3b16";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let y = 0; y < 1024; y += 64) {
      ctx.fillStyle = (y / 64) % 2 === 0 ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.07)";
      ctx.fillRect(0, y, 1024, 64);
      ctx.strokeStyle = "#291304";
      ctx.lineWidth = 7;
      ctx.strokeRect(0, y, 1024, 64);
    }
  } else if (type === "marble") {
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(0, 0, 1024, 1024);
    for (let r = 0; r < 4; r++) {
      for (let col = 0; col < 4; col++) {
        ctx.fillStyle = (r + col) % 2 === 0 ? "#334155" : "#0f172a";
        ctx.fillRect(col * 256, r * 256, 256, 256);
        ctx.strokeStyle = "#64748b";
        ctx.lineWidth = 5;
        ctx.strokeRect(col * 256, r * 256, 256, 256);
      }
    }
  } else if (type === "velvet") {
    ctx.fillStyle = "#881337";
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

// COSTRUISCE UN PERSONAGGIO UMANO 3D ORGANICO E SCOLPITO (Stile ShiftHappensStories)
function createOrganicHuman3D(role: string): HumanRig {
  const root = new THREE.Group();
  const pelvis = new THREE.Group();
  pelvis.position.y = 1.94;
  root.add(pelvis);

  const torso = new THREE.Group();
  pelvis.add(torso);

  // Materiale Pelle Umana PBR con Subsurface Sheen e Clearcoat morbido
  const skinMat = new THREE.MeshPhysicalMaterial({
    color: 0xf4c4a8,
    roughness: 0.42,
    metalness: 0.02,
    clearcoat: 0.18,
    clearcoatRoughness: 0.35,
    sheen: 0.35,
    sheenColor: new THREE.Color(0xff9980),
  });

  const cfg: Record<string, { tunic: number; pants: number; hair: number; cape?: number; armor?: boolean; crown?: boolean; glasses?: boolean }> = {
    king: { tunic: 0x991b1b, pants: 0x3b0764, hair: 0xb45309, cape: 0x7f1d1d, crown: true },
    groom: { tunic: 0x1d4ed8, pants: 0x0f172a, hair: 0x3b1e08 },
    general: { tunic: 0x475569, pants: 0x1e293b, hair: 0x18181b, cape: 0x991b1b, armor: true },
    banker: { tunic: 0x047857, pants: 0x064e3b, hair: 0x52525b, glasses: true },
    noble1: { tunic: 0x6b21a8, pants: 0x1e1b4b, hair: 0xd97706 },
    noble2: { tunic: 0x9a3412, pants: 0x27272a, hair: 0x18181b },
  };
  const c = cfg[role] || cfg.groom;

  const clothMat = new THREE.MeshPhysicalMaterial({ color: c.tunic, roughness: 0.62, clearcoat: 0.05, sheen: 0.4 });
  const pantsMat = new THREE.MeshStandardMaterial({ color: c.pants, roughness: 0.72 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.2, metalness: 0.9 });
  const steelMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.18, metalness: 0.92 });
  const leatherMat = new THREE.MeshStandardMaterial({ color: 0x271507, roughness: 0.38, metalness: 0.12 });
  const hairMat = new THREE.MeshStandardMaterial({ color: c.hair, roughness: 0.75 });
  const whiteClothMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.55 });

  // BUSTO ORGANICO SCOLPITO (Capsule morbide + Pectorals + Spalle arrotondate)
  const upperTorso = new THREE.Mesh(new THREE.CapsuleGeometry(0.46, 0.58, 20, 28), c.armor ? steelMat : clothMat);
  upperTorso.scale.set(1.12, 1.0, 0.76);
  upperTorso.position.y = 0.66;
  upperTorso.castShadow = true;
  upperTorso.receiveShadow = true;
  torso.add(upperTorso);

  const hipsMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.43, 0.25, 16, 24), pantsMat);
  hipsMesh.scale.set(1.06, 1.0, 0.76);
  hipsMesh.position.y = 0.1;
  torso.add(hipsMesh);

  // Colletto Camicia 3D e Cintura
  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.06, 12, 24), whiteClothMat);
  collar.rotation.x = Math.PI * 0.5;
  collar.position.set(0, 1.18, 0.02);
  torso.add(collar);

  const belt = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.12, 24), leatherMat);
  belt.scale.set(1.02, 1, 0.74);
  belt.position.y = 0.18;
  torso.add(belt);

  const buckle = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.16, 0.08), goldMat);
  buckle.position.set(0, 0.18, 0.36);
  torso.add(buckle);

  if (role === "king") {
    const ermine = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.16, 16, 28), whiteClothMat);
    ermine.rotation.x = Math.PI * 0.5;
    ermine.scale.set(1.1, 0.82, 1.0);
    ermine.position.y = 1.1;
    torso.add(ermine);

    const chain = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.045, 12, 24), goldMat);
    chain.rotation.x = Math.PI * 0.35;
    chain.position.set(0, 0.88, 0.18);
    torso.add(chain);
  }

  if (c.cape) {
    const cape = new THREE.Mesh(
      new THREE.CylinderGeometry(0.48, 0.88, 2.15, 24, 1, false, Math.PI * 0.65, Math.PI * 1.7),
      new THREE.MeshPhysicalMaterial({ color: c.cape, roughness: 0.65, side: THREE.DoubleSide })
    );
    cape.position.set(0, 0.18, -0.18);
    cape.castShadow = true;
    torso.add(cape);
  }

  // COLLO E TESTA UMANA ORGANICA SCOLPITA (Zero spigoli!)
  const neck = new THREE.Mesh(new THREE.CapsuleGeometry(0.16, 0.24, 16, 20), skinMat);
  neck.position.y = 1.32;
  torso.add(neck);

  const head = new THREE.Group();
  head.position.y = 1.72;
  torso.add(head);

  // Cranio + Guance e Mascella morbida
  const cranium = new THREE.Mesh(new THREE.SphereGeometry(0.41, 32, 32), skinMat);
  cranium.scale.set(0.94, 1.08, 0.98);
  cranium.castShadow = true;
  head.add(cranium);

  const lowerJaw = new THREE.Group();
  lowerJaw.position.set(0, -0.1, 0.05);
  head.add(lowerJaw);

  const jawMesh = new THREE.Mesh(new THREE.SphereGeometry(0.34, 28, 28), skinMat);
  jawMesh.scale.set(0.95, 0.88, 0.95);
  lowerJaw.add(jawMesh);

  // Zigomi scolpiti
  for (const side of [-1, 1]) {
    const cheek = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 16), skinMat);
    cheek.scale.set(1.1, 0.75, 0.9);
    cheek.position.set(side * 0.21, -0.06, 0.26);
    head.add(cheek);
  }

  // Naso umano organico (Ponte nasale + Punta arrotondata + Narici)
  const noseBridge = new THREE.Mesh(new THREE.CapsuleGeometry(0.048, 0.14, 12, 16), skinMat);
  noseBridge.position.set(0, 0.02, 0.39);
  noseBridge.rotation.x = -0.32;
  const noseTip = new THREE.Mesh(new THREE.SphereGeometry(0.062, 16, 16), skinMat);
  noseTip.position.set(0, -0.05, 0.44);
  head.add(noseBridge, noseTip);

  // Orecchie umane
  for (const side of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.CapsuleGeometry(0.055, 0.08, 12, 16), skinMat);
    ear.position.set(side * 0.38, -0.02, 0.02);
    ear.rotation.z = side * 0.15;
    head.add(ear);
  }

  // Occhi 3D con Palpebre superiori, Sclera, Iride e Pupilla
  const makeEye = (xPos: number) => {
    const eg = new THREE.Group();
    eg.position.set(xPos, 0.08, 0.34);
    const sclera = new THREE.Mesh(
      new THREE.SphereGeometry(0.076, 20, 20),
      new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.08, clearcoat: 1.0 })
    );
    const iris = new THREE.Mesh(
      new THREE.SphereGeometry(0.042, 16, 16),
      new THREE.MeshStandardMaterial({ color: role === "king" || role === "noble1" ? 0x2563eb : 0x3b1e08, roughness: 0.2 })
    );
    iris.position.z = 0.052;
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.022, 12, 12), new THREE.MeshBasicMaterial({ color: 0x050505 }));
    pupil.position.z = 0.07;

    // Palpebra superiore 3D
    const eyelid = new THREE.Mesh(
      new THREE.SphereGeometry(0.082, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.42),
      skinMat
    );
    eyelid.rotation.x = -0.25;
    eg.add(sclera, iris, pupil, eyelid);
    head.add(eg);
    return eg;
  };
  makeEye(-0.15);
  makeEye(0.15);

  // Sopracciglia organiche arrotondate
  const browGeo = new THREE.CapsuleGeometry(0.028, 0.12, 10, 14);
  const browL = new THREE.Mesh(browGeo, hairMat);
  browL.rotation.z = Math.PI * 0.5;
  browL.position.set(-0.15, 0.21, 0.37);
  const browR = new THREE.Mesh(browGeo, hairMat);
  browR.rotation.z = Math.PI * 0.5;
  browR.position.set(0.15, 0.21, 0.37);
  head.add(browL, browR);

  // Labbra umane 3D
  const lipMat = new THREE.MeshStandardMaterial({ color: 0xc26d60, roughness: 0.45 });
  const upperLip = new THREE.Mesh(new THREE.CapsuleGeometry(0.028, 0.13, 10, 14), lipMat);
  upperLip.rotation.z = Math.PI * 0.5;
  upperLip.position.set(0, -0.17, 0.37);
  head.add(upperLip);

  // Goccia di sudore 3D per le scene di tensione
  const sweatDrop = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 12, 12),
    new THREE.MeshPhysicalMaterial({ color: 0x38bdf8, roughness: 0.1, transmission: 0.5, clearcoat: 1 })
  );
  sweatDrop.scale.set(0.8, 1.4, 0.8);
  sweatDrop.position.set(-0.34, 0.18, 0.28);
  sweatDrop.visible = false;
  head.add(sweatDrop);

  // Capelli 3D scolpiti a ciocche morbide + Copricapi
  const hairBase = new THREE.Mesh(new THREE.SphereGeometry(0.43, 28, 24, 0, Math.PI * 2, 0, Math.PI * 0.58), hairMat);
  hairBase.position.set(0, 0.05, -0.02);
  hairBase.rotation.x = -0.22;
  head.add(hairBase);

  for (const hx of [-0.18, 0, 0.18]) {
    const lock = new THREE.Mesh(new THREE.CapsuleGeometry(0.085, 0.18, 12, 16), hairMat);
    lock.rotation.z = 1.25;
    lock.position.set(hx, 0.33, 0.26);
    head.add(lock);
  }

  if (role === "king") {
    const beard = new THREE.Mesh(new THREE.SphereGeometry(0.36, 24, 20), hairMat);
    beard.scale.set(1.02, 0.78, 0.95);
    beard.position.set(0, -0.22, 0.14);
    head.add(beard);

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
      const spike = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.18, 10), goldMat);
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

  // BRACCIA UMANE MORBIDE CON GOMITI E MANI A 5 DITA
  const buildArm = (isLeft: boolean) => {
    const sh = new THREE.Group();
    sh.position.set(isLeft ? -0.56 : 0.56, 1.04, 0);
    torso.add(sh);

    const shoulderCap = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 16), c.armor ? steelMat : clothMat);
    sh.add(shoulderCap);

    const upper = new THREE.Mesh(new THREE.CapsuleGeometry(0.125, 0.42, 14, 18), c.armor ? steelMat : clothMat);
    upper.position.y = -0.26;
    upper.castShadow = true;
    sh.add(upper);

    const elb = new THREE.Group();
    elb.position.y = -0.52;
    sh.add(elb);

    const fore = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.38, 14, 18), skinMat);
    fore.position.y = -0.24;
    fore.castShadow = true;
    elb.add(fore);

    const hand = new THREE.Group();
    hand.position.y = -0.5;
    elb.add(hand);

    const palm = new THREE.Mesh(new THREE.SphereGeometry(0.085, 14, 14), skinMat);
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
    const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.36, 24), whiteClothMat);
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

  // GAMBE UMANE MORBIDE CON GINOCCHIA E STIVALI TUDOR
  const buildLeg = (isLeft: boolean) => {
    const hip = new THREE.Group();
    hip.position.set(isLeft ? -0.24 : 0.24, 0, 0);
    pelvis.add(hip);

    const thigh = new THREE.Mesh(new THREE.CapsuleGeometry(0.16, 0.62, 14, 18), pantsMat);
    thigh.position.y = -0.44;
    thigh.castShadow = true;
    hip.add(thigh);

    const knee = new THREE.Group();
    knee.position.y = -0.88;
    hip.add(knee);

    const calf = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.62, 14, 18), pantsMat);
    calf.position.y = -0.43;
    calf.castShadow = true;
    knee.add(calf);

    const shoe = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.24, 12, 16), leatherMat);
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
    upperLip,
    lowerJaw,
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

  const bob = isWalking ? Math.abs(Math.sin(walkPhase)) * 0.09 : 0;
  rig.pelvis.position.y = 1.94 + bob;
  rig.torso.rotation.y = isWalking ? Math.sin(walkPhase) * 0.09 : 0;

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

  const armWave = isWalking ? Math.sin(walkPhase) * 0.38 : 0;
  rig.shL.rotation.x = (shLDeg * Math.PI) / 180 - armWave;
  rig.elbL.rotation.x = (elbLDeg * Math.PI) / 180;
  rig.shR.rotation.x = (shRDeg * Math.PI) / 180 + armWave;
  rig.elbR.rotation.x = (elbRDeg * Math.PI) / 180;

  Object.keys(rig.propsR).forEach((k) => (rig.propsR[k].visible = k === propR));
  Object.keys(rig.propsL).forEach((k) => (rig.propsL[k].visible = k === propL));

  rig.head.rotation.y = headYaw;
  rig.head.rotation.x = headPitch;
  rig.sweatDrop.visible = mood === "sweat" || mood === "shock";

  if (mood === "angry") {
    rig.browL.rotation.z = Math.PI * 0.5 - 0.32;
    rig.browR.rotation.z = Math.PI * 0.5 + 0.32;
    rig.browL.position.y = 0.19;
    rig.browR.position.y = 0.19;
    rig.lowerJaw.position.y = -0.11;
  } else if (mood === "shock" || mood === "sweat") {
    rig.browL.rotation.z = Math.PI * 0.5 + 0.22;
    rig.browR.rotation.z = Math.PI * 0.5 - 0.22;
    rig.browL.position.y = 0.25;
    rig.browR.position.y = 0.25;
    rig.lowerJaw.position.y = -0.14;
  } else if (mood === "smug") {
    rig.browL.rotation.z = Math.PI * 0.5 - 0.12;
    rig.browR.rotation.z = Math.PI * 0.5 + 0.25;
    rig.browL.position.y = 0.2;
    rig.browR.position.y = 0.24;
    rig.lowerJaw.position.y = -0.1;
  } else {
    rig.browL.rotation.z = Math.PI * 0.5;
    rig.browR.rotation.z = Math.PI * 0.5;
    rig.browL.position.y = 0.21;
    rig.browR.position.y = 0.21;
    rig.lowerJaw.position.y = -0.1;
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
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.22;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0f172a);
  scene.fog = new THREE.FogExp2(0x0f172a, 0.016);

  const pmrem = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  envScene.background = new THREE.Color(0x334155);
  const l1 = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 16), new THREE.MeshBasicMaterial({ color: 0xfffbeb }));
  l1.position.set(15, 25, 15);
  const l2 = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 16), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
  l2.position.set(-15, 15, -10);
  envScene.add(l1, l2);
  scene.environment = pmrem.fromScene(envScene).texture;

  const camera = new THREE.PerspectiveCamera(35, 1080 / 1920, 0.1, 140);

  const hemi = new THREE.HemisphereLight(0xfffbeb, 0x1e293b, 0.85);
  scene.add(hemi);

  const keyLight = new THREE.SpotLight(0xfff7ed, 2.8);
  keyLight.position.set(7, 16, 10);
  keyLight.angle = Math.PI * 0.38;
  keyLight.penumbra = 0.6;
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width = 2048;
  keyLight.shadow.mapSize.height = 2048;
  keyLight.shadow.bias = -0.0004;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.25);
  rimLight.position.set(-8, 10, -6);
  scene.add(rimLight);

  // Materiali con RILIEVO 3D (bumpMap)
  const stoneTex = makePBRTexture("stone");
  const stoneMat = new THREE.MeshStandardMaterial({ map: stoneTex, bumpMap: stoneTex, bumpScale: 0.045, roughness: 0.72 });
  const woodTex = makePBRTexture("wood");
  const woodMat = new THREE.MeshStandardMaterial({ map: woodTex, bumpMap: woodTex, bumpScale: 0.03, roughness: 0.52 });
  const marbleTex = makePBRTexture("marble");
  const marbleMat = new THREE.MeshStandardMaterial({ map: marbleTex, bumpMap: marbleTex, bumpScale: 0.015, roughness: 0.18, metalness: 0.15 });
  const velvetTex = makePBRTexture("velvet");
  const velvetMat = new THREE.MeshStandardMaterial({ map: velvetTex, bumpMap: velvetTex, bumpScale: 0.02, roughness: 0.75 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.2, metalness: 0.9 });

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

  // Colonne 3D + Torce 3D sulle colonne con vere Fiamme Luminose
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

        const pl = new THREE.PointLight(0xf97316, 1.5, 15);
        pl.position.set(sconceX, 4.8, zPos + 0.3);
        scene.add(pl);
        torchLights.push(pl);
      }
    }
  }

  // Libreria 3D Reale sullo sfondo
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
    king: createOrganicHuman3D("king"),
    groom: createOrganicHuman3D("groom"),
    general: createOrganicHuman3D("general"),
    banker: createOrganicHuman3D("banker"),
    noble1: createOrganicHuman3D("noble1"),
    noble2: createOrganicHuman3D("noble2"),
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
    if (!CACHE) CACHE = initWorld(canvas);

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
        camera.position.set(interpolate(p, [0, 0.52], [2.4, 1.5]), 2.1, interpolate(p, [0, 0.52], [4.2, 3.2]));
        camera.lookAt(0.8, 1.2, 1.0);
      } else {
        camera.position.set(interpolate(p, [0.52, 1], [-0.8, 0.4]), 3.2, interpolate(p, [0.52, 1], [3.6, 2.9]));
        camera.lookAt(-0.2, 3.1, 0.8);
      }
      poseHumanRig(actors.groom, true, -0.35, 0.8, 0.22, wPhase, false, "smug", -35, -45, -45, -55, "key", "goldbag", 0.15, -0.05);
    } else if (idx === 1) {
      doorPivot.rotation.y = interpolate(p, [0.45, 1], [0, 1.35], clamp);
      const zWalk = interpolate(p, [0, 1], [2.2, -3.4]);
      camera.position.set(2.2, 3.1, zWalk + 4.8);
      camera.lookAt(0, 2.7, zWalk - 1.2);
      poseHumanRig(actors.king, true, -0.65, zWalk, Math.PI, wPhase, true, "normal", 15, -20, -35, -40, "key", "none", 0.2, 0);
      poseHumanRig(actors.groom, true, 0.65, zWalk + 1.1, Math.PI, wPhase + 1.5, true, "normal", 15, -20, 15, -20, "none", "none", -0.2, 0);
    } else if (idx === 2) {
      stoolGroup.visible = true;
      if (sub === 0) {
        camera.position.set(1.4, 3.1, 1.8);
        camera.lookAt(-0.8, 2.6, -1.6);
      } else {
        camera.position.set(-0.6, 3.3, 1.4);
        camera.lookAt(0.75, 3.1, -0.8);
      }
      poseHumanRig(actors.king, true, -1.2, -1.6, 0.35, 0, false, "smug", 15, -25, -40, -35, "none", "none", 0.25, 0);
      poseHumanRig(actors.groom, true, 0.85, -0.8, -0.35, 0, false, "shock", 20, -30, -55, -65, "paper", "none", -0.25, 0.08);
    } else if (idx === 3) {
      camera.position.set(interpolate(p, [0, 1], [-1.8, 1.8]), 3.1, 4.2);
      camera.lookAt(0, 3.0, 0.5);
      poseHumanRig(actors.king, true, 0, 0.5, 0, 0, false, "smug", -25, -35, -50, -45, "key", "none", interpolate(p, [0, 1], [-0.2, 0.2]), 0);
    } else if (idx === 4) {
      const gx = interpolate(p, [0, 0.45], [-2.2, 0], clamp);
      camera.position.set(1.4, 3.2, 4.0);
      camera.lookAt(0, 2.9, 0.5);
      poseHumanRig(actors.general, true, gx, 0.5, 0.15, wPhase, p < 0.45, p < 0.55 ? "smug" : "shock", -25, -35, -65, -45, "sword", "none", 0.1, 0);
    } else if (idx === 5) {
      chestGroup.visible = true;
      const bx = interpolate(p, [0, 0.45], [-2.0, -0.4], clamp);
      camera.position.set(-1.3, 3.1, 4.2);
      camera.lookAt(0.2, 2.8, 0.8);
      poseHumanRig(actors.banker, true, bx, 0.8, -0.15, wPhase, p < 0.45, p < 0.55 ? "smug" : "shock", -45, -50, -50, -55, "goldbag", "goldbag", -0.1, 0);
    } else if (idx === 6) {
      doorPivot.rotation.y = interpolate(p, [0.2, 1], [0, 1.25], clamp);
      camera.position.set(interpolate(p, [0, 1], [-1.1, 1.1]), 3.2, -1.8);
      camera.lookAt(0, 3.1, -4.8);
      poseHumanRig(actors.groom, true, 0, -4.8, 0, 0, false, "smug", 15, -20, -55, -55, "key", "none", 0.1, 0);
    } else if (idx === 7) {
      doorPivot.rotation.y = 1.4;
      const zIn = interpolate(p, [0, 1], [-2.8, -8.2]);
      camera.position.set(2.1, 3.4, -0.5);
      camera.lookAt(0, 2.8, -6.5);
      poseHumanRig(actors.king, true, -0.55, zIn, Math.PI, wPhase, true, "normal", 15, -20, 15, -20);
      poseHumanRig(actors.groom, true, 0.65, zIn + 1.2, Math.PI, wPhase + 1.4, true, "sweat", 15, -20, -50, -60, "paper", "none");
    } else if (idx === 8) {
      stoolGroup.visible = true;
      smokeParticles.forEach((sm, i) => {
        sm.visible = true;
        const cycle = (frame * 0.04 + i * 0.5) % 3.5;
        sm.position.set(-1.35 + Math.sin(frame * 0.08 + i) * 0.45, 1.4 + cycle * 0.85, -2.1 + Math.cos(frame * 0.07 + i) * 0.35);
        sm.scale.setScalar(0.6 + cycle * 0.45);
      });
      camera.position.set(interpolate(p, [0, 1], [1.6, 0.4]), 3.1, 2.6);
      camera.lookAt(-0.3, 2.8, -1.2);
      poseHumanRig(actors.groom, true, 0.65, -0.9, -0.25, 0, false, "sweat", -45, -55, -55, -65, "paper", "none", -0.35, 0.1);
    } else if (idx === 9) {
      const lunge = Math.sin(frame * 0.26) * 0.55;
      camera.position.set(Math.sin(p * 2.2) * 2.4, 3.2, 3.2);
      camera.lookAt(0, 2.8, -2.2);
      poseHumanRig(actors.noble1, true, -1.15 + lunge, -2.2, 0.48, wPhase, true, "angry", 20, -30, -65 + Math.sin(frame * 0.38) * 35, -35, "sword", "none", 0.3, 0);
      poseHumanRig(actors.noble2, true, 1.15 - lunge, -2.2, -0.48, wPhase + 1, true, "angry", 20, -30, -65 + Math.cos(frame * 0.38) * 35, -35, "sword", "none", -0.3, 0);
    } else if (idx === 10) {
      camera.position.set(0.2, 3.35, interpolate(p, [0, 1], [2.8, 2.1]));
      camera.lookAt(0, 3.25, 0);
      poseHumanRig(actors.groom, true, 0, 0, 0, 0, false, "smug", 15, -20, -55, -60, "key", "none", 0.12, -0.05);
    } else if (idx === 11) {
      doorPivot.rotation.y = interpolate(p, [0, 0.35], [1.2, 0], clamp);
      ironBar.visible = p > 0.32;
      ironBar.position.y = interpolate(p, [0.32, 0.72], [7.5, 3.2], clamp);
      camera.position.set(interpolate(p, [0, 1], [-1.8, 1.8]), 3.3, -1.5);
      camera.lookAt(0, 3.1, -5.8);
      poseHumanRig(actors.king, true, -0.95, -5.2, 0.25, 0, false, "normal", 15, -20, 15, -20, "none", "none", 0.25, 0);
      poseHumanRig(actors.groom, true, 0.95, -5.2, -0.25, 0, false, "smug", 15, -20, -50, -55, "key", "none", -0.25, 0);
    } else if (idx === 12 || idx === 13) {
      stoolGroup.visible = true;
      if (idx === 12) {
        camera.position.set(1.35, 3.35, 1.4);
        camera.lookAt(-0.75, 3.1, -0.8);
      } else {
        camera.position.set(-1.15, 3.35, 1.4);
        camera.lookAt(0.75, 3.1, -0.8);
      }
      poseHumanRig(actors.king, true, -0.85, -0.8, 0.42, 0, false, "smug", 15, -20, -45, -50, "none", "none", 0.3, 0);
      poseHumanRig(actors.groom, true, 0.85, -0.8, -0.42, 0, false, "smug", 15, -20, -55, -60, "scroll", "none", -0.3, 0);
    } else if (idx === 14) {
      camera.position.set(-1.6, 3.2, 3.8);
      camera.lookAt(0, 2.9, 0);
      poseHumanRig(actors.king, true, -0.95, 0, 0.35, 0, false, "angry", 15, -20, -75, -20, "none", "none", 0.35, 0);
      poseHumanRig(actors.noble1, true, interpolate(p, [0, 1], [0.7, 1.65]), 0, -0.35, wPhase, true, "sweat", -45, -50, -45, -50, "none", "none", -0.35, 0);
    } else if (idx === 15) {
      ironBar.visible = true;
      ironBar.position.y = 3.2;
      camera.position.set(1.6, 3.2, -1.8);
      camera.lookAt(0, 2.9, -5.2);
      poseHumanRig(actors.noble2, true, interpolate(p, [0, 0.55], [-2.1, -1.05], clamp), -4.8, 0.45, wPhase, p < 0.55, "sweat", -45, -55, -45, -55, "none", "none", 0.3, 0);
      poseHumanRig(actors.groom, true, 0.85, -4.8, -0.35, 0, false, "smug", 15, -20, -55, -55, "key", "none", -0.3, 0);
    } else if (idx === 16) {
      ironBar.visible = true;
      ironBar.position.y = 3.2;
      camera.position.set(interpolate(p, [0, 1], [-2.2, 2.2]), 3.5, -0.8);
      camera.lookAt(0, 2.8, -5.2);
      poseHumanRig(actors.general, true, -1.45, -4.8, 0.15, wPhase, p < 0.5, "sweat", -35, -45, -35, -45);
      poseHumanRig(actors.banker, true, 0, -4.6, 0, wPhase + 1, p < 0.5, "sweat", 15, -20, -50, -55, "goldbag", "none");
      poseHumanRig(actors.noble1, true, 1.45, -4.8, -0.15, wPhase + 2, p < 0.5, "sweat", -35, -45, -35, -45);
    } else {
      chestGroup.visible = true;
      camera.position.set(Math.sin(p * 1.6) * 1.4, interpolate(p, [0, 1], [2.7, 3.3]), interpolate(p, [0, 1], [4.6, 3.4]));
      camera.lookAt(0, 3.0, 0.4);
      poseHumanRig(actors.groom, true, 0, 0.6, 0, 0, false, "smug", -45, -50, -55, -60, "paper", "goldbag", 0, -0.05);
      poseHumanRig(actors.king, true, -1.55, -0.8, 0.25, 0, false, "normal", 15, -20, 15, -20);
      poseHumanRig(actors.general, true, 1.55, -0.8, -0.25, 0, false, "sweat", 15, -20, 15, -20);
    }

    renderer.render(scene, camera);
  }, [frame, idx, p]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#09090b" }}>
      <Audio src={staticFile("voce.mp3")} />
      <canvas ref={canvasRef} width={1080} height={1920} style={{ width: "100%", height: "100%" }} />
    </AbsoluteFill>
  );
};
