MVP vertical slice (Stage 3)
MVP Goal

Answer, truthfully and inspectably:

“Given my committed time blocks, ledgered progress, and planning parameters, what is my required daily quota by project, what is the total daily load, and where am I infeasible (or require stretch) — without mutating anything silently?”

MVP Scope (Included)

Authoritative truth layers (must be real, not mocked):

Blocks (Time Truth)

Create/read blocks with inclusive date ranges

Enforce block types (Stage-2 list only)

Enforce hard constraint: AWAY_FROM_STUDIO excludes studio-required blocks (at minimum: INTERNAL_CORRECTIONS and PUBLISHER_CORRECTIONS_WINDOW; optionally also RECORDING_WINDOW depending on how strictly you interpret “studio-required”—but AWAY must remove recordable days regardless)

Projects (Commitments)

Minimal Project fields required to compute quotas:

id, name, status

planned_finished_hours

contract_start_date, delivery_deadline

priority (for later displacement reporting; not used to auto-move anything)

LedgerEntry (Production Truth)

Append-only ledger entries with date, project_id, finished_hours_recorded

Aggregation: recorded FH per project

DayClosure

Mark a day closed (minimal: store closure record)

Quota recomputation uses remaining FH and remaining recordable days; closure prevents “rewriting what the plan expected that day” (in MVP we can implement closure as: once closed, the day is excluded from “remaining recordable days” and actuals are what they are; no retroactive smoothing)

DayOverride (NO_RECORDING)

Per project/day override that removes that day from remaining recordable days for that project

Does not move deadlines

PlanningParameters (Versioned)

baseline_fh_per_day, stretch_fh_per_day

versioning rule: parameter edits never change existing booked plans (in MVP, enforce by attaching projects to a parameter_version at planning time)

Core computations (the “truth outputs”):
7) Remaining FH

planned_fh − sum(ledger fh)

Remaining recordable days

days in RECORDING_WINDOW

minus AWAY_FROM_STUDIO days

minus DayOverride(NO_RECORDING)

Daily quota per project

remaining_fh / remaining_recordable_days

explicit infeasible if remaining_recordable_days = 0 and remaining_fh > 0

Total daily load

sum of active project quotas per day

compare to baseline and stretch capacities (flagging only; no auto-stretch)

Reporting (inspectability, not UI):
11) Explainability trace for any quota

For a given project/day, output the numbers used:

remaining_fh, remaining_recordable_days, excluded days list (away/override), window bounds

MVP Scope (Explicitly Excluded)

These are Stage-2 features, but not required for the first shippable slice:

Scenario overlay (E7)

Slot-finding (E8)

Corrections effort estimator + default correction block sizing (E5) — except the hard constraint rule that corrections blocks must not overlap AWAY if you create them manually

Financial projections (E9)

Displacement reporting (part of later what-if insertion / slot-finding)

Any UI / calendar integration / automation plumbing

MVP “Must Never Lie” Invariants (enforced in MVP)

AWAY days are hard exclusions (cannot be treated as “still workable”)

Buffers never dilute recording quotas (SICK_BUFFER is a block type, but it must not reduce computed quotas unless it is represented as time removed from the recording window via blocks/overrides — i.e., only explicit time truths can change capacity)

Ledger is append-only

Parameter edits are non-retroactive

Infeasibility is explicit (no “best effort” hiding)

MVP Completion Criteria (what “done” means)

Given a small fixture dataset (2 projects, overlapping windows, an away day, one override, some ledger entries), the system outputs:

per-project daily quotas

per-day total load

baseline/stress flags

explicit infeasible states

explainability trace sufficient to hand-calc and verify

Potential Stage-2 Conflict to watch (callout)

DayClosure semantics: Stage-2 says “today’s quota is frozen; under/over rolls forward.” If we implement closure in MVP as “exclude closed days from remaining recordable days and recompute,” that matches roll-forward behavior but we must ensure we’re not implying the system knew the quota at the time unless we also record the “expected quota at closure time.”

If you want strict fidelity, MVP should store “quota snapshot at close.” That’s still Stage-2 compliant, but it adds a tiny bit of scope. (I’m flagging it now because future-you will care.)

By default, the final calendar day within a project window is treated as non-recording, unless explicitly converted into a recording day by removing or overriding buffers.
