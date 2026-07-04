# Last-Making Decisions of Record — MASTER FILE

Single source of truth for how lasts are parameterized, measured, and fitted
in this repo. **Read this before designing any new last or template — these
decisions are settled and are not revisited without a new human directive.**
Companion: `METHOD.md` (technique provenance / 3DShoemaker mapping),
`last_params.md` at repo root (the research PRD this registry audits against).

## 1. Parameter registry (audited against last_params.md, 2026-07-04)

Status legend: **L1** = design-level fit parameter (sizing/allowances →
fit_targets.json) · **L2** = template shape control (shape_params.json) ·
**REP** = measured & reported, no hard target · **CFG** = config flag ·
**EXCL** = excluded (reason given) · **DEF** = deferred.

| last_params.md parameter | Status | Where / note |
|---|---|---|
| Heel point, toe point, featherline, seat, waist, cone | L2 | landmarks.json + shape curves |
| Ball/joint points (1st & 5th MPJ, medial 69% / lateral 63% of foot) | **L1** | sizing json `stations`; oblique joint line (Decision #2) |
| Ball-line point (41% across) | CFG | recorded in sizing json; used when foot tracings arrive (bespoke) |
| Instep point (middle cuneiform ≈ 50% foot) | L1 | sizing json |
| Vamp point / throat | DEF | pattern-making landmark → Stage 5 style YAML |
| Last length (full/stick) | L1 | barleycorn table |
| Functional length + stylistic toe extension | L1 | fit_targets `functional_length_mm`, `toe_extension_mm` |
| Stick length (traditional flat-along-ground def.) | REP | our stick = X-extent in shod pose; equivalent, documented |
| Arch (heel-to-ball) length | L1 | implied by joint stations |
| Ball girth (oblique joint plane) | L1 | measured via `joint_plane_girth` |
| Waist girth | L1 | near-vertical station ±8° (Decision #3) |
| Instep girth | L1 | min-tape sweep 0–45° |
| Short heel girth | L1 (estimate-class) | rear-seat→instep-crown plane (Decision #4) |
| Long heel girth | REP | rear-seat→cone-peak plane; foot relation long=short+40–46 does NOT transfer to a cone-truncated last (Decision #4) |
| Ankle girth + malleolus height | EXCL | boots only; N/A for dress shoe; add when a boot template exists |
| Ball width / tread width | L1 | caliper across the joint line |
| Waist width | REP | from feather outline |
| Heel-seat width | L1 | station 0.17 |
| Backpart width | REP | outline width at 0.10 |
| Heel height | L1 | native to each template (Decision #5) |
| Heel pitch (seat slope) | REP | degrees over seat region |
| Toe spring | L1 | sole-linked rule |
| Wedge angle | REP | derived seat→tread line |
| Toe box height | L1 floor + REP | ≥8 mm over toes; measured at toe line |
| Instep/cone heights (back-cone, front-cone caps) | L2 | `top_profile_z` control points; cone peak reported |
| Instep-girth fill-up | L1 | in allowances (net values; decomposition documented) |
| Backseam / topline heights | DEF | Stage 5 style templates (upper, not last) |
| Feather-edge type (hard 90° for GYW) | CFG | `feather_edge: hard_90` |
| Feather-edge girth allowance | L1 | decomposition note in fit.json |
| Bottom flat vs foot-shaped | CFG | `bottom_style: flat_cambered` + `bottom_camber_mm` |
| Bottom profile / rocker | L2 | `bottom_profile_z` |
| Heel curve (rear profile) | L2 + REP | emergent from control curves; `back_curve()` reports it |
| Toe flare / swing (inflare) | **L2 (new)** | `centerline_shift_y`; inflare-only bound in LSQ |
| Seat docking correction | DEF | bespoke-only small length correction; note in sizing json when bespoke mode lands |
| Insert/insole depth | L1 | fit.json `insert_depth_mm` (0.5 default) |
| Girth cross-section curves | L2 | the section loft itself |
| Wall quadrants (4-quadrant bias) | **L2 (new)** | `dome_asym` (per-side wall fullness) + `crown_shift_y` + `dome_power` — together give quadrant-level control |
| Body wall / toe wall curves | L2 | covered by `dome_power` + `top_profile_z` locality |
| Cap (ridge) heights | L2 | `top_profile_z` points |
| Clipping-plane inspection | tool | `snapshots/sections.png` plates |
| CV grid density | L2 | `mesh` block |
| NURBS sole/upper/top decomposition | EXCL | implementation-specific to Rhino-class tools; our dense analytic loft with feather crease is the equivalent (METHOD.md) |
| Curvature-continuity (zebra) gate | DEF | add to Stage 3 print QA as automated fairness check |
| Size & width indices, grading, allowances | L1 | sizing + allowances json |
| Cheaney 125 anchor | CFG | `cross_check_cheaney_125` in sizing json — see Open Items |

## 2. Decisions of record

1. **Architecture**: in-house template built by dense analytic cross-section
   lofting (PCHIP control curves × cos^p domes, feather = hard crease), fit
   guaranteed by the measurement-validation loop. External/purchased last
   meshes remain drop-in compatible (escape hatch, METHOD.md).
2. **Joint-anchored oblique ball line** (2026-07-04, from last_params.md):
   medial joint at 0.69 / lateral at 0.63 of FOOT length (US 7,770,306;
   Koleff). Replaces the earlier "0.72 of stick" vertical ball station, which
   measured ~15 mm too far forward. Ball girth = snug tape about the joint
   line (`joint_plane_girth`). Consequences: instep station 0.50 of foot,
   waist = midway(instep, ball-line midpoint). Validated: short-heel
   measurement immediately moved from 347 → 329 vs the 325 anthropometric
   estimate, and the joint bulges now align with the reference sole.
3. **Waist girth is a defined near-vertical measure** (±8° sweep), not a
   free-settling tape (a free tape slides forward and under-reads).
4. **Heel girth conventions**: short heel = plane through rear-seat pivot
   (0.04) and the instep crown point; long heel = same pivot to the cone
   peak, REPORT-ONLY (a pitched, cone-truncated last has no ankle; Koleff's
   long=short+40–46 relation is a foot relation, kept as calibration
   reference only).
5. **One template per heel height** — never re-pitch (last_creation.md
   caveat). This template: 25 mm.
6. **Left last = mirror of right** at pattern/print time; asymmetry
   (joint stagger, inflare swing, quadrant bias, crown lean) lives in the
   right master.
7. **Reference images**: classification/curve-extraction only, never
   image-to-mesh. Handedness of a sole photo is DETERMINED FROM JOINT
   ANATOMY (anterior bulge = medial), not assumed — a sole-up photo of a
   left shoe reads right-handed.
8. **LSQ style-zone fitting** (`tools/lsq_fit.py`), the error-minimization
   step run before morphing: free variables = style-zone control points
   (x ≥ 0.70) of outlines/crown/swing; fit zone FROZEN; robust soft-L1 loss
   (f_scale 2 mm); side view masked to (0.62–0.90 of shoe length) with the
   shoe→last vertical datum fitted as a bounded nuisance scalar; tips beyond
   0.965 excluded (a sole's blunt corner is irreducible against a last that
   closes to a point); crown points forward of the side mask stay hand-set
   and are blended after; swing bounded inflare-only; post-fit: mesh rebuilt,
   girths + toe-box floor re-validated, junction faired, all logged in
   LSQ_REPORT.md. Achieved on round_25mm: RMS 9.9 → 3.0 mm.
9. **Gate artifacts** for every template revision: snapshots (5 views +
   section plates), `reference/overlay.png`, `template_view.blend`,
   `mock/` (upper+sole+heel preview + `mock_view.blend`), TEMPLATE_REPORT.md.

## 3. Open calibration items (physical trial resolves; do NOT silently change)

1. **Length/girth anchor**: barleycorn+snug targets (stick 287.6 / ball 245.4
   at UK 9 F) vs Cheaney 125 real-maker table (298 / 251). Also effective toe
   allowance 14.1 mm vs nominal 17. One config switch re-anchors if the trial
   says so.
2. **Secondary girths/widths** (instep offset, waist offset, short-heel
   ratio, heel/tread widths) are grade-derived estimates.
3. **Sole overhang** in reference extraction assumed 6 mm uniform; chunky
   casual soles run wider (the reference joint width ≈93 mm vs our F-fit
   99 mm — may simply mean the ref shoe is sleeker/narrower than UK 9 F;
   fitting-width question E vs F for future designs).
4. **Short-heel pitch effect**: flat-foot ratio target does not model heel
   pitch; current agreement (329 vs 325) is good but unconfirmed physically.
