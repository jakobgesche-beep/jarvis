#!/bin/bash
# Tages-Briefing – via macOS LaunchAgent täglich um 8 Uhr ausführen
# Einrichten: scripts/install_launchagent.sh

cd ~/jarvis
source .venv/bin/activate

python -c "
import asyncio
from dotenv import load_dotenv
load_dotenv()

from core.brain import Brain
from core.memory import Memory
from core.speaker import Speaker

async def briefing():
    memory = Memory()
    brain = Brain(memory=memory)
    speaker = Speaker()

    response = await brain.process(
        'Gib mir ein kurzes Morgen-Briefing: Was steht heute an? '
        'Wie ist das Wetter? Gibt es wichtige ungelesene E-Mails?'
    )
    await speaker.say(response)

asyncio.run(briefing())
"
