Stage 3 — MVP Ticket Pack

Bellows Capacity Planner

EPIC E1 — Time Truth: Blocks
E1-T1 — Define canonical block types

Scope

Implement closed enum of allowed block types.

Definition of Done

Only Stage-2 block types are accepted.

Unknown types are rejected loudly.

Acceptance Test

Creating a block with HOLIDAY fails with a clear error.

Failure Modes

Silent coercion to another type

Free-text block types

E1-T2 — Inclusive date range semantics

Scope

Define and document inclusive start/end behavior for blocks.

Definition of Done

A block with start = end occupies exactly one day.

All date iteration respects inclusivity.

Acceptance Test

A 3-day window produces exactly 3 candidate days.

Failure Modes

Off-by-one errors

Mixed inclusive/exclusive logic

E1-T3 — Canonical timezone & deadline moment

Scope

Define canonical planning timezone.

Define default contractual deadline moment.

Rules

Internal planning timezone = GMT (DST-aware)

Default deadline = 17:00 US Eastern on stated date

Convert to absolute moment internally

Definition of Done

Given a delivery date, system computes correct GMT deadline moment.

DST transitions handled correctly.

Acceptance Test

Same project in winter vs summer yields different GMT deadline.

Deadline at 00:01 does not create an extra usable day.

Failure Modes

Treating deadlines as date-only

Ignoring DST

E1-T4 — Block collision detection (hard exclusions)

Scope

Detect illegal overlaps involving AWAY_FROM_STUDIO.

Definition of Done

Overlaps that violate hard rules are rejected at creation time.

No auto-resolution.

Acceptance Test

Attempt to overlap INTERNAL_CORRECTIONS with AWAY fails.

Failure Modes

Soft acceptance

Silent clipping

EPIC E6 — Project Lifecycle & Immutability
E6-T1 — Minimal project entity

Scope

Implement minimal Project fields required for MVP:

id, name, status

planned_finished_hours

contract_start_date

delivery_deadline

priority

Definition of Done

Projects can be created and referenced by blocks and ledger entries.

Acceptance Test

Ledger entry cannot reference nonexistent project.

Failure Modes

Projects owning time directly

Missing required fields

E6-T2 — Deadline immutability after booking

Scope

Enforce delivery deadline lock for BOOKED projects.

Definition of Done

Deadline cannot be auto-changed by recomputation or parameter edits.

Manual edits are explicit and logged.

Acceptance Test

Parameter change does not move booked project deadline.

Failure Modes

Silent deadline drift

“Helpful” auto-rescheduling

EPIC E2 — Production Truth: Ledger & Closure
E2-T1 — Append-only ledger enforcement

Scope

Implement ledger entries as append-only records.

Definition of Done

Entries cannot be edited or deleted.

Corrections require compensating entries.

Acceptance Test

Attempt to delete entry fails.

Failure Modes

Mutable history

Hidden overwrites

E2-T2 — Ledger aggregation by project

Scope

Compute total recorded FH per project.

Definition of Done

Remaining FH derives only from ledger sum.

Acceptance Test

Adding a ledger entry immediately changes remaining FH.

Failure Modes

Cached totals

Negative FH not flagged

E2-T3 — DayClosure semantics

Scope

Implement explicit day closure.

Rules

Closed days are excluded from future “remaining days”.

Performance rolls forward.

Definition of Done

Closing a day reduces remaining recordable days.

No retroactive smoothing.

Acceptance Test

Closing a low-output day increases future quotas.

Failure Modes

Rewriting expectations

Partial closure states

EPIC E3 — Capacity Truth: Planning Parameters
E3-T1 — PlanningParameters version model

Scope

Implement immutable parameter versions.

Fields

baseline_fh_per_day

stretch_fh_per_day

Definition of Done

New parameter version created on edit.

Old versions remain intact.

Acceptance Test

Editing baseline creates a new version.

Failure Modes

Global mutable settings

E3-T2 — Bind projects to parameter version

Scope

Associate each project with a parameter version at planning time.

Definition of Done

Booked projects do not change versions automatically.

Acceptance Test

Parameter update does not affect existing booked project quotas.

Failure Modes

Retroactive drift

Implicit replanning

EPIC E5 — Day-Level Modifiers
E5-T1 — DayOverride (NO_RECORDING)

Scope

Implement per-project NO_RECORDING override.

Definition of Done

Override removes that day from recordable days.

Does not move endpoints.

Acceptance Test

Applying override increases daily quota.

Failure Modes

Sliding deadlines

Treating override as a block

EPIC E4 — Core Capacity Computation
E4-T1 — Remaining recordable days calculation

Scope

Compute remaining recordable days per project. All day iteration is evaluated in the canonical planning timezone.

Rules

Days in RECORDING_WINDOW

Minus AWAY_FROM_STUDIO

Minus DayOverride(NO_RECORDING)

Minus closed days

Final day counted only if explicitly recordable via absence of buffers or explicit override.

Definition of Done

Correct denominator produced for quota calc.

Acceptance Test

AWAY or override removes exactly one day.

Failure Modes

Buffer softening

Off-by-one errors

E4-T2 — Remaining FH calculation

Scope

Compute remaining FH per project.

Definition of Done

planned_fh − ledger_sum

Explicit error if negative.

Acceptance Test

Over-recording flags error state.

Failure Modes

Silent negatives

E4-T3 — Daily quota per project

Scope

Compute quota_fh_per_day.

Definition of Done

quota = remaining_fh / remaining_recordable_days

Infeasible if days = 0 and FH > 0.

Acceptance Test

Zero days + FH remaining → infeasible state.

Failure Modes

Dividing by zero silently

Rounding down

E4-T4 — Total daily load aggregation

Scope

Sum quotas across projects per day.

Definition of Done

Produce per-day total load.

Flag baseline exceedance and stretch requirement.

Acceptance Test

Overlapping projects exceed baseline correctly flagged.

Failure Modes

Auto-stretch

Hiding overload

EPIC E10 — System Integrity & Trust Guards
E10-T1 — Explicit infeasibility detection

Scope

Detect and surface infeasible plans.

Definition of Done

Infeasible states are explicit and unignorable.

Acceptance Test

FH remaining with zero days → infeasible.

Failure Modes

Masking infeasibility as stretch

E10-T2 — Explainability trace

Scope

Provide full trace for any quota or infeasible state.

Trace Includes

Remaining FH

Remaining recordable days

Excluded days (away, override, closure)

Parameter version used

Deadline moment

Definition of Done

Human can reconstruct math manually.

Acceptance Test

Trace output matches hand calculation.

Failure Modes

Black-box numbers

Ticket Pack Status

✅ MVP-only

✅ All Stage-2 invariants preserved

✅ All high-risk items mitigated

✅ No UI or tooling assumptions