"""
cron_once.py — one market-hours-gated pass of the agent.
Used by Render Cron and GitHub Actions (and works locally too). It runs the
agent only when the US market is open; otherwise it exits quietly. It needs
AGENT_MODE=LIVE_PAPER + the paper keys in the environment to actually trade.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

et = datetime.now(ZoneInfo('America/New_York'))
is_open = et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16

if is_open:
    import agent
    agent.run_once()
else:
    print(f"Market closed ({et:%Y-%m-%d %H:%M} ET) — no action.")
