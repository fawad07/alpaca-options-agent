"""
mcp_inspect.py — print the exact input parameters for the options tools,
so we wire the agent's MCP calls correctly. Run: .venv/bin/python mcp_inspect.py
"""
from __future__ import annotations
import asyncio, json
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp_test import server_params   # reuse the same server launch

SHOW = ['get_option_contracts', 'get_option_snapshot', 'place_option_order',
        'get_all_positions', 'close_position']

async def main():
    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name: t for t in (await session.list_tools()).tools}
            for name in SHOW:
                t = tools.get(name)
                print("=" * 70)
                if not t:
                    print(f"{name}: NOT FOUND"); continue
                print(name)
                desc = (t.description or '').strip().split('\n')[0]
                print(f"  desc: {desc[:120]}")
                props = (t.inputSchema or {}).get('properties', {})
                required = set((t.inputSchema or {}).get('required', []))
                for p, meta in props.items():
                    star = '*' if p in required else ' '
                    typ = meta.get('type', meta.get('anyOf', '?'))
                    print(f"   {star} {p}: {typ}")

if __name__ == '__main__':
    asyncio.run(main())
