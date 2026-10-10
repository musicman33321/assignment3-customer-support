"""Stage 3 throwaway CLI: log in, then loop on `You:` and print the agent's final text.

Stage 4 replaces the body of the loop with the pipeline's event stream and a renderer.
Satisfies C-1 (email + hidden password, `quit`/`exit`/`q` ends the loop).
"""

from __future__ import annotations

import asyncio
import getpass
import sys

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from toolbox_core import ToolboxClient

from support.agent import build_agent
from support.tools import TOOLBOX_URL, load_agent_tools, verify_login

APP_NAME = "support"
QUIT_WORDS = {"quit", "exit", "q"}


async def run_turn(runner: Runner, user_id: str, session_id: str, text: str) -> str:
    """Send one message through the ADK runner and return the final reply text."""
    message = types.Content(role="user", parts=[types.Part(text=text)])
    final = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text or "" for p in event.content.parts)
    return final


async def main() -> None:
    load_dotenv()
    async with ToolboxClient(TOOLBOX_URL) as client:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        user = await verify_login(client, email, password)
        if not user:
            print("Invalid email or password.")
            sys.exit(1)
        print(f"Welcome, {user['full_name']}. Type quit to leave.\n")

        # One toolset per login, with this user's email bound into every ownership parameter.
        tools = await load_agent_tools(client, email)
        agent = build_agent(tools)
        sessions = InMemorySessionService()
        session = await sessions.create_session(app_name=APP_NAME, user_id=email)
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=sessions)

        while True:
            try:
                text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                continue
            if text.lower() in QUIT_WORDS:
                break
            reply = await run_turn(runner, email, session.id, text)
            print(f"Agent: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())
