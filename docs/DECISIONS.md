# Architecture Decision Log

## ADR-001: Calibration Score formula and unlock threshold
**Date:** 2026-07-19
**Status:** Accepted
**Decider:** Ricardo Roberts

### Context
Two calibration score implementations coexist: Probability Lab (live,
user-facing) computes `100*(1-2*brier)` with score visible at 5 resolved
predictions. The gamification engine computes `100*(1-brier)` with unlock
at 10. Before the engine becomes the single source of truth, one formula
must win — a silent migration would visibly change scores users already see.

### Decision
The canonical Calibration Score is **`100*(1-2*brier)`, clamped to [0, 100]**.
Score becomes **visible at 5** resolved predictions, labeled "provisional"
until **10**, at which point it is labeled "established."

### Rationale
- Honest anchor: a no-skill coin-flipper (brier = 0.25) scores 50, not 75.
  The flattering formula contradicts the product's honesfeedback brand.
- Continuity: users already see Lab-formula numbers. Changing formulas
  would shift every visible score ~25 points with no change in user behavior.
- Retention: raising the unlock 5 to 10 would re-lock scores users have
  earned. The provisional/established label captures statistical caution
  without taking anything away.
- Patent alignment: formula and thresholds match the provisional patent
  specification (Section 6, Claims 2-3). Filed as U.S. Provisional
  Application No. 64/119,278 on July 25, 2026.  specification (Section 6, Claims 2-3), filing in progress.

### Consequences
- Gamification engine's scoring adapts to the Lab formula (engine
  architecture wins; Lab formula wins).
- Migration path: dual-write on resolve, then soak/compare, then cut reads
  over behind a flag, then retire Lab aggregate writes last.
- Tests in the 119-test suite that assert `100*(1-brier)` values must be
  updated alongside the formula change (updates per this ADR, not
  regressions).
