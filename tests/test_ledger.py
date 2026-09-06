import pytest

from takabooks import ledger
from takabooks.ledger import add_entry, load_entries, summarize


def test_add_and_load(tmp_path):
    path = tmp_path / "ledger.json"
    add_entry("income", 50_000, "salary", entry_date="2026-09-01", path=path)
    add_entry("expense", 12_500.50, "rent", entry_date="2026-09-02", path=path)

    entries = load_entries(path)
    assert len(entries) == 2
    assert entries[0].type == "income"
    assert entries[0].note == "salary"
    assert entries[1].amount == 12_500.50


def test_load_missing_file_returns_empty(tmp_path):
    assert load_entries(tmp_path / "nope.json") == []


def test_add_persists_across_calls(tmp_path):
    path = tmp_path / "ledger.json"
    add_entry("income", 1_000, path=path)
    add_entry("income", 2_000, path=path)
    assert [e.amount for e in load_entries(path)] == [1_000, 2_000]


def test_invalid_type_and_amount(tmp_path):
    with pytest.raises(ValueError, match="entry type"):
        add_entry("gift", 100, path=tmp_path / "l.json")
    with pytest.raises(ValueError, match="positive"):
        add_entry("income", 0, path=tmp_path / "l.json")


def test_summarize():
    entries = [
        ledger.Entry("2026-09-01", "income", 100_000, "salary"),
        ledger.Entry("2026-09-02", "expense", 30_000, "rent"),
        ledger.Entry("2026-09-03", "expense", 5_000, "food"),
    ]
    totals = summarize(entries)
    assert totals == {"income": 100_000, "expense": 35_000, "net": 65_000}
