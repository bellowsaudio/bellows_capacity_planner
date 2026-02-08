# Bellows Audio — Business Intelligence System  
## Stage 1: Inception (Problem Clarity)

---

## Purpose

Design and implement a single, trustable business intelligence system for Bellows Audio that integrates:

- Scheduling and capacity planning
- Production progress tracking
- Revenue projection and tracking
- Royalty-share prospecting and comparison

The system must preserve existing contractual commitments, reflect real production capacity, and support better decision-making when new opportunities arise while already booked.

---

## Core Problem Statement

Bellows Audio currently relies on an Excel-based scheduling and revenue system built on outdated productivity assumptions. As a result, capacity is underestimated, bookings are layered intuitively, and downtime is unclear. When a new, high-value or better-fit project arrives while “booked up,” it is difficult to know truthfully whether it fits — and if not, which existing commitment would need to be displaced.

A separate production progress system provides essential daily quotas and ETA confidence but requires manual data entry despite being largely automatable. A third, currently lapsed royalty/prospecting system exists but is disconnected from scheduling reality, making opportunity-cost comparisons difficult.

The problem is not lack of data, but lack of **integration, updated assumptions, and a single authoritative view of time, production, and commitments**.

---

## Canonical Scenario (Primary Pain Point)

> “I’m booked until September. A publisher offers a better job than some already booked work. I need to know:
> - whether it actually fits,
> - if not, what would have to give way,
> - and what the workload and financial implications would be —
> without guessing, over-optimising, or lying to future me.”

---

## Who This System Is For

- Sole user: Harry / Bellows Audio
- Single-operator business
- No collaboration, permissions, or multi-user requirements
- Transparency and inspectability matter more than polish

---

## Units of Truth

- **Finished Hours (FH)** are the primary unit of production truth.
- The key daily question is:

  > “How many finished hours must I record today to stay on track?”

- Pages, words, hours worked, and fluency metrics are **diagnostic**, not authoritative.

---

## Scheduling Philosophy

### Contract Time vs Production Time

- **Contract start dates and delivery deadlines are immutable once agreed.**
- Delivery dates must remain visible even if recording finishes early.
- Improved productivity must **not** rewrite agreed dates; it only affects daily quotas and visible slack.

---

## Recording, Corrections, and Buffers

### Recording Phase
- Daily quotas are expressed **only in finished hours (FH/day)**.
- Baseline output is the default.
- Stretch (sprint) output is optional and explicit.
- Buffers must **not** soften or dilute recording quotas.

### Corrections Phase
- Corrections are planned as a **separate block**, typically ≤ 1 day.
- Corrections occur **after recording completes**.
- Corrections time is derived from historical data:
  - CPFH (corrections per finished hour)
  - Average seconds per correction (default ~30s)
- Corrections do not affect daily recording quotas.

### Publisher Corrections Window (External Window)
Sometimes a publisher specifies an external "corrections window" (their proofer / QA period).
This window must be representable in the schedule as a visible, date-bounded constraint.

- This window is not a major time-cost driver for planning (my pre-screening via Pozotron typically leaves minimal fixes).
- However, it is a **studio-availability constraint**: I must be able to be in the studio and responsive during this window.
- Therefore, publisher correction windows must not overlap with days marked "Away from studio".
- These windows may exist in addition to my own internal corrections phase (which always occurs after recording).

### Sick-Day Buffer
- Default buffer: **1 sick day**
- Treated as a reserve day at the end of the overall process
- Not visible in daily quotas
- Not blended into productivity assumptions

---

## Planning vs Execution

### Planning-Time (Feasibility)
When assessing whether a project fits or finding a slot, total workload includes:
- Recording FH
- Corrections block
- Sick-day buffer

This protects the plan.

### Execution-Time (Daily Work)
Daily view shows:
- Required finished hours to record today
- Optional stretch target (if chosen)
- Corrections and buffers remain future blocks, not daily dilution

This keeps execution honest and psychologically legible.

---

## Sprint / Stretch Semantics

- Stretch is a **daily execution choice**, not a project-level property.
- Planning may assume that some days *might* use stretch to assess feasibility.
- On any given day:
  - Baseline is always acceptable
  - Stretch is optional
- Choosing stretch affects downstream quotas but **never changes delivery dates**.
- Overperformance is treated as a bonus, not an expectation.

---

## Booking Experiments (What-If Scenarios)

When tentatively inserting a new project, the system must show:

- Per-book daily FH quota implied
- Total required FH/day across all active projects
- Where baseline is exceeded
- Where stretch would be required
- Which days become pressure points

The system advises; the user decides.

---

## Next Available Slot Feature

The system must support:

- “Next available slot for an N-finished-hour book”
- Default assumption: baseline productivity
- Optional toggle: “What if I sprint for N weeks?”
- Output:
  - Earliest feasible start date
  - Estimated completion date
- Delivery dates remain negotiable until agreed, then lock.

---

## Decision Values (Default Priority Order)

When tradeoffs are required, the system should surface information aligned with this default hierarchy:

1. Creative / personal fit
2. Relational / reputational cost
3. Financial implications
4. Deadline risk (lowest concern, given proven sprint capacity)

The system must never optimise purely for profit.

---

## Parameter Updates and Immutability Rules

- Planning parameters (baseline FH, CPFH, correction timing, sick-day defaults) are editable.
- **Updates apply only to future or explicitly unlocked plans.**
- Existing agreed plans remain immutable unless deliberately replanned.
- Productivity baseline increases:
  - Affect future daily quotas
  - Do not rewrite delivery dates

---

## Automation Expectations

- Production progress (finished hours) should be ingestible automatically from DAW exports.
- Financial admin states (invoiced, paid, payment terms) remain manual.
- Revenue projections roll from estimates to actuals as real FH is recorded.

---

## Non-Goals

- Multi-user support
- Automatic contract renegotiation
- Enforced rest or health policing
- Perfect royalty prediction
- A “profit-maximising” scheduler

---

## Stage-1 Completion Criteria

Stage 1 is complete when:
- The system can truthfully answer “Can I take this job?”
- Daily quotas are honest and legible
- Buffers protect the plan without lying to execution
- Past-me cannot gaslight future-me

---

**Status:** Stage 1 — Inception COMPLETE
