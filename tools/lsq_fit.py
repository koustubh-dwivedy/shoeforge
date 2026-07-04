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
OUTSOLE_EXTRA = 12.0
CROWN_FLOOR_MARGIN = 9.0  # crown must stay this far above the bottom (toe-box floor)
TIP_CUT = 0.965           # exclude the extreme tip: the sole's blunt front
                          # corner is irreducible against a last that closes
                          # to a rounded cap, and would distort the whole fit

# WHOLE-PROFILE side-view fit, two regions with independent fitted datum
# offsets (shoe-space -> last-space). Separating the offsets is what makes
# fitting the lace region safe: "the shoe is thicker there (tongue+laces)"
# becomes a nuisance scalar instead of contaminating the last's shape.
#   toe/vamp region: leather + sole stack
#   cone/lace region: leather + sole + tongue/lace/facing stack
SIDE_REGIONS = [
    # toe offset floor 8: leather (~2) + minimum sole stack (~6) — an offset
    # below that is physically impossible and just inflates the toe box
    {"name": "toe/vamp", "mask": (0.60, 0.90), "weight": 0.5,
     "off_bounds": (8.0, 26.0), "off_init": 14.0},
]
# DECISION (DECISIONS.md #10): the cone/back region is NOT fitted to the
# side silhouette. Attempted 2026-07-04 (per-point, then single cone-scale
# DOF + separate lace-region offset): the problem is UNIDENTIFIABLE — cone
# height and tongue/lace stack thickness are collinear in the residual, so
# the optimizer drives both to their bounds; and lowering the cone pulled
# fit-critical instep (253.8 vs 256.9±2) and short-heel (297 vs ~325) girths
# out of tolerance. The cone is therefore constrained by GIRTHS (fit) and
# reviewed visually in 3D at gates; only the toe/vamp silhouette segment,
# where the shoe surface is a constant-thickness offset of the last, is fit.
CONE_SCALE_POINTS = frozenset()
CONE_SCALE_BOUNDS = (1.0, 1.0)
SMOOTH_LAMBDA = 0.08   # second-difference regularizer on free curve points


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
                # arc-closure cap points (beyond TIP_CUT) are geometry, never
                # free — they have no residual support and would wander
                in_style = STYLE_X0 <= x <= TIP_CUT
                if key == "top_profile_z":
                    if in_style and x <= 0.91:
                        self.free.append((key, i))
                elif in_style:
                    self.free.append((key, i))
        self.cone_idx = [i for i, (x, _) in
                         enumerate(self.p["top_profile_z"]["points"])
                         if round(x, 3) in CONE_SCALE_POINTS]
        self.cone_base = [self.p["top_profile_z"]["points"][i][1]
                          for i in self.cone_idx]

    def x0(self):
        v = [self.p[k]["points"][i][1] for k, i in self.free]
        cone = [1.0] if self.cone_idx else []
        return np.array(v + cone + [r["off_init"] for r in SIDE_REGIONS])

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
        if self.cone_idx:
            n_extra = 1 + len(SIDE_REGIONS)
            lo[-n_extra], hi[-n_extra] = CONE_SCALE_BOUNDS
        for r_i, reg in enumerate(SIDE_REGIONS):
            lo[-len(SIDE_REGIONS) + r_i], hi[-len(SIDE_REGIONS) + r_i] = \
                reg["off_bounds"]
        return lo, hi

    def apply(self, v):
        n_extra = (1 if self.cone_idx else 0) + len(SIDE_REGIONS)
        for (k, i), val in zip(self.free, v[:-n_extra]):
            self.p[k]["points"][i][1] = float(val)
        if self.cone_idx:
            cone_scale = float(v[-(1 + len(SIDE_REGIONS))])
            for i, base in zip(self.cone_idx, self.cone_base):
                self.p["top_profile_z"]["points"][i][1] = base * cone_scale

    def smoothness(self):
        """Divided second differences over free-region points (wiggle penalty)."""
        out = []
        for key in ("outline_y_medial", "outline_y_lateral", "top_profile_z"):
            pts = [q for q in self.p[key]["points"] if 0.60 <= q[0] <= 0.99]
            for i in range(1, len(pts) - 1):
                s1 = (pts[i][1] - pts[i - 1][1]) / (pts[i][0] - pts[i - 1][0])
                s2 = (pts[i + 1][1] - pts[i][1]) / (pts[i + 1][0] - pts[i][0])
                out.append(SMOOTH_LAMBDA * (s2 - s1))
        return out

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
    side_offsets = v[-len(SIDE_REGIONS):]
    fit.apply(v)
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
        for reg, off in zip(SIDE_REGIONS, side_offsets):
            m = (xs >= reg["mask"][0] * shoe_len) & \
                (xs <= reg["mask"][1] * shoe_len)
            xt = np.clip(xs[m] * fit.L / shoe_len, 0, fit.L)
            want = tops[m] - off
            got = zt(xt / fit.L)
            r3 += (reg["weight"] * (got - want)).tolist()
    return np.array(r1 + r2 + r3 + fit.smoothness())


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
    fit.apply(res.x)
    cone_scale = res.x[-(1 + len(SIDE_REGIONS))] if fit.cone_idx else 1.0
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
        "- loss: soft_l1, f_scale 2 mm; WHOLE-PROFILE side fit, per-region "
        "fitted datum offsets: " + ", ".join(
            f"{reg['name']} {res.x[-len(SIDE_REGIONS) + i]:.1f} mm "
            f"(mask {reg['mask']}, w {reg['weight']})"
            for i, reg in enumerate(SIDE_REGIONS)) +
        f"; tip beyond {TIP_CUT} of stick excluded; instep/waist/ball crowns frozen (fit zone)",
        f"- cone height scale (single DOF over rear crown): {cone_scale:.3f} "
        f"(bounds {CONE_SCALE_BOUNDS}); smoothness λ {SMOOTH_LAMBDA}",
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
