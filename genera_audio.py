import asyncio
import edge_tts
import os

os.makedirs("public", exist_ok=True)

TEXT = "Imagine landing the most powerful, highly paid job in the entire kingdom, but your only actual duty is... wiping your boss's butt. Back in Tudor England, the most coveted role in the royal court wasn't a top general or a wealthy banker. It was the Groom of the Stool, the guy officially in charge of the King's toilet time. It sounds like an absolute punishment, but the richest nobles literally fought each other for this job. Why? Because you were locked in a private room with the King every single day. You became his ultimate confidant. You knew all his dark secrets, you knew who he hated, and you controlled exactly who got to speak with him. So, while everyone else was outside begging for power, the guy holding the royal toilet paper was actually secretly running the country."
VOICE = "en-US-ChristopherNeural"
OUTPUT_FILE = "public/voce.mp3"

async def _main() -> None:
    communicate = edge_tts.Communicate(TEXT, VOICE, rate="+5%")
    await communicate.save(OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(_main())
