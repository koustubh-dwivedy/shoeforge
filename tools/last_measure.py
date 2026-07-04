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


def min_tape_girth(mesh, pivot, sweep_deg, n_angles=41, min_z_extent=0.0):
    """Minimal snug-tape perimeter over plane tilts φ∈sweep about +Y through
    `pivot`. Returns (girth_mm, best_angle_deg). Sections whose vertical
    extent is below `min_z_extent` are rejected (degenerate corner slivers
    would otherwise win the minimization)."""
    best, best_phi = None, None
    for phi in np.linspace(sweep_deg[0], sweep_deg[1], n_angles):
        nrm = (np.cos(phi * DEG), 0.0, np.sin(phi * DEG))
        pts = _section_points(mesh, pivot, nrm)
        if pts is None or np.ptp(pts[:, 2]) < min_z_extent:
            continue
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
        med = np.median(pts[:, 1])
        near = pts[np.abs(pts[:, 1] - med) <= np.ptp(pts[:, 1]) * 0.5 + 1e-9]
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
    # normal(φ)=(cosφ,0,sinφ): φ<0 leans the plane's top FORWARD (toward toe),
    # φ>0 leans it back toward the heel.
    "ball": (-30.0, 20.0),   # sweep is about the oblique JOINT LINE axis
    # waist is a defined near-vertical station measure, not a settling tape
    "waist": (-8.0, 8.0),
    "instep": (0.0, 45.0),
}


def joint_plane_girth(mesh, p_med, p_lat, sweep_deg, n_angles=25):
    """Ball girth on the oblique joint plane (last_params.md §D): the tape
    passes through the 1st (medial) and 5th (lateral) MPJ points. The plane
    contains the joint line; the sweep rotates it about that line, and the
    snug tape takes the minimum. Returns (girth, best_angle_deg)."""
    p_med, p_lat = np.asarray(p_med, float), np.asarray(p_lat, float)
    axis = p_lat - p_med
    axis /= np.linalg.norm(axis)
    n0 = np.cross(axis, [0.0, 0.0, 1.0])
    n0 /= np.linalg.norm(n0)
    origin = 0.5 * (p_med + p_lat)
    zhat = np.cross(n0, axis)
    best, best_phi = None, None
    for phi in np.linspace(sweep_deg[0], sweep_deg[1], n_angles):
        nrm = n0 * np.cos(phi * DEG) + zhat * np.sin(phi * DEG)
        p = tape_perimeter(mesh, origin, nrm)
        if p is not None and (best is None or p < best):
            best, best_phi = p, float(phi)
    return best, best_phi


def measure_last(mesh: trimesh.Trimesh, landmarks: dict,
                 stations: dict | None = None) -> dict:
    """Full lastmaker metrology. `landmarks` needs stick fractions and the
    feather outline; `stations` overrides fractions/sweeps."""
    st = {
        "medial_joint_fraction": 0.656, "lateral_joint_fraction": 0.599,
        "waist_fraction": 0.552, "instep_fraction": 0.476,
        "heel_width_fraction": 0.17, "short_heel_pivot_fraction": 0.04,
        "heel_height_fraction": 0.09,
        "sweeps": DEFAULT_SWEEPS,
    }
    st.update(landmarks.get("station_fractions") or {})
    st.update(stations or {})

    x0 = float(mesh.bounds[0][0])
    stick = float(np.ptp(mesh.bounds[:, 0]))
    prof = bottom_profile(mesh)

    def bottom_z(x):
        return float(np.interp(x, prof[:, 0], prof[:, 1]))

    def station_x(frac):
        return x0 + frac * stick

    height = float(np.ptp(mesh.bounds[:, 2]))
    feather = np.asarray(landmarks["feather_outline_xy"]) \
        if "feather_outline_xy" in landmarks else None

    def outline_side_y(x, side):
        """y of the feather outline at station x on one side (+1 lat, -1 med)."""
        if feather is None:
            return None
        pts, m = feather, len(feather)
        ys = []
        for i in range(m):
            p, q = pts[i], pts[(i + 1) % m]
            if (p[0] - x) * (q[0] - x) <= 0 and p[0] != q[0]:
                t = (x - p[0]) / (q[0] - p[0])
                ys.append(p[1] + t * (q[1] - p[1]))
        if not ys:
            return None
        return max(ys) if side > 0 else min(ys)

    girths, angles = {}, {}
    # ball girth: oblique plane through the medial (1st MPJ) and lateral
    # (5th MPJ) joint points on the feather line
    x_m, x_l = station_x(st["medial_joint_fraction"]), \
        station_x(st["lateral_joint_fraction"])
    y_m = outline_side_y(x_m, -1) or 0.0
    y_l = outline_side_y(x_l, +1) or 0.0
    p_med = (x_m, y_m, bottom_z(x_m))
    p_lat = (x_l, y_l, bottom_z(x_l))
    girths["ball"], angles["ball"] = joint_plane_girth(
        mesh, p_med, p_lat, st["sweeps"]["ball"])

    for name in ("waist", "instep"):
        x = station_x(st[f"{name}_fraction"])
        pivot = (x, 0.0, bottom_z(x))
        girths[name], angles[name] = min_tape_girth(mesh, pivot,
                                                    st["sweeps"][name])

    # heel girths: DEFINED measures (not settling tapes) from the rear
    # heel-seat pivot. Short heel anchors on the instep crown point; long
    # heel anchors on the cone peak (REPORT-ONLY — a cone-truncated last has
    # no ankle, so the foot relation long=short+40-46 does not transfer).
    xp = station_x(st["short_heel_pivot_fraction"])
    pivot = np.array([xp, 0.0, bottom_z(xp)])
    xi = station_x(st["instep_fraction"])
    sec_i = _section_points(mesh, (xi, 0, 0), (1, 0, 0))
    crown_z = float(sec_i[:, 2].max()) if sec_i is not None else height
    base_phi = -np.degrees(np.arctan2(xi - pivot[0], crown_z - pivot[2]))
    girths["short_heel"], angles["short_heel"] = min_tape_girth(
        mesh, pivot, (base_phi - 3, base_phi + 3), n_angles=7,
        min_z_extent=0.45 * height)
    peak = mesh.vertices[int(np.argmax(mesh.vertices[:, 2]))]
    phi_pk = -np.degrees(np.arctan2(peak[0] - pivot[0], peak[2] - pivot[2]))
    girths["long_heel"], angles["long_heel"] = min_tape_girth(
        mesh, pivot, (phi_pk - 3, phi_pk + 3), n_angles=7,
        min_z_extent=0.45 * height)

    # widths: caliper across the joint line for tread; stations for the rest
    tread_w = (y_l - y_m) if feather is not None else None
    seat_w = outline_width_at(feather, station_x(st["heel_width_fraction"])) \
        if feather is not None else None
    waist_w = outline_width_at(feather, station_x(st["waist_fraction"])) \
        if feather is not None else None
    backpart_w = outline_width_at(feather, station_x(0.10)) \
        if feather is not None else None

    # heel height convention: bottom-profile z at the heel-seat point
    # (~0.09 of stick) — documented choice
    heel_h = bottom_z(station_x(st["heel_height_fraction"]))
    toe_spring = float(prof[-1][1])
    toe_line_x = landmarks.get("toe_line_x") or (x0 + 0.94 * stick)
    sec = _section_points(mesh, (toe_line_x, 0, 0), (1, 0, 0))
    toe_box_h = float(np.ptp(sec[:, 2])) if sec is not None else None

    # derived angles (last_params.md §F): heel pitch = seat slope over the
    # seat region; wedge angle = seat point to tread contact line
    seat_pts = prof[(prof[:, 0] >= x0 + 0.05 * stick) &
                    (prof[:, 0] <= x0 + 0.15 * stick)]
    heel_pitch = float(np.degrees(np.arctan2(
        seat_pts[0][1] - seat_pts[-1][1], seat_pts[-1][0] - seat_pts[0][0]))) \
        if len(seat_pts) > 1 else None
    i_tread = int(np.argmin(prof[:, 1]))
    wedge = float(np.degrees(np.arctan2(
        heel_h - prof[i_tread][1], prof[i_tread][0] - station_x(st["heel_height_fraction"]))))

    rnd = lambda v: round(v, 2) if v is not None else None
    return {
        "stick_length_mm": round(stick, 2),
        "functional_length_mm": rnd(landmarks.get("functional_length_mm")),
        "ball_girth_mm": rnd(girths["ball"]),
        "waist_girth_mm": rnd(girths["waist"]),
        "instep_girth_mm": rnd(girths["instep"]),
        "short_heel_girth_mm": rnd(girths["short_heel"]),
        "long_heel_girth_mm": rnd(girths["long_heel"]),
        "tread_width_mm": rnd(tread_w),
        "seat_width_mm": rnd(seat_w),
        "waist_width_mm": rnd(waist_w),
        "backpart_width_mm": rnd(backpart_w),
        "heel_height_mm": round(float(heel_h), 2),
        "heel_pitch_deg": rnd(heel_pitch),
        "wedge_angle_deg": rnd(wedge),
        "toe_spring_mm": round(toe_spring, 2),
        "toe_box_height_mm": round(toe_box_h, 2) if toe_box_h else None,
        "cone_peak": {"x_mm": rnd(float(peak[0])), "z_mm": rnd(float(peak[2]))},
        "tape_angles_deg": {k: round(v, 1) for k, v in angles.items() if v is not None},
        "watertight": bool(mesh.is_watertight),
        "volume_l": round(float(mesh.volume) / 1e6, 4) if mesh.is_watertight else None,
    }


if __name__ == "__main__":
    import sys
    mesh = trimesh.load(sys.argv[1], force="mesh")
    lm = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
    print(json.dumps(measure_last(mesh, lm), indent=2))
