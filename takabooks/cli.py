"""Command-line interface for TakaBooks."""

import argparse
import sys
from pathlib import Path

from takabooks import ledger
from takabooks.tax import TAX_FREE_THRESHOLDS, TAX_YEAR, compute_tax


def fmt(amount: float) -> str:
    """Format a BDT amount with thousand separators."""
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def cmd_tax(args: argparse.Namespace) -> int:
    try:
        result = compute_tax(
            income=args.income,
            category=args.category,
            guardian_of_disabled=args.guardian,
            new_taxpayer=args.new_taxpayer,
            non_resident=args.non_resident,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Income tax for FY {TAX_YEAR} (Bangladesh)")
    print(f"  Total income:        Tk {fmt(result.total_income)}")
    if not args.non_resident:
        print(f"  Tax-free threshold:  Tk {fmt(result.tax_free_threshold)}")
        print(f"  Taxable income:      Tk {fmt(result.taxable_income)}")
        for slab in result.slabs:
            upper = "above" if slab.upper is None else fmt(slab.upper)
            print(
                f"    {fmt(slab.lower)} - {upper}"
                f" @ {slab.rate:.0%}: Tk {fmt(slab.tax)}"
                f"  (on Tk {fmt(slab.taxable)})"
            )
        if result.taxable_income > 0:
            print(f"  Slab tax:            Tk {fmt(result.slab_tax)}")
            if result.total_tax == result.minimum_tax and result.slab_tax < result.minimum_tax:
                print(f"  Minimum tax applies: Tk {fmt(result.minimum_tax)}")
    print(f"  Total tax:           Tk {fmt(result.total_tax)}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    try:
        entry = ledger.add_entry(
            entry_type=args.type,
            amount=args.amount,
            note=" ".join(args.note),
            entry_date=args.date,
            path=args.ledger_file,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"added {entry.type} of Tk {fmt(entry.amount)} on {entry.date}: {entry.note}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = ledger.load_entries(args.ledger_file)
    if not entries:
        print("no entries yet")
        return 0
    for e in entries:
        print(f"{e.date}  {e.type:<7}  Tk {fmt(e.amount):>12}  {e.note}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    totals = ledger.summarize(ledger.load_entries(args.ledger_file))
    print(f"Total income:   Tk {fmt(totals['income'])}")
    print(f"Total expenses: Tk {fmt(totals['expense'])}")
    print(f"Net balance:    Tk {fmt(totals['net'])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="takabooks",
        description="Bangladesh income tax calculator and simple income/expense ledger",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_tax = sub.add_parser("tax", help="compute individual income tax (FY 2025-26)")
    p_tax.add_argument("income", type=float, help="total annual income in BDT")
    p_tax.add_argument(
        "--category",
        choices=sorted(TAX_FREE_THRESHOLDS),
        default="general",
        help="taxpayer category (affects the tax-free threshold)",
    )
    p_tax.add_argument(
        "--guardian",
        action="store_true",
        help="parent/guardian of a physically challenged person (+Tk 50,000 exemption)",
    )
    p_tax.add_argument(
        "--new-taxpayer",
        action="store_true",
        help="minimum tax Tk 1,000 instead of Tk 5,000",
    )
    p_tax.add_argument(
        "--non-resident",
        action="store_true",
        help="non-resident, non-Bangladeshi citizen (flat 30%%)",
    )
    p_tax.set_defaults(func=cmd_tax)

    p_add = sub.add_parser("add", help="add an income or expense entry")
    p_add.add_argument("type", choices=ledger.ENTRY_TYPES)
    p_add.add_argument("amount", type=float, help="amount in BDT")
    p_add.add_argument("note", nargs="*", help="optional note")
    p_add.add_argument("--date", help="entry date, ISO format (default: today)")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list ledger entries")
    p_list.set_defaults(func=cmd_list)

    p_summary = sub.add_parser("summary", help="show income/expense totals")
    p_summary.set_defaults(func=cmd_summary)

    for p in (p_add, p_list, p_summary):
        p.add_argument(
            "--ledger-file",
            type=Path,
            default=ledger.DEFAULT_LEDGER_PATH,
            help=f"ledger JSON file (default: {ledger.DEFAULT_LEDGER_PATH})",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
