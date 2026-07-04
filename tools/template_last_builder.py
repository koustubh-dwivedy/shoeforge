"""In-house base template last builder (WORKFLOW §S2.1, decision of record:
modeled in-house, no external mesh).

Method: dense analytic cross-section lofting (last_creation.md §8, classical
approach). Every longitudinal control curve is a shape-preserving PCHIP spline
over the config points in data/templates/lasts/<name>/shape_params.json.
Each cross-section is a flat (slightly cambered) bottom between the two
feather-edge corners plus a cos^p dome for the walls/crown, so the feather
edge is a true hard crease by construction. Smoothness comes from analytic
curves sampled densely — no subdivision pass (it would soften the feather).

Outputs (into the template directory):
    template.ply, landmarks.json, snapshots/*.png, TEMPLATE_REPORT.md

Usage: .venv/bin/python tools/template_last_builder.py round_25mm [targets.json]
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.interpolate import PchipInterpolator

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from last_measure import measure_last  # noqa: E402


def spline(pts):
    a = np.asarray(pts, dtype=float)
    return PchipInterpolator(a[:, 0], a[:, 1])


def build_mesh(p: dict) -> tuple[trimesh.Trimesh, dict]:
    L = p["stick_length_mm"]
    zb = spline(p["bottom_profile_z"]["points"])
    zt = spline(p["top_profile_z"]["points"])
    ym = spline(p["outline_y_medial"]["points"])
    yl = spline(p["outline_y_lateral"]["points"])
    dp = spline(p["dome_power"]["points"])
    cs = spline(p["crown_shift_y"]["points"])
    zero = lambda f: 0.0
    cl = spline(p["centerline_shift_y"]["points"]) \
        if "centerline_shift_y" in p else zero      # toe swing / inflare
    da = spline(p["dome_asym"]["points"]) \
        if "dome_asym" in p else zero               # quadrant wall bias

    m = p["mesh"]
    nsec, nd, nb = m["n_sections"], m["n_dome_points"], m["n_bottom_points"]
    eps = m["end_clearance_mm"] / L
    camber = p["bottom_camber_mm"]

    fracs = np.linspace(eps, 1.0 - eps, nsec)
    rings = []
    for f in fracs:
        x = f * L
        swing = float(cl(f))
        y_med, y_lat = float(ym(f)) + swing, float(yl(f)) + swing
        z_bot, z_top = float(zb(f)), float(zt(f))
        mid, half = 0.5 * (y_lat + y_med), 0.5 * (y_lat - y_med)
        h = max(z_top - z_bot, 0.8)
        pw, shift, asym = float(dp(f)), float(cs(f)), float(da(f))

        # bottom edge: medial corner -> lateral corner (slight downward camber)
        ub = np.linspace(-1.0, 1.0, nb + 2)[1:-1]
        yb = mid + half * ub
        zbot_line = z_bot - camber * (1.0 - ub ** 2)
        bottom = np.column_stack([np.full(nb, x), yb, zbot_line])

        # dome: lateral corner -> crown -> medial corner (u: +1 -> -1);
        # quadrant bias: per-side exponent (asym<0 = fuller lateral wall)
        ud = np.linspace(1.0, -1.0, nd + 2)
        yd = mid + half * np.sin(ud * np.pi / 2) + shift * np.cos(ud * np.pi / 2)
        zd = z_bot + h * np.cos(ud * np.pi / 2) ** (pw * (1.0 + asym * ud))
        dome = np.column_stack([np.full(nd + 2, x), yd, zd])

        rings.append(np.vstack([bottom, dome[1:-1]]))  # corners live in `bottom`? no:
        # ring order: bottom (medial->lateral, open) + lateral corner + dome + medial corner
        rings[-1] = np.vstack([
            [[x, y_med, z_bot]], bottom, [[x, y_lat, z_bot]], dome[1:-1]
        ])

    rings = np.asarray(rings)               # (nsec, R, 3)
    R = rings.shape[1]
    verts = rings.reshape(-1, 3)

    # heel / toe tip vertices close the ends
    heel_tip = np.array([0.0, float(cl(0)), 0.5 * (float(zb(0)) + float(zt(0)))])
    toe_tip = np.array([L, 0.5 * (float(ym(1)) + float(yl(1))) + float(cl(1)),
                        0.5 * (float(zb(1)) + float(zt(1)))])
    verts = np.vstack([verts, heel_tip, toe_tip])
    i_heel, i_toe = len(verts) - 2, len(verts) - 1

    faces = []
    for s in range(len(fracs) - 1):
        a0, b0 = s * R, (s + 1) * R
        for k in range(R):
            k2 = (k + 1) % R
            faces.append([a0 + k, b0 + k, b0 + k2])
            faces.append([a0 + k, b0 + k2, a0 + k2])
    first, last = 0, (len(fracs) - 1) * R
    for k in range(R):
        k2 = (k + 1) % R
        faces.append([i_heel, first + k2, first + k])
        faces.append([i_toe, last + k, last + k2])

    mesh = trimesh.Trimesh(vertices=verts, faces=np.asarray(faces), process=True)
    trimesh.repair.fix_normals(mesh)

    # feather outline polygon (forward along medial, back along lateral),
    # including the centerline swing
    ff = np.linspace(eps, 1 - eps, 160)
    swing_ff = np.array([float(cl(t)) for t in ff])
    outline = np.vstack([
        np.column_stack([ff * L, ym(ff) + swing_ff]),
        np.column_stack([ff[::-1] * L, yl(ff[::-1]) + swing_ff[::-1]]),
    ])
    lm_fr = p["landmark_fractions"]
    landmarks = {
        "heel_point": [0.0, float(cl(0)), float(zb(0))],
        "toe_point": [L, float(toe_tip[1]), float(zb(1))],
        "stick_length_mm": L,
        "functional_length_mm": p.get("functional_length_mm"),
        "feather_outline_xy": outline.round(3).tolist(),
        "toe_line_x": p.get("functional_length_mm"),  # toe tips of the mapped foot
        "station_fractions": lm_fr,
        "feather_edge": p.get("feather_edge", "hard_90"),
        "bottom_style": p.get("bottom_style", "flat_cambered"),
        "axes_note": "X heel->toe, Y lateral+ (right last), Z up; ground z=0",
    }
    return mesh, landmarks


# ------------------------------------------------------------------ snapshots

def snapshots(mesh, p, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    v, f = mesh.vertices, mesh.faces
    views = [("lateral", 0, -90), ("medial", 0, 90), ("top", 90, -90),
             ("three_quarter", 28, -55), ("back", 5, 180)]
    for name, elev, azim in views:
        fig = plt.figure(figsize=(9, 5), dpi=130)
        ax = fig.add_subplot(projection="3d")
        ax.plot_trisurf(v[:, 0], v[:, 1], f, v[:, 2], color="#c8b89a",
                        edgecolor="none", shade=True, antialiased=False)
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect(np.ptp(v, axis=0))
        ax.set_axis_off()
        ax.set_title(f"{name}  (25 mm heel pitch, ground z=0)")
        fig.tight_layout()
        fig.savefig(outdir / f"{name}.png", bbox_inches="tight")
        plt.close(fig)

    # cross-section plates at the landmark stations
    L = p["stick_length_mm"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), dpi=130)
    for ax, (name, fr) in zip(axes, [("seat 0.17", 0.17), ("instep 0.48", 0.48),
                                     ("waist 0.55", 0.55), ("ball line 0.63", 0.63)]):
        sec = mesh.section(plane_origin=(fr * L, 0, 0), plane_normal=(1, 0, 0))
        for seg in sec.discrete:
            s = np.asarray(seg)
            ax.plot(s[:, 1], s[:, 2], "k-", lw=1)
        ax.set_title(name)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.axhline(0, color="tab:blue", lw=0.6)
    fig.suptitle("Vertical cross-sections (y-z, mm); blue = ground plane")
    fig.tight_layout()
    fig.savefig(outdir / "sections.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ report

def report(meas, targets, mesh, path: Path):
    lines = ["# Template Last Report — round_25mm (in-house, right last)", "",
             f"- watertight: **{meas['watertight']}**  ·  volume: {meas['volume_l']} L",
             f"- faces: {len(mesh.faces)}  ·  vertices: {len(mesh.vertices)}", "",
             "| Measurement | Template | UK 9 F target | Δ | In tol? |",
             "|---|---|---|---|---|"]
    keys = [("stick_length_mm", "Stick length"), ("ball_girth_mm", "Ball girth"),
            ("instep_girth_mm", "Instep girth"), ("waist_girth_mm", "Waist girth"),
            ("short_heel_girth_mm", "Short heel girth"),
            ("tread_width_mm", "Tread width"), ("seat_width_mm", "Seat width"),
            ("heel_height_mm", "Heel height"), ("toe_spring_mm", "Toe spring")]
    for k, name in keys:
        got = meas[k]
        t = targets["targets"].get(k)
        if t is None or got is None:
            lines.append(f"| {name} | {got} | — | — | — |")
            continue
        tgt = t["target"]
        tol = t.get("tol", (t.get("max", tgt) - t.get("min", tgt)) / 2 or 2.0)
        if "min" in t:  # range-style target (toe spring)
            ok = t["min"] <= got <= t["max"]
            lines.append(f"| {name} | {got} | {t['min']}–{t['max']} | — | {'✅' if ok else '❌'} |")
        else:
            d = round(got - tgt, 2)
            ok = abs(d) <= tol
            lines.append(f"| {name} | {got} | {tgt} ±{tol} | {d:+} | {'✅' if ok else '❌'} |")
    lines += ["",
              f"- toe-box height at 0.94·stick: {meas['toe_box_height_mm']} mm",
              f"- snug-tape settle angles (deg): {meas['tape_angles_deg']}", "",
              "Template values need NOT hit targets exactly — Stage 2's morph/validation "
              "loop closes residuals. This report shows the starting distance.", ""]
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    name = sys.argv[1]
    tdir = REPO / "data" / "templates" / "lasts" / name
    params = json.loads((tdir / "shape_params.json").read_text())
    mesh, landmarks = build_mesh(params)
    mesh.export(tdir / "template.ply")
    (tdir / "landmarks.json").write_text(json.dumps(landmarks, indent=2))

    meas = measure_last(mesh, landmarks)
    print(json.dumps(meas, indent=2))
    snapshots(mesh, params, tdir / "snapshots")
    if len(sys.argv) > 2:
        targets = json.loads(Path(sys.argv[2]).read_text())
        report(meas, targets, mesh, tdir / "TEMPLATE_REPORT.md")
    print(f"exported {tdir / 'template.ply'}  watertight={mesh.is_watertight}")
