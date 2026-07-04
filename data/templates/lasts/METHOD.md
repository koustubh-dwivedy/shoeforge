# Last Parametrization Method — provenance, vocabulary mapping, extensibility

## Are we using established techniques?

Yes — at the level that matters (the method family), with an in-house
implementation where the established tools are proprietary.

The architecture is the consensus of the field as researched in
`last_creation.md` (§8, §B, §11):

1. **Cross-section parametric modeling** — the classical footwear-CAD
   approach (patented lasts are defined by dense cross-sections along the
   length axis; Amza/Zapciu/Popescu, MATEC 2019, parameterize a last as
   splined intersection curves driven by a handful of measurements). Our
   builder (`tools/template_last_builder.py`) lofts ~116 analytic sections.
2. **Template morphing + measurement-validation loop** — "global grading with
   local deformation" (Cheng & Perng et al.), and SATRA's digital last
   assessment model: measure the mesh at defined stations, compare to targets,
   iterate to tolerance. Our `tools/last_measure.py` + Stage 2 loop.
3. **Fit zone vs style zone** — the key architectural principle (Crockett &
   Jones last guide; last_creation.md finding #2): heel-to-ball is
   deterministic from tables + allowances; forward of the ball line is
   image/brief-driven aesthetics.

## Mapping to 3DShoemaker's parameter vocabulary

3DShoemaker (Rhino plugin) is the closest tried-and-tested public system;
last_creation.md (§8) calls its vocabulary "the most instructive existing
parameter vocabulary." Our parameters map 1:1 where it counts:

| 3DShoemaker parameter | shoeforge equivalent |
|---|---|
| Size index | `stick_length_mm` via barleycorn table (`data/sizing/uk_men.json`) |
| Width index | width-fitting girth steps (`width_fittings` in sizing json) |
| Ball / waist / instep girth | station girth targets (`fit_targets.json`) + validation loop |
| Ball / heel / instep width | tread & seat width targets from the feather outline |
| Heel height | `heel_height_mm` — native to each template (a last is balanced for ONE heel height) |
| Toe spring | `toe_spring_mm`, sole-thickness-linked rule in `data/allowances/fit.json` |
| Feather-edge & instep fill allowances | `data/allowances/fit.json` girth allowances |
| Template body vs toe independence | fit zone / style zone split (`fit_targets.json → zones`) |
| Fit customizations (±5 mm steps) | Stage 2 morph scaling-field adjustments |
| SubD template surface | dense analytic loft: PCHIP longitudinal control curves × cos^p dome sections |

## What is in-house, and why

The exact surface construction (PCHIP splines for bottom profile / feather
outline / crown / dome power / crown shift, cos^p wall sections with the
feather edge as a hard crease) is ours. Reason: the tried-and-tested
implementations are closed — 3DShoemaker sells Rhino templates; Shoemaster /
ICad3D+ / Romans CAD are commercial suites — and no open template format
exists. The in-house construction implements the same classical method those
tools implement, and every numeric choice lives in a versioned config
(`shape_params.json`), not code.

**Escape hatch (by design):** the pipeline consumes ANY watertight last mesh
with landmarks. A purchased 3DShoemaker per-size last or a scanned lastmaker
last can be dropped into `data/templates/lasts/<name>/` as a template and the
whole downstream pipeline (morph → validate → patterns) works unchanged. The
in-house builder is one template source among several, not a lock-in.

## Extensibility contract (how this isn't wasted effort)

- One directory per template: `shape_params.json` (all geometry), `template.ply`
  (built mesh), `landmarks.json`, `snapshots/`, `template_view.blend` (3D
  review), `reference/` (user-supplied silhouette references + overlay.png),
  `TEMPLATE_REPORT.md` (measurements vs targets).
- **New size / new design**: never re-model — Stage 2 morphs a template to the
  design's `fit_targets.json`.
- **New toe family** (almond, chisel, square): copy the closest template dir,
  edit ONLY style-zone control points (x ≳ 0.75), rebuild, review at a gate.
- **New heel height**: new template built at that pitch (re-pitching an
  existing last is explicitly discouraged — last_creation.md caveat).
- Measurement conventions (tape model, plane tilts, station definitions) are
  documented in `tools/last_measure.py`'s docstring and validated by
  `tools/tests/test_last_measure.py` against closed-form solids.
- Reference images are used per the workflow's classification-not-
  reconstruction rule; `tools/ref_overlay.py` overlays extracted reference
  silhouettes on template curves for gate review (style zone only — the fit
  zone stays measurement-driven).
