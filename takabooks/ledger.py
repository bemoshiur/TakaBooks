"""Simple JSON-file income/expense ledger."""

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

DEFAULT_LEDGER_PATH = Path.home() / ".takabooks" / "ledger.json"

ENTRY_TYPES = ("income", "expense")


@dataclass
class Entry:
    date: str  # ISO format, e.g. "2026-09-06"
    type: str  # "income" or "expense"
    amount: float
    note: str = ""


def load_entries(path: Path = DEFAULT_LEDGER_PATH) -> list[Entry]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Entry(**item) for item in data]


def save_entries(entries: list[Entry], path: Path = DEFAULT_LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(e) for e in entries], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_entry(
    entry_type: str,
    amount: float,
    note: str = "",
    entry_date: str | None = None,
    path: Path = DEFAULT_LEDGER_PATH,
) -> Entry:
    if entry_type not in ENTRY_TYPES:
        raise ValueError(f"entry type must be one of: {', '.join(ENTRY_TYPES)}")
    if amount <= 0:
        raise ValueError("amount must be positive")
    entry = Entry(
        date=entry_date or date.today().isoformat(),
        type=entry_type,
        amount=amount,
        note=note,
    )
    entries = load_entries(path)
    entries.append(entry)
    save_entries(entries, path)
    return entry


def summarize(entries: list[Entry]) -> dict[str, float]:
    """Total income, total expense, and net balance."""
    income = sum(e.amount for e in entries if e.type == "income")
    expense = sum(e.amount for e in entries if e.type == "expense")
    return {"income": income, "expense": expense, "net": income - expense}
