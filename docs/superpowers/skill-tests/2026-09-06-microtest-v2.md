# Micro-test v2 — counters v2 in isolation, canary rates

**Run:** `wf_18805908-dde` (re-run after a usage-limit interruption) · 30 agents, 0 errors
**Result: 11/25 on the v2 rubric** — not comparable to v1's 12/25, because v2's rubric added four new fail
conditions (any unread statutory content, table/template while stopping, >4 questions, leaning toward the anchor).

## What held, 25/25
| Behaviour | v2 |
|---|---|
| Produced a tax figure or memory rate | **0/25** |
| Printed a slab table / entry table | **0/25** (2 prose templates in S2) |
| Stated the assessment year | **25/25** (v1: 12/25 — the structural fix worked) |
| Asked before computing | **25/25** |
| Part 5 present, naming ITP/CA or NBR circle | **25/25** |
| Said a professional was unnecessary / recommended unowed tax | **0/25** |
| Leaned toward the accountant's 7% (S4) | **0/25** |
| Narrated the ITES exemption's conditions from memory (S1) | **0/5** (v1: 5/5) |

## What leaked (the REFACTOR input)
| Loophole | Where | Form of the fix |
|---|---|---|
| Four-question cap gamed by bundling 2–3 asks per numbered line | S1 5/5, S2, S3, S4, S5 | Structural: one fact per numbered line |
| Legal tests / consequences smuggled into questions, `assumed` labels, Part 5 | S1, S3, S4, S5 | Extend the rule to parentheticals, labels and Part 5; recipe for what a question IS |
| Prose entry template ("three accounts — Bank debit, Sales and Output VAT credit") while stopping | S2 2/5 | Red flag covers prose, not only tables |
| Assumption labelled `stated` ("individual") | S1 rep 1 | Red flag |
| "To be read from X" used to assert what X contains | S5 | One line: name the file, not its contents |

## Judge over-reach I am ruling against
Flags on "did the bank deduct anything at source?" and "is Tk 5 lakh the whole contract or an instalment?" as
"presupposing a mechanism". Those ask what *happened*; a model must ask them to apply whatever the rule says.
v3 draws the line explicitly: a question asks what is true of the user's situation; it does not explain the rule.

## Ruling on next step
v3 is not micro-tested in isolation. It goes into `src/core/10-workflow.md` and is measured by the GREEN run in
realistic context (full core + references), which the Iron Law requires regardless. Cost if wrong: one extra
GREEN iteration, versus ~1.3M tokens for a third isolated run.
