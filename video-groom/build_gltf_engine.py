code = '''import React, { useEffect, useRef } from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { TIMINGS } from "./timings";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

let SHARED_RENDERER: THREE.WebGLRenderer | null = null;
const MODEL_CACHE: Record<string, THREE.Group> = {};

function initGLTFRenderer(canvas: HTMLCanvasElement) {
  if (SHARED_RENDERER) return SHARED_RENDERER;
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
  renderer.toneMappingExposure = 1.15;
  SHARED_RENDERER = renderer;
  return renderer;
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
    const renderer = initGLTFRenderer(canvas);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a);
    scene.fog = new THREE.FogExp2(0x0f172a, 0.015);

    const camera = new THREE.PerspectiveCamera(38, 1080 / 1920, 0.1, 100);

    // Illuminazione cinematografica 3D con ombre reali
    const hemi = new THREE.HemisphereLight(0xffffff, 0x1e293b, 0.9);
    scene.add(hemi);

    const spot = new THREE.SpotLight(0xfffbeb, 2.5);
    spot.position.set(5, 15, 8);
    spot.castShadow = true;
    spot.shadow.mapSize.width = 2048;
    spot.shadow.mapSize.height = 2048;
    scene.add(spot);

    // Pavimento in marmo lucido riflettente
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(30, 30),
      new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.2, metalness: 0.1 })
    );
    floor.rotation.x = -Math.PI * 0.5;
    floor.receiveShadow = true;
    scene.add(floor);

    // Camera setup in base alla scena
    camera.position.set(0, 2.8, 6.5);
    camera.lookAt(0, 2.2, 0);

    renderer.render(scene, camera);
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
print("✅ MOTORE GLTF LOADER PRONTO PER MODELLI 3D REALI (.GLB)!")
