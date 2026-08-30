"""Conceptual Blender geometry for the BlackMamba Solar Clock.

VISUALIZATION ONLY — NOT MANUFACTURING GEOMETRY.

The teeth generated here are intentionally simplified radial blocks. They are
not involute profiles and no stress/contact claims should be derived from them.
"""

import math

try:
    import bpy
except ImportError as exc:  # pragma: no cover - Blender-only module
    raise RuntimeError("Run this script inside Blender's Python environment") from exc


def create_visual_spur_gear(
    name: str,
    num_teeth: int,
    pitch_radius: float,
    tooth_height: float,
    thickness: float,
    location=(0.0, 0.0, 0.0),
):
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    faces = []
    steps = num_teeth * 4

    for i in range(steps):
        angle = 2.0 * math.pi * i / steps
        is_tooth = (i % 4) in (1, 2)
        radius = pitch_radius + (
            tooth_height / 2.0 if is_tooth else -tooth_height / 2.0
        )
        x = location[0] + radius * math.cos(angle)
        y = location[1] + radius * math.sin(angle)
        z0 = location[2] - thickness / 2.0
        z1 = location[2] + thickness / 2.0
        verts.extend([(x, y, z0), (x, y, z1)])

    pair_count = len(verts) // 2
    for pair in range(pair_count):
        nxt = (pair + 1) % pair_count
        a = pair * 2
        b = a + 1
        c = nxt * 2 + 1
        d = nxt * 2
        faces.append([a, b, c, d])

    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return obj


def create_flywheel(name="Flywheel", radius=1.2, thickness=0.30, z=0.60):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=thickness, location=(0, 0, z))
    obj = bpy.context.active_object
    obj.name = name
    return obj


def build_clock_core():
    # Conceptual 10:1 visual pair. Real industrial architecture is expected
    # to use a separately engineered multi-path/planetary transmission.
    create_visual_spur_gear(
        "Master_Wheel_Visual",
        num_teeth=100,
        pitch_radius=2.25,
        tooth_height=0.12,
        thickness=0.40,
    )
    create_visual_spur_gear(
        "Stage1_Pinion_Visual",
        num_teeth=10,
        pitch_radius=0.225,
        tooth_height=0.12,
        thickness=0.40,
        location=(2.475, 0.0, 0.0),
    )
    create_flywheel()


if __name__ == "__main__":
    build_clock_core()
