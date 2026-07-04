# SHOE DEVELOPMENT WORKFLOW — Claude Code Execution Guide

**What this file is:** The master instruction set for developing one complete shoe design — from UK size + design brief + inspiration images, through in-house last generation, to (a) a photorealistic 3D render and (b) production-ready 2D cutting patterns, plus (c) a 3D-printable last file. Claude Code executes this workflow one stage at a time, with the human reviewing at defined gates.

**How to execute this workflow (read first, every session):**

1. Each design lives in its own run directory: `designs/<design-slug>/` (e.g., `designs/oxford-almond-uk8/`). The run directory IS the pipeline state. Every stage reads the previous stage's artifacts from it and writes its own.
2. On starting or resuming a design, read `designs/<slug>/STATUS.md` to determine the current stage, then continue from there. If it doesn't exist, this is a new design: create the run directory and begin at Stage 0.
3. After completing each stage, update `STATUS.md` (stage completed, artifacts produced, open issues, next stage) and STOP for human review at every gate marked **[GATE]**. Do not proceed past a gate without explicit approval.
4. Reusable code goes in `tools/` at repo root (shared across all designs). Design-specific throwaway scripts go in the run directory under `scratch/`. Before writing any new tool, check whether `tools/` already has it from a previous run — extend rather than duplicate. The pipeline is expected to harden organically: the first design build will create most tools; later designs mostly reuse them.
5. Reference data (grading tables, allowance tables, template lasts, style templates) lives in `data/` at repo root. If a required data file doesn't exist yet, creating it (from the numbers in this document) is part of the stage.
6. All geometry code is pure Python (`trimesh`, `numpy`, `scipy`, `shapely`, `pyclipper`, `libigl` bindings where available, `ezdxf`, `svgwrite`) — headless and testable. Blender (`bpy` module or `blender --background --python`) is used ONLY in Stage 6 (visualization) and never owns pattern- or fit-critical data.
7. Units: millimetres everywhere. Coordinate convention: X = last length axis (heel → toe positive), Y = medial–lateral (lateral positive for right foot), Z = up. Last rests with heel seat and tread on a virtual ground plane consistent with its heel height.
8. When this document gives a numeric value, treat it as a **configurable default** stored in `data/` config files — never hardcode it inline.

**Repo layout (create on first run):**

```
shoeforge/
  WORKFLOW.md              # this file
  data/
    sizing/uk_men.json     # size→length/girth tables (Stage 1 creates from §S1)
    allowances/fit.json    # foot→last allowances (§S1)
    allowances/pattern.json# seam/lasting allowances (§S5)
    templates/lasts/       # base last meshes + landmark annotations
    templates/styles/      # style template YAMLs (derby, oxford, loafer)
    materials/             # Blender shader library, HDRIs
  tools/                   # reusable scripts, accumulated across runs
  designs/<slug>/          # one per design (run directory)
    spec/  last/  shell/  style/  patterns/  sole/  renders/  print/  scratch/
    STATUS.md  REVIEW.md
```

---

## PIPELINE OVERVIEW

| Stage | Name | Key output | Gate? |
|---|---|---|---|
| 0 | Intake & DesignSpec | `spec/design_spec.json` | [GATE] |
| 1 | Fit targets | `last/fit_targets.json` | — |
| 2 | Last generation & fit validation loop | `last/last.ply` + `last/fit_report.md` | [GATE] |
| 3 | Printable last engineering | `print/last_print.3mf` + print spec | [GATE] |
| 4 | Shell flattening & standard | `shell/shell_map.json` + distortion report | — |
| 5 | Style application & pattern engineering | `patterns/*.svg/.dxf` + validation report | [GATE] |
| 6 | 3D assembly & rendering | `renders/*.png` + turntable | [GATE] |
| 7 | Sole unit & tech pack | `sole/*`, `techpack.pdf`, final manifest | [GATE] |

Stages 2–3 (last) and 4–6 (shoe) are sequential on the first pass. On iteration, re-enter at the earliest affected stage: a fit change re-enters at Stage 1; a style change re-enters at Stage 5; a material change re-enters at Stage 6 only.

---

## STAGE 0 — INTAKE & DESIGNSPEC

**Inputs (from human):** UK men's size (and width fitting if known; default F), free-text design brief, inspiration images (drop into `designs/<slug>/spec/inspiration/`).

**Do:**
1. Parse the brief and images into a structured `design_spec.json`: shoe type/template (derby | cap-toe oxford | brogued variants | penny loafer), construction (`gyw` default), toe character (round | almond | soft-chisel | chisel | square), toe elongation (standard | elongated), detailing (cap, brogue scheme, apron), materials & colors, heel height (default 25 mm for men's dress GYW; range 20–30 mm), sole spec (single leather ≈ 5 mm default), edge treatments.
2. Image handling is **classification, not reconstruction**: analyze the inspiration images to classify toe shape family, toe elongation, silhouette character (sleek/round-profile), topline height, and detailing cues; record the classification and confidence per image in the spec with a `source: image` tag so the human can override. Do NOT attempt image-to-mesh.
3. Where the brief is silent, fill defaults and mark them `assumed: true`.
4. Write `spec/design_spec.json` (validate against `tools/spec_schema.py`; create the schema if absent) and a one-page `spec/SPEC_SUMMARY.md` in plain language.

**[GATE]** Human confirms the spec summary — especially size/width, toe shape, heel height, and anything marked `assumed`.

---## STAGE 1 — FIT TARGETS (foot → last numbers)

**Purpose:** Convert UK size + width fitting into the target measurement set the last must hit. This stage is pure table math — no geometry.

**S1.1 — Sizing and grading rules (create `data/sizing/uk_men.json` if absent):**
- UK adult sizing: barleycorn system; 1 full size = 1/3 inch = **8.46 mm** in last length; half size = 4.23 mm.
- Last stick length for UK men's size S (adult): `length_mm = (S + 25) × 8.46` — i.e., size 8 ≈ 279 mm stick length. Store as formula + explicit table for sizes 5–13 so it can be sanity-checked against the research report's table; if the report's numbers differ, the table in `data/` wins and the formula becomes documentation.
- Girth grade: **6.35 mm (1/4 inch) per full size** on ball (joint) girth; **≈ 4.7–5 mm per size** on instep; waist scales with ball.
- Width fittings (English system E–G around standard F): **6.35 mm ball girth per fitting step** (quarter-inch rule; some makers use 6 mm — configurable), tread width ≈ +2 mm per step.

**S1.2 — Foot→last allowances (create `data/allowances/fit.json` if absent):** For GYW men's dress shoes (snug dress fit, calf leather):
- **Toe allowance** beyond longest toe: round 15–18 mm, almond 18–22 mm, chisel 20–25 mm, elongated square/chisel 25–35 mm (style zone — see S1.4).
- **Ball girth:** last girth ≈ foot girth **+0 to −5 mm** (dress fit; leather stretch absorbs snugness). Default −2 mm.
- **Instep girth:** foot **+0 to +3 mm** default +1.5 mm (instep hold without pressure).
- **Short heel girth:** foot **−3 to −6 mm** (heel grip is negative allowance). Default −4 mm.
- **Waist:** proportional to ball; for a beveled-waist aesthetic allow −3 mm option.
- **Seat width:** foot heel width −2 to −4 mm.
- Every value: `{default, min, max, rationale}` in the JSON.

**S1.3 — Derive the target sheet:** From size+fitting → reference foot dimensions (via the anthropometric table in `data/sizing/`; UK 8 F male reference ≈ foot length 265 mm, ball girth 241 mm — verify against stored table) → apply allowances → **`last/fit_targets.json`**: stick length, ball girth & position (ball line at ~72–74% of stick length from heel... store as heel-to-ball fraction ≈ 0.72 default), instep girth & station, waist girth, short/long heel girths, seat width, tread width, toe allowance, toe spring target (**8–12 mm** for 5 mm leather sole; store sole-thickness-linked rule), heel height from spec, feather-edge sharpness spec.
- Include per-measurement **tolerances**: ±2 mm girths, ±1.5 mm lengths, ±1 mm widths (SATRA-informed defaults; configurable).

**S1.4 — Fit zone vs style zone:** Record in the targets file: everything from heel to just beyond the ball line + toe height over the toes region is **fit-critical** (tolerances above are hard). The toe box beyond the toes is the **style zone** — free for aesthetic shaping provided minimum toe-box height above toe tips (≥ 8 mm at the toe line) and toe allowance are respected. Stage 2 must obey this split.

**Output:** `last/fit_targets.json` + `last/FIT_TARGETS.md` (human-readable table). No gate — Stage 2 validates against these numbers mechanically.

---

## STAGE 2 — LAST GENERATION & FIT VALIDATION LOOP

**Architecture: template-morphing with cross-section control** (chosen over from-scratch parametric lofting: dramatically lower risk, and fit lives in measurements, not in sculptural novelty).

**S2.1 — Template last:** Load the base last mesh for the spec's toe family from `data/templates/lasts/` (each template: watertight mesh + `landmarks.json`: toe point, heel point, heel-to-ball axis, feather-line polyline, back curve, cone line, measurement station planes for ball/instep/waist/heels). If no template exists yet for this family, acquiring/annotating one IS the task: source a clean digital last (GrabCAD/Cults3D for bootstrap; lastmaker-grade later), repair it (`trimesh`: watertight, normals, ~50–150k faces), align to the canonical frame, and annotate landmarks (feather line via bottom-edge dihedral analysis; verify visually via a rendered wireframe snapshot for the human).

**S2.2 — Measurement engine (`tools/last_measure.py`, reusable and central):** Given any last mesh + landmarks: stick length; girths as closed cross-section perimeters at the defined stations (plane sections tilted per lastmaking convention at ball/instep; document chosen plane definitions in the tool); widths; heel curve profile; toe spring (tread-plane geometry); heel height; toe-box height over the toe line; bottom (feather-line) outline extraction. This tool is the arbiter of "does a foot fit" — build it FIRST and test it on the raw template against known values.

**S2.3 — Morph to targets, in order:**
1. **Global length scale** to target stick length (anisotropic: scale X to length; leave Y/Z for girth steps).
2. **Cross-section girth scaling:** smooth axial scaling field on Y/Z, interpolated (monotone spline) between stations, hitting ball/instep/waist/heel girth targets; preserve bottom-width vs side-height proportions per template ratios; keep feather line fair.
3. **Heel height & toe spring:** re-pitch the bottom profile to spec heel height; set toe spring via bottom-curve rotation forward of the ball; re-level to ground plane.
4. **Style-zone shaping:** apply toe-shape parameters (elongation, chisel flattening, taper) via region-limited cage/RBF deformation forward of the style-zone boundary ONLY. Fit zone must remain untouched by style operations — enforce by asserting fit-zone vertex displacement < 0.2 mm from step 3's result.
5. **Fairing pass** (light Laplacian on modified regions, feather edge preserved as a hard crease).

**S2.4 — Validation loop (the fit guarantee):** Measure (S2.2) → compare to `fit_targets.json` → if any fit-critical measurement is out of tolerance, adjust the corresponding scaling-field control point and repeat. Converge ≤ 10 iterations; if not converging, stop and report which measurement conflicts (usually means the template family is wrong — flag for human).
- Additional hard checks: mesh watertight & manifold; feather line closed and fair (curvature continuity report); toe-box height ≥ minimum; symmetry sanity (a last is intentionally asymmetric — check medial/lateral difference is within template-characteristic bounds, not zero and not wild); volume within ±8% of template-predicted volume for the size (catches degenerate morphs).

**Outputs:** `last/last.ply` (design last, mm), `last/landmarks.json` (updated), `last/fit_report.md` — target-vs-achieved table with pass/fail per measurement, plus 4-view snapshot renders (matplotlib/trimesh scene is fine) and cross-section overlay plots at each station.

**[GATE]** Human reviews fit report + silhouette snapshots. This is the single most important gate in the pipeline: approve fit AND look before anything downstream runs. (Honest caveat, stated in the report: computational validation guarantees the last matches lastmaking-standard numbers for that size; only a physical fit trial confirms an individual foot's comfort.)

---

## STAGE 3 — PRINTABLE LAST ENGINEERING

**Purpose:** Turn the design last into a 3D-print package that survives real GYW shoemaking (lasting pliers, tacks, welting, heat).

**Do:**
1. **Material/process spec** (write `print/PRINT_SPEC.md`): default **PETG** (cold lasting) with explicit warning that heat-setting/heat lasting above ~70 °C requires **ABS/ASA or PA**; PLA prohibited for heated processes. Walls ≥ **5 mm** (6 perimeters at 0.8 mm nozzle or equivalent), infill ≥ 40% gyroid (research indicated near-solid to 5 mm-wall configurations survive lasting; store both options), layer 0.2 mm, orientation heel-down/vertical-ish to favor feather-edge fidelity — record chosen orientation and why.
2. **Mechanical features (parametrize in `tools/last_print_prep.py`):**
   - **Thimble:** cylindrical bore at the standard lasting-jack position in the cone, sized for a metal insert (default 12 mm bore for a copper/steel thimble, press-fit, glue-in); never rely on bare plastic on the jack pin.
   - **De-lasting mechanism:** default **V-cut hinged last** (scoop-block geometry: V-kerf + pivot bore for a steel pin + clearance so the back part folds forward) — required for GYW since the lasted shoe cannot slip off a solid last. Alternative selectable: two-part telescopic. Generate as boolean ops on the mesh; verify hinge kinematics by swept-volume clearance check.
   - **Tack strategy:** the printed bottom won't hold tacks like hornbeam — add a 2 mm recessed pocket on the last bottom (inside the feather line, forward of heel) sized for a glued leather/cork insert, OR specify holding via lasting tape/staple-free method in the print spec. Default: recessed insert pocket.
3. **Print geometry QA:** min wall thickness map, overhang report vs chosen orientation, feather-edge chamfer check (edge must survive printing: verify local thickness at feather ≥ 1.2 mm; if the design last's feather is too knife-sharp to print, add a 0.4 mm micro-flat on the PRINT copy only — the design last for Stage 4 stays sharp), shrinkage compensation scale factor (per-material config, PETG ≈ +0.3–0.5%).
4. **Export:** `print/last_print.3mf` (or STL + a slicer profile note), plus `print/POSTPROCESS.md` (sand tread & feather region to 240 grit, fit thimble, fit hinge pin, glue bottom insert).

**[GATE]** Human approves print spec (and typically prints + handles the last here before investing in patterns; the workflow supports proceeding in parallel if desired).

---

## STAGE 4 — SHELL FLATTENING & STANDARD

**Purpose:** Build the persistent 3D↔2D map that everything downstream shares. Uses the DESIGN last from Stage 2.

**Do:**
1. **Shell extraction:** last surface above the feather line minus top-opening region; cut along back (heel) curve and front cone line → medial and lateral half-shells.
2. **Flatten each half:** preference order — BFF CLI (boundary-controlled conformal, cone singularities for area-distortion control) → ARAP (`igl` bindings; better length preservation) → LSCM only as bootstrap. Record per-face **area and shear strain fields**.
3. **Mean form:** average medial/lateral flattened boundaries + landmark positions (classical mean-form method); persist per-side maps too for later corrections.
4. **Springing:** apply parameterized 2D corrections (heel-spring pivot of backpart; throat opening at vamp) with defaults in `data/allowances/pattern.json` (springing block) — these are the craft corrections pure math misses.
5. **Persist `shell/shell_map.json`** (+ NPZ arrays): shell submesh refs, per-vertex 2D coords (medial/lateral/mean), inverse lookup structure, strain fields, 2D landmark positions.
6. **Report:** `shell/DISTORTION.md` — strain heatmap images, max/mean area & shear distortion, flags where in-plane strain exceeds the leather budget (default flag > 3% area strain) with dart-suggestion notes.

No gate (mechanical stage), but STOP if max fit-zone strain > 6% — that indicates a shell-cut or flattening problem to fix before patterns.

---

## STAGE 5 — STYLE APPLICATION & PATTERN ENGINEERING

**Do:**
1. **Load style template** from `data/templates/styles/<type>.yaml` (create per §templates below if absent): parametric 2D style-curve constructions anchored to 2D landmarks (vamp point at heel-to-ball-derived fraction, counter height, facing length, cap line, topline) + **piece graph** (pieces: vamp, cap, quarters, facings, tongue, counter/heel strip, apron as applicable; seam edges annotated: type [underlay | folded-edge overlay | closed back seam | binding], overlap direction, stitch rows/offsets, allowance rule each side).
2. **Instantiate curves** on the mean form with the spec's parameters; lift to 3D through the shell map; write both representations to `style/style_graph.json`. Emit a quick 3D preview snapshot (style lines drawn on last mesh) for sanity.
3. **Derive production patterns** per piece: net (stitch-line) outline → cut outline via per-edge polygon offsetting (`pyclipper`) using `data/allowances/pattern.json` — defaults: lasting margin 15–19 mm scalloped (less at waist), underlay 8–12 mm, folded edge 4 mm, closed back seam 2 mm, raw/burnished 0; linings (reduced 1–2 mm at topline, seam-shifted), toe puff & counter stiffener sub-patterns, notches (seam ends/midpoints/centerlines), stitch guide lines, brogue punch centers per scheme, grain/tight-to-toe arrows, labels + mirror flags.
4. **HARD VALIDATION GATES (the definition of "working"):**
   - Mating stitch-line lengths equal within ±1.0 mm or ±1% (whichever larger);
   - Re-projected pieces tile the shell exactly once outside declared overlaps (no gaps/double cover);
   - Simple polygons, min feature width ≥ 2 mm, notch clearance ok;
   - Per-piece flattening strain within leather budget, else emit dart/relief suggestions and fail.
5. **Export:** per-piece + combined sheets: SVG and DXF at true 1:1 mm with layers (CUT / STITCH / PUNCH / MARKS), tiled A4 PDF with registration marks + printed scale ruler. Write `patterns/VALIDATION.md`.

**[GATE]** Human reviews pattern sheet + validation report. All hard gates must be green.

---

## STAGE 6 — 3D ASSEMBLY & RENDER (Blender only here)

**Do:** Build the presentation model from pipeline artifacts (never the reverse): lift piece regions to 3D shell patches; solidify by material thickness with correct layering (cap over vamp over quarters); Geometry Nodes stitcher along lifted seam curves + perforator for brogueing; bottom unit in 3D (insole at feather line, welt sweep, outsole with edge profile + toe spring, stacked heel at spec height); apply material library (calf PBR, burnished edges, sole finish); studio HDRI; Cycles stills (3/4 front, side profile, top, back, sole) + 24-frame turntable → `renders/`.

**[GATE]** Human approves the look. Style-parameter tweaks → re-enter Stage 5 (cheap); toe/silhouette tweaks → re-enter Stage 2 style-zone step (fit unaffected if confined to style zone — assert this).

---

## STAGE 7 — SOLE UNIT & TECH PACK

**Do:**
1. **Sole patterns (GYW):** insole outline = feather-line projection; rib/holdfast line inset 8–12 mm; welt strip spec (heel-breast→heel-breast perimeter + 60 mm working allowance; width default 22 mm); outsole = insole + welt exposure (5–7 mm forepart, 2–3 mm waist for beveled option); heel lifts from heel seat to spec height (lift thickness 5 mm default → count computed); top piece. Export to `sole/` (SVG/DXF).
2. **Tech pack** (`techpack.pdf` via HTML→PDF): piece list with thumbnails, materials/thicknesses, allowance table actually used, stitch specs, assembly order (closing sequence, then lasting → welting → soling → heeling), BOM incl. last print spec, renders, fit-report summary.
3. **Final manifest** `MANIFEST.json`: every artifact with hash + stage provenance. Update `STATUS.md` → `complete`.

**[GATE]** Final human sign-off.

---

## STYLE TEMPLATE AUTHORING NOTES (for `data/templates/styles/`)

Build in this order (each reuses the previous): **plain derby** (vamp+tongue, two quarters — simplest topology) → **cap-toe oxford** (closed lacing: quarters/facings under vamp; cap seam) → **brogued variants** (punch schemes as decoration layer on oxford/derby) → **penny loafer** (apron + strap constructs). Template = YAML: parameters with defaults/ranges, curve constructions (anchored Béziers in mean-form coordinates), piece graph with seam semantics. Classical proportional defaults so an un-tuned brief still yields a well-proportioned shoe.

## STANDING RULES & FAILURE PROTOCOL

- Numeric defaults live in `data/`; this document is their citation, config is their home.
- If a stage's inputs are missing/invalid, do not improvise silently — state what's missing in `STATUS.md` and ask.
- If a validation fails twice on the same cause, stop and present the conflict to the human with options rather than loosening tolerances. Tolerances are only changed by human edit to `data/` configs.
- Known honest limits (repeat in reports where relevant): flattening ≠ leather behavior (anisotropic stretch not simulated — keep strain budgets conservative and mark tight-to-toe); computational fit ≠ individual-foot comfort (physical trial closes the loop); springing values and allowance tables should be calibrated once against a real sample and the `data/` defaults updated — that calibration run is expected and valuable, not a failure.

## QUICK GLOSSARY

Last (form shoe is built on) · Feather edge (side-wall/bottom boundary) · Stick length (heel–toe last length) · Ball/joint girth (circumference at widest forepart) · Instep/waist/short-heel girths (fit stations) · Toe spring (toe rise off ground) · Heel pitch/height · Vamp/quarters/facings/cap/tongue/counter (upper pieces) · Topline/throat · Shell/standard/mean form (flattened last surface / master pattern / medial-lateral average) · Springing (post-flattening craft corrections) · Lasting margin (leather pulled under last onto insole) · Welt/rib (GYW stitching anatomy) · Clicking/closing (cutting/stitching) · Tight-to-toe (leather stretch direction) · Scoop block / hinged last (de-lasting mechanism) · Thimble (metal jack-pin insert).

---
*Execution note for Claude Code: on every new session, read this file top-to-bottom, then `designs/<slug>/STATUS.md`, then proceed. Build `tools/last_measure.py` before any morphing work — measurement is the arbiter of everything.*
