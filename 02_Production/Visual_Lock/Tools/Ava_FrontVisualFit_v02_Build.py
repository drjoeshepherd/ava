"""AVA-FIT-FRONT-02 build: FrontFit_v14 -> FrontVisualFit_v02 (visual-construction refinement).

Run inside Blender against the verified v14 baseline (never saved over):

    blender -b 02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend --factory-startup ^
        --python 02_Production/Visual_Lock/Tools/Ava_FrontVisualFit_v02_Build.py -- ^
        --steps eyes,hair,face,graphite,hands,torso,limbs,feet,materials,modules ^
        --save 02_Production/Visual_Lock/FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend

Optional: --preview <png> renders CAM_CANON_FRONT (locked camera, locked lights) after the build.

Rules this script follows (SIGN AVA-FIT-FRONT-02):
  * Only live GEO_* / live face-control / live joint objects are edited. Legacy Shell_*, Canon_*,
    HairShell_*, HairGroup_* objects are never re-enabled.
  * Rig, bones, constraints, drivers, actions, cameras and lights are not touched. Every object keeps
    its parent armature and parent bone, so articulation is unchanged. Control objects keep their names.
  * Geometry is built in world space from canonical-raster pixel coordinates through the locked
    front camera (600x800, ortho_scale 7.367555, target z 3.387494) and written into each object's
    local space, so the bone-relative attachment is preserved.
  * An object that cannot be fixed in place is replaced by a new production object that takes its
    name; the old one is renamed RETIRED_v02_<name>, render-disabled and moved to a retired
    collection (not deleted). Every replacement is listed in the printed change report.
"""

import argparse
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# Locked front camera -> world mapping (Ava_Camera_Lock_v1.0.json).
PX_PER_UNIT = 800 / 7.367555
CAM_Z = 3.387494

REPORT = {"steps": [], "replaced": [], "retired": [], "edited": [], "created": [], "materials": []}
RIG = "RIG_Ava_Master"


def W(px, py):
    """Canonical pixel (600x800 front frame) -> world (X, Z)."""
    return (px - 300) / PX_PER_UNIT, CAM_Z + (400 - py) / PX_PER_UNIT


def U(pixels):
    """Pixel length -> world units."""
    return pixels / PX_PER_UNIT


def log(kind, item):
    if item not in REPORT[kind]:
        REPORT[kind].append(item)


# ---------------------------------------------------------------------------
# Object / parenting helpers
# ---------------------------------------------------------------------------

def arm():
    return bpy.data.objects[RIG]


def bone_parent_matrix(bone_name):
    """World matrix Blender uses for BONE parenting (posed bone, at the bone tail)."""
    a = arm()
    pb = a.pose.bones[bone_name]
    return a.matrix_world @ pb.matrix @ Matrix.Translation((0.0, pb.length, 0.0))


def update():
    bpy.context.view_layer.update()


def retired_collection():
    name = "AVA_Retired_FrontVisualFit_v02"
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def retire(obj):
    old = obj.name
    obj.name = "RETIRED_v02_" + old
    obj.hide_render = True
    obj.hide_viewport = True
    coll = retired_collection()
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    log("retired", old)
    return obj


def new_object_like(name, data, like):
    """New object linked to the same collections and bone as `like` (world = identity)."""
    obj = bpy.data.objects.new(name, data)
    for c in like.users_collection:
        c.objects.link(obj)
    attach(obj, like.parent, like.parent_type, like.parent_bone)
    return obj


def new_object(name, data, collection_of, bone):
    obj = bpy.data.objects.new(name, data)
    for c in bpy.data.objects[collection_of].users_collection:
        c.objects.link(obj)
    attach(obj, arm(), "BONE", bone)
    log("created", name)
    return obj


def attach(obj, parent, parent_type, parent_bone):
    """Parent with world transform = identity, so mesh data can be authored in world space."""
    obj.parent = parent
    if parent is None:
        obj.matrix_parent_inverse = Matrix.Identity(4)
    elif parent_type == "BONE":
        obj.parent_type = "BONE"
        obj.parent_bone = parent_bone
        obj.matrix_parent_inverse = bone_parent_matrix(parent_bone).inverted()
    else:
        obj.parent_type = parent_type
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_basis = Matrix.Identity(4)


def rebase_to_world(obj):
    """Keep the object, its parent and parent bone, but make its world matrix identity."""
    attach(obj, obj.parent, obj.parent_type, obj.parent_bone)


def set_mesh_world(obj, bm, keep_transform=True, smooth=True):
    """Write a world-space bmesh into obj (local = matrix_world^-1 @ world)."""
    update()
    if keep_transform:
        bm.transform(obj.matrix_world.inverted())
    mesh = bpy.data.meshes.new(obj.name + "_v02")
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    old = obj.data
    mats = [s.material for s in obj.material_slots]
    obj.data = mesh
    for m in mats:
        mesh.materials.append(m)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def subsurf(obj, levels=2):
    for m in list(obj.modifiers):
        if m.type in ("SUBSURF", "SOLIDIFY", "BEVEL"):
            obj.modifiers.remove(m)
    m = obj.modifiers.new("AVA_v02_Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def principled(name, base, rough=0.45, metallic=0.0, spec=0.4, coat=0.0, emission=None, strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = spec
    bsdf.inputs["Coat Weight"].default_value = coat
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    log("materials", name)
    return mat


# ---------------------------------------------------------------------------
# Geometry builders (world space)
# ---------------------------------------------------------------------------

def ellipsoid(center, radii, segments=32, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    bm.transform(Matrix.Translation(center) @ Matrix.Diagonal((*radii, 1.0)))
    return bm


def catmull(points, samples):
    pts = [Vector(p) for p in points]
    pts = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    out = []
    segs = len(pts) - 3
    for i in range(samples):
        t = i / (samples - 1) * segs
        k = min(int(t), segs - 1)
        u = t - k
        p0, p1, p2, p3 = pts[k:k + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


def interp(profile, t):
    """Piecewise-linear profile [(t, value), ...]."""
    for (t0, v0), (t1, v1) in zip(profile, profile[1:]):
        if t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * f
    return profile[-1][1]


def sweep(spine, width, thick_out, thick_in, normal_fn, samples=28, sec=12, power=2.4, twist=None):
    """Lens-section sweep along a spine: broad sculpted lock / shell / capsule.

    width, thick_out, thick_in: profiles over t in [0, 1]. normal_fn(point) -> outward direction.
    """
    path = catmull(spine, samples)
    bm = bmesh.new()
    rings = []
    for i, c in enumerate(path):
        t = i / (samples - 1)
        tan = (path[min(i + 1, samples - 1)] - path[max(i - 1, 0)]).normalized()
        n = Vector(normal_fn(c))
        n = (n - tan * n.dot(tan)).normalized()
        b = tan.cross(n).normalized()
        if twist:
            ang = interp(twist, t)
            n, b = n * math.cos(ang) + b * math.sin(ang), b * math.cos(ang) - n * math.sin(ang)
        w, to, ti = interp(width, t), interp(thick_out, t), interp(thick_in, t)
        ring = []
        for k in range(sec + 1):
            s = -1 + 2 * k / sec
            h = (1 - abs(s) ** power) ** (1 / power)
            ring.append(bm.verts.new(c + b * (s * w / 2) + n * (to * h)))
        for k in range(sec - 1, 0, -1):
            s = -1 + 2 * k / sec
            h = (1 - abs(s) ** power) ** (1 / power)
            ring.append(bm.verts.new(c + b * (s * w / 2 * 0.97) - n * (ti * h)))
        rings.append(ring)
    n_ring = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n_ring):
            bm.faces.new((r0[k], r0[(k + 1) % n_ring], r1[(k + 1) % n_ring], r1[k]))
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        center = bm.verts.new(sum((v.co for v in ring), Vector()) / n_ring)
        for k in range(n_ring):
            a, b2 = ring[k], ring[(k + 1) % n_ring]
            bm.faces.new((center, b2, a) if rev else (center, a, b2))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def capsule(p0, p1, r0, r1, sides=16, rings=10):
    """Rounded capsule between two world points with end radii r0, r1."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = (p1 - p0)
    length = axis.length
    z = axis.normalized()
    x = z.orthogonal().normalized()
    y = z.cross(x)
    bm = bmesh.new()
    rows = []
    profile = []
    for i in range(rings + 1):  # start hemisphere
        a = -math.pi / 2 + (math.pi / 2) * i / rings
        profile.append((r0 * math.sin(a), r0 * math.cos(a)))
    for i in range(1, rings + 1):  # end hemisphere
        a = (math.pi / 2) * i / rings
        profile.append((length + r1 * math.sin(a), r1 * math.cos(a)))
    for zz, rr in profile:
        row = []
        for k in range(sides):
            ang = 2 * math.pi * k / sides
            row.append(bm.verts.new(p0 + z * zz + (x * math.cos(ang) + y * math.sin(ang)) * max(rr, 1e-5)))
        rows.append(row)
    for r0_, r1_ in zip(rows, rows[1:]):
        for k in range(sides):
            bm.faces.new((r0_[k], r0_[(k + 1) % sides], r1_[(k + 1) % sides], r1_[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def torus(center, normal, major, minor, major_seg=64, minor_seg=12, squash=(1.0, 1.0)):
    bm = bmesh.new()
    n = Vector(normal).normalized()
    u = n.orthogonal().normalized()
    v = n.cross(u)
    if abs(n.y) > 0.9:  # facing the camera: keep u = X, v = Z for squash
        u, v = Vector((1, 0, 0)), Vector((0, 0, 1))
    rows = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        radial = (u * math.cos(a) * squash[0] + v * math.sin(a) * squash[1])
        c = Vector(center) + radial * major
        rdir = radial.normalized()
        row = [bm.verts.new(c + (rdir * math.cos(2 * math.pi * j / minor_seg) + n * math.sin(2 * math.pi * j / minor_seg)) * minor)
               for j in range(minor_seg)]
        rows.append(row)
    for i in range(major_seg):
        r0, r1 = rows[i], rows[(i + 1) % major_seg]
        for j in range(minor_seg):
            bm.faces.new((r0[j], r0[(j + 1) % minor_seg], r1[(j + 1) % minor_seg], r1[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def set_curve_world(obj, points_world, radii, bevel, resolution=4, cyclic=False, kind="BEZIER"):
    """Replace a curve object's splines with one world-space spline (taper via point radius)."""
    update()
    inv = obj.matrix_world.inverted()
    cu = obj.data
    cu.splines.clear()
    cu.bevel_mode = "ROUND"
    cu.bevel_depth = bevel
    cu.bevel_resolution = resolution
    cu.extrude = 0.0
    cu.use_fill_caps = True
    if kind == "BEZIER":
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(points_world) - 1)
        for bp, p, r in zip(sp.bezier_points, points_world, radii):
            bp.co = inv @ Vector(p)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            bp.radius = r
    else:
        sp = cu.splines.new("POLY")
        sp.points.add(len(points_world) - 1)
        for pt, p, r in zip(sp.points, points_world, radii):
            pt.co = (*(inv @ Vector(p)), 1.0)
            pt.radius = r
    sp.use_cyclic_u = cyclic
    sp.resolution_u = 12
    return obj


def new_curve_object(name, like_bone, collection_of):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    return new_object(name, cu, collection_of, like_bone)


# ---------------------------------------------------------------------------
# Head surface helpers (for placing face features on the live Shell_Head)
# ---------------------------------------------------------------------------

def surface_y(obj_name, x, z, fallback):
    """Front-most hit of a ray cast along +Y from the camera side at (x, z)."""
    obj = bpy.data.objects[obj_name]
    update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    inv = ev.matrix_world.inverted()
    origin = inv @ Vector((x, -20.0, z))
    direction = (inv.to_3x3() @ Vector((0, 1, 0))).normalized()
    ok, loc, _n, _i = ev.ray_cast(origin, direction)
    return (ev.matrix_world @ loc).y if ok else fallback


# ---------------------------------------------------------------------------
# STEP 1 — EYES
# ---------------------------------------------------------------------------

# Canonical eye geometry, read from Targets/Ava_Target_Front.png and Ava_Geometry_Lock_v1.1.json.
# Key = object suffix (.R = character right = image left). Pixel coordinates in the locked front frame.
#   box    canonical eye-feature box (Geometry Lock eye_bounding_box)
#   amber  canonical amber-iris box implied by the lock (eye box minus the 20 px / 32 px measurement margins)
EYES = {
    ".R": {"box": (189, 208, 279, 314), "amber": (208.5, 239.5, 259.5, 282.5), "dir": -1,
           "lash": [(190.5, 256), (195, 243), (205, 228.5), (219, 217), (232, 213), (247, 214.5), (260, 220.5), (269, 229), (274, 237)],
           "lash_r": [0.45, 0.85, 1.0, 1.0, 1.0, 0.85, 0.7, 0.5, 0.3],
           "lid": [(198, 274), (210, 284), (226, 289.5), (243, 289), (257, 283), (266, 274)],
           "brow": [(188, 184), (212, 174), (240, 173)]},
    ".L": {"box": (317, 204, 404, 303), "amber": (336.5, 235.5, 384.5, 271.5), "dir": 1,
           "lash": [(402.5, 246), (399, 232), (390, 218), (376, 210), (362, 208), (348, 210), (337, 216.5), (330, 225), (326, 233)],
           "lash_r": [0.45, 0.85, 1.0, 1.0, 1.0, 0.85, 0.7, 0.5, 0.3],
           "lid": [(399, 263), (388, 272.5), (373, 278), (357, 277.5), (344, 272), (336, 263)],
           "brow": [(343, 170), (368, 160), (394, 166)]},
}
LIMBAL_EDGE = 0.90   # iris radius fraction where the amber region ends and the limbal band begins


def smooth_points(points, radii, samples=40):
    pts = catmull([Vector((p[0], 0.0, p[1])) for p in points], samples)
    rad = [interp([(i / (len(radii) - 1), r) for i, r in enumerate(radii)], j / (samples - 1)) for j in range(samples)]
    return [(p.x, p.z) for p in pts], rad


def face_curve(obj, pixel_points, radii, bevel_px, depth_fn):
    xz, rad = smooth_points([W(px, py) for px, py in pixel_points], radii)
    pts = [(x, depth_fn(x, z), z) for x, z in xz]
    set_curve_world(obj, pts, rad, bevel=U(bevel_px), resolution=3, kind="POLY")


def step_eyes():
    lash_mat = principled("MAT_Ava_Lash_v02", (0.018, 0.016, 0.015), rough=0.42, spec=0.35)
    lid_mat = principled("MAT_Ava_LowerLid_v02", (0.22, 0.18, 0.16), rough=0.5, spec=0.3)
    seam_mat = principled("MAT_Ava_EyeSeam_v02", (0.05, 0.046, 0.043), rough=0.75, spec=0.12)
    sclera_mat = principled("MAT_Ava_Sclera_v02", (0.80, 0.795, 0.775), rough=0.32, spec=0.4)
    catch_mat = principled("MAT_Ava_Catchlight_v02", (1.0, 1.0, 1.0), rough=0.2, emission=(1.0, 0.98, 0.95), strength=2.5)
    pupil_mat = principled("MAT_Ava_Pupil_v02", (0.004, 0.003, 0.002), rough=0.25, spec=0.35)
    brow_mat = principled("MAT_Ava_Brow_v02", (0.36, 0.33, 0.31), rough=0.6, spec=0.3)
    iris_mat = iris_material()

    for side, e in EYES.items():
        x0, y0, x1, y1 = e["box"]
        ax0, ay0, ax1, ay1 = e["amber"]
        lash_top = min(p[1] for p in e["lash"])

        # Iris disc: near-round, tucked under the lash line. Its amber region (inside the limbal band)
        # covers the canonical amber box, so the locked eye-measurement window is preserved.
        rx_px = (ax1 - ax0) / 2 / LIMBAL_EDGE
        rz_px = 1.1 * rx_px
        c_px = (ax0 + ax1) / 2
        c_py = ay1 - LIMBAL_EDGE * rz_px
        v_top = (c_py - ay0) / rz_px
        cx, cz = W(c_px, c_py)
        irx, irz = U(rx_px), U(rz_px)

        # Sclera: subtle off-white lens sized to the canonical eye opening, set just proud of the face.
        sclera = bpy.data.objects["Eye_Sclera" + side]
        xs = [p[0] for p in e["lash"]] + [p[0] for p in e["lid"]]
        open_x0, open_x1 = min(xs) + 4, max(xs) - 4
        open_y0, open_y1 = lash_top + 3, max(p[1] for p in e["lid"])
        sx, sz = W((open_x0 + open_x1) / 2, (open_y0 + open_y1) / 2)
        front = surface_y("Shell_Head", sx, sz, -1.0)
        sclera_front = front - 0.11
        bm = ellipsoid((sx, sclera_front + 0.09, sz), (U((open_x1 - open_x0) / 2), 0.09, U((open_y1 - open_y0) / 2)), 48, 24)
        for m in list(sclera.modifiers):
            sclera.modifiers.remove(m)
        rebase_to_world(sclera)
        set_mesh_world(sclera, bm)
        set_material(sclera, sclera_mat)
        log("edited", sclera.name)

        iris = bpy.data.objects["GEO_CanonicalIris" + side]
        iy = sclera_front + 0.02
        iris_front = iy - 0.045
        bm = ellipsoid((cx, iy, cz), (irx, 0.045, irz), 64, 32)
        uv = bm.loops.layers.uv.new("IrisUV")
        for face in bm.faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[uv].uv = ((co.x - cx) / irx, (co.z - cz) / irz)
        set_mesh_world(iris, bm)
        set_material(iris, iris_mat)
        iris["iris_v_top"] = v_top
        log("edited", iris.name)

        # Pupil: large and round, in the upper iris (canonical dark upper iris).
        pupil = bpy.data.objects["GEO_CanonicalPupil" + side]
        pr = 0.47 * rx_px
        p_px, p_py = c_px, c_py - 0.16 * rz_px
        px_, pz_ = W(p_px, p_py)
        bm = ellipsoid((px_, iris_front + 0.012, pz_), (U(pr), 0.012, U(pr * 1.05)), 32, 16)
        set_mesh_world(pupil, bm)
        set_material(pupil, pupil_mat)
        log("edited", pupil.name)

        # Catchlight: one controlled highlight on the upper-outer edge of the pupil.
        catch = bpy.data.objects["GEO_CanonicalCatchlight" + side]
        kx, kz = W(p_px + 0.62 * pr, p_py - 0.62 * pr)
        bm = ellipsoid((kx, iris_front - 0.004, kz), (U(4.0), 0.008, U(4.4)), 24, 12)
        set_mesh_world(catch, bm)
        set_material(catch, catch_mat)
        log("edited", catch.name)

        # Upper lash line: existing blink control object (name, parent and driver kept).
        lid = bpy.data.objects["CTRL_Eyelid" + side]
        face_curve(lid, e["lash"], e["lash_r"], 3.8,
                   lambda x, z: min(surface_y("Shell_Head", x, z, -1.1) - 0.05, iris_front - 0.03))
        set_material(lid, lash_mat)
        log("edited", lid.name)

        # Lower lid: thin, lighter, subordinate (new production object on DEF_Head).
        name = "GEO_LowerLid" + side
        low = bpy.data.objects.get(name) or new_curve_object(name, "DEF_Head", "CTRL_Eyelid" + side)
        face_curve(low, e["lid"], [0.35, 0.8, 1.0, 1.0, 0.8, 0.35], 1.0,
                   lambda x, z: min(surface_y("Shell_Head", x, z, -1.1) - 0.03, iris_front - 0.02))
        set_material(low, lid_mat)

        # Brow: soft, short, light-taupe arc high above the eye (canonical position).
        brow = bpy.data.objects["CTRL_Brow" + side]
        face_curve(brow, e["brow"], [0.4, 1.0, 0.5], 2.2, lambda x, z: surface_y("Shell_Head", x, z, -1.0) - 0.02)
        set_material(brow, brow_mat)
        log("edited", brow.name)

        # Eye-socket seam (same object as the v14 goggle ring): a thin warm-graphite part line on the face
        # shell that closes only the LOWER half of an almond socket, from the inner lash end round to the
        # outer lash flick. The thick upper lash line is the top of the socket, so no line floats above the
        # eye. Its inner and lower extremes sit on the canonical eye box.
        rim = bpy.data.objects["GEO_EyeRim" + side]
        line_px = 1.6
        bcx, bcy = (x0 + x1) / 2, (y0 + y1) / 2
        a_px, b_px = (x1 - x0 + 1) / 2 - line_px / 2 + 0.6, (y1 - y0 + 1) / 2 - line_px / 2 + 0.6
        pts, rad = [], []
        n = 72
        for i in range(n):
            th = math.radians(-24 + (228 * i / (n - 1)))
            px = bcx - e["dir"] * a_px * math.cos(th)
            py = bcy + b_px * math.sin(th)
            x, z = W(px, py)
            pts.append((x, surface_y("Shell_Head", x, z, -1.1) - 0.004, z))
            edge = min(i, n - 1 - i) / 8.0
            rad.append(min(1.0, 0.35 + 0.65 * edge))
        set_curve_world(rim, pts, rad, bevel=U(line_px / 2), resolution=2, cyclic=False, kind="POLY")
        set_material(rim, seam_mat)
        log("edited", rim.name)


def iris_material():
    """Dimensional amber iris: deep upper iris, luminous gold lower iris, dark limbal band.

    Driven by the world-aligned 'IrisUV' map (u, v in [-1, 1]) and the object property iris_v_top.
    Hue is the locked amber (Ava_Material_Lock_v1.0.json amber_emission.rgb_linear); only value varies.
    """
    name = "MAT_Ava_Iris_v02"
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    L = nt.links.new

    def math_node(op, a=None, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def map_range(value, fmin, fmax, tmin=0.0, tmax=1.0, smooth=True):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
        n.clamp = True
        for key, v in (("Value", value), ("From Min", fmin), ("From Max", fmax), ("To Min", tmin), ("To Max", tmax)):
            if isinstance(v, (int, float)):
                n.inputs[key].default_value = v
            else:
                L(v, n.inputs[key])
        return n.outputs[0]

    def mix_rgb(fac, a, b):
        n = nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"
        L(fac, n.inputs["Factor"])
        for key, v in (("A", a), ("B", b)):
            if isinstance(v, tuple):
                n.inputs[key].default_value = (*v, 1.0)
            else:
                L(v, n.inputs[key])
        return n.outputs["Result"]

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "IrisUV"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(uvn.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_type = "OBJECT"; attr.attribute_name = "iris_v_top"
    vt = attr.outputs["Fac"]
    r = math_node("SQRT", math_node("ADD", math_node("MULTIPLY", u, u), math_node("MULTIPLY", v, v)))

    limb = map_range(r, LIMBAL_EDGE - 0.03, LIMBAL_EDGE + 0.05)
    # Deep upper iris: a soft radial shade around the pupil (pupil sits at v = +0.16) plus gentle top darkening.
    dv = math_node("SUBTRACT", v, 0.16)
    dp = math_node("SQRT", math_node("ADD", math_node("MULTIPLY", u, u), math_node("MULTIPLY", dv, dv)))
    shade = math_node("MAXIMUM", map_range(dp, 0.66, 0.40), math_node("MULTIPLY", map_range(v, 0.30, 0.92), 0.92))
    top = shade
    bright = map_range(v, -0.9, 0.5, 1.0, 0.55, smooth=False)

    amber = (1.0, 0.43, 0.008)
    base = mix_rgb(top, (0.16, 0.0688, 0.0013), (0.03, 0.0129, 0.0002))
    base = mix_rgb(limb, base, (0.008, 0.005, 0.003))
    L(base, bsdf.inputs["Base Color"])
    emis = nt.nodes.new("ShaderNodeVectorMath"); emis.operation = "SCALE"
    emis.inputs[0].default_value = amber
    L(bright, emis.inputs["Scale"])
    L(emis.outputs[0], bsdf.inputs["Emission Color"])
    strength = math_node("MULTIPLY", math_node("SUBTRACT", 1.0, limb), math_node("SUBTRACT", 1.0, top))
    L(math_node("MULTIPLY", strength, 1.15), bsdf.inputs["Emission Strength"])
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    bsdf.inputs["Coat Weight"].default_value = 0.0
    L(bsdf.outputs[0], out.inputs[0])
    log("materials", name)
    return mat


# ---------------------------------------------------------------------------
# STEP 2 — HAIR: nine sculpted bob masses (crown cap + eight broad overlapping locks)
# ---------------------------------------------------------------------------

# Crown cap ellipsoid fitted to the canonical head silhouette rows 37..150 (pixels -> world).
CAP_CENTER_PX = (292.0, 215.0)
CAP_RADII_PX = (180.0, 178.0)
CAP_Y, CAP_RY = 0.12, 1.40


def cap_frame():
    cx, cz = W(*CAP_CENTER_PX)
    return Vector((cx, CAP_Y, cz)), Vector((U(CAP_RADII_PX[0]), CAP_RY, U(CAP_RADII_PX[1])))


def cap_front_y(x, z, inset=0.0):
    c, r = cap_frame()
    q = 1 - ((x - c.x) / r.x) ** 2 - ((z - c.z) / r.z) ** 2
    return c.y - r.y * math.sqrt(max(q, 0.0)) + inset


def outward(p):
    c, r = cap_frame()
    d = Vector(((p[0] - c.x) / r.x ** 2, (p[1] - c.y) / r.y ** 2, (p[2] - c.z) / r.z ** 2))
    return d.normalized()


def facing(k):
    """Normal = outward from the crown blended toward the camera, so broad sides face the front view."""
    return lambda p: (outward(p) + Vector((0, -k, 0))).normalized()


def lock_points(spec, depth):
    pts, widths = [], []
    for px, py, w in spec:
        x, z = W(px, py)
        pts.append(Vector((x, depth(x, z, px, py), z)))
        widths.append(U(w))
    n = len(widths)
    return pts, [(i / (n - 1), widths[i]) for i in range(n)]


def head_or(fallback, offset):
    def depth(x, z, px, py):
        y = surface_y("Shell_Head", x, z, None)
        return (y - offset) if y is not None else fallback
    return depth


# Each lock: spine (px, py, width_px) traced from the canonical raster's lock edges, depth rule,
# thickness toward the camera / behind, normal blend, and the live object it rebuilds.
HAIR_LOCKS = {
    # Main fringe: from the parting, sweeping across the forehead to the image-left temple.
    "GEO_HairFringe_C": {"bone": "SEC_Hair_1.R", "spine": [
        (306, 44, 16), (301.5, 70, 60), (276.5, 83, 72), (250, 101, 80), (226.5, 119, 80), (207.5, 137.5, 79),
        (189, 157.5, 68), (174.5, 176.5, 55), (164, 197, 35), (160, 220, 6)],
        "depth": lambda x, z, px, py: min(cap_front_y(x, z, -0.03), (surface_y("Shell_Head", x, z, -0.6) or -0.6) - 0.10),
        "out": [(0, 0.075), (0.5, 0.09), (1, 0.03)], "in": [(0, 0.05), (1, 0.02)], "k": 1.6},
    # Outer lock on the image-left crown/temple, over the top of the listening module.
    "GEO_HairFringe_R": {"bone": "SEC_Hair_3.R", "spine": [
        (246, 60, 44), (210, 76, 54), (180.5, 95, 49), (158.5, 115, 53), (142, 135, 52), (130.5, 155, 49),
        (116, 175, 60), (106, 195, 66), (108, 214, 30), (116, 224, 6)],
        "depth": lambda x, z, px, py: cap_front_y(x, z, -0.02) if py < 150 else min(cap_front_y(x, z, -0.02), -0.30),
        "out": [(0, 0.08), (0.6, 0.10), (1, 0.04)], "in": [(0, 0.06), (1, 0.03)], "k": 1.6},
    # Fringe sweeping from the parting to the image-right temple.
    "GEO_HairFringe_L": {"bone": "SEC_Hair_1.L", "spine": [
        (310, 43, 16), (314, 69, 63), (345, 76.5, 70), (376.5, 91.5, 68), (401.5, 109, 64), (420.5, 127.5, 61), (433.5, 147.5, 58),
        (441, 170, 50), (437, 203, 10)],
        "depth": lambda x, z, px, py: min(cap_front_y(x, z, -0.03), (surface_y("Shell_Head", x, z, -0.6) or -0.6) - 0.10),
        "out": [(0, 0.07), (0.5, 0.085), (1, 0.03)], "in": [(0, 0.05), (1, 0.02)], "k": 1.6},
    # Image-left side lock framing the face, in front of the module's inner edge, curling in at the jaw.
    "GEO_HairBobSideShell_R": {"bone": "SEC_Hair_2.R", "spine": [
        (168, 150, 34), (161, 195, 42), (161, 245, 46), (167, 290, 44), (180, 320, 38), (200, 337, 26), (220, 343, 8)],
        "depth": head_or(-0.42, 0.10),
        "out": [(0, 0.08), (0.6, 0.11), (1, 0.05)], "in": [(0, 0.06), (1, 0.03)], "k": 1.4},
    # Image-left outer bob volume behind the module: the outer silhouette down to the jaw-line curl.
    "GEO_HairBobLowerCurl_R": {"bone": "SEC_Hair_2.R", "spine": [
        (130, 148, 18), (126, 162, 52), (115, 180, 70), (111, 205, 80), (110, 240, 80), (111, 275, 82), (118, 300, 76),
        (132, 318, 70), (152, 334, 60), (178, 346, 44), (208, 352, 22), (232, 354, 6)],
        "depth": lambda x, z, px, py: 0.22,
        "out": [(0, 0.16), (0.7, 0.2), (1, 0.08)], "in": [(0, 0.22), (1, 0.08)], "k": 2.0},
    # Image-right side lock between face and module, curling in under the cheek.
    "GEO_HairBobSideShell_L": {"bone": "SEC_Hair_2.L", "spine": [
        (430, 150, 26), (436, 200, 30), (440, 250, 32), (442, 292, 38), (436, 322, 38), (421, 336, 24), (407, 341, 7)],
        "depth": head_or(-0.42, 0.10),
        "out": [(0, 0.08), (0.6, 0.10), (1, 0.05)], "in": [(0, 0.06), (1, 0.03)], "k": 1.4},
    # Image-right outer bob volume behind the module.
    "GEO_HairBobLowerCurl_L": {"bone": "SEC_Hair_2.L", "spine": [
        (444, 148, 18), (446, 162, 50), (452, 185, 66), (456, 210, 72), (457, 238, 76), (452, 265, 64), (446, 285, 53),
        (440, 305, 41), (432, 324, 36), (414, 338, 30), (392, 346, 18), (372, 350, 6)],
        "depth": lambda x, z, px, py: 0.22,
        "out": [(0, 0.16), (0.7, 0.2), (1, 0.08)], "in": [(0, 0.22), (1, 0.08)], "k": 2.0},
}


# Canonical fringe lower edge (pixels), used as the cap's front hairline; the cap is cut 14 px above it so
# the fringe masses always cover the cut.
HAIRLINE_PX = [(60, 230), (140, 215), (170, 205), (200, 185), (220, 170), (240, 155), (260, 138), (285, 115),
               (305, 98), (330, 105), (355, 115), (380, 130), (400, 145), (415, 165), (425, 185), (440, 200), (540, 215)]


def hairline_z(x):
    px = x * PX_PER_UNIT + 300
    py = interp([(a, b) for a, b in HAIRLINE_PX], px) if px > HAIRLINE_PX[0][0] else HAIRLINE_PX[0][1]
    return W(px, py - 30)[1]


def build_cap(obj):
    c, r = cap_frame()
    bm = ellipsoid(c, r, 256, 128)
    doomed = [f for f in bm.faces
              if (lambda m: m.y < 0.02 and m.z < hairline_z(m.x))(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    doomed = [f for f in bm.faces if f.calc_center_median().z < 4.15]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    rebase_to_world(obj)
    set_mesh_world(obj, bm)
    sol = obj.modifiers.new("AVA_v02_Thickness", "SOLIDIFY")
    sol.thickness = 0.05
    sol.offset = -1.0
    return obj


def hair_material():
    """Silver-white sculpted hair: cool mid-tone body, soft sheen, and darker cavity shading where each
    broad mass turns away from the view, so overlapping masses read as separate sculpted sections."""
    mat = bpy.data.materials["MAT_Ava_HairSilver"]
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in list(nt.nodes):
        if n.name.startswith("AVA_v02_"):
            nt.nodes.remove(n)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.name = "AVA_v02_Facing"
    lw.inputs["Blend"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.name = "AVA_v02_CavityRamp"
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].position = 0.20; cr.elements[0].color = (0.80, 0.81, 0.85, 1)
    cr.elements[1].position = 0.80; cr.elements[1].color = (0.20, 0.21, 0.24, 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.36
    bsdf.inputs["Metallic"].default_value = 0.05
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    log("materials", mat.name)
    return mat


def step_hair():
    hair_mat = hair_material()
    cap = bpy.data.objects["GEO_HairBobCap_C"]
    build_cap(cap)
    log("edited", cap.name)
    for name, spec in HAIR_LOCKS.items():
        pts, width = lock_points(spec["spine"], spec["depth"])
        bm = sweep(pts, width, spec["out"], spec["in"], facing(spec["k"]), samples=40, sec=14, power=2.0)
        old = bpy.data.objects[name]
        if old.type != "MESH":
            # Curve tube fringe cannot carry a sculpted lens section: replace with a production mesh
            # object that takes the name, collections, parent armature and parent bone.
            retire(old)
            obj = new_object_like(name, bpy.data.meshes.new(name + "_v02"), old)
            obj.data.materials.append(hair_mat)
            log("replaced", "%s (CURVE tube) -> %s (MESH sculpted lock), parent %s" % (name, name, spec["bone"]))
            set_mesh_world(obj, bm)
        else:
            for m in list(old.modifiers):
                old.modifiers.remove(m)
            rebase_to_world(old)
            set_mesh_world(old, bm)
            obj = old
            log("edited", name)
        if obj.parent_bone != spec["bone"]:
            raise RuntimeError("%s parent bone changed (%s)" % (name, obj.parent_bone))
        set_material(obj, hair_mat)
        subsurf(obj, 1)


# ---------------------------------------------------------------------------
# STEP 3 — FACE: cheek volume, small lower face, minimal nose, dimensional mouth, warm ivory polymer
# ---------------------------------------------------------------------------

# Canonical face landmarks (pixels): cheek volume centres, nose, mouth corners/centre.
CHEEKS_PX = [(240, 312), (368, 306)]
NOSE_PX = (303, 279)
MOUTH_PX = [(282, 299), (292, 303.6), (304, 305.4), (316, 303.4), (327, 297.5)]


def step_face():
    face_mat = bpy.data.materials["MAT_Face_Polymer"]
    bsdf = next(n for n in face_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    # Warm ivory polymer (sRGB ~ 236/226/216): warmer than the white body shell, as in the canonical
    # raster, but low chroma — not peach, not skin.
    bsdf.inputs["Base Color"].default_value = (0.84, 0.76, 0.69, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    bsdf.inputs["Subsurface Weight"].default_value = 0.0
    log("materials", face_mat.name)

    # Shell_Head: broad soft cheeks and a smaller, rounder lower face (vertex displacement in world space;
    # the outer head silhouette above the jaw is left where it was).
    head = bpy.data.objects["Shell_Head"]
    update()
    mw, inv = head.matrix_world, head.matrix_world.inverted()
    mesh = head.data
    centre = mw @ Vector((0, 0, 0))
    cheeks = [Vector((W(*p)[0], 0.0, W(*p)[1])) for p in CHEEKS_PX]
    for v in mesh.vertices:
        p = mw @ v.co
        if p.y > -0.2:
            continue
        n = (p - centre).normalized()
        push = 0.0
        for c in cheeks:
            d2 = (p.x - c.x) ** 2 + (p.z - c.z) ** 2
            push += 0.075 * math.exp(-d2 / (2 * 0.30 ** 2))
        # small lower face: draw the chin region in slightly and forward-round it
        chin = max(0.0, (4.25 - p.z) / 0.35)
        q = p + n * push
        q.x *= 1.0 - 0.07 * min(chin, 1.0)
        q.y -= 0.02 * min(chin, 1.0)
        v.co = inv @ q
    mesh.update()
    log("edited", head.name)
    # Eye features sit on the face surface: re-project them onto the re-sculpted shell (idempotent step).
    step_eyes()

    # Nose: minimal soft bump at the canonical nose position.
    nose = bpy.data.objects["Nose_Minimal"]
    nx, nz = W(*NOSE_PX)
    ny = surface_y("Shell_Head", nx, nz, -1.15)
    set_mesh_world(nose, ellipsoid((nx, ny + 0.012, nz), (U(5.2), 0.045, U(3.8)), 32, 16))
    for m in list(nose.modifiers):
        nose.modifiers.remove(m)
    set_material(nose, face_mat)
    log("edited", nose.name)

    # Mouth: small dimensional crescent (thicker centre, tapered corners) on the existing smile control.
    mouth_mat = principled("MAT_Ava_Mouth_v02", (0.035, 0.02, 0.016), rough=0.38, spec=0.4)
    mouth = bpy.data.objects["CTRL_Mouth"]
    face_curve(mouth, MOUTH_PX, [0.25, 0.75, 1.0, 0.75, 0.25], 1.9,
               lambda x, z: surface_y("Shell_Head", x, z, -1.1) - 0.006)
    set_material(mouth, mouth_mat)
    log("edited", mouth.name)

    # Lower-lip form: a soft polymer swell under the mouth so the mouth reads as geometry, not a line.
    lip = bpy.data.objects.get("GEO_MouthLip_C") or new_object("GEO_MouthLip_C", bpy.data.meshes.new("GEO_MouthLip_C"), "Shell_Head", "DEF_Head")
    lx, lz = W(304, 309.5)
    ly = surface_y("Shell_Head", lx, lz, -1.1)
    set_mesh_world(lip, ellipsoid((lx, ly + 0.02, lz), (U(13), 0.035, U(3.4)), 32, 12))
    set_material(lip, face_mat)


# ---------------------------------------------------------------------------
# Body helpers
# ---------------------------------------------------------------------------

def bone_head(name):
    a = arm()
    return a.matrix_world @ a.pose.bones[name].head


def bone_tail(name):
    a = arm()
    return a.matrix_world @ a.pose.bones[name].tail


def toward_camera(_p):
    return Vector((0.0, -1.0, 0.0))


def vertical_sweep(px, py_top, py_bottom, widths_px, out, back, y_center=0.0, power=2.2, samples=36):
    """Front-facing rounded form defined by canonical pixel rows: widths_px = [(py, width_px), ...]."""
    x, z0 = W(px, py_top)
    _, z1 = W(px, py_bottom)
    spine = [Vector((x, y_center, z0 + (z1 - z0) * i / 8)) for i in range(9)]
    span = py_bottom - py_top
    width = [((py - py_top) / span, U(w)) for py, w in widths_px]
    return sweep(spine, width, out, back, toward_camera, samples=samples, sec=16, power=power)


def rebuild(name, bm, mat=None, sub=1, keep_mods=False):
    obj = bpy.data.objects[name]
    if not keep_mods:
        for m in list(obj.modifiers):
            obj.modifiers.remove(m)
    rebase_to_world(obj)
    set_mesh_world(obj, bm)
    if mat is not None:
        set_material(obj, mat)
    if sub:
        subsurf(obj, sub)
    log("edited", name)
    return obj


def graphite():
    return bpy.data.materials["MAT_Ava_Graphite"]


def white():
    return bpy.data.materials["MAT_Ava_CeramicWhite"]


def side_px(px_image_left, side):
    """Mirror an image-left pixel x about the canonical body centre (x = 298) for the image-right side."""
    return px_image_left if side == "R" else 596 - px_image_left


# Canonical body landmarks (pixels, image-left side; image-right mirrored about x = 298 unless given).
NECK = {"x": 302, "top": 338, "bottom": 374, "radius_px": 30}
COLLAR_PY = 366
SHOULDER_SOCKET = {"R": (233, 398), "L": (364, 398)}
HIP_BLOCK = {"R": (245, 481), "L": (353, 481)}
KNEE = {"R": (250, 606), "L": (355, 606)}


# ---------------------------------------------------------------------------
# STEP 4 — GRAPHITE STRUCTURE (functional articulation only)
# ---------------------------------------------------------------------------

def step_graphite():
    g = graphite()
    # Neck interface: a graphite column between chin and torso, with a collar ring at the torso opening.
    x, z_top = W(NECK["x"], NECK["top"])
    _, z_bot = W(NECK["x"], NECK["bottom"])
    r = U(NECK["radius_px"])
    bm = capsule((x, 0.0, z_bot), (x, 0.0, z_top), r, r * 0.92, sides=32, rings=8)
    # Head/neck interface: the column flares under the jaw (canonical dark neck mass below the chin).
    for v in bm.verts:
        t = max(0.0, min(1.0, (v.co.z - z_bot) / (z_top - z_bot)))
        k = 1.0 + 0.55 * t ** 2.2
        v.co.x = x + (v.co.x - x) * k
        v.co.y *= 0.85 + 0.15 * k
    rebuild("Joint_Neck", bm, g, sub=0)
    cx, cz = W(NECK["x"], COLLAR_PY)
    rebuild("GEO_NeckCollar_C", torus((cx, 0.0, cz), (0, 0, 1), U(36), U(5.5), 64, 16, squash=(1.0, 0.82)), g, sub=0)

    for side in ("L", "R"):
        sgn = 1 if side == "L" else -1
        # Shoulder articulation: socket between torso side and upper-arm shell.
        px, py = SHOULDER_SOCKET[side]
        sx, sz = W(px, py)
        rebuild("Joint_Shoulder." + side, ellipsoid((sx, -0.04, sz), (U(13), 0.36, U(34)), 32, 16), g, sub=0)
        # Elbow: graphite ball at the forearm pivot.
        e = bone_head("DEF_Forearm." + side)
        rebuild("Joint_Elbow." + side, ellipsoid((e.x, e.y - 0.02, e.z), (0.175, 0.19, 0.175), 32, 16), g, sub=0)
        # Wrist: graphite cuff ring around the forearm axis at the hand pivot.
        h = bone_head("DEF_Hand." + side)
        axis = (h - bone_head("DEF_Forearm." + side)).normalized()
        rebuild("Joint_Wrist." + side, torus(h - axis * 0.02, axis, 0.155, 0.07, 48, 16), g, sub=0)
        # Hip articulation: graphite blocks at the waist sides, above the thigh shells.
        px, py = HIP_BLOCK[side]
        hx, hz = W(px, py)
        rebuild("Joint_Hip." + side, ellipsoid((hx, -0.02, hz), (U(20), 0.40, U(25)), 32, 16), g, sub=0)
        # Knee: graphite cap between thigh and shin shells.
        px, py = KNEE[side]
        kx, kz = W(px, py)
        rebuild("Joint_Knee." + side, ellipsoid((kx, -0.10, kz), (U(26), 0.34, U(15)), 32, 16), g, sub=0)

    # Foot/leg interface: graphite soles at the canonical sole spans. The front measurement finds floor
    # contact as the bottom-region row with the most dark pixels, so the soles must stay the widest dark
    # rows below the waist (as they are in the canonical raster); bottom row kept at the v14 contact row.
    for side, f in FEET.items():
        x0, x1 = f["sole"]
        cx = (x0 + x1) / 2
        bm = vertical_sweep(cx, 714, 739.0, [(714, x1 - x0 - 22), (720, x1 - x0 - 4), (729, x1 - x0 + 2), (735, x1 - x0 + 4), (739.0, x1 - x0 - 6)],
                            [(0, 0.60), (0.5, 0.68), (1, 0.62)], [(0, 0.50), (1, 0.48)], y_center=-0.18, power=3.2, samples=18)
        rebuild("GEO_FootPad_" + side, bm, g, sub=0)

    # Waist / core: the pelvis becomes the canonical graphite core (V-shaped, narrowing between the thighs).
    bm = vertical_sweep(299, 452, 558, [(452, 128), (470, 138), (490, 112), (510, 90), (530, 70), (545, 54), (558, 30)],
                        [(0, 0.40), (0.5, 0.44), (1, 0.30)], [(0, 0.42), (1, 0.30)], y_center=0.02, power=2.4)
    rebuild("GEO_PelvisShell_C", bm, g, sub=1)


# ---------------------------------------------------------------------------
# STEP 5 — HANDS: graphite palm, individually readable capsule fingers, readable thumb
# ---------------------------------------------------------------------------

def step_hands():
    """Canonical front read: back of the hand toward the camera, compact palm, four fanned two-segment
    fingers curling slightly toward the camera, thumb on the body side. Every piece stays parented to its
    own v14 bone (Shell_Hand -> DEF_Hand, Finger_* -> DEF_<finger>); as in v14 the hand geometry sits
    outward of the hand bones to meet the canonical hand silhouette."""
    g = graphite()

    def rot(v, deg):
        a = math.radians(deg)
        return Vector((v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a)))

    for side in ("L", "R"):
        mirror = (lambda px: 600 - px) if side == "L" else (lambda px: px)

        def P(p2, y):
            x, z = W(mirror(p2.x), p2.y)
            return Vector((x, y, z))

        wrist = Vector((150.0, 518.0))
        axis = Vector((-50.0, 58.0)).normalized()
        perp = Vector((axis.y, -axis.x)) * -1          # points toward the body side / down
        if perp.x < 0:
            perp = -perp
        # Palm (back of the hand facing the camera).
        spine = [P(wrist + axis * 6, -0.05), P(wrist + axis * 26, -0.06), P(wrist + axis * 46, -0.07)]
        bm = sweep(spine, [(0, U(40)), (0.5, U(48)), (1, U(46))], [(0, 0.10), (1, 0.11)], [(0, 0.10), (1, 0.10)],
                   toward_camera, samples=14, sec=14, power=2.8)
        rebuild("Shell_Hand." + side, bm, g, sub=1)
        knuckles = wrist + axis * 47
        fingers = [("Index", 16.5, 7, 33), ("Middle", 5.5, 1, 36), ("Ring", -5.5, -5, 33), ("Pinky", -16.5, -11, 27)]
        for name, off, fan, length in fingers:
            k = knuckles + perp * off
            d1 = rot(axis, fan)
            p1 = k + d1 * (length * 0.55)
            d2 = rot(d1, 9)
            p2 = p1 + d2 * (length * 0.45)
            a0, a1, a2 = P(k, -0.08), P(p1, -0.12), P(p2, -0.19)
            rebuild("Finger_%s1.%s" % (name, side), capsule(a0, a1, U(6.4), U(6.0), 16, 6), g, sub=0)
            rebuild("Finger_%s2.%s" % (name, side), capsule(a1, a2, U(6.0), U(5.4), 16, 6), g, sub=0)
        t0 = wrist + axis * 18 + perp * 21
        t1 = t0 + rot(axis, 22) * 15
        t2 = t1 + rot(axis, 12) * 12
        rebuild("Finger_Thumb1." + side, capsule(P(t0, -0.10), P(t1, -0.16), U(7.0), U(6.4), 16, 6), g, sub=0)
        rebuild("Finger_Thumb2." + side, capsule(P(t1, -0.16), P(t2, -0.21), U(6.4), U(5.6), 16, 6), g, sub=0)

# ---------------------------------------------------------------------------
# STEP 6 — TORSO: smooth warm-white shell, canonical width, graphite waist below, integrated emitter
# ---------------------------------------------------------------------------

def step_torso():
    bm = vertical_sweep(298, 362, 492, [(362, 50), (366, 106), (372, 122), (388, 126), (405, 126), (425, 120),
                                        (442, 110), (456, 100), (468, 84), (480, 56), (492, 10)],
                        [(0, 0.40), (0.35, 0.56), (0.8, 0.50), (1, 0.30)], [(0, 0.40), (0.4, 0.52), (1, 0.32)],
                        y_center=0.0, power=2.3)
    torso = rebuild("GEO_TorsoShell_C", bm, white(), sub=1)
    # Chest emitter at the canonical position, seated on the new shell surface.
    ex, ez = W(297, 402)
    update()
    ey = surface_y("GEO_TorsoShell_C", ex, ez, -0.5)
    rebuild("GEO_ChestBezel_C", torus((ex, ey - 0.005, ez), (0, -1, 0), U(18.0), U(2.0), 64, 12), None, sub=0)
    rebuild("GEO_ChestEmission_C", torus((ex, ey - 0.012, ez), (0, -1, 0), U(13.5), U(3.4), 64, 12), None, sub=0)
    rebuild("GEO_ChestCore_C", ellipsoid((ex, ey + 0.012, ez), (U(6.5), 0.02, U(6.5)), 32, 16), None, sub=0)


# ---------------------------------------------------------------------------
# STEP 7 — LIMBS: rounded product-design shells with deliberate graphite gaps at each joint
# ---------------------------------------------------------------------------

def step_limbs():
    w = white()
    for side in ("L", "R"):
        sgn = 1 if side == "L" else -1
        # Upper arm: tapered capsule from just below the shoulder socket to above the elbow ball.
        a0, a1 = bone_head("DEF_UpperArm." + side), bone_tail("DEF_UpperArm." + side)
        d = (a1 - a0).normalized()
        medial = Vector((-sgn, 0.0, 0.0))
        bm = capsule(a0 + d * 0.04 + medial * 0.02, a1 - d * 0.22 + medial * 0.07, 0.265, 0.245, 32, 10)
        rebuild("GEO_UpperArmShell_" + side, bm, w, sub=0)
        # Forearm: full, rounded, swelling toward the body at the elbow end, tapering into the wrist cuff.
        f0, f1 = bone_head("DEF_Forearm." + side), bone_tail("DEF_Forearm." + side)
        d = (f1 - f0).normalized()
        bm = capsule(f0 + d * 0.20 + medial * 0.12, f1 - d * 0.10, 0.29, 0.215, 32, 10)
        rebuild("GEO_ForearmShell_" + side, bm, w, sub=0)
        # Thigh: large rounded ovoid (canonical position), top tucked under the hip blocks.
        cx = side_px(236, side) if side == "R" else 360
        bm = vertical_sweep(cx, 478, 608, [(478, 26), (484, 74), (494, 104), (510, 116), (540, 118), (572, 112), (592, 100), (602, 80), (608, 46)],
                            [(0, 0.34), (0.5, 0.48), (1, 0.30)], [(0, 0.34), (0.5, 0.46), (1, 0.30)], power=2.1)
        rebuild("GEO_ThighShell_" + side, bm, w, sub=1)
        # Shin: bell shape widening to the ankle, overlapping the foot top.
        # Canonical shins are asymmetric bells that meet at their widest row (the canonical silhouette is
        # continuous from 600 to 700 px), so the inner edges touch there.
        cx, wmax, yc = (228, 152, -0.03) if side == "R" else (359, 142, 0.03)
        bm = vertical_sweep(cx, 606, 706, [(606, 64), (612, 88), (620, 106), (640, 124), (665, wmax - 10), (690, wmax), (706, wmax - 4)],
                            [(0, 0.34), (0.6, 0.48), (1, 0.44)], [(0, 0.34), (1, 0.44)], y_center=yc, power=3.0)
        rebuild("GEO_ShinShell_" + side, bm, w, sub=1)
        # Hip disc: graphite articulation disc on the outer thigh with a thin locked-amber ring (canonical).
        px = 186 if side == "R" else 409
        hx, hz = W(px, 535)
        name = "GEO_HipDisc_" + side
        disc = bpy.data.objects.get(name) or new_object(name, bpy.data.meshes.new(name), "GEO_ThighShell_" + side, "DEF_Thigh." + side)
        outer = hx + sgn * 0.02
        bm = ellipsoid((outer, -0.05, hz), (0.05, 0.20, U(26)), 32, 16)
        set_mesh_world(disc, bm)
        set_material(disc, graphite())
        ring_name = "GEO_HipDiscRing_" + side
        ring = bpy.data.objects.get(ring_name) or new_object(ring_name, bpy.data.meshes.new(ring_name), "GEO_ThighShell_" + side, "DEF_Thigh." + side)
        set_mesh_world(ring, torus((outer + sgn * 0.035, -0.05, hz), (sgn, 0, 0), U(21), U(1.6), 48, 8, squash=(1.0, 1.0)))
        set_material(ring, amber_static_material())


def amber_static_material():
    """Locked amber hue for passive (non-state) indicator rings; not driven by the emotional-light rig."""
    return principled("MAT_Ava_AmberIndicator_v02", (0.30, 0.13, 0.002), rough=0.35, spec=0.3,
                      emission=(1.0, 0.43, 0.008), strength=0.55)


# ---------------------------------------------------------------------------
# STEP 8 — FEET: rounded, compact, stable; toe-cap trim and graphite sole
# ---------------------------------------------------------------------------

FEET = {"R": {"cx": 217, "sole": (157, 277)}, "L": {"cx": 360, "sole": (301, 420)}}


def step_feet():
    w, g = white(), graphite()
    for side, f in FEET.items():
        x0, x1 = f["sole"]
        cx = f["cx"]
        # Foot pod: wide stable base, rounded dome toe, top tucked under the shin bell.
        bm = vertical_sweep(cx, 668, 724, [(668, 80), (684, 106), (700, 120), (716, 122), (724, 112)],
                            [(0, 0.42), (0.5, 0.64), (1, 0.56)], [(0, 0.40), (1, 0.50)], y_center=-0.18, power=3.0)
        rebuild("GEO_FootPod_" + side, bm, w, sub=1)

        # Toe-cap trim: graphite arc where the shin meets the foot (canonical foot/leg interface).
        pts = []
        for px, py in [(cx - 50, 707), (cx - 34, 696), (cx - 14, 690.5), (cx + 10, 690.5), (cx + 32, 696), (cx + 50, 707)]:
            x, z = W(px, py)
            pts.append((x, z))
        spine = []
        update()
        for x, z in pts:
            y = surface_y("GEO_FootPod_" + side, x, z, -0.7)
            spine.append(Vector((x, y - 0.01, z)))
        bm = sweep(spine, [(0, U(3)), (0.5, U(5.5)), (1, U(3))], [(0, 0.02), (1, 0.02)], [(0, 0.02), (1, 0.02)],
                   toward_camera, samples=32, sec=8, power=2.0)
        rebuild("GEO_FootVamp_" + side, bm, g, sub=0)


# ---------------------------------------------------------------------------
# STEP 9 — MATERIALS: locked numeric targets; clean locked-hue amber
# ---------------------------------------------------------------------------

# Emission colour value applied to the driven amber materials. The hue stays the locked amber
# (Ava_Material_Lock_v1.0.json rgb_linear 1.0/0.43/0.008); only its value is scaled ("intensity" is an
# allowed variation). The rig drivers and the keyed light-state values are untouched, so every emotional
# state keeps its relative brightness; the scale only stops AgX from clipping the locked strengths
# (1.95-2.3 at frame 1) to peach.
AMBER_VALUE = 0.26


def lock_values(name, spec_block):
    mat = bpy.data.materials[name]
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if "base_rgb" in spec_block and not bsdf.inputs["Base Color"].is_linked:
        bsdf.inputs["Base Color"].default_value = (*spec_block["base_rgb"], 1.0)
    bsdf.inputs["Metallic"].default_value = spec_block["metallic"]
    bsdf.inputs["Roughness"].default_value = spec_block["roughness"]
    if "specular_ior_level" in spec_block:
        bsdf.inputs["Specular IOR Level"].default_value = spec_block["specular_ior_level"]
    log("materials", name)


def step_materials():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    lock = json.load(open(os.path.join(root, "02_Production", "Visual_Lock", "Ava_Material_Lock_v1.0.json"), encoding="utf-8"))
    lock_values("MAT_Ava_CeramicWhite", lock["white_shell"])
    lock_values("MAT_Ava_Graphite", lock["graphite"])
    lock_values("MAT_Ava_AccentGray", lock["accent_gray"])
    amber = lock["amber_emission"]["rgb_linear"]
    for name in ("MAT_Ava_AmberEmission_C", "MAT_Ava_AmberEmission_L", "MAT_Ava_AmberEmission_R"):
        mat = bpy.data.materials[name]
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Emission Color"].default_value = (amber[0] * AMBER_VALUE, amber[1] * AMBER_VALUE, amber[2] * AMBER_VALUE, 1.0)
        bsdf.inputs["Base Color"].default_value = (0.015, 0.012, 0.010, 1.0)   # diffuse amber washed the light to peach
        bsdf.inputs["Roughness"].default_value = 0.3
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
        log("materials", name)
    # Passive indicator rings and the iris use the same locked hue.
    ind = amber_static_material()
    bsdf = next(n for n in ind.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Emission Color"].default_value = (*amber, 1.0)


# ---------------------------------------------------------------------------
# STEP 10 — LISTENING MODULES: integration only (concept, size and placement unchanged)
# ---------------------------------------------------------------------------

def step_modules():
    accent = bpy.data.materials["MAT_Ava_AccentGray"]
    g = graphite()
    for side in ("L", "R"):
        housing = bpy.data.objects["GEO_ListeningHousing_" + side]
        update()
        c = housing.matrix_world.translation.copy()           # v14 module centre (kept)
        # Clean amber: a thin, even emission ring (was a broad band that clipped to peach).
        rebuild("GEO_ListeningEmission_" + side, torus((c.x, -0.118, c.z), (0, -1, 0), 0.272, 0.021, 96, 12), None, sub=0)
        # Gasket: accent-grey transition ring between housing and light.
        rebuild("GEO_ListeningGasket_" + side, torus((c.x, -0.07, c.z), (0, -1, 0), 0.312, 0.034, 96, 12), accent, sub=0)
        # Core: domed satin graphite so its form reads against the housing.
        rebuild("GEO_ListeningCore_" + side, ellipsoid((c.x, -0.10, c.z), (0.205, 0.05, 0.205), 48, 16), g, sub=0)


# ---------------------------------------------------------------------------

STEPS = {"eyes": step_eyes, "hair": step_hair, "face": step_face, "graphite": step_graphite, "hands": step_hands,
         "torso": step_torso, "limbs": step_limbs, "feet": step_feet, "materials": step_materials, "modules": step_modules}
ORDER = ["eyes", "hair", "face", "graphite", "hands", "torso", "limbs", "feet", "materials", "modules"]


def render_preview(path):
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["CAM_CANON_FRONT"]
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 600, 800, 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default=",".join(ORDER))
    parser.add_argument("--save")
    parser.add_argument("--preview")
    parser.add_argument("--report")
    parser.add_argument("--debug-colors", default="", help="Comma list of object names to tint (preview only; never with --save).")
    args = parser.parse_args(argv)
    if args.debug_colors and args.save:
        sys.exit("--debug-colors is preview-only.")
    source = bpy.data.filepath
    steps = [s for s in ORDER if s in args.steps.split(",")]
    unknown = set(args.steps.split(",")) - set(STEPS)
    if unknown:
        sys.exit("Unknown or unimplemented steps: %s" % sorted(unknown))
    for name in steps:
        STEPS[name]()
        REPORT["steps"].append(name)
        update()
    if args.save:
        target = os.path.abspath(args.save)
        if os.path.abspath(source) == target:
            sys.exit("Refusing to overwrite the source baseline.")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=target, copy=True, compress=False)
    if args.debug_colors:
        palette = [(1, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.3, 1), (1, 0.8, 0), (1, 0, 1), (0, 0.9, 0.9), (1, 0.5, 0), (0.5, 0.2, 1), (0.4, 0.4, 0.4)]
        for i, name in enumerate(args.debug_colors.split(",")):
            obj = bpy.data.objects[name]
            m = principled("DEBUG_%d" % i, palette[i % len(palette)], rough=0.6)
            for slot in obj.material_slots:
                slot.material = m
    if args.preview:
        render_preview(os.path.abspath(args.preview))
    REPORT["source"] = source
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump(REPORT, handle, indent=2)
    print("AVA_V02_BUILD_OK " + json.dumps({"steps": REPORT["steps"], "replaced": REPORT["replaced"], "retired": REPORT["retired"]}))


main()
