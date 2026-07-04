"""Overlay reference-image silhouettes onto template-last curves (GATE 2a aid).

Reconciles inspiration images with the modeled last per the workflow's
classification-not-reconstruction philosophy: reference curves are extracted,
scaled, and OVERLAID for the human (and the style-zone parameter edits) to
judge — they never drive geometry directly, and the fit zone stays
measurement-driven.

Corrections applied so the comparison is apples-to-apples:
- ref_top is a SOLE photo: the outsole is wider and longer than the last
  bottom by the welt/sole overhang → the extracted outline is shrunk by
  `sole_overhang_mm` (shapely negative buffer) and length-matched to stick.
- ref_side is a finished shoe: upper thickness, laces and heel block are
  present; the side overlay is qualitative (style zone: toe profile, vamp
  descent) — noted on the plot.

Usage: .venv/bin/python tools/ref_overlay.py data/templates/lasts/round_25mm
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import Polygon

SOLE_OVERHANG_MM = 6.0     # welt + sole edge beyond the last, all round
OUTSOLE_EXTRA_LEN = 12.0   # outsole longer than stick (toe + heel exposure)


def components(img_path, thresh=150):
    gray = np.asarray(Image.open(img_path).convert("L"), dtype=float)
    mask = gray < thresh
    labels, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    return labels, sizes


def sole_outline_mm(img_path, stick_mm):
    """Extract the sole (right-half, largest dark blob) outline; return the
    estimated LAST-bottom outline in mm, heel at x=0, toe at +x."""
    labels, sizes = components(img_path)
    h, w = labels.shape
    best, best_size = None, 0
    for i, s in enumerate(sizes, start=1):
        ys, xs = np.nonzero(labels == i)
        if s > best_size and xs.mean() > w / 2:
            best, best_size = i, s
    m = labels == best
    rows = np.nonzero(m.any(axis=1))[0]
    pts_l, pts_r = [], []
    for r in rows:
        cols = np.nonzero(m[r])[0]
        pts_l.append((r, cols.min()))
        pts_r.append((r, cols.max()))
    # image: sole vertical, toe at top. axis: x_mm along length, y_mm across
    r0, r1 = rows.min(), rows.max()
    scale = (stick_mm + OUTSOLE_EXTRA_LEN) / (r1 - r0)
    ctr = np.mean([c for _, c in pts_l + pts_r])
    poly = [( (r1 - r) * scale, (c - ctr) * scale) for r, c in pts_l] + \
           [( (r1 - r) * scale, (c - ctr) * scale) for r, c in reversed(pts_r)]
    # de-rotate: the photographed sole may be a few degrees off-axis
    arr = np.asarray(poly)
    arr -= arr.mean(axis=0)
    _, vecs = np.linalg.eigh(np.cov(arr.T))
    major = vecs[:, -1] * np.sign(vecs[0, -1])
    rot = np.array([[major[0], major[1]], [-major[1], major[0]]])
    poly = arr @ rot.T
    shrunk = Polygon(poly).buffer(-SOLE_OVERHANG_MM).simplify(0.4)
    xy = np.asarray(shrunk.exterior.coords)
    xy[:, 1] *= -1.0   # ref_top shows a LEFT sole; mirror to right-last frame
    # re-scale length to stick and re-anchor heel at 0
    xy[:, 0] -= xy[:, 0].min()
    xy[:, 0] *= stick_mm / xy[:, 0].max()
    return xy


def side_profile_mm(img_path, stick_mm):
    """Top silhouette + ground line of the side-view shoe, in mm (ground y=0).
    Returns (x, y_top) arrays, toe at +x."""
    labels, sizes = components(img_path)
    keep = [i for i, s in enumerate(sizes, start=1) if s > 0.002 * labels.size]
    m = np.isin(labels, keep)
    cols = np.nonzero(m.any(axis=0))[0]
    c0, c1 = cols.min(), cols.max()
    ground_row = np.nonzero(m.any(axis=1))[0].max()
    scale = (stick_mm + OUTSOLE_EXTRA_LEN) / (c1 - c0)
    xs, tops = [], []
    for c in cols:
        rr = np.nonzero(m[:, c])[0]
        xs.append((c - c0) * scale)
        tops.append((ground_row - rr.min()) * scale)
    x = np.asarray(xs)
    # heel on the left in ref_side? detect: the taller half is the heel/cone
    if np.mean(tops[: len(tops) // 2]) < np.mean(tops[len(tops) // 2:]):
        x = x.max() - x[::-1]
        tops = tops[::-1]
    return x, np.asarray(tops)


if __name__ == "__main__":
    tdir = Path(sys.argv[1])
    lm = json.loads((tdir / "landmarks.json").read_text())
    stick = lm["stick_length_mm"]
    feather = np.asarray(lm["feather_outline_xy"])
    rdir = tdir / "reference"

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), dpi=130)

    ax = axes[0]
    ax.plot(feather[:, 0], feather[:, 1], "k-", lw=1.6,
            label="template feather outline (last bottom)")
    try:
        ref = sole_outline_mm(rdir / "ref_top.jpg", stick)
        ax.plot(ref[:, 0], ref[:, 1], "r--", lw=1.4,
                label=f"ref_top sole − {SOLE_OVERHANG_MM} mm overhang (scaled)")
    except Exception as e:  # noqa: BLE001
        ax.text(0.05, 0.5, f"ref_top extraction failed: {e}", transform=ax.transAxes)
    ax.set_title("Bottom outline: template vs reference sole (mm)")
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(loc="upper left")

    ax = axes[1]
    bp = json.loads((tdir / "shape_params.json").read_text())
    from scipy.interpolate import PchipInterpolator
    f = np.linspace(0, 1, 200)
    zt = PchipInterpolator(*np.asarray(bp["top_profile_z"]["points"]).T)(f)
    zb = PchipInterpolator(*np.asarray(bp["bottom_profile_z"]["points"]).T)(f)
    ax.plot(f * stick, zt, "k-", lw=1.6, label="template crown profile")
    ax.plot(f * stick, zb, "k-", lw=1.0, label="template bottom profile")
    try:
        x, top = side_profile_mm(rdir / "ref_side.jpg", stick)
        ax.plot(x, top, "r--", lw=1.4,
                label="ref_side top silhouette (incl. upper/laces/heel — qualitative)")
    except Exception as e:  # noqa: BLE001
        ax.text(0.05, 0.5, f"ref_side extraction failed: {e}", transform=ax.transAxes)
    ax.axhline(0, color="tab:blue", lw=0.8, label="ground z=0")
    ax.set_title("Side profile: template vs reference shoe (mm) — compare toe/vamp REGION SHAPE, not absolute height")
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(loc="upper right")

    fig.tight_layout()
    out = rdir / "overlay.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"saved {out}")
