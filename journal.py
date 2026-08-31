"""
journal.py — the agent's permanent DECISION JOURNAL (for the presentation).

Every cloud run appends ONE row to `activity.csv` and regenerates `ACTIVITY.md`,
so there is always a visible, timestamped record of what happened on each pass:
  • a trade was placed,  • a signal fired but was risk-gated,
  • no signal at all,     • or the market was closed.

This is the "no surprises" audit trail: if it ran, there's a line. If a day had
no trades, the journal SAYS so explicitly instead of leaving an empty dashboard.
"""
from __future__ import annotations
import csv, os

CSV = os.path.join(os.path.dirname(__file__), 'activity.csv')
MD = os.path.join(os.path.dirname(__file__), 'ACTIVITY.md')
FIELDS = ['timestamp_et', 'market', 'equity', 'open_positions',
          'new_trades', 'exits', 'summary']


def record(row: dict) -> None:
    clean = {k: row.get(k, '') for k in FIELDS}
    is_new = not os.path.exists(CSV)
    with open(CSV, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(clean)
    _render_md()


def _render_md() -> None:
    with open(CSV) as f:
        rows = list(csv.DictReader(f))
    open_rows = [r for r in rows if r.get('market') == 'open']
    total_trades = sum(int(r['new_trades'] or 0) for r in rows)
    total_exits = sum(int(r['exits'] or 0) for r in rows)

    lines = [
        "# 📓 Risk Gate — Decision Journal",
        "",
        "Auto-written by the agent on **every** cloud run. Proof it ran, and an",
        "honest record of what it decided — including days with no trades.",
        "",
        f"- **Runs logged:** {len(rows)}  ({len(open_rows)} during market hours)",
        f"- **Trades placed:** {total_trades}   ·   **Positions closed:** {total_exits}",
        "",
        "| Time (ET) | Market | Equity | Open | New | Exits | What happened |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows[-60:]:                       # last 60 runs, newest at the bottom
        eq = r.get('equity', '')
        try:
            eq = f"${float(eq):,.0f}"
        except (TypeError, ValueError):
            eq = eq or "—"
        lines.append(
            f"| {r.get('timestamp_et','')} | {r.get('market','')} | {eq} | "
            f"{r.get('open_positions','') or '—'} | {r.get('new_trades','') or '0'} | "
            f"{r.get('exits','') or '0'} | {r.get('summary','')} |")
    lines.append("")
    with open(MD, 'w') as f:
        f.write("\n".join(lines) + "\n")
