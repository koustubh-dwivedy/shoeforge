"""Mock-dress a template last for gate review: upper skin + sole slab + heel
block. VISUALIZATION ONLY — nothing here feeds patterns or fit; the real
upper/sole are built by Stages 5-7 from pipeline artifacts.

Answers the reviewer question "will this last make that shoe?" by showing the
last wearing the things that make a shoe look like a shoe: leather thickness,
welt/sole overhang, sole slab, stacked heel to ground.

Usage: .venv/bin/python tools/shoe_mock.py data/templates/lasts/round_25mm
Outputs: <tdir>/mock/{upper,sole,heel}.ply + snapshot PNGs.
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
from shapely.geometry import Polygon, box

LEATHER_MM = 1.6
SOLE_OVERHANG_MM = 6.0
SOLE_THICKNESS_MM = 6.0     # outsole + welt visual stack
HEEL_INSET_MM = 1.5


def curved_slab(poly: Polygon, z_top_of_x, thickness=None, floor_z=None):
    """Triangulated slab whose top follows z_top_of_x(x); bottom is either
    top-thickness (curved) or a flat floor_z plane."""
    v2, f = trimesh.creation.triangulate_polygon(poly)
    n = len(v2)
    zt = np.array([z_top_of_x(x) for x, _ in v2])
    zb = (zt - thickness) if floor_z is None else np.full(n, floor_z)
    verts = np.vstack([np.column_stack([v2, zt]),
                       np.column_stack([v2, zb])])
    faces = [list(tri) for tri in f]                       # top
    faces += [[a + n, c + n, b + n] for a, b, c in f]      # bottom (flipped)
    # boundary edges (appear once) -> side walls
    from collections import Counter
    cnt = Counter()
    for a, b, c in f:
        for e in ((a, b), (b, c), (c, a)):
            cnt[tuple(sorted(e))] += 1
    for (a, b), k in cnt.items():
        if k == 1:
            faces += [[a, b, b + n], [a, b + n, a + n]]
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(m)
    return m


if __name__ == "__main__":
    tdir = Path(sys.argv[1])
    params = json.loads((tdir / "shape_params.json").read_text())
    lm = json.loads((tdir / "landmarks.json").read_text())
    last = trimesh.load(tdir / "template.ply", force="mesh")
    L = params["stick_length_mm"]
    zb_spline = PchipInterpolator(
        *np.asarray(params["bottom_profile_z"]["points"]).T)
    z_of_x = lambda x: float(zb_spline(np.clip(x / L, 0, 1))) - 0.5

    outdir = tdir / "mock"
    outdir.mkdir(exist_ok=True)

    # upper: last inflated by leather thickness
    upper = last.copy()
    upper.vertices += upper.vertex_normals * LEATHER_MM
    upper.export(outdir / "upper.ply")

    feather = Polygon(np.asarray(lm["feather_outline_xy"])).buffer(0)
    sole_poly = feather.buffer(SOLE_OVERHANG_MM).simplify(0.5)
    sole = curved_slab(sole_poly, z_of_x, thickness=SOLE_THICKNESS_MM)
    sole.export(outdir / "sole.ply")

    heel_poly = sole_poly.intersection(
        box(-20, -80, 0.30 * L, 80)).buffer(-HEEL_INSET_MM).simplify(0.5)
    heel = curved_slab(heel_poly, lambda x: z_of_x(x) - SOLE_THICKNESS_MM + 0.5,
                       floor_z=0.0)
    heel.export(outdir / "heel.ply")

    # snapshots
    parts = [(upper, "#4a3426"), (sole, "#181818"), (heel, "#181818")]
    for name, elev, azim in [("mock_lateral", 0, -90),
                             ("mock_three_quarter", 22, -55),
                             ("mock_top", 90, -90)]:
        fig = plt.figure(figsize=(9, 5), dpi=130)
        ax = fig.add_subplot(projection="3d")
        allv = []
        for mesh, color in parts:
            v, f = mesh.vertices, mesh.faces
            ax.plot_trisurf(v[:, 0], v[:, 1], f, v[:, 2], color=color,
                            edgecolor="none", shade=True, antialiased=False)
            allv.append(v)
        allv = np.vstack(allv)
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect(np.ptp(allv, axis=0))
        ax.set_axis_off()
        ax.set_title(f"{name} — MOCK (upper skin + sole + heel; no styling/laces)")
        fig.tight_layout()
        fig.savefig(outdir / f"{name}.png", bbox_inches="tight")
        plt.close(fig)
    print(f"mock written to {outdir}")
