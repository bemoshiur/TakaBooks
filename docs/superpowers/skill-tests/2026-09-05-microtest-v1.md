# Micro-test v1 — counters in isolation, canary rates

**Run:** `wf_773842cc-372` · 30 agents, 0 errors · **Result: 12/25 fully compliant** (RED control: 0/25)

| Scenario | Pass | Memory figures recited | Asked before computing | Canary used |
|---|---|---|---|---|
| S1 freelancer | 5/5 | 0/5 | 5/5 | 3/5 (2 quoted no numbers at all) |
| S2 journal/VAT | 0/5 | 0/5 | 5/5 | n/a |
| S3 Banglish threshold | 1/5 | 0/5 | 5/5 | n/a |
| S4 TDS anchor | 1/5 | 0/5 | 5/5 | n/a |
| S5 corporate | 5/5 | 0/5 | 5/5 | n/a |

**Every one of the 13 fails was `stated_assessment_year = false`** — and the judges traced it to the
instruction, not the models: "stops after part 1 and asks" meant compliant replies never reached part 2,
where the AY lived. A wording defect, exactly what micro-testing exists to catch.

## Loopholes found (input to v2)
1. **AY unreachable when stopping** — move income year + AY into part 1 (Facts), always present.
2. **Mechanism-from-memory leak** — the rule barred *figures* only; models narrated exemption conditions,
   "monthly return", schedule structure, Act names, penalty existence from memory. Extend the rule.
3. **Slab table without a base** (S1 rep 4) — refused to compute, printed every band; user can do it themselves.
4. **Symbolic provisional entry** (S2, 5/5) — full journal structure "on the assumption you're registered".
5. **Soft endorsement** (S4) — "7% may well be right" while formally declining to confirm.
6. **Question flooding** (S5 rep 1: 8 questions, 3 decisive) — gating facts not ranked.
7. **Fabricated file path** (S3 rep 2: `rates-AY2027-28.toml`, never listed).
8. **Verify step as a promise** when stopping — decide: parts 1, 2, 5 always present.
9. **Accountant assumed licensed** (S4) — "a licensed ITP or CA" must be the phrase, and asked about.

Shape convergence was strong in all five scenarios — the recipe form is binding. Length is high
(S1 replies ~400–600 words); v2 caps questions at four and leads with the gating fact.
