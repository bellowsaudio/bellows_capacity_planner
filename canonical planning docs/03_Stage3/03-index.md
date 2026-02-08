# Stage 3 — Planning & Task Decomposition (INDEX)

**Project:** Bellows Capacity Planner  
**Stage:** 3  
**Status:** LOCKED  
**Depends on:**  
- Stage 1 — Inception (canonical)  
- Stage 2 — Architecture (canonical)

---

## Purpose of Stage 3

Stage 3 translates the Stage-2 architecture into **executable, testable work**.

It exists to:
- Decompose the system into atomic, verifiable tasks
- Make hidden dependencies and trust-breaking risks explicit
- Define an MVP that already tells the truth
- Prevent silent scope drift during implementation

Stage 3 introduces **no new features** and revisits **no Stage-2 decisions**.

---

## Canonical Stage-3 Artifacts

The following documents together define the complete and authoritative output of Stage 3:

1. **Epic Breakdown**  
   `03a-epic-breakdown.md`  
   Defines the stable epics and their responsibilities, mapped to Stage-2 concepts.

2. **MVP Vertical Slice**  
   `03b-mvp-vertical-slice.md`  
   Defines the smallest shippable system that preserves all “must never lie” invariants.

3. **Critical-Path Ordering**  
   `03c-critical-path-ordering.md`  
   Defines the dependency order required to build the MVP without introducing trust errors.

4. **Risk Register**  
   `03d-risk-register.md`  
   Enumerates trust-breaking failure modes and binds each to concrete mitigations.

5. **MVP Ticket Pack**  
   `03e-ticket-pack-mvp.md`  
   Provides issue-tracker-ready, atomic tickets with explicit Definitions of Done and acceptance tests.

---

## Locked Assumptions & Clarifications

The following clarifications are binding for implementation:

- **Canonical planning timezone:** GMT (DST-aware)
- **Default contractual deadline:** 17:00 US Eastern Time on the stated delivery date
- **Deadlines are moments, not dates**
- **No “bonus day” is created by post-midnight deadline moments**
- **Final window days are non-recording by default** unless explicitly converted
- **Booked projects remain bound to the PlanningParameters version active at booking**
- **Legacy data migration is out of scope** and will be handled in a later dedicated stage

---

## Immutability Statement

Once Stage 3 is locked:

- Epic boundaries must not change
- MVP scope must not expand silently
- Tickets may be reordered or split **only** within their epic
- Any change that alters scope, invariants, or assumptions requires explicit reopening of Stage 3

---

## Stage-3 Completion Declaration

Stage 3 is complete when:
- All artifacts listed above exist and are locked
- The MVP ticket pack is ready for direct execution
- Implementation can begin without reopening architectural questions

**Implementation begins in Stage 4.**
