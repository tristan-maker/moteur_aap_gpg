import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

# Charge les variables d'environnement (.env)
load_dotenv("gpg_agent/.env")
os.environ["DRIVE_VAULT_FOLDER_ID"] = "1zCnczHgBQW0Zk6FdcctWWjl6dUmcvBuN"
os.environ["DRIVE_OUTPUT_PARENT_FOLDER_ID"] = "1-7DrkohVJjLcAgthjPoJ-1HAAxPhixYG"

from gpg_agent.agent import root_agent

async def main():
    print("==========================================================================")
    print("🚀 LANCEMENT DU TEST DE VEILLE RÉELLE (GOOGLE SEARCH + DATA ROOM DRIVE)")
    print("==========================================================================")
    runner = InMemoryRunner(agent=root_agent, app_name="gpg_veille_test")
    session = await runner.session_service.create_session(
        app_name="gpg_veille_test", user_id="tristan"
    )

    prompt = (
        "Lance une veille web réelle sur les appels à projets 2026/2027 en France "
        "(sport, inclusion des jeunes QPV, mentorat, montagne/voile, FDVA, Agence Nationale du Sport, "
        "Fondation de France ou Fondations bancaires). Sélectionne la meilleure opportunité active "
        "trouvée et génère immédiatement sa Data Room complète dans notre Google Drive."
    )

    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    async for event in runner.run_async(
        user_id="tristan", session_id=session.id, new_message=msg
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"\n--- [{event.author}] ---\n{part.text}")

if __name__ == "__main__":
    asyncio.run(main())
