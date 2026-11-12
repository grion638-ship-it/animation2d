txt = open("src/GroomStory.tsx").read()
txt = txt.replace("THREE.PCFSoftShadowMap", "THREE.PCFShadowMap")
txt = txt.replace("keyLight.shadow.mapSize.width = 2048;", "keyLight.shadow.mapSize.width = 1024;")
txt = txt.replace("keyLight.shadow.mapSize.height = 2048;", "keyLight.shadow.mapSize.height = 1024;")
txt = txt.replace(
    "if (!CACHE) CACHE = initWorld(canvas);",
    "if (!CACHE || CACHE.renderer.domElement !== canvas) { if (CACHE) CACHE.renderer.dispose(); CACHE = initWorld(canvas); }"
)
open("src/GroomStory.tsx", "w").write(txt)
print("✅ SCUDO ANTI-CRASH RAM APPLICATO!")
