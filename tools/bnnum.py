#!/usr/bin/env python3
"""TakaBooks — Bangla numerals, as Bangladeshi statutes actually write them.

Searching enacted text for a figure is not string matching.  ITA 2023 writes
Tk 7,50,000 as ``৭,৫০,০০০`` — Bangla digits, lakh/crore grouping — and often
again in words, ``সাত লক্ষ পঞ্চাশ হাজার``.  A percentage appears as ``১০%``,
``১০ শতাংশ`` or ``শতকরা ১০ ভাগ``.  A search that knows only ``750000`` finds
none of them, which reads as "the statute does not say this" when in fact it
says it four ways.

Standard library only.
"""

from __future__ import annotations

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
TO_BN = str.maketrans("0123456789", BN_DIGITS)
TO_EN = str.maketrans(BN_DIGITS, "0123456789")

_UNITS = ["", "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়"]


def to_bn(value: int | str) -> str:
    """12345 -> '১২৩৪৫'"""
    return str(value).translate(TO_BN)


def to_en(text: str) -> str:
    """'১২৩৪৫' -> '12345'"""
    return text.translate(TO_EN)


def group_bd(value: int) -> str:
    """Bangladeshi lakh/crore grouping in Bangla digits: 750000 -> '৭,৫০,০০০'.

    The last three digits group together, everything above them in twos — the
    same rule ``takabooks.Money`` uses for display.
    """
    s = str(abs(int(value)))
    if len(s) <= 3:
        out = s
    else:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        out = ",".join(parts) + "," + tail
    return ("-" if int(value) < 0 else "") + out.translate(TO_BN)


def group_intl(value: int) -> str:
    """1234567 -> '১,২৩৪,৫৬৭' — some drafting uses international grouping."""
    return f"{abs(int(value)):,}".translate(TO_BN)


def in_words(value: int) -> list[str]:
    """Rough Bangla word forms for the round figures statutes actually spell out.

    Deliberately partial: it covers exact multiples of লক্ষ / কোটি / হাজার,
    which is how thresholds are written, and returns nothing for a figure that
    would need full spelling-out.  A missing form costs a search hit; a WRONG
    form would cost a false match, so the bias is to stay silent.
    """
    value = int(value)
    out: list[str] = []
    for size, word in ((10_000_000, "কোটি"), (100_000, "লক্ষ"), (1_000, "হাজার")):
        if value and value % size == 0:
            count = value // size
            if 1 <= count <= 9:
                out.append(f"{_UNITS[count]} {word}")
            out.append(f"{to_bn(count)} {word}")
            if word == "লক্ষ":
                out.append(f"{to_bn(count)} লাখ")
            break
    return out


def money_forms(value) -> list[str]:
    """Every way a taka figure plausibly appears in enacted Bangla text."""
    try:
        n = int(str(value).replace(",", "").split(".")[0])
    except (TypeError, ValueError):
        return []
    forms = {to_bn(n), group_bd(n), group_intl(n)}
    forms.update(in_words(n))
    return sorted(f for f in forms if f)


def percent_forms(value) -> list[str]:
    """'27.5' -> ['২৭.৫%', '২৭.৫ শতাংশ', ...].  Trailing zeros are dropped the
    way drafting does: 15.00 is written ১৫, never ১৫.০০."""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    bn = to_bn(text)
    return [f"{bn}%", f"{bn} শতাংশ", f"শতকরা {bn}", f"{bn} ভাগ", bn]


def forms_for(value, unit: str) -> list[str]:
    """Dispatch on the rates file's own unit vocabulary."""
    unit = (unit or "").lower()
    if unit.startswith("bdt") or unit in {"taka", "money"}:
        return money_forms(value)
    if unit == "percent":
        return percent_forms(value)
    if unit == "count":
        return [to_bn(value), str(value)]
    return []


if __name__ == "__main__":  # a quick self-check, not a test suite
    assert group_bd(750000) == "৭,৫০,০০০", group_bd(750000)
    assert group_bd(500) == "৫০০"
    assert group_bd(12345678) == "১,২৩,৪৫,৬৭৮", group_bd(12345678)
    assert "সাত লক্ষ" not in money_forms(750000)      # 7.5 lakh is not a round লক্ষ
    assert "পাঁচ লক্ষ" in money_forms(500000), money_forms(500000)
    assert percent_forms("15.00")[0] == "১৫%"
    print("bnnum self-check OK")
    for v, u in ((750000, "BDT"), (500000, "BDT"), (5000000, "BDT"), ("27.5", "percent")):
        print(f"  {v!s:>9} {u:<8} -> {forms_for(v, u)}")
