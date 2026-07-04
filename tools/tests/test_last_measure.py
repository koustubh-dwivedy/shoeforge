"""Ground-truth tests for tools/last_measure.py against analytic solids.

Closed-form expectations:
- Cylinder (axis X, radius r): vertical section perimeter = 2*pi*r.
  A plane tilted by phi about Y cuts an ellipse with semi-axes r and r/cos(phi)
  -> perimeter grows with |phi|, so the min-tape sweep must return the
  vertical cut (phi ~ 0) and 2*pi*r.
- Box (a x b x c): vertical section perimeter = 2*(b+c); stick length = a.
- Sphere sections through the center: great circle 2*pi*R at every tilt.

Run: .venv/bin/python tools/tests/test_last_measure.py
"""

import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from last_measure import min_tape_girth, tape_perimeter, bottom_profile  # noqa: E402

FAIL = 0


def check(name, got, want, rel_tol=0.001):
    global FAIL
    err = abs(got - want) / abs(want)
    ok = err <= rel_tol
    FAIL += (not ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got:.3f}, want {want:.3f} "
          f"(err {err * 100:.3f}%, tol {rel_tol * 100:.1f}%)")


def cylinder_x(radius=40.0, length=300.0, sections=512):
    c = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    return c


# 1. Cylinder vertical section = 2*pi*r
cyl = cylinder_x()
p = tape_perimeter(cyl, (0, 0, 0), (1, 0, 0))
check("cylinder vertical girth", p, 2 * np.pi * 40.0)

# 2. Cylinder tilted section = Ramanujan ellipse perimeter (r, r/cos(phi))
phi = np.radians(20.0)
a, b = 40.0 / np.cos(phi), 40.0
h = ((a - b) / (a + b)) ** 2
ellipse = np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))
p = tape_perimeter(cyl, (0, 0, 0), (np.cos(phi), 0, np.sin(phi)))
check("cylinder 20deg tilted girth (ellipse)", p, ellipse)

# 3. Min-tape sweep on the cylinder settles at the vertical cut
g, best_phi = min_tape_girth(cyl, (0, 0, 0), (-25, 25), n_angles=51)
check("cylinder min-tape girth", g, 2 * np.pi * 40.0)
check("cylinder min-tape angle ~0", best_phi + 100.0, 100.0, rel_tol=0.02)

# 4. Box: vertical section perimeter and stick length
box = trimesh.creation.box(extents=(280.0, 90.0, 70.0))
box = box.subdivide().subdivide()
p = tape_perimeter(box, (0, 0, 0), (1, 0, 0))
check("box vertical girth", p, 2 * (90.0 + 70.0))
check("box stick length", float(np.ptp(box.bounds[:, 0])), 280.0)

# 5. Sphere: any center section is a great circle
sph = trimesh.creation.icosphere(subdivisions=5, radius=50.0)
for ang in (0.0, 30.0, 55.0):
    r = np.radians(ang)
    p = tape_perimeter(sph, (0, 0, 0), (np.cos(r), 0, np.sin(r)))
    check(f"sphere {ang:.0f}deg great circle", p, 2 * np.pi * 50.0, rel_tol=0.002)

# 6. Bottom profile of the box is flat at z = -35
prof = bottom_profile(box)
check("box bottom profile flat", float(prof[:, 1].mean()), -35.0, rel_tol=0.001)

print(f"\n{'ALL PASS' if FAIL == 0 else f'{FAIL} FAILURE(S)'}")
sys.exit(1 if FAIL else 0)
