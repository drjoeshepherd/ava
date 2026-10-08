"""AVA-FIT-FRONT-03 build: FrontVisualFit_v02 -> FrontVisualFit_v03 (canonical visual and rig-fit correction).

Run inside Blender against the v02 checkpoint (never saved over):

    blender -b 02_Production/Visual_Lock/FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend --factory-startup ^
        --python 02_Production/Visual_Lock/Tools/Ava_FrontVisualFit_v03_Build.py -- ^
        --steps eyes_face,amber,arms,hands,hair,legs,feet,modules ^
        --save 02_Production/Visual_Lock/FrontVisualFit_v03/Ava_v1.0_FrontVisualFit_v03.blend

Geometry helpers are loaded at runtime from Ava_FrontVisualFit_v02_Build.py (unchanged; its SHA-256 is checked
and recorded) so v02 stays reproducible and v03 reuses exactly the same construction code.

Rules (SIGN AVA-FIT-FRONT-03): Material Lock numbers, canonical targets, cameras, lights, colour management,
actions, keyed values and drivers are never edited. The arm rest pose (bones of the arm chains and their IK
target/pole controls) is the only rig change, as authorised in section 4; bone names, hierarchy, constraints
and drivers are unchanged. Legacy and retired objects stay hidden and non-rendering; nothing is deleted.
"""

import argparse
import hashlib
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
V02_BUILDER = os.path.join(TOOLS, "Ava_FrontVisualFit_v02_Build.py")
V02_BUILDER_SHA256 = "EB45BA454A9950C10950B603860A8EF9ABEE94DDAFA0707B237C08942755E5D8"
_src = open(V02_BUILDER, "rb").read()
if hashlib.sha256(_src).hexdigest().upper() != V02_BUILDER_SHA256:
    sys.exit("Ava_FrontVisualFit_v02_Build.py changed; v03 depends on the recorded v02 builder.")
_text = _src.decode("utf-8")
exec(compile(_text[:_text.index('STEPS = {"eyes"')], V02_BUILDER, "exec"), globals())  # noqa: S102 (repo-local, hash-checked)

REPORT.update({"rig_edits": [], "qa_notes": []})


def retire_keep_name(obj):
    """Hide and move to the retired collection without renaming (name stays reserved for semantics)."""
    obj.hide_render = True
    obj.hide_viewport = True
    coll = retired_collection()
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    log("retired", obj.name + " (render-disabled, name kept)")


# ---------------------------------------------------------------------------
# STEP 2 — EYES AND FACE
# ---------------------------------------------------------------------------

# Canonical eye anatomy (pixels), read from Targets/Ava_Target_Front.png with Ava_EyeAnatomy_vNext.py:
#   lash bounds  L 185..262 x 218..257   R 336..408 x 202..248
#   iris (amber) L width 51, bottom 282  R width 48, bottom 271; centres x 234.0 / 360.5
EYES3 = {
    ".R": {"dir": -1, "iris_w": 51, "iris_x": 234.0, "iris_bottom": 282.5,
           "lash": [(187, 254), (192, 240), (203, 228), (218, 221.5), (233, 220.5), (248, 222.5), (258, 228), (262, 234)],
           "lash_r": [0.40, 0.85, 1.0, 1.0, 1.0, 0.9, 0.65, 0.35],
           "lower": [(193, 252), (205, 272), (220, 284), (236, 289), (251, 284), (260, 270), (263, 240)],
           "lid": [(222, 290.5), (236, 292), (249, 289)]},
    ".L": {"dir": 1, "iris_w": 48, "iris_x": 360.5, "iris_bottom": 271.5,
           "lash": [(338, 230), (344, 217), (356, 209), (370, 205.5), (385, 207), (397, 213), (404, 223), (407, 235), (405, 245)],
           "lash_r": [0.35, 0.65, 0.9, 1.0, 1.0, 1.0, 0.9, 0.7, 0.4],
           "lower": [(339, 236), (343, 258), (356, 273), (370, 277.5), (385, 274), (397, 262), (403, 247)],
           "lid": [(355, 279), (369, 281), (382, 278)]},
}
LASH_RADIUS_PX = 3.4
CHEEK_WARM = {"centres_px": [(238, 312), (372, 306)], "radius_px": 28, "colour": (0.86, 0.50, 0.40), "max_mix": 0.85}
FACE_IVORY = (0.85, 0.72, 0.61)   # warm ivory polymer (sRGB ~ 237/220/204); renders near-neutral under the locked grey world


def polyline_y(points, px):
    pts = sorted(points)
    if px <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if px <= x1:
            return y0 + (y1 - y0) * (px - x0) / max(1e-6, x1 - x0)
    return pts[-1][1]


def almond_sclera(e, depth_at):
    """Eye opening shaped by the lids: top under the lash line, bottom along the lower-lid curve."""
    lash_xs = [p[0] for p in e["lash"]]
    x0, x1 = min(lash_xs) + 4, max(lash_xs) - 3
    top_pts = [(x, y + LASH_RADIUS_PX * 0.6) for x, y in e["lash"]]
    bm = bmesh.new()
    nu, nv = 40, 14
    grid = []
    for i in range(nu + 1):
        u = i / nu
        px = x0 + (x1 - x0) * u
        top = polyline_y(top_pts, px)
        bot = max(top + 1.0, polyline_y(e["lower"], px))
        row = []
        for j in range(nv + 1):
            v = j / nv
            py = top + (bot - top) * v
            x, z = W(px, py)
            bulge = 0.045 * (math.sin(math.pi * u) ** 0.6) * (math.sin(math.pi * v) ** 0.6)
            row.append(bm.verts.new((x, depth_at(x, z) - 0.010 - bulge, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cheek_warmth(face_mat, head):
    """Localized cheek warmth in Shell_Head object space (follows the head); base stays warm ivory."""
    nt = face_mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in list(nt.nodes):
        if n.name.startswith("AVA_v03_"):
            nt.nodes.remove(n)
    base = tuple(bsdf.inputs["Base Color"].default_value)
    update()
    inv = head.matrix_world.inverted()
    tex = nt.nodes.new("ShaderNodeTexCoord"); tex.name = "AVA_v03_Coord"; tex.object = head
    mask_sum = None
    for px, py in CHEEK_WARM["centres_px"]:
        x, z = W(px, py)
        y = surface_y("Shell_Head", x, z, -1.0)
        c_local = inv @ Vector((x, y, z))
        r_local = (inv.to_3x3() @ Vector((U(CHEEK_WARM["radius_px"]), 0, 0))).length
        d = nt.nodes.new("ShaderNodeVectorMath"); d.name = "AVA_v03_Dist"; d.operation = "DISTANCE"
        nt.links.new(tex.outputs["Object"], d.inputs[0]); d.inputs[1].default_value = c_local
        m = nt.nodes.new("ShaderNodeMapRange"); m.name = "AVA_v03_Falloff"; m.interpolation_type = "SMOOTHSTEP"
        nt.links.new(d.outputs["Value"], m.inputs["Value"])
        m.inputs["From Min"].default_value = 0.0; m.inputs["From Max"].default_value = r_local * 1.6
        m.inputs["To Min"].default_value = CHEEK_WARM["max_mix"]; m.inputs["To Max"].default_value = 0.0
        if mask_sum is None:
            mask_sum = m.outputs[0]
        else:
            add = nt.nodes.new("ShaderNodeMath"); add.name = "AVA_v03_Add"; add.operation = "MAXIMUM"
            nt.links.new(mask_sum, add.inputs[0]); nt.links.new(m.outputs[0], add.inputs[1]); mask_sum = add.outputs[0]
    mix = nt.nodes.new("ShaderNodeMix"); mix.name = "AVA_v03_CheekMix"; mix.data_type = "RGBA"
    nt.links.new(mask_sum, mix.inputs["Factor"])
    mix.inputs["A"].default_value = base
    mix.inputs["B"].default_value = (*CHEEK_WARM["colour"], 1.0)
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    log("materials", face_mat.name + " (cheek warmth mask)")


def step_eyes_face():
    # Face volume first (eye features are projected onto the final surface).
    head = bpy.data.objects["Shell_Head"]
    update()
    mw, inv = head.matrix_world, head.matrix_world.inverted()
    centre = mw @ Vector((0, 0, 0))
    cheeks = [Vector((W(*p)[0], 0.0, W(*p)[1])) for p in CHEEK_WARM["centres_px"]]
    for v in head.data.vertices:
        p = mw @ v.co
        if p.y > -0.25:
            continue
        n = (p - centre).normalized()
        push = sum(0.05 * math.exp(-((p.x - c.x) ** 2 + (p.z - c.z) ** 2) / (2 * 0.34 ** 2)) for c in cheeks)
        v.co = inv @ (p + n * push)
    head.data.update()
    log("edited", "Shell_Head (cheek / lower-face fullness)")
    face_mat = bpy.data.materials["MAT_Face_Polymer"]
    next(n for n in face_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*FACE_IVORY, 1.0)
    cheek_warmth(face_mat, head)

    sclera_mat = principled("MAT_Ava_Sclera_v03", (0.90, 0.895, 0.875), rough=0.3, spec=0.35)
    lash_mat = bpy.data.materials["MAT_Ava_Lash_v02"]
    lid_mat = principled("MAT_Ava_LowerLid_v03", (0.42, 0.34, 0.30), rough=0.55, spec=0.25)
    head_y = lambda x, z: surface_y("Shell_Head", x, z, -1.0)
    for side, e in EYES3.items():
        # Remove the socket seam (no eye-outline ring of any kind).
        rim = bpy.data.objects.get("GEO_EyeRim" + side)
        if rim and not rim.hide_render:
            retire_keep_name(rim)
        # Sclera = eye opening shaped by the lids.
        sclera = bpy.data.objects["Eye_Sclera" + side]
        rebase_to_world(sclera)
        set_mesh_world(sclera, almond_sclera(e, head_y))
        set_material(sclera, sclera_mat)
        log("edited", sclera.name)
        # Iris: canonical amber width, bottom on the canonical lower lid, top tucked under the lash.
        lash_bottom = min(p[1] for p in e["lash"]) + LASH_RADIUS_PX
        rx_px = (e["iris_w"] - 2.0) / (2 * LIMBAL_EDGE)
        rz_px = min(1.25 * rx_px, max(1.1 * rx_px, (e["iris_bottom"] - (lash_bottom + 2)) / (1 + LIMBAL_EDGE)))
        c_py = e["iris_bottom"] - LIMBAL_EDGE * rz_px
        cx, cz = W(e["iris_x"], c_py)
        front = head_y(cx, cz) - 0.06
        iy = front - 0.01
        iris_front = iy - 0.045
        iris = bpy.data.objects["GEO_CanonicalIris" + side]
        bm = ellipsoid((cx, iy, cz), (U(rx_px), 0.045, U(rz_px)), 64, 32)
        uv = bm.loops.layers.uv.new("IrisUV")
        for f in bm.faces:
            for loop in f.loops:
                co = loop.vert.co
                loop[uv].uv = ((co.x - cx) / U(rx_px), (co.z - cz) / U(rz_px))
        set_mesh_world(iris, bm)
        log("edited", iris.name)
        pr = 0.47 * rx_px
        p_px, p_py = e["iris_x"], c_py - 0.16 * rz_px
        px_, pz_ = W(p_px, p_py)
        set_mesh_world(bpy.data.objects["GEO_CanonicalPupil" + side], ellipsoid((px_, iris_front + 0.012, pz_), (U(pr), 0.012, U(pr * 1.05)), 32, 16))
        kx, kz = W(p_px + 0.62 * pr, p_py - 0.62 * pr)
        set_mesh_world(bpy.data.objects["GEO_CanonicalCatchlight" + side], ellipsoid((kx, iris_front - 0.004, kz), (U(4.0), 0.008, U(4.4)), 24, 12))
        # Strong canonical upper lash line on the existing blink control (name, parent, driver kept).
        lid = bpy.data.objects["CTRL_Eyelid" + side]
        face_curve(lid, e["lash"], e["lash_r"], LASH_RADIUS_PX, lambda x, z: min(head_y(x, z) - 0.05, iris_front - 0.03))
        set_material(lid, lash_mat)
        log("edited", lid.name)
        # Short, subtle lower-lid indication only.
        low = bpy.data.objects["GEO_LowerLid" + side]
        face_curve(low, e["lid"], [0.3, 1.0, 0.3], 0.9, lambda x, z: min(head_y(x, z) - 0.03, iris_front - 0.02))
        set_material(low, lid_mat)
        log("edited", low.name)
    # Brows keep their v02 placement but are re-seated on the re-sculpted face.
    for side, e in EYES.items():
        brow = bpy.data.objects["CTRL_Brow" + side]
        face_curve(brow, e["brow"], [0.4, 1.0, 0.5], 2.2, lambda x, z: head_y(x, z) - 0.02)
    # Mouth, lip and nose re-seated on the re-sculpted face (same canonical positions as v02).
    face_curve(bpy.data.objects["CTRL_Mouth"], MOUTH_PX, [0.25, 0.75, 1.0, 0.75, 0.25], 1.9, lambda x, z: head_y(x, z) - 0.006)
    lx, lz = W(304, 309.5)
    set_mesh_world(bpy.data.objects["GEO_MouthLip_C"], ellipsoid((lx, head_y(lx, lz) + 0.02, lz), (U(13), 0.035, U(3.4)), 32, 12))
    nx, nz = W(*NOSE_PX)
    set_mesh_world(bpy.data.objects["Nose_Minimal"], ellipsoid((nx, head_y(nx, nz) + 0.012, nz), (U(5.2), 0.045, U(3.8)), 32, 16))


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# STEP 3 — AMBER SHADER RESPONSE (locked numbers restored; response shaped by construction)
# ---------------------------------------------------------------------------

AMBER_DRIVEN = ("MAT_Ava_AmberEmission_C", "MAT_Ava_AmberEmission_L", "MAT_Ava_AmberEmission_R")
V14_DRIVEN_BSDF = {"Base Color": (0.32, 0.09, 0.001, 1.0), "Roughness": 0.28, "Specular IOR Level": 0.5, "Metallic": 0.04}
SUBSTRATE_VALUE = 0.06            # visible gold substrate = locked hue at low value (non-emissive)
RESPONSE_EDGE, RESPONSE_CORE = 0.10, 0.26


def material_lock():
    root = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS)))
    return json.load(open(os.path.join(root, "02_Production", "Visual_Lock", "Ava_Material_Lock_v1.0.json"), encoding="utf-8"))


def step_amber():
    """The driven Principled BSDF (node name, Emission Strength driver and keyed state values unchanged)
    carries the LOCKED emission colour again. Its output is blended over a non-emissive gold substrate
    (same locked hue) by a view-facing response mask, so the ring stays readable gold at low emission,
    glows brightest along its camera-facing core, and does not clip to peach under the locked AgX view."""
    amber = tuple(material_lock()["amber_emission"]["rgb_linear"])
    for name in AMBER_DRIVEN:
        mat = bpy.data.materials[name]
        nt = mat.node_tree
        p = nt.nodes["Principled BSDF"]
        p.inputs["Emission Color"].default_value = (*amber, 1.0)
        for key, value in V14_DRIVEN_BSDF.items():
            p.inputs[key].default_value = value
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        for n in list(nt.nodes):
            if n.name.startswith("AVA_v03_"):
                nt.nodes.remove(n)
        sub = nt.nodes.new("ShaderNodeBsdfPrincipled"); sub.name = "AVA_v03_AmberSubstrate"
        sub.inputs["Base Color"].default_value = (amber[0] * SUBSTRATE_VALUE, amber[1] * SUBSTRATE_VALUE, amber[2] * SUBSTRATE_VALUE, 1.0)
        sub.inputs["Roughness"].default_value = 0.4
        sub.inputs["Specular IOR Level"].default_value = 0.15
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.name = "AVA_v03_Facing"; lw.inputs["Blend"].default_value = 0.5
        resp = nt.nodes.new("ShaderNodeMapRange"); resp.name = "AVA_v03_Response"; resp.interpolation_type = "SMOOTHSTEP"
        nt.links.new(lw.outputs["Facing"], resp.inputs["Value"])
        resp.inputs["From Min"].default_value = 0.0; resp.inputs["From Max"].default_value = 0.85
        resp.inputs["To Min"].default_value = RESPONSE_CORE; resp.inputs["To Max"].default_value = RESPONSE_EDGE
        mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "AVA_v03_EmissionResponse"
        nt.links.new(resp.outputs[0], mix.inputs[0])
        nt.links.new(sub.outputs[0], mix.inputs[1])
        nt.links.new(p.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        log("materials", name + " (locked colour restored; substrate + response mix)")


# ---------------------------------------------------------------------------
# STEP 4 — CANONICAL NEUTRAL ARM POSE (rest pose of the arm chains; SIGN section 4)
# ---------------------------------------------------------------------------

# Canonical joint centres (pixels, image-left arm; the image-right arm is the mirror about x = 300), from the dark joint
# components of Targets/Ava_Target_Front.png: elbows (183,447) / (402,452) 42 px wide; wrist cuff centre about (115,515) /
# (485,515); hands (70..137 x 506..584) / (447..517 x 506..581).
# Left and right canonical arms differ by a few pixels (natural asymmetry); the neutral rest pose uses
# their average so the rig stays symmetric. Shoulder pivots are unchanged.
ARM_JOINTS_PX = {"elbow": (190.5, 449.5), "wrist": (117, 515), "hand_tail": (99, 547)}
# Canonical shoulder socket (dark component (221..248, 360..427), centroid (235,390)); mirrored for the other side.
SOCKET3_PX, SOCKET3_R_PX = (235, 392), (13.5, 33)
HAND_TAIL_Y = -0.10


def joint_world(name, side):
    px, py = ARM_JOINTS_PX[name]
    if side == "L":
        px = 600 - px
    x, z = W(px, py)
    return Vector((x, HAND_TAIL_Y if name == "hand_tail" else 0.0, z))


def aim_bone(eb, head, tail):
    """Re-aim an edit bone with the minimal rotation from its old direction (keeps its roll frame)."""
    old = eb.matrix.copy()
    old_dir = (eb.tail - eb.head).normalized()
    new_dir = (tail - head).normalized()
    rot = old_dir.rotation_difference(new_dir).to_matrix()
    m = (rot @ old.to_3x3()).to_4x4()
    m.translation = head
    eb.matrix = m
    eb.length = (tail - head).length
    return eb.matrix @ old.inverted()


def enter_edit(obj):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.view_layer.objects:
        if o.select_get():
            o.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")


def step_arms():
    a = arm()
    update()
    enter_edit(a)
    eb = a.data.edit_bones
    for side in ("L", "R"):
        up, fo, ha = eb["DEF_UpperArm." + side], eb["DEF_Forearm." + side], eb["DEF_Hand." + side]
        before = {n: (tuple(round(v, 4) for v in eb[n].head), tuple(round(v, 4) for v in eb[n].tail), round(eb[n].roll, 5))
                  for n in ("DEF_UpperArm." + side, "DEF_Forearm." + side, "DEF_Hand." + side)}
        shoulder = up.head.copy()
        elbow, wrist, tail = joint_world("elbow", side), joint_world("wrist", side), joint_world("hand_tail", side)
        old_wrist = ha.head.copy()
        fingers = [b for b in eb if b.parent and (b.parent.name == ha.name or (b.parent.parent and b.parent.parent.name == ha.name))]
        finger_old = {b.name: b.matrix.copy() for b in fingers}
        aim_bone(up, shoulder, elbow)
        if fo.use_connect is False:
            pass
        aim_bone(fo, elbow, wrist)
        t_hand = aim_bone(ha, wrist, tail)
        for b in fingers:
            b.matrix = t_hand @ finger_old[b.name]
        delta = wrist - old_wrist
        ik = eb["CTRL_Hand_IK." + side]
        ik.head += delta; ik.tail += delta
        pole = eb["CTRL_ElbowPole." + side]
        off = pole.tail - pole.head
        pole.head = Vector((elbow.x, pole.head.y, elbow.z)); pole.tail = pole.head + off
        REPORT["rig_edits"].append({"side": side, "before": before,
                                    "after": {n: (tuple(round(v, 4) for v in eb[n].head), tuple(round(v, 4) for v in eb[n].tail), round(eb[n].roll, 5))
                                              for n in ("DEF_UpperArm." + side, "DEF_Forearm." + side, "DEF_Hand." + side)},
                                    "moved_rigidly_with_hand": sorted(finger_old), "ik_target_moved_by": tuple(round(v, 4) for v in delta),
                                    "pole_moved_to": tuple(round(v, 4) for v in pole.head)})
    bpy.ops.object.mode_set(mode="OBJECT")
    update()
    # Shells rebuilt on the corrected joints at canonical size (no inflation), with joint gaps.
    w, g = white(), graphite()
    for side in ("L", "R"):
        s0, s1 = bone_head("DEF_UpperArm." + side), bone_tail("DEF_UpperArm." + side)
        d = (s1 - s0).normalized()
        rebuild("GEO_UpperArmShell_" + side, capsule(s0 + d * 0.06, s1 - d * 0.18, 0.225, 0.21, 32, 10), w, sub=0)
        f0, f1 = bone_head("DEF_Forearm." + side), bone_tail("DEF_Forearm." + side)
        d = (f1 - f0).normalized()
        rebuild("GEO_ForearmShell_" + side, capsule(f0 + d * 0.19, f1 - d * 0.09, 0.245, 0.205, 32, 10), w, sub=0)
        rebuild("Joint_Elbow." + side, ellipsoid((f0.x, f0.y - 0.02, f0.z), (0.19, 0.19, 0.185), 32, 16), g, sub=0)
        h = bone_head("DEF_Hand." + side)
        rebuild("Joint_Wrist." + side, torus(h - d * 0.02, d, 0.15, 0.065, 48, 16), g, sub=0)
        px, py = SOCKET3_PX
        sx, sz = W(px if side == "R" else 600 - px, py)
        rebuild("Joint_Shoulder." + side, ellipsoid((sx, -0.04, sz), (U(SOCKET3_R_PX[0]), 0.34, U(SOCKET3_R_PX[1])), 32, 16), g, sub=0)
        # Provisional: the v02 hand pieces carried v14's outward offset from the hand bone; re-seat them on the
        # canonical hand centre until step 5 rebuilds them bone-aligned.
        update()
        objs = [bpy.data.objects["Shell_Hand." + side]] + [bpy.data.objects["Finger_%s%d.%s" % (n, i, side)]
                for n in ("Thumb", "Index", "Middle", "Ring", "Pinky") for i in (1, 2)]
        pts = [o.matrix_world @ Vector(corner) for o in objs for corner in o.bound_box]
        centre = sum(pts, Vector()) / len(pts)
        hx, hz = W(111 if side == "R" else 489, 545)
        delta = Vector((hx - centre.x, 0.0, hz - centre.z))
        for o in objs:
            o.matrix_world = Matrix.Translation(delta) @ o.matrix_world


# ---------------------------------------------------------------------------
# STEP 5 — HAND AND FINGER RIG ALIGNMENT (finger rest bones + bone-aligned geometry)
# ---------------------------------------------------------------------------

# Canonical hand (image-left; pixels): back of the hand toward the camera, wrist cuff at the forearm end, four
# compact fingers fanned slightly and curled, thumb on the body side. Offsets are across the knuckle line
# (positive = toward the body), fan angles in degrees (positive = toward the body).
FINGERS = [("Index", 14.5, 7, 0.150, 0.118), ("Middle", 4.8, 1, 0.162, 0.124), ("Ring", -4.8, -5, 0.152, 0.118), ("Pinky", -14.5, -12, 0.128, 0.104)]
FINGER_R = (0.060, 0.055)
CURL_DEG = (14, 30)          # relaxed neutral curl of segment 1 and 2 toward the palm
THUMB = {"root_along": 15, "root_across": 13, "turn": -12, "len": (0.128, 0.104), "r": (0.064, 0.058)}


def hand_frame(side):
    """World-space hand frame from the corrected DEF_Hand bone: a (down the hand), p (across, toward body),
    n (back-of-hand normal, toward the camera)."""
    h, t = bone_head("DEF_Hand." + side), bone_tail("DEF_Hand." + side)
    a = (t - h); a.y = 0.0; a.normalize()
    p = Vector((-a.z, 0.0, a.x)) if side == "R" else Vector((a.z, 0.0, -a.x))
    if (p.x > 0) != (side == "R"):
        p = -p
    return h, t, a, p, Vector((0.0, -1.0, 0.0))


def rotate_about(v, axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis) @ v


def step_hands():
    a_obj = arm()
    update()
    frames = {s: hand_frame(s) for s in ("L", "R")}
    enter_edit(a_obj)
    eb = a_obj.data.edit_bones
    layout = {}
    for side, (h, t, a, p, n) in frames.items():
        knuckle_line = t + Vector((0.0, -0.02, 0.0))
        for name, off, fan, l1, l2 in FINGERS:
            k = knuckle_line + p * U(off)
            d0 = rotate_about(a, n, fan if side == "R" else -fan)
            curl_axis = p.cross(d0).normalized() if False else d0.cross(n).normalized()
            d1 = rotate_about(d0, curl_axis, CURL_DEG[0]) if False else (d0 * math.cos(math.radians(CURL_DEG[0])) + Vector((0, 1, 0)) * math.sin(math.radians(CURL_DEG[0]))).normalized()
            d2 = (d0 * math.cos(math.radians(CURL_DEG[0] + CURL_DEG[1])) + Vector((0, 1, 0)) * math.sin(math.radians(CURL_DEG[0] + CURL_DEG[1]))).normalized()
            b1, b2 = eb["DEF_%s1.%s" % (name, side)], eb["DEF_%s2.%s" % (name, side)]
            b1.head, b1.tail = k, k + d1 * l1
            b2.head, b2.tail = b1.tail.copy(), b1.tail + d2 * l2
            for b in (b1, b2):
                b.align_roll(n)
            layout[(side, name)] = (k, b1.tail.copy(), b2.tail.copy())
        root = h + a * U(THUMB["root_along"]) + p * U(THUMB["root_across"]) + Vector((0.0, -0.10, 0.0))
        dt = rotate_about(a, n, THUMB["turn"] if side == "R" else -THUMB["turn"])
        dt = (dt + Vector((0.0, -0.75, 0.0))).normalized()
        dt2 = (dt * 0.85 + a * 0.15 + Vector((0.0, 0.25, 0.0))).normalized()
        t1, t2 = eb["DEF_Thumb1." + side], eb["DEF_Thumb2." + side]
        t1.head, t1.tail = root, root + dt * THUMB["len"][0]
        t2.head, t2.tail = t1.tail.copy(), t1.tail + dt2 * THUMB["len"][1]
        for b in (t1, t2):
            b.align_roll(n)
        REPORT["rig_edits"].append({"side": side, "finger_rest_bones": {
            b.name: (tuple(round(v, 4) for v in b.head), tuple(round(v, 4) for v in b.tail), round(b.roll, 5))
            for b in eb if b.name.startswith(("DEF_Index", "DEF_Middle", "DEF_Ring", "DEF_Pinky", "DEF_Thumb")) and b.name.endswith("." + side)}})
    bpy.ops.object.mode_set(mode="OBJECT")
    update()
    g = graphite()
    for side, (h, t, a, p, n) in frames.items():
        # Palm: compact rounded volume from the wrist cuff to the knuckle line (back of the hand to camera).
        spine = [h + a * 0.04 + Vector((0, -0.04, 0)), (h + t) / 2 + Vector((0, -0.05, 0)), t + a * 0.02 + Vector((0, -0.05, 0))]
        bm = sweep(spine, [(0, U(38)), (0.55, U(46)), (1, U(44))], [(0, 0.10), (1, 0.11)], [(0, 0.10), (1, 0.10)],
                   toward_camera, samples=14, sec=14, power=2.6)
        rebuild("Shell_Hand." + side, bm, g, sub=1)
        # Every finger/thumb segment is a capsule exactly on its own bone (head = pivot, along the bone axis).
        for name in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
            for i, r in ((1, 0), (2, 1)):
                bone = "DEF_%s%d.%s" % (name, i, side)
                b0, b1 = bone_head(bone), bone_tail(bone)
                radii = THUMB["r"] if name == "Thumb" else FINGER_R
                rebuild("Finger_%s%d.%s" % (name, i, side), capsule(b0, b1, radii[r], radii[r] * 0.92, 16, 6), g, sub=0)
                obj = bpy.data.objects["Finger_%s%d.%s" % (name, i, side)]
                if obj.parent_bone != bone:
                    raise RuntimeError("%s is parented to %s, expected %s" % (obj.name, obj.parent_bone, bone))


# ---------------------------------------------------------------------------
# STEP 6 — HAIR REFINEMENT (graphite crown structure, parting, sharper overlapping forms, inward-curled bob)
# ---------------------------------------------------------------------------

# Canonical graphite crown band (dark arc visible between the crown layer and the fringes) and parting line.
CROWN_BAND_PX = [(150, 140), (168, 112), (185, 97), (205, 80), (230, 65), (258, 54), (285, 48), (300, 47),
                 (318, 49), (345, 55), (370, 64), (392, 78), (412, 96), (430, 120), (442, 150)]
PARTING_PX = [(300, 49), (302, 64), (304, 80), (305, 96)]

HAIR3 = {
    "GEO_HairFringe_C": [(302.5, 76, 48), (283.5, 85.5, 65), (258, 99.5, 81), (234, 113.5, 89), (213.5, 129, 93),
                         (193, 145, 91), (176.5, 161.5, 84), (164, 182, 65), (160, 222, 8)],
    "GEO_HairFringe_L": [(310, 76, 48), (335, 82.5, 51), (361.5, 92, 52), (386, 107, 52), (405, 124, 52),
                         (420, 144, 52), (431, 165, 49), (437, 187, 34), (433, 205, 6)],
    "GEO_HairFringe_R": [(251, 50, 22), (227, 60, 26), (205, 72, 30), (185, 88, 36), (167, 108, 42), (151, 130, 48),
                         (138, 152, 52), (127, 172, 58), (117, 192, 56), (112, 210, 30), (116, 222, 6)],
    "GEO_HairBobSideShell_R": [(168, 150, 34), (161, 195, 42), (161, 245, 46), (167, 290, 44), (180, 320, 38),
                               (196, 334, 30), (214, 340, 20), (228, 338, 7)],
    "GEO_HairBobSideShell_L": [(430, 150, 26), (436, 200, 30), (440, 250, 32), (442, 292, 38), (436, 322, 38),
                               (424, 334, 28), (410, 339, 18), (398, 336, 6)],
    "GEO_HairBobLowerCurl_R": [(130, 148, 18), (124, 162, 56), (112, 180, 76), (107, 205, 88), (106, 240, 88),
                               (107, 275, 90), (115, 300, 82), (132, 318, 70), (152, 334, 60), (178, 345, 44),
                               (206, 349, 24), (226, 345, 7)],
    "GEO_HairBobLowerCurl_L": [(444, 148, 18), (446, 162, 50), (452, 185, 66), (456, 210, 72), (457, 238, 76),
                               (452, 265, 64), (446, 285, 53), (440, 305, 41), (432, 324, 36), (414, 337, 30),
                               (394, 343, 18), (378, 340, 6)],
}


def sweep_uv(spine, width, thick_out, thick_in, normal_fn, samples=40, sec=14, power=1.7):
    """sweep() plus a UV map (u along the spine, v across) for directional fibre shading."""
    bm = sweep(spine, width, thick_out, thick_in, normal_fn, samples=samples, sec=sec, power=power)
    uv = bm.loops.layers.uv.new("LockUV")
    ring = 2 * sec
    for f in bm.faces:
        for loop in f.loops:
            i = loop.vert.index
            body = samples * ring
            if i < body:
                loop[uv].uv = ((i // ring) / (samples - 1), (i % ring) / ring)
            else:
                loop[uv].uv = (0.0 if i == body else 1.0, 0.5)
    return bm


def hair_material3():
    mat = bpy.data.materials["MAT_Ava_HairSilver"]
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ramp = nt.nodes["AVA_v02_CavityRamp"]
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.82, 0.83, 0.86, 1)
    ramp.color_ramp.elements[1].position = 0.86
    ramp.color_ramp.elements[1].color = (0.34, 0.35, 0.38, 1)
    for n in list(nt.nodes):
        if n.name.startswith("AVA_v03_"):
            nt.nodes.remove(n)
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.name = "AVA_v03_LockUV"; uvn.uv_map = "LockUV"
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.name = "AVA_v03_Fibre"
    wave.wave_type = "BANDS"; wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 9.0; wave.inputs["Distortion"].default_value = 1.5
    wave.inputs["Detail"].default_value = 1.0
    nt.links.new(uvn.outputs["UV"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.name = "AVA_v03_FibreBump"
    bump.inputs["Strength"].default_value = 0.12; bump.inputs["Distance"].default_value = 0.004
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    log("materials", mat.name + " (softer cavity, fibre bump)")
    return mat


def step_hair():
    hair_mat = hair_material3()
    # Crown cap re-centred on the canonical crown (silhouette rows 37..100 are centred near x 297-300).
    global CAP_CENTER_PX, CAP_RADII_PX
    CAP_CENTER_PX, CAP_RADII_PX = (297.0, 215.0), (183.0, 178.0)
    cap = build_cap(bpy.data.objects["GEO_HairBobCap_C"])
    # Trim the cap's low side edge (now hidden by the outer bob volumes) so it cannot poke through them.
    me = cap.data
    bm = bmesh.new(); bm.from_mesh(me)
    update()
    mw = cap.matrix_world
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if (mw @ f.calc_center_median()).z < 4.45], context="FACES")
    bm.to_mesh(me); bm.free()
    set_material(cap, hair_mat)
    log("edited", "GEO_HairBobCap_C (re-centred crown)")
    for name, spine_px in HAIR3.items():
        spec = HAIR_LOCKS[name]
        pts, width = lock_points(spine_px, spec["depth"])
        out = [(t, v * 0.75) for t, v in spec["out"]]
        inn = [(t, v * 0.7) for t, v in spec["in"]]
        obj = bpy.data.objects[name]
        bone = obj.parent_bone
        rebase_to_world(obj)
        set_mesh_world(obj, sweep_uv(pts, width, out, inn, facing(spec["k"])))
        set_material(obj, hair_mat)
        subsurf(obj, 1)
        if obj.parent_bone != bone:
            raise RuntimeError("hair group parent changed for " + name)
        log("edited", name)
    # Graphite crown band and parting (canonical crown structure under the hair; parented to DEF_Head).
    g = graphite()
    pieces = []
    for pts_px, w_px in ((CROWN_BAND_PX, 10.0), (PARTING_PX, 5.0)):
        spine = []
        for px, py in pts_px:
            x, z = W(px, py)
            spine.append(Vector((x, cap_front_y(x, z, -0.012), z)))
        pieces.append(sweep(spine, [(0, U(w_px)), (1, U(w_px))], [(0, 0.03), (1, 0.03)], [(0, 0.03), (1, 0.03)],
                            lambda p: outward(p), samples=48, sec=8, power=2.0))
    bm = bmesh.new()
    for piece in pieces:
        tmp = bpy.data.meshes.new("tmp_band")
        piece.to_mesh(tmp); piece.free()
        bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    name = "GEO_CrownBand_C"
    band = bpy.data.objects.get(name) or new_object(name, bpy.data.meshes.new(name), "GEO_HairBobCap_C", "DEF_Head")
    set_mesh_world(band, bm)
    set_material(band, g)


# ---------------------------------------------------------------------------
# STEP 7 — PELVIS AND LEG REFINEMENT
# ---------------------------------------------------------------------------

def profile_sweep(rows_px, out, back, y_center=0.0, power=2.3, samples=40):
    """Front-facing rounded form along a (possibly slanted) spine: rows_px = [(px, py, width_px), ...]."""
    py0, py1 = rows_px[0][1], rows_px[-1][1]
    spine, width = [], []
    for px, py, wpx in rows_px:
        x, z = W(px, py)
        spine.append(Vector((x, y_center, z)))
        width.append(((py - py0) / (py1 - py0), U(wpx)))
    return sweep(spine, width, out, back, toward_camera, samples=samples, sec=16, power=power)


# Canonical left thigh (image-left): outer edge ~ 178-183 px, inner top slanting away from the core.
THIGH_ROWS_R = [(215, 480, 18), (214, 485, 50), (215, 492, 68), (217, 500, 78), (220, 515, 86), (223, 530, 92), (226, 545, 98),
                (230, 560, 104), (235, 575, 108), (238, 590, 104), (240, 600, 92), (241, 606, 70), (242, 610, 40)]


def step_legs():
    w, g = white(), graphite()
    # Compact rounded graphite core (canonical U-shaped core between the thighs, not a V plate).
    bm = vertical_sweep(299, 462, 557, [(462, 112), (475, 122), (490, 110), (505, 98), (520, 90), (535, 76), (548, 56), (557, 28)],
                        [(0, 0.34), (0.5, 0.40), (1, 0.26)], [(0, 0.38), (1, 0.28)], y_center=0.02, power=2.6)
    rebuild("GEO_PelvisShell_C", bm, g, sub=1)
    # Torso: shallower, higher lower edge so the compact core reads as a rounded U below it.
    bm = vertical_sweep(298, 362, 486, [(362, 50), (366, 106), (372, 122), (388, 126), (405, 126), (425, 120),
                                        (442, 110), (456, 100), (468, 86), (478, 62), (486, 20)],
                        [(0, 0.40), (0.35, 0.56), (0.8, 0.50), (1, 0.30)], [(0, 0.40), (0.4, 0.52), (1, 0.32)],
                        y_center=0.0, power=2.3)
    rebuild("GEO_TorsoShell_C", bm, w, sub=1)
    for side in ("L", "R"):
        px, py = HIP_BLOCK[side]
        hx, hz = W(px, py)
        rebuild("Joint_Hip." + side, ellipsoid((hx, -0.02, hz + U(1)), (U(21), 0.38, U(26)), 32, 16), g, sub=0)
        # Thigh: gently convex ovoid, rounded at both ends (canonical broad thigh, not a box).
        rows = THIGH_ROWS_R if side == "R" else [(596 - px, py, wpx) for px, py, wpx in THIGH_ROWS_R]
        bm = profile_sweep(rows, [(0, 0.28), (0.5, 0.48), (1, 0.30)], [(0, 0.28), (0.5, 0.46), (1, 0.30)], power=2.0)
        rebuild("GEO_ThighShell_" + side, bm, w, sub=1)
        # Knee: visible graphite joint between thigh and shin.
        px, py = KNEE[side]
        kx, kz = W(px, py)
        rebuild("Joint_Knee." + side, ellipsoid((kx, -0.10, kz), (U(30), 0.34, U(15)), 32, 16), g, sub=0)
        # Shin: compact bell, narrow under the knee and flaring to the canonical meeting row.
        cx, wmax, yc = (228, 152, -0.03) if side == "R" else (359, 142, 0.03)
        bm = vertical_sweep(cx, 605, 697, [(605, 70), (610, 100), (620, 110), (640, 120), (660, wmax - 14), (676, wmax - 5),
                                           (686, wmax), (697, wmax - 12)],
                            [(0, 0.34), (0.6, 0.48), (1, 0.44)], [(0, 0.34), (1, 0.44)], y_center=yc, power=2.8)
        rebuild("GEO_ShinShell_" + side, bm, w, sub=1)


# ---------------------------------------------------------------------------
# STEP 8 — FOOT REFINEMENT (domed pods, toe-cap transition, stable sole; floor contact unchanged)
# ---------------------------------------------------------------------------

def step_feet():
    w, g = white(), graphite()
    for side, f in FEET.items():
        x0, x1 = f["sole"]
        cx = (x0 + x1) / 2
        # Softly domed white upper: rounded corners, bulging forward toward the toe.
        bm = profile_sweep([(cx, 674, 40), (cx, 680, 84), (cx, 690, 108), (cx, 702, 120), (cx, 714, 122), (cx, 722, 112)],
                           [(0, 0.40), (0.55, 0.66), (1, 0.62)], [(0, 0.40), (1, 0.50)], y_center=-0.18, power=2.2, samples=24)
        rebuild("GEO_FootPod_" + side, bm, w, sub=1)
        # Graphite toe-cap transition arc on the dome.
        update()
        spine = []
        for px, py in [(cx - 50, 713), (cx - 33, 703), (cx - 12, 698.5), (cx + 12, 698.5), (cx + 33, 703), (cx + 50, 713)]:
            x, z = W(px, py)
            spine.append(Vector((x, surface_y("GEO_FootPod_" + side, x, z, -0.7) - 0.008, z)))
        bm = sweep(spine, [(0, U(3)), (0.5, U(5.5)), (1, U(3))], [(0, 0.02), (1, 0.02)], [(0, 0.02), (1, 0.02)],
                   toward_camera, samples=32, sec=8, power=2.0)
        rebuild("GEO_FootVamp_" + side, bm, g, sub=0)
        # Stable graphite sole tray (widest dark rows below the waist; bottom row = v14 floor contact).
        bm = profile_sweep([(cx, 713, x1 - x0 - 26), (cx, 718, x1 - x0 - 2), (cx, 728, x1 - x0 + 4), (cx, 735, x1 - x0 + 4),
                            (cx, 739.0, x1 - x0 - 8)], [(0, 0.62), (0.5, 0.70), (1, 0.64)], [(0, 0.50), (1, 0.48)],
                           y_center=-0.18, power=3.0, samples=18)
        rebuild("GEO_FootPad_" + side, bm, g, sub=0)


# ---------------------------------------------------------------------------
# STEP 9 — LISTENING-MODULE PRESENTATION (concept, scale, placement and left/right control unchanged)
# ---------------------------------------------------------------------------

def step_modules():
    accent, g = bpy.data.materials["MAT_Ava_AccentGray"], graphite()
    for side in ("L", "R"):
        c = bpy.data.objects["GEO_ListeningHousing_" + side].matrix_world.translation.copy()
        # Luminous locked-amber ring (driven material MAT_Ava_AmberEmission_<side> unchanged): fuller tube so the
        # bright camera-facing core of the response shader reads as light, with deep-gold edges.
        rebuild("GEO_ListeningEmission_" + side, torus((c.x, -0.118, c.z), (0, -1, 0), 0.272, 0.029, 96, 16), None, sub=0)
        # Restrained gasket: thin accent-grey line between housing and light.
        rebuild("GEO_ListeningGasket_" + side, torus((c.x, -0.075, c.z), (0, -1, 0), 0.312, 0.018, 96, 10), accent, sub=0)
        rebuild("GEO_ListeningCore_" + side, ellipsoid((c.x, -0.10, c.z), (0.215, 0.05, 0.215), 48, 16), g, sub=0)
        mat = bpy.data.objects["GEO_ListeningEmission_" + side].material_slots[0].material.name
        if mat != "MAT_Ava_AmberEmission_" + side:
            raise RuntimeError("ring %s lost its independent driven material (%s)" % (side, mat))


def render_preview(path):
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["CAM_CANON_FRONT"]
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 600, 800, 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


STEPS3 = {"eyes_face": step_eyes_face, "amber": step_amber, "arms": step_arms, "hands": step_hands, "hair": step_hair, "legs": step_legs, "feet": step_feet, "modules": step_modules}
ORDER3 = ["eyes_face", "amber", "arms", "hands", "hair", "legs", "feet", "modules"]


def main3():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default=",".join(ORDER3))
    parser.add_argument("--save")
    parser.add_argument("--preview")
    parser.add_argument("--report")
    parser.add_argument("--debug-colors", default="", help="Preview only: comma list of objects to tint.")
    args = parser.parse_args(argv)
    if args.debug_colors and args.save:
        sys.exit("--debug-colors is preview-only.")
    source = bpy.data.filepath
    if not source.replace("\\", "/").endswith("FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend"):
        sys.exit("v03 builds only from the FrontVisualFit_v02 checkpoint (got %s)." % source)
    names = args.steps.split(",")
    unknown = set(names) - set(STEPS3)
    if unknown:
        sys.exit("Unknown or unimplemented steps: %s" % sorted(unknown))
    for name in [s for s in ORDER3 if s in names]:
        STEPS3[name]()
        REPORT["steps"].append(name)
        update()
    if args.save:
        target = os.path.abspath(args.save)
        if os.path.abspath(source) == target or "FrontVisualFit_v02" in target or "FrontFit_v14" in target:
            sys.exit("Refusing to overwrite a protected checkpoint.")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=target, copy=True, compress=False)
    if args.debug_colors:
        palette = [(1, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.3, 1), (1, 0.8, 0), (1, 0, 1), (0, 0.9, 0.9)]
        for i, name in enumerate(args.debug_colors.split(",")):
            m = principled("DEBUG_%d" % i, palette[i % len(palette)], rough=0.6)
            for slot in bpy.data.objects[name].material_slots:
                slot.material = m
    if args.preview:
        render_preview(os.path.abspath(args.preview))
    REPORT["source"] = source
    REPORT["v02_builder_sha256"] = V02_BUILDER_SHA256
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump(REPORT, handle, indent=2)
    print("AVA_V03_BUILD_OK " + json.dumps({"steps": REPORT["steps"]}))


main3()
