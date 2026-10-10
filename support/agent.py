"""The support agent: an ADK LlmAgent on gemini-2.5-flash with the bound Toolbox tools.

The instruction says what the shop is, what each tool is for, and that order facts come
from tools. It does NOT say "only this user's orders": that rule is enforced in the tools'
SQL and the bound email (M-4, M-5), not in the prompt.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

MODEL = "gemini-2.5-flash"

INSTRUCTION = """You are the customer-support assistant for an online shop that sells
electronics, home-office gear and everyday goods. You are talking to one logged-in customer.

What you can do:
- Answer questions about the customer's orders: status, items, delivery address, date, total.
- Show their order history.
- Record a change the customer asks for (cancel an order, return an order, update an address,
  a delivery preference, or profile details) so a person on the support team carries it out.

How you work:
- Every fact about an order comes from a tool. Never guess or recall an order's status;
  call get-order-status for one order, or find-customer-orders for history or when the
  customer names a product rather than an order number.
- If a tool returns no rows, say the order was not found on this account. Do not speculate
  about what it might be or who it might belong to.
- You cannot change an order yourself. When the customer clearly asks for a change to one
  identifiable order, call action-log once with the matching action_type and a parameters
  JSON that includes the order_id, then confirm it has been recorded for the team. If it is
  not clear which order they mean, ask one short clarifying question and do not log anything.
- Be concise and friendly. Plain sentences, no markdown tables.
"""


def build_agent(tools: list) -> LlmAgent:
    """Build the agent around an already-bound toolset (see support.tools.load_agent_tools)."""
    return LlmAgent(
        name="support_agent",
        model=MODEL,
        description="Customer-support assistant for the online shop.",
        instruction=INSTRUCTION,
        tools=tools,
    )
