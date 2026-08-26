"""
mcp_test.py — prove the agent can talk to Alpaca THROUGH the MCP server.

It launches Alpaca's official MCP server as a subprocess (stdio), lists the
tools it exposes, and calls `get_account_info` — so we confirm the whole
MCP path works before wiring it into the autonomous agent.

Run (with keys in .env):   .venv/bin/python mcp_test.py
"""
from __future__ import annotations
import asyncio, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import config as C

# the MCP server console script that pip installed into this venv
SERVER_CMD = os.path.join(os.path.dirname(sys.executable), 'alpaca-mcp-server')

def server_params() -> StdioServerParameters:
    env = {**os.environ,
           'ALPACA_API_KEY': C.ALPACA_API_KEY,
           'ALPACA_SECRET_KEY': C.ALPACA_SECRET_KEY,
           'ALPACA_PAPER_TRADE': 'true'}          # paper only
    return StdioServerParameters(command=SERVER_CMD, args=[], env=env)

WANT = ['get_account_info', 'get_option_contracts', 'get_option_chain',
        'get_option_snapshot', 'place_option_order', 'get_all_positions',
        'close_position', 'get_orders']

async def main():
    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"✅ Connected to Alpaca via MCP — {len(names)} tools exposed\n")
            print("   Tools we'll need for the options agent:")
            for w in WANT:
                print(f"     {'✅' if w in names else '❌ MISSING'}  {w}")
            print("\n--- calling get_account_info THROUGH MCP ---")
            res = await session.call_tool('get_account_info', {})
            for c in res.content:
                text = getattr(c, 'text', None)
                if text:
                    print(text)

if __name__ == '__main__':
    asyncio.run(main())
