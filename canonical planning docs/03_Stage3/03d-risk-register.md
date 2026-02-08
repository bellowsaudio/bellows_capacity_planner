Stage 3 — Risk Register (MVP)

Purpose:
Identify trust-breaking failure modes early, name them explicitly, and bind each to concrete mitigations in the MVP plan.

Framing rule:
If this risk occurs, would future-you feel misled rather than merely inconvenienced?
If yes, it belongs here.

R1 — Off-by-One Day Errors (Inclusive / Exclusive Confusion)

Description
Miscounting days in blocks or windows (e.g. treating start/end inconsistently) creates phantom capacity or phantom infeasibility.

Impact

Inflated remaining recordable days

Artificially low quotas

Missed deadline risk hidden until too late

Where It Can Occur

Block date semantics

Remaining recordable days calculation

Deadline-day interpretation

Mitigation

Canonical rule: all blocks use inclusive start/end

Deadline evaluated as a moment, not a date

Midnight boundary rule explicitly enforced (no bonus days)

Bound To

E1.2 — Block Date Semantics

E1.x — Canonical Timezone & Deadline Moment

E4.1 — Remaining Recordable Days

Acceptable in MVP?
❌ No. Must be eliminated.

R2 — Timezone / DST Drift

Description
Incorrect conversion between US Eastern deadlines and UK working days, especially around DST transitions, silently adds or removes a usable day.

Impact

Planner disagrees with real-world calendar

False feasibility or false panic

Particularly dangerous near deadlines

Where It Can Occur

Deadline moment calculation

“Last recordable day” logic

Mitigation

Single canonical planning timezone (GMT, DST-aware)

Deadlines stored as absolute moments

No date-only deadlines internally

Bound To

E1.x — Canonical Timezone & Deadline Moment

E10.1 — Infeasibility Detection (deadline-day misclassification)

Acceptable in MVP?
❌ No. Must be eliminated.

R3 — AWAY_FROM_STUDIO Softened or Ignored

Description
AWAY days accidentally treated as “low capacity” instead of zero capacity, or overridden implicitly.

Impact

System claims feasibility when recording is physically impossible

Violates “must never lie” rule

Where It Can Occur

Block overlap handling

Remaining recordable days computation

Mitigation

AWAY is a hard exclusion

No auto-override, no partial credit

Illegal overlaps rejected at creation time

Bound To

E1.3 — Block Collision Detection

E4.1 — Remaining Recordable Days

Acceptable in MVP?
❌ No.

R4 — Buffers Quietly Diluting Quotas

Description
Sick buffers or corrections time implicitly reduce daily quotas rather than removing days explicitly.

Impact

Quotas look comfortable when they shouldn’t

Execution pressure hidden

Where It Can Occur

Corrections handling

Final-day logic

Misuse of “buffer” as soft time

Mitigation

Buffers only affect capacity if represented as:

blocks, or

DayOverride(NO_RECORDING)

No other mechanism may change denominators

Bound To

E5.3 — DayOverride (NO_RECORDING)

E4.1 — Remaining Recordable Days

Acceptable in MVP?
❌ No.

R5 — Retroactive Parameter Drift

Description
Changing baseline FH/day or stretch assumptions silently alters quotas for already-booked projects.

Impact

Old plans rewritten without consent

Loss of auditability

Confusion about why numbers changed

Where It Can Occur

Parameter edits

Quota recomputation

Mitigation

Immutable PlanningParameters versions

Explicit binding of projects to parameter version

Replanning requires deliberate unlock

Bound To

E3.1 — Parameter Version Model

E3.2 — Parameter Binding to Projects

Acceptable in MVP?
❌ No.

R6 — Ledger Mutability / History Rewrites

Description
Ledger entries edited or deleted instead of corrected via append-only records.

Impact

Production truth becomes fictional

Past performance rewritten to fit plans

Where It Can Occur

Ledger CRUD operations

Data cleanup

Mitigation

Append-only ledger

Corrections handled via compensating entries

Clear source tagging

Bound To

E2.1 — Ledger Append-Only Enforcement

Acceptable in MVP?
❌ No.

R7 — Day Closure Rewrites Expectations

Description
Closing a day retroactively changes what the system “expected” that day, instead of rolling forward.

Impact

Loss of accountability

Quotas feel unstable or revisionist

Where It Can Occur

DayClosure implementation

Quota recomputation logic

Mitigation

Closed days excluded from future calculations

(Optional but recommended) snapshot expected quota at closure

Bound To

E2.3 — DayClosure

E10.2 — Explainability Trace

Acceptable in MVP?
⚠️ Partially — snapshotting can be deferred if roll-forward behavior is explicit and inspectable.

R8 — Infeasibility Masked as Stretch

Description
System treats impossible plans as merely “high stretch” instead of explicitly infeasible.

Impact

False reassurance

Late failure discovery

Where It Can Occur

Quota calculation

Load aggregation

Mitigation

Explicit infeasible state:

remaining FH > 0

remaining recordable days = 0

Stretch never resolves infeasibility

Bound To

E4.2 — Daily Quota Calculation

E10.1 — Infeasibility Detection

Acceptable in MVP?
❌ No.

R9 — Scenario Leakage into Base Plan

(Low risk in MVP, but named early)

Description
What-if computations mutate committed state.

Impact

Trust collapse

Hard-to-trace plan corruption

Mitigation

Full isolation of scenario data

No shared references

Bound To

(Future) E7 — Scenario Overlay

Acceptable in MVP?
✅ Acceptable to defer, since scenarios are excluded from MVP.

R10 — Opaque Numbers (No Explainability)

Description
User cannot reconstruct how a quota or infeasibility was computed.

Impact

Distrust

Over-reliance or abandonment of system

Where It Can Occur

Aggregated outputs

Cached results

Mitigation

Explainability trace for every derived number:

inputs

exclusions

parameter version

Bound To

E10.2 — Explainability Trace

Acceptable in MVP?
❌ No.

Risk Register Summary

Non-negotiable to eliminate in MVP:

R1, R2, R3, R4, R5, R6, R8, R10

Conditionally acceptable / deferrable:

R7 (quota snapshot nuance)

R9 (scenarios, explicitly out of MVP)