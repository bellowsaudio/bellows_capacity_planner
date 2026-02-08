High-Level Epic Map (Stage-2 Aligned)

Each epic maps cleanly to one or more Stage-2 concepts. No epic crosses conceptual boundaries.

Epic	Stage-2 Concept(s)
E1	Time Truth — Blocks
E2	Production Truth — Ledger & Day Closure
E3	Capacity Truth — Planning Parameters
E4	Quota Computation Engine
E5	Corrections Architecture
E6	Project Lifecycle & Immutability
E7	Scenario Overlay (What-If)
E8	Slot-Finding
E9	Financial Projection (Minimal)
E10	System Integrity & Failure Guards

We proceed one epic at a time, topologically ordered to expose hidden dependencies early.

EPIC E1 — Time Truth: Block System

Purpose: Establish the single authoritative representation of time.
Everything else derives from this. Day is evaluated in canonical timezone.

E1.1 — Define Block Type Registry

Scope
Create an explicit, closed set of block types.

Definition of Done

Block types exactly match Stage-2 list:

RECORDING_WINDOW

INTERNAL_CORRECTIONS

SICK_BUFFER

PUBLISHER_CORRECTIONS_WINDOW

AWAY_FROM_STUDIO

No additional types exist.

Acceptance Test

Attempting to create a block with an unknown type fails loudly.

Failure Modes

❌ Allowing “free-text” block types (violates Time Truth)

❌ Silent coercion to nearest valid type

E1.2 — Block Date Semantics (Inclusive Ranges)

Scope
Define and enforce inclusive start/end semantics.

Definition of Done

A block with start = end occupies exactly one day.

All downstream computations treat dates consistently.

Acceptance Test

A 1-day AWAY block removes exactly one recordable day.

A 3-day window produces exactly 3 candidate days.

Failure Modes

❌ Off-by-one errors that inflate capacity

❌ Mixed inclusive/exclusive semantics

E1.3 — Block Collision Detection (Hard Constraints)

Scope
Detect illegal overlaps without resolving them.

Definition of Done

System can detect:

Any block overlapping AWAY_FROM_STUDIO where overlap is forbidden

Publisher corrections overlapping AWAY days

Acceptance Test

Creating an overlapping block yields a clear error explaining why it’s illegal.

Failure Modes

❌ Auto-shifting blocks (forbidden by Stage-2)

❌ Silent overlap acceptance

E1.4 — Project ↔ Block Association Rules

Scope
Clarify which blocks may or may not reference a project.

Definition of Done

RECORDING_WINDOW, INTERNAL_CORRECTIONS, PUBLISHER_CORRECTIONS_WINDOW may reference a project.

SICK_BUFFER, AWAY_FROM_STUDIO may not (or must be null).

Acceptance Test

Attempting to assign a project to AWAY_FROM_STUDIO fails.

Failure Modes

❌ Time truth becoming project-owned

❌ Ambiguous ownership of “away” time

EPIC E2 — Production Truth: Ledger & Day Closure

Purpose: Ensure production truth is append-only, inspectable, and frozen correctly.

E2.1 — Ledger Entry Append-Only Enforcement

Scope
Prevent deletion or mutation of ledger entries.

Definition of Done

Ledger entries can only be added.

Any edit attempt creates a new entry with correction notes.

Acceptance Test

Attempt to edit/delete an entry fails or is recorded as a compensating entry.

Failure Modes

❌ Silent retroactive changes

❌ “Fixing” history instead of correcting it

E2.2 — Ledger Aggregation by Project

Scope
Compute total recorded FH per project.

Definition of Done

Sum of FH matches raw ledger entries.

No cached or stored totals.

Acceptance Test

Adding a new ledger entry updates remaining FH immediately.

Failure Modes

❌ Cached totals drifting from truth

❌ Negative remaining FH not detected

E2.3 — Day Closure Semantics

Scope
Define what “closing a day” means computationally.

Definition of Done

Closing a day freezes:

That day’s quota expectations

Over/under performance

Future quotas recompute from remaining FH/days.

Acceptance Test

Closing a low-output day increases future daily quotas.

Re-opening is impossible without explicit administrative action.

Failure Modes

❌ Silent retroactive quota changes

❌ Partial closure states

EPIC E3 — Capacity Truth: Planning Parameters

Purpose: Parameters exist, are versioned, and never rewrite history.

E3.1 — Parameter Versioning Model

Scope
Create immutable parameter versions.

Definition of Done

Each parameter change creates a new version.

Existing booked projects continue referencing their original version.

Acceptance Test

Changing baseline FH/day does not alter existing plans.

Failure Modes

❌ Global mutable settings

❌ Silent retroactive plan changes

E3.2 — Parameter Application Rules

Scope
Define when new parameters apply.

Definition of Done

Parameters apply only to:

New projects

Explicitly unlocked replans

Acceptance Test

Attempt to “refresh all plans” is rejected.

Failure Modes

❌ Implicit global recalculation

❌ Hidden plan drift

EPIC E4 — Quota Computation Engine

Purpose: Convert truth into numbers without lying.

E4.1 — Remaining Recordable Days Calculation

Scope
Compute remaining days correctly. Must consider deadline moment, not just date.

Definition of Done

Days counted:

Inside RECORDING_WINDOW

Minus AWAY_FROM_STUDIO

Minus DayOverride(NO_RECORDING)

Acceptance Test

Adding a corrections-only day increases quota.

Away day always reduces available days.

Failure Modes

❌ Buffers softening quotas

❌ Overlapping exclusions double-counted

E4.2 — Daily Quota Calculation

Scope
Compute quota_fh_per_day.

Definition of Done

quota = remaining_fh / remaining_recordable_days

No rounding that hides infeasibility.

Acceptance Test

If remaining days = 0 and FH > 0 → explicit infeasible state.

Failure Modes

❌ Dividing by zero silently

❌ Rounding down quotas

E4.3 — Total Daily Load Aggregation

Scope
Sum quotas across projects per day.

Definition of Done

Produces per-day load

Compared against baseline and stretch separately

Acceptance Test

A day exceeding baseline but within stretch is flagged, not blocked.

Failure Modes

❌ Automatic stretch assumption

❌ Per-project isolation hiding overload

EPIC E5 — Corrections Architecture

Purpose: Corrections consume time but never quota.

E5.1 — Corrections Effort Estimator (View-Only)

Scope
Compute estimated corrections hours.

Definition of Done

Computation visible but not actionable.

Cannot influence scheduling directly.

Acceptance Test

Changing CPFH changes estimate only.

Failure Modes

❌ Using estimate to auto-create blocks

❌ Treating estimate as authoritative

E5.2 — Corrections Block Defaults

Scope
Generate default correction blocks per rules.

Definition of Done

≤15 FH → 1 day

15 FH → 2 days

Editable manually

Acceptance Test

A 16 FH project defaults to 2 correction days.

Failure Modes

❌ Auto-resizing based on estimates

❌ Consuming quota

E5.3 — Corrections-Only Days via DayOverride

Scope
Implement NO_RECORDING override.

Definition of Done

Override reduces recordable days.

Does not move delivery dates.

Acceptance Test

Applying override increases daily quota.

Failure Modes

❌ Sliding endpoints

❌ Treating override as a block

EPIC E6 — Project Lifecycle & Immutability

Purpose: Prevent silent plan corruption.

E6.1 — Project Status Transitions

Scope
Define legal state transitions.

Definition of Done

Illegal transitions are rejected.

BOOKED → locks apply.

Acceptance Test

BOOKED project cannot auto-change deadline.

Failure Modes

❌ Soft enforcement

❌ Status used as UI hint only

E6.2 — Deadline Lock Enforcement

Scope
Lock delivery deadline post-booking.

Definition of Done

Deadline immutable unless manually edited.

No auto-moves from recomputation.

Acceptance Test

Parameter change does not move deadline.

Failure Modes

❌ Deadline drift

❌ “Helpful” rescheduling

EPIC E7 — Scenario Overlay (What-If)

Purpose: Explore without mutating truth.

E7.1 — Scenario Isolation

Scope
Ensure scenarios never mutate base state.

Definition of Done

Scenario holds its own blocks, projects, overrides.

Acceptance Test

Discarding scenario leaves base untouched.

Failure Modes

❌ Shared object references

❌ Partial leakage

E7.2 — Scenario Recompute Engine

Scope
Recompute quotas and loads inside scenario.

Definition of Done

Outputs baseline exceedance, stretch needs, infeasible days.

Acceptance Test

Removing scenario restores original metrics.

Failure Modes

❌ Cached base results reused

❌ Auto-resolution of conflicts

EPIC E8 — Slot-Finding

Purpose: Answer “when could this fit?” honestly.

E8.1 — Slot-Finding Core Algorithm

Scope
Search future windows for N-FH fit.

Definition of Done

Considers:

Recording window

Corrections

Sick buffer

Hard constraints

Acceptance Test

Returns earliest feasible window or explicit “none”.

Failure Modes

❌ Ignoring buffers

❌ Forcing stretch silently

E8.2 — Displacement Reporting

Scope
Identify what would be displaced.

Definition of Done

Lists candidate displaced projects by priority.

Never auto-removes anything.

Acceptance Test

VITAL projects are flagged distinctly.

Failure Modes

❌ Auto-reordering

❌ Priority ignored

EPIC E9 — Financial Projection (Minimal)

Purpose: Answer sufficiency, not optimise income.

E9.1 — Flat Fee Projection

Scope
Project expected payment dates.

Definition of Done

Currency preserved.

GBP shown via planning rate.

Acceptance Test

Changing FX rate does not alter stored amounts.

Failure Modes

❌ Overwriting original currency

❌ Treating estimates as cash

E9.2 — Royalty Timeline Model

Scope
Model royalty delay stages.

Definition of Done

Completion → QA → Release → Payment.

All dates inspectable.

Acceptance Test

Shifting release shifts payment accordingly.

Failure Modes

❌ Single magic date

❌ Pretending royalties are predictable

EPIC E10 — System Integrity & Trust Guards

Purpose: Make lying impossible.

E10.1 — Infeasibility Detection

Scope
Explicitly represent infeasible states.

Definition of Done that doesn't count a deadline moment slipping into next day as a 'ghost day'.

System can say “this cannot be done”.

Acceptance Test

Zero remaining days with FH remaining produces infeasible flag.

Failure Modes

❌ Fallback heuristics

❌ Pretending stretch fixes everything

E10.2 — Auditability Hooks

Scope
Ensure every derived number can be traced.

Definition of Done

For any quota, system can list:

Remaining FH

Remaining days

Overrides applied

Acceptance Test

Human can reconstruct math manually.

Failure Modes

❌ Black-box outputs

❌ Cached mystery numbers