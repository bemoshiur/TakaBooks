# TakaBooks

Bangladesh individual income tax calculator and a simple income/expense ledger, as a Python CLI.

Tax rates follow the Finance Ordinance 2025 (FY 2025-26, assessment year 2026-27).

## Install

```sh
pip install -e .
```

Or run without installing: `python3 -m takabooks.cli ...` from the repo root.

## Usage

### Income tax

```sh
takabooks tax 1500000                      # general taxpayer
takabooks tax 1500000 --category female-senior
takabooks tax 1500000 --guardian           # +Tk 50,000 exemption
takabooks tax 1500000 --new-taxpayer       # minimum tax Tk 1,000
takabooks tax 1500000 --non-resident       # flat 30%
```

Tax-free thresholds (FY 2025-26):

| Category | Threshold (Tk) |
|---|---|
| general | 400,000 |
| female-senior (women / 65+) | 450,000 |
| disabled | 525,000 |
| third-gender | 525,000 |
| freedom-fighter (war-wounded, gazetted) | 550,000 |

Slabs above the threshold: next 300k @10%, next 400k @15%, next 500k @20%,
next 2M @25%, rest @30%. Minimum tax Tk 5,000 (Tk 1,000 for new taxpayers)
applies when income exceeds the threshold.

### Ledger

Entries are stored in `~/.takabooks/ledger.json` (override with `--ledger-file`).

```sh
takabooks add income 85000 "September salary"
takabooks add expense 25000 rent --date 2026-09-01
takabooks list
takabooks summary
```

## Tests

```sh
python3 -m pytest tests/
```
