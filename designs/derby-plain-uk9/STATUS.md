# STATUS — derby-plain-uk9

**Current stage:** 2 (Last generation) — template built, **holding at [GATE 2a]**
**Next:** on approval → S2.3 morph + S2.4 validation loop → GATE 2b (fit report)

## Stage log

### Stage 2 (part 1) — measurement engine + base template (2026-07-04) — GATE 2a PENDING
- `tools/last_measure.py`: snug-tape metrology (convex-hull planar sections,
  min-tape sweeps; waist and short-heel are DEFINED near-fixed-plane measures —
  conventions documented in the module docstring). Ground-truth tests vs analytic
  solids: ALL PASS at ≤0.015% error (`tools/tests/test_last_measure.py`).
- `tools/template_last_builder.py` + `data/templates/lasts/round_25mm/`:
  in-house round-toe template, RIGHT last, built natively at 25 mm pitch,
  UK 9 F dimensions. Watertight, 18k faces, feather edge a true hard crease.
  7 build iterations (girth tuning, vamp-break softening, waist→joint outline
  smoothing, toe blunting).
- Measurements vs targets: stick/ball/waist/instep/tread/seat/heel-height/
  toe-spring/toe-box ALL IN TOLERANCE. Short-heel reads 345.9 vs soft target
  325 — see open issues.
- Open issues:
  1. Short-heel girth target (ratio-estimate 1.33×ball, flat foot) does not
     model the 25 mm-pitch effect; measured 345.9 (1.41×ball) is plausible for
     a pitched last. Flagged for physical calibration; NOT chased by loosening
     tolerances (standing rule).
  2. Aesthetic v1 limits (for human eyes at the gate): vamp-break descent is
     pronounced; slight facet line at the joint in the top view; back curve
     fairly upright; heel asymmetry mild.
- **GATE 2a: awaiting human review of silhouettes**
  (`data/templates/lasts/round_25mm/snapshots/` + `TEMPLATE_REPORT.md`).

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
