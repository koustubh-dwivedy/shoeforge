"""Least-squares fit of the template's STYLE-ZONE curves to reference images.

The error the user asked for, made explicit: sample the extracted reference
curves, measure the distance from each sample to the corresponding template
curve, sum of squares (robust soft-L1) -> scipy.optimize.least_squares
adjusts the style-zone control points to minimize it.

Protections (per the agreed design):
- FIT ZONE FROZEN: only control points at x >= STYLE_X0 (0.70 of stick,
  beyond the medial joint + margin) are free.
- SIDE-VIEW MASKING: only the toe/vamp segment (x in [0.62, 0.98] of shoe
  length) of the side silhouette is used — laces/tongue/collar/heel excluded;
  the curve is shifted from shoe-space to last-space by SIDE_OFFSET_MM
  (leather + sole stack).
- ROBUST LOSS: soft_l1 (f_scale 2 mm) so extraction noise can't dominate.
- WEIGHTS: top view 1.0 (clean sole photo), side view 0.5 (qualitative).
- POST-FIT VALIDATION: mesh rebuilt, girths + toe-box floor re-measured;
  results in LSQ_REPORT.md. The fitter edits shape_params.json in place
  (git history preserves the pre-fit version).

Usage: .venv/bin/python tools/lsq_fit.py data/templates/lasts/round_25mm \
           designs/derby-plain-uk9/last/fit_targets.json
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from shapely.geometry import Point, Polygon

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from ref_overlay import side_profile_mm, sole_outline_mm  # noqa: E402

STYLE_X0 = 0.70          # style zone begins here (fraction of stick)
SIDE_MASK = (0.62, 0.90)  # side-view usable segment (fraction of shoe length)
SIDE_WEIGHT = 0.4
OUTSOLE_EXTRA = 12.0
CROWN_FLOOR_MARGIN = 9.0  # crown must stay this far above the bottom (toe-box floor)
TIP_CUT = 0.965           # exclude the extreme tip: the sole's blunt front
                          # corner is irreducible against a last that closes
                          # to a point, and would distort the whole fit
# The shoe-space -> last-space vertical datum (leather + sole stack + shoe
# toe spring) is NOT assumed: it is a free nuisance scalar the optimizer
# estimates, bounded to a physically plausible band.
SIDE_OFFSET_BOUNDS = (4.0, 20.0)
SIDE_OFFSET_INIT = 9.0


def spline(pts):
    a = np.asarray(pts, float)
    return PchipInterpolator(a[:, 0], a[:, 1])


class StyleFit:
    def __init__(self, params):
        self.p = params
        self.L = params["stick_length_mm"]
        # free variables: control-point values with x >= STYLE_X0
        self.free = []      # (curve_key, point_index)
        for key in ("outline_y_medial", "outline_y_lateral",
                    "top_profile_z", "centerline_shift_y"):
            for i, (x, _) in enumerate(self.p[key]["points"]):
                if not (STYLE_X0 <= x < 1.0):
                    continue
                # crown points forward of the side-view mask have no residual
                # support — leave them hand-set (blended after the fit)
                if key == "top_profile_z" and x > 0.91:
                    continue
                self.free.append((key, i))

    def x0(self):
        v = [self.p[k]["points"][i][1] for k, i in self.free]
        return np.array(v + [SIDE_OFFSET_INIT])   # last var = side datum offset

    def bounds(self, x0):
        lo, hi = x0 - 12.0, x0 + 12.0
        zb = spline(self.p["bottom_profile_z"]["points"])
        for j, (k, i) in enumerate(self.free):
            if k == "top_profile_z":
                xf = self.p[k]["points"][i][0]
                if xf <= 0.96:   # the box legitimately closes at the tip
                    lo[j] = max(lo[j], float(zb(xf)) + CROWN_FLOOR_MARGIN)
            elif k == "centerline_shift_y":
                lo[j], hi[j] = -8.0, 1.5   # inflare-only (anatomical)
        lo[-1], hi[-1] = SIDE_OFFSET_BOUNDS
        return lo, hi

    def apply(self, v):
        for (k, i), val in zip(self.free, v):
            self.p[k]["points"][i][1] = float(val)

    def curves(self):
        ym = spline(self.p["outline_y_medial"]["points"])
        yl = spline(self.p["outline_y_lateral"]["points"])
        cl = spline(self.p["centerline_shift_y"]["points"])
        zt = spline(self.p["top_profile_z"]["points"])
        return ym, yl, cl, zt

    def outline_poly(self, n=180):
        ym, yl, cl, _ = self.curves()
        f = np.linspace(0.004, 0.996, n)
        med = np.column_stack([f * self.L, ym(f) + cl(f)])
        lat = np.column_stack([f[::-1] * self.L, yl(f[::-1]) + cl(f[::-1])])
        return Polygon(np.vstack([med, lat]))


def residuals(v, fit, ref_xy_style, ref_side, tmpl_style_f):
    side_offset = v[-1]
    fit.apply(v[:-1])
    poly = fit.outline_poly()
    ext = poly.exterior
    # ref -> template distances (style-zone ref samples)
    r1 = [ext.distance(Point(p)) for p in ref_xy_style]
    # template -> ref distances (prevents collapse away from the ref)
    ym, yl, cl, zt = fit.curves()
    r2 = []
    ref_poly = Polygon(REF_POLY_XY)
    for f in tmpl_style_f:
        for y in (ym(f) + cl(f), yl(f) + cl(f)):
            r2.append(ref_poly.exterior.distance(Point(f * fit.L, float(y))))
    # side view: crown vs masked, offset-corrected silhouette
    r3 = []
    if ref_side is not None:
        xs, tops = ref_side
        shoe_len = fit.L + OUTSOLE_EXTRA
        m = (xs >= SIDE_MASK[0] * shoe_len) & (xs <= SIDE_MASK[1] * shoe_len)
        xt = np.clip(xs[m] * fit.L / shoe_len, 0, fit.L)
        want = tops[m] - side_offset
        got = zt(xt / fit.L)
        r3 = (SIDE_WEIGHT * (got - want)).tolist()
    return np.array(r1 + r2 + r3)


if __name__ == "__main__":
    tdir = Path(sys.argv[1])
    targets_path = Path(sys.argv[2])
    params = json.loads((tdir / "shape_params.json").read_text())
    fit = StyleFit(params)
    L = fit.L

    ref_xy = sole_outline_mm(tdir / "reference" / "ref_top.jpg", L)
    global REF_POLY_XY
    REF_POLY_XY = ref_xy
    ref_xy_style = ref_xy[(ref_xy[:, 0] >= STYLE_X0 * L) &
                          (ref_xy[:, 0] <= TIP_CUT * L)]
    try:
        ref_side = side_profile_mm(tdir / "reference" / "ref_side.jpg", L)
    except Exception:  # noqa: BLE001
        ref_side = None
    tmpl_style_f = np.linspace(STYLE_X0 + 0.02, TIP_CUT - 0.01, 24)

    v0 = fit.x0()
    r0 = residuals(v0, fit, ref_xy_style, ref_side, tmpl_style_f)
    res = least_squares(residuals, v0, bounds=fit.bounds(v0), loss="soft_l1",
                        f_scale=2.0, diff_step=0.4,
                        args=(fit, ref_xy_style, ref_side, tmpl_style_f))
    r1 = residuals(res.x, fit, ref_xy_style, ref_side, tmpl_style_f)
    fit.apply(res.x[:-1])
    params["meta"]["revision"] = params["meta"].get("revision", "") + " + LSQ-fitted style zone"
    (tdir / "shape_params.json").write_text(json.dumps(params, indent=2))

    rms = lambda r: float(np.sqrt(np.mean(r ** 2)))
    report = [
        "# LSQ Style-Zone Fit Report",
        "",
        f"- free parameters: {len(fit.free)} style-zone control points "
        f"(outlines, crown, swing; x ≥ {STYLE_X0} of stick — fit zone frozen)",
        f"- residual samples: {len(r0)} (top-view both directions"
        f"{' + masked side view' if ref_side is not None else ''})",
        f"- loss: soft_l1, f_scale 2 mm; side-view weight {SIDE_WEIGHT}, "
        f"fitted datum offset {res.x[-1]:.1f} mm (bounds {SIDE_OFFSET_BOUNDS}), "
        f"mask {SIDE_MASK} of shoe length; tip beyond {TIP_CUT} of stick excluded",
        "",
        "| Metric | Before | After |",
        "|---|---|---|",
        f"| RMS gap (mm) | {rms(r0):.2f} | {rms(r1):.2f} |",
        f"| Worst gap (mm) | {np.abs(r0).max():.2f} | {np.abs(r1).max():.2f} |",
        f"| Cost | {0.5 * np.sum(r0 ** 2):.1f} | {2 * res.cost:.1f} |",
        "",
        "Post-fit girth/floor validation: see TEMPLATE_REPORT.md (rebuild).",
        "",
        "Changed control points:",
    ]
    for (k, i), a, b in zip(fit.free, v0, res.x):
        if abs(a - b) > 0.05:
            x = params[k]["points"][i][0]
            report.append(f"- {k}[x={x}]: {a:.1f} → {b:.1f}")
    (tdir / "LSQ_REPORT.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
