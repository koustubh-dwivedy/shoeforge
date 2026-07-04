"""Measurement engine for lasts (WORKFLOW §S2.2) — THE arbiter of fit.

Coordinate convention (WORKFLOW rule 7): X = length axis, heel→toe positive;
Y = medial–lateral (lateral positive for a right last); Z = up. Units mm.
The last is posed "shod": tread region touching z≈0, heel-seat bottom raised
by its heel height, per rule 7.

Plane definitions (documented per WORKFLOW):
- A girth is modeled as a SNUG TAPE: the perimeter of the CONVEX HULL of a
  planar mesh section (a tape bridges concavities), MINIMIZED over a sweep of
  plane tilts about the medial-lateral (Y) axis through a station pivot point
  on the bottom profile. A naive vertical slice overreads girths wherever the
  surface is oblique (instep especially) — the sweep finds where a real tape
  would settle.
- Station pivots sit on the bottom profile at configured fractions of stick
  length; tilt φ rotates the plane normal (1,0,0) about +Y:
  normal(φ) = (cos φ, 0, sin φ). Sweep ranges per station live in
  data/sizing/uk_men.json-adjacent config or the caller's `stations` dict.
- Widths (tread/seat) are read from the feather-line outline (landmarks), not
  from shell sections, matching how a lastmaker calipers the bottom.

Toe spring = bottom-profile height above ground at the toe tip.
Heel height = bottom-profile height above ground at the heel-seat point.
Toe-box height = vertical section extent (z_max - z_min) at the toe-line
station (simplification documented: the foot's toe thickness is not modeled;
the configured floor in data/allowances/fit.json accounts for it).
"""

import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import ConvexHull

DEG = np.pi / 180.0


# ---------------------------------------------------------------- sections

def _section_points(mesh: trimesh.Trimesh, origin, normal) -> np.ndarray | None:
    """All 3D points of the mesh∩plane section, or None if empty."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return None
    pts = np.vstack([np.asarray(seg) for seg in sec.discrete])
    return pts if len(pts) >= 3 else None


def tape_perimeter(mesh, origin, normal) -> float | None:
    """Snug-tape (convex hull) perimeter of the planar section, in mm."""
    pts = _section_points(mesh, origin, normal)
    if pts is None:
        return None
    n = np.asarray(normal, dtype=float)
    n /= np.linalg.norm(n)
    # in-plane 2D coordinates
    a = np.cross(n, [0.0, 1.0, 0.0])
    if np.linalg.norm(a) < 1e-9:
        a = np.cross(n, [1.0, 0.0, 0.0])
    a /= np.linalg.norm(a)
    b = np.cross(n, a)
    uv = np.column_stack([(pts - origin) @ a, (pts - origin) @ b])
    hull = ConvexHull(uv)
    loop = uv[hull.vertices]
    return float(np.linalg.norm(np.diff(np.vstack([loop, loop[:1]]), axis=0),
                                axis=1).sum())


def min_tape_girth(mesh, pivot, sweep_deg, n_angles=41):
    """Minimal snug-tape perimeter over plane tilts φ∈sweep about +Y through
    `pivot`. Returns (girth_mm, best_angle_deg)."""
    best, best_phi = None, None
    for phi in np.linspace(sweep_deg[0], sweep_deg[1], n_angles):
        nrm = (np.cos(phi * DEG), 0.0, np.sin(phi * DEG))
        p = tape_perimeter(mesh, pivot, nrm)
        if p is not None and (best is None or p < best):
            best, best_phi = p, float(phi)
    return best, best_phi


# ------------------------------------------------------------ bottom / profiles

def bottom_profile(mesh, n=240) -> np.ndarray:
    """(x, z_min) polyline along the length axis via vertical ray sampling."""
    x0, x1 = mesh.bounds[0][0], mesh.bounds[1][0]
    xs = np.linspace(x0 + 0.5, x1 - 0.5, n)
    out = []
    for x in xs:
        pts = _section_points(mesh, (x, 0, 0), (1, 0, 0))
        if pts is None:
            continue
        near = pts[np.abs(pts[:, 1]) < np.ptp(pts[:, 1]) * 0.5 + 1e-9]
        out.append((x, float(near[:, 2].min())))
    return np.asarray(out)


def back_curve(mesh, n=80) -> np.ndarray:
    """Heel back-curve profile: mesh ∩ (Y=0) for the rear 20% of length."""
    pts = _section_points(mesh, (0, 0, 0), (0, 1, 0))
    if pts is None:
        return np.empty((0, 2))
    x_cut = mesh.bounds[0][0] + 0.2 * np.ptp(mesh.bounds[:, 0])
    rear = pts[pts[:, 0] <= x_cut]
    order = np.argsort(rear[:, 2])
    return rear[order][:, [0, 2]]


def outline_width_at(outline_xy: np.ndarray, x: float) -> float:
    """Width (max Y - min Y) of a closed feather outline at station x."""
    pts = np.asarray(outline_xy)
    ys = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        if (p[0] - x) * (q[0] - x) <= 0 and p[0] != q[0]:
            t = (x - p[0]) / (q[0] - p[0])
            ys.append(p[1] + t * (q[1] - p[1]))
    return float(max(ys) - min(ys)) if len(ys) >= 2 else float("nan")


def extract_feather_line(mesh, dihedral_deg=50.0):
    """Fallback feather extraction via face-adjacency dihedral creases near the
    bottom. Prefer the landmarks polyline written by the builder."""
    ang = mesh.face_adjacency_angles
    sharp = mesh.face_adjacency_edges[ang > dihedral_deg * DEG]
    if not len(sharp):
        return None
    v = mesh.vertices[np.unique(sharp)]
    zc = mesh.bounds[0][2] + 0.45 * np.ptp(mesh.bounds[:, 2])
    return v[v[:, 2] < zc]


# ---------------------------------------------------------------- main entry

DEFAULT_SWEEPS = {  # degrees; documented convention, override via `stations`
    "ball": (-25.0, 25.0),
    "waist": (-20.0, 20.0),
    "instep": (0.0, 45.0),
    "short_heel": (30.0, 70.0),
}


def measure_last(mesh: trimesh.Trimesh, landmarks: dict,
                 stations: dict | None = None) -> dict:
    """Full lastmaker metrology. `landmarks` needs stick fractions and the
    feather outline; `stations` overrides fractions/sweeps."""
    st = {
        "ball_fraction": 0.72, "waist_fraction": 0.62, "instep_fraction": 0.52,
        "heel_width_fraction": 0.17, "short_heel_fraction": 0.09,
        "sweeps": DEFAULT_SWEEPS,
    }
    st.update(stations or {})

    x0 = float(mesh.bounds[0][0])
    stick = float(np.ptp(mesh.bounds[:, 0]))
    prof = bottom_profile(mesh)

    def bottom_z(x):
        return float(np.interp(x, prof[:, 0], prof[:, 1]))

    def station_x(frac):
        return x0 + frac * stick

    girths, angles = {}, {}
    for name, frac in [("ball", st["ball_fraction"]),
                       ("waist", st["waist_fraction"]),
                       ("instep", st["instep_fraction"]),
                       ("short_heel", st["short_heel_fraction"])]:
        x = station_x(frac)
        pivot = (x, 0.0, bottom_z(x))
        g, phi = min_tape_girth(mesh, pivot, st["sweeps"][name])
        girths[name], angles[name] = g, phi

    feather = np.asarray(landmarks["feather_outline_xy"]) \
        if "feather_outline_xy" in landmarks else None
    tread_w = outline_width_at(feather, station_x(st["ball_fraction"])) \
        if feather is not None else None
    seat_w = outline_width_at(feather, station_x(st["heel_width_fraction"])) \
        if feather is not None else None

    heel_h = prof[prof[:, 0] <= x0 + 0.10 * stick][:, 1].max()
    toe_spring = float(prof[-1][1])
    toe_line_x = landmarks.get("toe_line_x", x0 + 0.94 * stick)
    sec = _section_points(mesh, (toe_line_x, 0, 0), (1, 0, 0))
    toe_box_h = float(np.ptp(sec[:, 2])) if sec is not None else None

    return {
        "stick_length_mm": round(stick, 2),
        "ball_girth_mm": round(girths["ball"], 2),
        "waist_girth_mm": round(girths["waist"], 2),
        "instep_girth_mm": round(girths["instep"], 2),
        "short_heel_girth_mm": round(girths["short_heel"], 2),
        "tread_width_mm": round(tread_w, 2) if tread_w else None,
        "seat_width_mm": round(seat_w, 2) if seat_w else None,
        "heel_height_mm": round(float(heel_h), 2),
        "toe_spring_mm": round(toe_spring, 2),
        "toe_box_height_mm": round(toe_box_h, 2) if toe_box_h else None,
        "tape_angles_deg": {k: round(v, 1) for k, v in angles.items() if v is not None},
        "watertight": bool(mesh.is_watertight),
        "volume_l": round(float(mesh.volume) / 1e6, 4) if mesh.is_watertight else None,
    }


if __name__ == "__main__":
    import sys
    mesh = trimesh.load(sys.argv[1], force="mesh")
    lm = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
    print(json.dumps(measure_last(mesh, lm), indent=2))
