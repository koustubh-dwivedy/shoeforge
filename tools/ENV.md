# Environment Record

Recreate with: `python3.13 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt`

## Python
- Interpreter: Python 3.13 (Homebrew, `/opt/homebrew/bin/python3.13`) in `.venv/`
  (3.14 avoided: binary-wheel availability for the geometry stack)
- Key packages (installed 2026-07-04): numpy 2.5.0, scipy 1.18.0, trimesh 4.12.2,
  shapely 2.1.2, pyclipper 1.4.0, ezdxf 1.4.4, svgwrite 1.4.3, matplotlib 3.11.0,
  libigl 2.6.2, rtree 1.4.1, networkx 3.6.1, pillow 12.3.0, pyyaml 6.0.3
- Full pin list: `tools/requirements.txt`

## Blender (Stage 6 only)
- Blender 5.1.2 — `/opt/homebrew/bin/blender` (also `/Applications/Blender.app`)
- Invoked headless only: `blender --background --python <script>`

## Flattening (Stage 4)
- BFF CLI: NOT installed (no Homebrew formula). Per WORKFLOW preference order the
  active flattener is **ARAP via libigl** (installed, imports verified).
- Optional upgrade when Stage 4 starts: build BFF from source
  (github.com/GeometryCollective/boundary-first-flattening) and put `bff` on PATH;
  Stage 4 code should probe for the CLI and prefer it when present.

## Conventions (from WORKFLOW.md)
- Units: mm. X = last length (heel→toe +), Y = medial–lateral (lateral + for right
  foot), Z = up. Geometry code is headless pure Python; Blender never owns
  fit- or pattern-critical data.
