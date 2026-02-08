Stage 3 — Critical-Path Ordering (MVP)
Principle Used

Truth must exist before computation.
Computation must exist before advice.
Guards must exist before convenience.

Anything that can silently corrupt trust is pulled earlier than feels comfortable.

Phase 0 — Precondition (Conceptual, Not a Build Step)

Assumption locked:

Stage-2 architecture is canonical

MVP scope is locked

Booked-under-old-assumptions rule is acknowledged

No work happens here; this is just the “we don’t reopen this” marker.

Phase 1 — Time Truth (Absolute First)

If time lies, everything lies.

1. Block Type Registry

(E1.1)

Why first:

Every later computation depends on block semantics

If block types are fuzzy, exclusions will leak

Must exist before:

any date math

any quota logic

any override logic

Deadline moment evaluated in canonical timezone

2. Block Date Semantics (Inclusive Ranges)

(E1.2)

Why now:

Off-by-one errors are the most dangerous silent failure

Fixing this later rewrites all downstream math

Hard requirement before:

remaining recordable days

quota calculation

infeasibility detection

3. Block Collision Detection (Hard Constraints)

(E1.3)

Why this early:

Prevents illegal states from ever entering the system

Especially: AWAY_FROM_STUDIO overlaps

Important:

This is detection only, not resolution

No auto-movement, no healing

Phase 2 — Commitments & Immutability

You can’t compute capacity until you know what’s locked.

4. Minimal Project Entity + Status Rules

(E6.1, partial)

Includes:

Project identity

planned_finished_hours

contract start / delivery deadline

status (BOOKED matters)

Why here:

Parameter binding depends on booking state

Ledger entries need a valid project

5. Deadline Lock Enforcement

(E6.2)

Why before parameters:

Prevents “helpful recomputation” later

Makes old bad assumptions visible instead of corrected

This must exist before:

any quota recomputation logic

any parameter changes are allowed

Phase 3 — Production Truth

Reality enters the system here. It must never be rewritten.

6. Ledger Append-Only Enforcement

(E2.1)

Why now:

Ledger is the only source of production truth

If this is mutable, quotas become fiction

Must be in place before:

remaining FH

day closure

any “roll-forward” behavior

7. Ledger Aggregation (Recorded FH per Project)

(E2.2)

Why here:

Remaining FH is the first derived number

Everything else stacks on top of it

Phase 4 — Planning Parameters (Versioned)

This is where old assumptions and new assumptions safely coexist.

8. PlanningParameters Version Model

(E3.1)

Includes:

baseline_fh_per_day

stretch_fh_per_day

immutable versions

Why before quota math:

Quotas must know which assumptions they’re bound to

Prevents retroactive recalculation bugs

9. Parameter Binding to Projects

(E3.2)

Why critical:

This is what makes “booked under old assumptions” safe

Without this, parameter edits become silent rewrites

Hard rule enforced here:

Booked projects do not change parameter version unless explicitly unlocked

Phase 5 — Day-Level Truth Modifiers

These change capacity, not time bounds.

10. DayOverride (NO_RECORDING)

(E5.3)

Why before quotas:

Overrides remove recordable days

Quotas must see the reduced denominator

Important:

Overrides do not move endpoints

Overrides do not consume quota

11. DayClosure

(E2.3)

Why here:

Closure freezes history and forces roll-forward

Needs ledger + parameters + overrides already defined

Note:

This is where we must be careful not to “rewrite expectations”

If we snapshot quota at closure, that snapshot logic belongs here

Phase 6 — Core Capacity Computation

Only now is it safe to do math.

12. Remaining Recordable Days

(E4.1)

Depends on:

Blocks

AWAY exclusions

DayOverrides

DayClosure (closed days excluded from future)

This is the denominator of truth. Evaluated in local timezone, consider deadline moment, not just date.

13. Remaining FH

(E4.1 / 5.1)

Simple, but critical:

planned_fh − ledger sum

Must never go negative silently

14. Daily Quota per Project

(E4.2)

Why now:

All inputs are finally stable

Any infeasibility can be stated honestly

Explicit outcomes:

quota number

OR infeasible state (zero days, FH remaining)

Phase 7 — Load & Stress Visibility

The system stops advising and starts warning.

15. Total Daily Load Aggregation

(E4.3)

Produces:

per-day total load

baseline exceedance flags

stretch-required flags (advisory only)

No auto-stretch. Ever.

Phase 8 — Trust Guards (Interleaved but Finalised)

These don’t add features — they prevent lies.

16. Infeasibility Detection

(E10.1)

Hard failures:

FH remaining, no recordable days

AWAY overlaps causing zero capacity

Locked deadline with impossible quotas

Must be explicit and unignorable. Doesn't count 'ghost day' when deadline moment slips into next date without reasonable opportunity for work in the canonical planning timezone.

17. Explainability Trace

(E10.2)

Why this closes the MVP:

Makes the system auditable

Lets human verify with pen and paper

If this exists:

trust is preserved

future extensions are safe

First Runnable, Truth-Telling State (Important Milestone)

After Step 14, you already have:

Locked time

Immutable commitments

Real production truth

Honest quotas

Explicit infeasibility

Everything after that improves visibility, not truth.

Why this ordering matters

This sequence prevents:

retroactive parameter drift

buffer-softened quotas

AWAY days being “kind of workable”

ledger edits rewriting history

old assumptions being silently “fixed”

It ensures that when Stage 4 starts, any partial implementation already tells the truth, even if it’s ugly.

Next Stage-3 step

If you’re happy with this ordering, the final Stage-3 deliverables are straightforward:

Risk register (mapped directly to these steps)

Issue-tracker-ready ticket pack (for MVP only)

Once those are done, you can cleanly declare:

Stage 3 complete. Proceed to Stage 4: Implementation.