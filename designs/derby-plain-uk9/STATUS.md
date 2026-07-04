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
- GATE 2a round 1 feedback (2026-07-04): top view "looks like a duck"; user
  wants 3D review; user supplied ref_top.jpg / ref_side.jpg (stored in
  `data/templates/lasts/round_25mm/reference/` — used per the workflow's
  classification-not-reconstruction philosophy, here as qualitative
  silhouette references).
- Round 2 (v11): midfoot widths raised so width builds continuously heel→ball
  (arch ~75-80% of ball width, lateral edge one convex sweep — matched to
  ref_top); crowns lowered to hold girths (wide/low arch saddle); forepart
  keeps width longer; vamp break smoother. All primary girths remain IN
  TOLERANCE. New: `template_view.blend` (open in Blender to orbit in 3D;
  generated each build by `tools/make_viewer_blend.py`; ground plane = z0).
- Open issues:
  1. Short-heel girth target (ratio-estimate 1.33×ball, flat foot) does not
     model the 25 mm-pitch effect; measured 347.7 (1.42×ball) is plausible for
     a pitched last. Flagged for physical calibration; NOT chased by loosening
     tolerances (standing rule).
- Round 3 (v13), responding to user Q4-Q6: (Q4) asymmetry strengthened —
  lateral joint peak moved posterior (0.70) of medial (0.74), toe apex offset
  medial (y=-4), medial arch cut deeper; left last = mirror of right (standard
  practice, applied at print/pattern time). (Q5) `data/templates/lasts/METHOD.md`
  documents the parametrization: classical cross-section lofting + template
  morphing + SATRA-style validation, parameter vocabulary mapped 1:1 to
  3DShoemaker's; in-house surface construction only where commercial tools are
  proprietary; external/purchased templates remain drop-in compatible.
  (Q6) `tools/ref_overlay.py` extracts reference silhouettes (PCA-aligned,
  sole-overhang-corrected, mirrored to right frame) and overlays them on
  template curves → `reference/overlay.png`; toe made fuller/squarer per
  overlay; gap now mostly within sole-overhang uncertainty. All fit-critical
  measurements remain IN TOLERANCE (ball 244.1, waist 240.7, instep 257.5,
  tread 98.5, seat 63.0, heel 24.2, spring 9.5, toe-box 18.0).
- Round 4 (v14-v16), user directives: (1) parameter audit vs last_params.md —
  registry in `data/templates/lasts/DECISIONS.md`; implemented: joint-anchored
  OBLIQUE ball line (medial 0.69/lateral 0.63 of foot; replaces 0.72-of-stick),
  re-derived stations (instep 0.4755, waist 0.5516 of stick), long-heel girth
  (report-only), toe flare/inflare (`centerline_shift_y`), quadrant wall bias
  (`dome_asym`), functional length + toe extension, insert depth, decomposed
  girth allowances, Cheaney 125 cross-anchor (OPEN ITEM), extra reported
  measures (waist/backpart width, heel pitch, wedge angle, cone peak).
  Short-heel immediately improved 347→329 vs 325 estimate. (2) LSQ style-zone
  fit implemented (`tools/lsq_fit.py`) and run: RMS ref-gap 9.9→3.0 mm; ref
  sole handedness determined from joint anatomy (no mirror); side-view datum
  fitted as nuisance scalar; post-fit girth re-validation caught+fixed a ball
  overread (vamp-break hollow); fit/style junction faired. (3) Master file:
  `data/templates/lasts/DECISIONS.md`.
- Fit-critical after LSQ (v16): ball 245.1 ✓, waist 241.5 ✓, instep 256.7 ✓,
  tread 98.8 ✓, seat 63.0 ✓, heel 24.2 ✓, spring 10.0 ✓, toe-box 24.6 ✓,
  short-heel 329.0 (estimate 325, Δ+4 — calibration item).
- Round 5 (v17), user feedback: (1) pointed nose/heel tips — root cause: fan
  closure to a tip vertex over near-linear outline tails; fixed with
  circular-arc closure points + cosine section spacing (DECISIONS.md #11).
  (2) side-profile distortion / "fit the entire part" — whole-profile LSQ
  attempted (two-region masks, per-region fitted datum offsets, single
  cone-scale DOF, smoothness regularizer): the toe/vamp fit converged and is
  KEPT (RMS 7.1→3.2 mm); the cone/lace region proved UNIDENTIFIABLE (cone
  height collinear with tongue/lace stack; both ran to bounds) and dragged
  fit-critical instep + short-heel girths out — cone reverted to
  girth-constrained values, decision recorded (DECISIONS.md #10). Frozen
  crown anchor at 0.67 added so toe-box styling can't leak into the ball
  girth zone.
- Fit-critical (v17): ball 244.2 ✓, waist 241.8 ✓, instep 256.7 ✓, short-heel
  329.0 (est. 325), tread 98.5 ✓, seat 63.0 ✓, heel 24.2 ✓, spring 10.0 ✓,
  toe-box 24.6 ✓. Watertight ✓.
- **GATE 2a (round 5): awaiting human review** — template_view.blend,
  mock/mock_view.blend, snapshots/, reference/overlay.png, LSQ_REPORT.md,
  TEMPLATE_REPORT.md.

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
