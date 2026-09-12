"""
journal.py — the agent's permanent DECISION JOURNAL (for the presentation + track record).

Per-account (v2, step 8): account 'A'/'default' keeps the original `activity.csv`
(7-column V1 schema — the pure options track record, untouched). Any other account
(e.g. 'B') writes a SEPARATE `activity-<account>.csv` that also records `account` and
`assets` (which asset classes traded), so multi-account/multi-asset runs are distinct.

Every run — traded, no-signal, market-closed, or errored — writes ONE row, so there is
always a visible record.
"""
from __future__ import annotations
import csv, os

_DIR = os.path.dirname(__file__)
LEGACY_FIELDS = ['timestamp_et', 'market', 'equity', 'open_positions',
                 'new_trades', 'exits', 'summary']
FIELDS = ['timestamp_et', 'account', 'assets', 'market', 'equity',
          'open_positions', 'new_trades', 'exits', 'summary']


def _paths(account: str):
    """(csv_path, md_path, fields, label). 'A'/'default' → legacy activity.csv (V1)."""
    if account in ('A', 'default', ''):
        return (os.path.join(_DIR, 'activity.csv'),
                os.path.join(_DIR, 'ACTIVITY.md'), LEGACY_FIELDS, 'A')
    safe = account.replace('/', '-')
    return (os.path.join(_DIR, f'activity-{safe}.csv'),
            os.path.join(_DIR, f'ACTIVITY-{safe}.md'), FIELDS, account)


def record(row: dict) -> None:
    account = str(row.get('account') or 'A')
    csv_path, md_path, fields, label = _paths(account)
    clean = {k: row.get(k, '') for k in fields}
    is_new = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            w.writeheader()
        w.writerow(clean)
    _render_md(csv_path, md_path, fields, label)


def _render_md(csv_path, md_path, fields, label) -> None:
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    open_rows = [r for r in rows if r.get('market') == 'open']
    total_trades = sum(int(r.get('new_trades') or 0) for r in rows)
    total_exits = sum(int(r.get('exits') or 0) for r in rows)
    has_assets = 'assets' in fields

    lines = [
        f"# 📓 Risk Gate — Decision Journal ({label})",
        "",
        "Auto-written by the agent on **every** cloud run. Proof it ran, and an",
        "honest record of what it decided — including days with no trades.",
        "",
        f"- **Runs logged:** {len(rows)}  ({len(open_rows)} during market hours)",
        f"- **Trades placed:** {total_trades}   ·   **Positions closed:** {total_exits}",
        "",
        "| Time (ET) |" + (" Assets |" if has_assets else "") +
        " Market | Equity | Open | New | Exits | What happened |",
        "|---|" + ("---|" if has_assets else "") + "---|---|---|---|---|---|",
    ]
    for r in rows[-60:]:
        eq = r.get('equity', '')
        try:
            eq = f"${float(eq):,.0f}"
        except (TypeError, ValueError):
            eq = eq or "—"
        assets_col = f" {r.get('assets', '') or '—'} |" if has_assets else ""
        lines.append(
            f"| {r.get('timestamp_et', '')} |{assets_col} {r.get('market', '')} | {eq} | "
            f"{r.get('open_positions', '') or '—'} | {r.get('new_trades', '') or '0'} | "
            f"{r.get('exits', '') or '0'} | {r.get('summary', '')} |")
    lines.append("")
    with open(md_path, 'w') as f:
        f.write("\n".join(lines) + "\n")
