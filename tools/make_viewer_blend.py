"""Package a mesh into a ready-to-open .blend for 3D gate review.

Viewer only — Blender never owns fit- or pattern-critical data (WORKFLOW
rule 6); the .ply remains the artifact of record.

Usage:
    blender --background --python tools/make_viewer_blend.py -- <out.blend> <in1.ply> [in2.ply ...]

Scene: meshes smooth-shaded (material chosen by filename: upper=leather brown,
sole/heel=near-black, else clay), ground plane at z=0 (judge heel pitch / toe
spring against it), sun + fill lights, mm units.
"""

import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
blend_path, ply_paths = args[0], args[1:]

COLORS = {"upper": (0.16, 0.09, 0.05, 1.0), "sole": (0.02, 0.02, 0.02, 1.0),
          "heel": (0.02, 0.02, 0.02, 1.0), "clay": (0.65, 0.55, 0.42, 1.0)}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"

from pathlib import Path
for ply_path in ply_paths:
    bpy.ops.wm.ply_import(filepath=ply_path)
    obj = bpy.context.selected_objects[0]
    stem = Path(ply_path).stem.lower()
    obj.name = stem.upper()
    for poly in obj.data.polygons:
        poly.use_smooth = True
    key = next((k for k in COLORS if k in stem), "clay")
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = COLORS[key]
    bsdf.inputs["Roughness"].default_value = 0.45 if key == "upper" else 0.6
    obj.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=900, location=(140, 0, 0))
ground = bpy.context.active_object
ground.name = "GROUND_z0"
gmat = bpy.data.materials.new("ground")
gmat.use_nodes = True
gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = \
    (0.85, 0.85, 0.87, 1.0)
ground.data.materials.append(gmat)

for name, loc, energy in [("sun", (200, -300, 500), 4.0),
                          ("fill", (-150, 250, 300), 1.5)]:
    light_data = bpy.data.lights.new(name, type="SUN")
    light_data.energy = energy
    light = bpy.data.objects.new(name, light_data)
    light.location = loc
    import math
    light.rotation_euler = (math.radians(35), 0.0,
                            math.atan2(-loc[1], -loc[0]))
    scene.collection.objects.link(light)

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"viewer saved: {blend_path}")
