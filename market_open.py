"""market_open.py — prints OPEN if the US market is in regular hours, else CLOSED.
Timezone-safe (checks Eastern Time regardless of the machine's clock).
Note: does not account for market holidays — on a holiday Alpaca simply rejects
the order, which is harmless."""
from datetime import datetime
from zoneinfo import ZoneInfo

et = datetime.now(ZoneInfo('America/New_York'))
is_open = et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16
print('OPEN' if is_open else 'CLOSED')
