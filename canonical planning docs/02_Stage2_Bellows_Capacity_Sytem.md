# Bellows Capacity Planner  
## Stage 2 — Architecture (Deliberate Minimalism)

**Status:** COMPLETE  
**Depends on:** Stage 1 — Inception (Canonical)  
**Purpose of Stage 2:**  
Define the smallest possible conceptual system that can truthfully answer:

> “Given real constraints and capacity, can I take this job — and if not, what must give way?”

No implementation, no tools, no UI decisions.  
Only entities, state, computations, and invariants.

---

## 1. System Boundary

### 1.1 Inside Scope (Stage 2)

Bellows Capacity Planner consists of four conceptual layers:

1. **Time Truth**
   - A single, authoritative schedule composed of date-bounded blocks
   - Day-level resolution, scrollable arbitrarily far into the future

2. **Production Truth**
   - Finished Hours (FH) as the unit of record
   - Append-only progress ledger
   - Daily closure semantics (“today is done”)

3. **Capacity Truth**
   - Baseline FH/day
   - Optional stretch FH/day (execution choice)
   - Versioned planning parameters

4. **Advisory Modeling**
   - What-if booking experiments
   - Stretch simulations
   - Displacement visibility (never automatic)

A lightweight **financial projection layer** is included only to the extent needed
to answer: *“Is this enough work / income?”*

---

### 1.2 Explicitly Out of Scope

- UI design, calendars, databases
- Automation plumbing or integrations
- Multi-user features
- Profit-optimising schedulers
- Perfect royalty prediction
- Enforced rest or health rules

The system advises; the human decides.

---

## 2. Core Entities and State Ownership

### 2.1 Project

Represents a contractual or prospective commitment.

**Key fields**
- `project_id`
- `name`
- `status`  
  (`PROSPECT | TENTATIVE | BOOKED | IN_PROGRESS | RECORDED | DELIVERED | ARCHIVED`)
- `priority`  
  (`VITAL | NEGOTIABLE`)
- `contract_start_date`
- `delivery_deadline` *(computationally immutable once booked; manually editable)*
- `planned_finished_hours`
- `estimated_total_pages` (optional)
- `estimated_total_fh_override` (optional)
- `rate`, `billing_type`, `currency`

**Responsibilities**
- Holds commitments and assumptions
- Does **not** own time directly (blocks do)
- Does **not** decide stretch or daily quotas

---

### 2.2 Block (Authoritative Time Model)

All time commitments are expressed as blocks.

**Fields**
- `block_id`
- `type`
- `start_date`, `end_date` (inclusive)
- `project_id` (nullable)
- `notes`

**Block types**
- `RECORDING_WINDOW`
- `INTERNAL_CORRECTIONS`
- `SICK_BUFFER`
- `PUBLISHER_CORRECTIONS_WINDOW`
- `AWAY_FROM_STUDIO`

**Rules**
- Blocks are the *only* truth of time being spoken for
- Recording quotas are derived from blocks; never softened by buffers

---

### 2.3 LedgerEntry (Production Truth)

Append-only record of work completed.

**Fields**
- `date`
- `project_id`
- `finished_hours_recorded`
- optional: `pages_completed`
- `source` (manual / imported)

Ledger entries are never deleted.

---

### 2.4 DayClosure

Explicitly marks a day as complete.

**Fields**
- `date`
- `closed_at`
- `notes`

Once closed:
- Today’s quota is frozen
- Any under/over-performance rolls forward into remaining days

---

### 2.5 DayOverride (Minimal but Crucial)

Allows re-classification of specific days *per project*.

**Fields**
- `date`
- `project_id`
- `mode`
  - `NORMAL`
  - `NO_RECORDING`
- `reason` (optional)

**Purpose**
- Convert a recording day into a corrections-only or admin day
- Reduce remaining recordable days
- Recompute quotas backward through the window
- Endpoints never move

Stretch remains available on all remaining days.

---

### 2.6 PlanningParameters (Versioned)

Planning assumptions, never silently retroactive.

**Core parameters**
- `baseline_fh_per_day`
- `stretch_fh_per_day`
- `cpfh` (corrections per finished hour)
- `seconds_per_correction`
- `default_sick_buffer_days`
- `usd_to_gbp_planning_rate`

Updates apply only to:
- new plans
- or explicitly unlocked/replanned projects

---

### 2.7 Scenario (What-If Overlay)

A scenario is an overlay on the committed plan.

**Contains**
- Tentative projects
- Provisional blocks
- Assumed stretch days
- Optional DayOverrides

Scenarios recompute everything but mutate nothing.

---

## 3. Length Estimation (Two-Track Model)

### 3.1 Authoritative Track (FH-based)
- Initial estimate from wordcount
- Manually overridable if proven wrong
- Used for all quota calculations

### 3.2 Diagnostic Track (Pages-based)
- Derived from:
  - `recorded_fh / pages_completed`
- Produces:
  - estimated total FH
  - estimated remaining FH
- Shown side-by-side for confidence checking
- Never auto-replaces authoritative estimate

---

## 4. Corrections Architecture

### 4.1 Corrections Effort (Computed, View-Only)
- `estimated_corrections_hours = FH × CPFH × seconds_per_fix`

This number informs judgement only.

### 4.2 Corrections Blocks (Authoritative for Time)
- Default:
  - ≤15 FH → 1 day
  - >15 FH → 2 days
- Editable per project
- Studio-required but **not quota-consuming**
- May overlap other projects’ recording days
- Must not overlap `AWAY_FROM_STUDIO`

### 4.3 Corrections-Only Days Inside Recording
- Achieved via `DayOverride(NO_RECORDING)`
- Reduces recordable days
- Raises quotas accordingly
- Does not move delivery dates

---

## 5. Core Computations (Conceptual)

### 5.1 Remaining Work
remaining_fh = planned_fh - sum(ledger.fh)


### 5.2 Remaining Recordable Days
For a project:
- days in `RECORDING_WINDOW`
- minus `AWAY_FROM_STUDIO`
- minus `DayOverride(NO_RECORDING)`

### 5.3 Daily Quota
quota_fh_per_day = remaining_fh / remaining_recordable_days


### 5.4 Total Daily Load
Sum quotas across all active projects per day.

Compare against:
- baseline capacity
- stretch capacity (if assumed or performed)

---

### 5.5 Slot-Finding (N-FH Book)
Find earliest future window where:
- N FH fits at baseline (or optional sprint)
- corrections + sick buffer also fit
- no hard constraint collisions

Outputs:
- earliest feasible start
- estimated recording completion
- estimated plan completion

---

### 5.6 What-If Insertion
On insertion:
- recompute quotas
- show:
  - baseline exceedance
  - stretch requirement
  - hard infeasible days
- surface candidate displaced projects by priority
- never auto-move anything

---

## 6. Stretch Semantics

- Stretch is a **daily execution choice**
- Not a project attribute
- Planning may *assume* stretch on selected days
- Execution records actual stretch via ledger
- Stretch never rewrites deadlines

---

## 7. Financial Projection (Minimal, Inspectable)

### 7.1 Flat / PFH Projects
- Manual invoice date
- Per-project payment terms
- Derived expected payment date
- Currency preserved; GBP shown via planning rate

### 7.2 Royalty Share Projects
Timeline:
1. Audiobook completed (manual)
2. QA approval (~10 working days)
3. Release date
4. First payment = release + 1 month

Uses:
- manual lifetime revenue estimate
- reusable revenue profile (front-loaded, long tail)
- monthly cashflow projection

### 7.3 CashEvent (Non-Scheduled Income)
Quick manual entries:
- `date_paid`
- `amount`
- `currency`
- optional project link

### 7.4 Reporting Frames
- Calendar year
- UK tax year (April–April)
- Rolling 12 months

---

## 8. Immutability Rules

### 8.1 When a Project Is Booked
- Contract start date locks
- Delivery deadline locks against automatic change
- Core blocks lock
- Parameter updates do not retroactively apply

### 8.2 Explicit Replanning
- Requires deliberate unlock
- Produces a new plan version
- Never silent

### 8.3 Archival
- Projects are archived, never deleted
- Ledger history is preserved
- Default views show active projects only

---

## 9. Failure Modes

### Must Never Happen
- Feasible plans that overlap AWAY days
- Publisher windows overlapping AWAY days
- Buffers diluting recording quotas
- Silent date changes due to parameter edits
- Currency amounts overwritten by conversion

### Acceptable Imperfections
- Coarse corrections estimates
- Approximate royalty projections
- Day-level (not hour-level) planning

---

## 10. Stage 2 Completion Statement

Stage 2 is complete when:

- Time is represented only as explicit blocks
- Production truth flows only from the ledger
- Quotas are always derivable, inspectable, and honest
- Stretch is explicit and reversible
- Buffers protect plans without lying to execution
- Nothing important changes silently

**Ready for Stage 3: Planning & Task Decomposition.**
