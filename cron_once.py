"""
cron_once.py — one market-hours-gated pass of the agent.
Used by GitHub Actions (and works locally too). Runs the agent only when the US
market is open; otherwise it exits quietly. It needs AGENT_MODE=LIVE_PAPER + the
paper keys in the environment to actually trade.

Every pass — traded, no-signal, market-closed, or errored — writes ONE row to the
decision journal (activity.csv / ACTIVITY.md) so there is always a visible record.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import journal

et = datetime.now(ZoneInfo('America/New_York'))
is_open = et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16
stamp = f"{et:%Y-%m-%d %H:%M}"

if not is_open:
    print(f"Market closed ({stamp} ET) — no action.")
    journal.record({'timestamp_et': stamp, 'market': 'closed',
                    'summary': 'market closed — no action'})
else:
    import agent
    try:
        summ = agent.run_once() or {}
        summ.setdefault('timestamp_et', stamp)
        summ.setdefault('market', 'open')
        journal.record(summ)
    except Exception as e:
        import traceback
        traceback.print_exc()
        journal.record({'timestamp_et': stamp, 'market': 'open',
                        'summary': f'ERROR: {type(e).__name__}: {e}'})
        raise
