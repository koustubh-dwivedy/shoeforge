# STATUS — derby-plain-uk9

**Current stage:** 2 (Last generation) — IN PROGRESS (measurement engine, then template → GATE 2a)
**Next gate:** [GATE 2a] template-last silhouette review

## Stage log

### Stage 1 — Fit targets (2026-07-04) — COMPLETE (no gate)
- Artifacts: `data/sizing/uk_men.json`, `data/allowances/fit.json` (repo-level configs),
  `tools/fit_targets.py`, `last/fit_targets.json`, `last/FIT_TARGETS.md`.
- UK 9 F targets: stick 287.6 ±1.5, ball 245.4 ±2 @0.72, instep 256.9 ±2 @0.52,
  waist 241.4 ±2 @0.62, short heel 325.0 ±2, seat width 63 ±1, tread width 99 ±1,
  toe spring 8–12 (target 10), heel 25, toe-box ≥8. Foot ball girth 247.4 sits inside
  the Best & Less UK9 range (244–249) ✓.
- Open notes (carried in FIT_TARGETS.md): (a) effective toe allowance from the
  barleycorn table is ~14.1 mm vs nominal round 17 — inherent in WORKFLOW's own
  anchor numbers; table is authority; flagged for physical calibration.
  (b) instep/waist/short-heel/widths are grade-derived estimates pending calibration.

### Stage 0 — Intake & DesignSpec (2026-07-04) — COMPLETE, GATE 1 APPROVED
- Artifacts: `spec/design_spec.json` (validates OK against `tools/spec_schema.py`),
  `spec/SPEC_SUMMARY.md`
- **GATE 1 approved by user 2026-07-04** (spec as summarized; all `assumed` defaults accepted).

### Stage 0 — Intake & DesignSpec (2026-07-04)
- Artifacts: `spec/design_spec.json` (validates OK against `tools/spec_schema.py`),
  `spec/SPEC_SUMMARY.md`
- Inputs: user brief via Q&A — plain derby shakedown, UK 9 F, round toe, 25 mm heel;
  no inspiration images. Silent fields defaulted with `assumed: true`
  (black calf 1.6 mm, GYW, single leather 5 mm sole, stacked heel, burnished edges).
- Open issues: none.
- **GATE 1: awaiting human confirmation of `spec/SPEC_SUMMARY.md`** — especially
  the `assumed` rows.

## Standing context
- Pipeline authority: `WORKFLOW.md` (repo root); research: `last_creation.md`.
- Project isolation: nothing is read or reused from any prior project.
- Env: `.venv` Python 3.13 geometry stack (see `tools/ENV.md`); Blender 5.1.2
  reserved for Stage 6.
- Decisions of record: base template last will be MODELED IN-HOUSE at 25 mm
  dress pitch (no downloaded mesh) — extra review gate 2a before morphing;
  full pipeline incl. Stage 3 print engineering.
