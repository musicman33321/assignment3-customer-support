"""Toolbox access: login check and the agent's toolset, with the session email bound.

Stage 3 decisions: the agent loads the whole `support-agent` toolset (three tools), and the
customer's email is bound to a fixed value at login (M-5), so the model never sees or fills
`customer_email` / `user_email`. All database access goes through these tools (M-2).
"""

from __future__ import annotations

import json
import os

from toolbox_core import ToolboxClient

TOOLBOX_URL = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000")
AGENT_TOOLSET = "support-agent"


async def verify_login(client: ToolboxClient, email: str, password: str) -> dict | None:
    """Return the user row if the credentials match, else None. Uses the `auth` toolset only."""
    tool = await client.load_tool("verify-login")
    raw = await tool(email=email, password=password)
    data = json.loads(raw) if isinstance(raw, str) and raw else raw
    # The Toolbox returns a bare object for one row, a list for several, and null for none.
    if isinstance(data, list):
        return data[0] if data else None
    return data or None


async def load_agent_tools(client: ToolboxClient, email: str) -> list:
    """Load the agent's toolset with the logged-in email bound into every ownership parameter.

    `bound_params` removes these parameters from the schema the model sees, so there is no
    way for a prompt to substitute another customer's email (M-4, M-5). `strict=False` lets
    each bound name apply to the tools that declare it (`customer_email` on the two read
    tools, `user_email` on action-log).
    """
    return await client.load_toolset(
        AGENT_TOOLSET,
        bound_params={"customer_email": email, "user_email": email},
        strict=False,
    )
