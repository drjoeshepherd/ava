"""Ava rig / articulation QA (read-only). Created by AVA-FIT-FRONT-03.

    blender -b <checkpoint.blend> --factory-startup --python 02_Production/Visual_Lock/Tools/Ava_RigQA.py -- --out <json>

Everything happens in memory; the .blend is never saved. Tests that need to override keyed values detach
the actions for the test only (in memory) and restore them before the next test.
"""

import hashlib
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

RIG = "RIG_Ava_Master"
FINGERS = ("Thumb", "Index", "Middle", "Ring", "Pinky")
LEGACY = ("Shell_", "Canon_", "HairShell_", "HairGroup_", "RETIRED_")
LIVE_LEGACY_NAMED = {"Shell_Head", "Shell_Hand.L", "Shell_Hand.R"}


def h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest().upper()


def r(v, n=6):
    return [round(x, n) for x in v]


def dg():
    a = bpy.data.objects.get(RIG)
    if a is not None:
        a.update_tag()          # custom-property edits do not tag dependents (drivers) on their own
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


def world_verts(name):
    o = bpy.data.objects[name]
    ev = o.evaluated_get(dg())
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return pts


def principal_axis(pts):
    c = sum(pts, Vector()) / len(pts)
    cov = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    v = Vector((1, 1, 1)).normalized()
    for _ in range(60):
        v = (cov @ v).normalized()
    return c, v


def line_dist(p, c, axis):
    d = p - c
    return (d - axis * d.dot(axis)).length


def set_rot(pb, deg):
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (math.radians(deg), 0, 0)


def bone_world(a, name):
    pb = a.pose.bones[name]
    return a.matrix_world @ pb.head, a.matrix_world @ pb.tail


def detach_actions():
    saved = {}
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            saved[o.name] = o.animation_data.action
            o.animation_data.action = None
    return saved


def restore_actions(saved):
    for name, act in saved.items():
        bpy.data.objects[name].animation_data.action = act


def reset_pose(a):
    for pb in a.pose.bones:
        pb.rotation_mode = pb.rotation_mode
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def main():
    out = sys.argv[sys.argv.index("--") + 2]
    a = bpy.data.objects[RIG]
    R = {"blend": bpy.data.filepath, "blender": bpy.app.version_string}

    # Inventory ---------------------------------------------------------------
    R["rig"] = {"bone_count": len(a.data.bones),
                "constraints": [{"bone": pb.name, "type": c.type, "valid": c.is_valid} for pb in a.pose.bones for c in pb.constraints],
                "object_constraints": [{"object": o.name, "type": c.type, "valid": c.is_valid} for o in bpy.data.objects for c in o.constraints]}
    R["rig"]["constraint_count"] = len(R["rig"]["constraints"]) + len(R["rig"]["object_constraints"])
    R["rig"]["broken_constraints"] = [c for c in R["rig"]["constraints"] + R["rig"]["object_constraints"] if not c["valid"]]
    drivers = []
    for coll in (bpy.data.objects, bpy.data.materials, bpy.data.shape_keys, bpy.data.meshes, bpy.data.curves, bpy.data.armatures):
        for idb in coll:
            for ad in [getattr(idb, "animation_data", None)] + ([idb.node_tree.animation_data] if getattr(idb, "node_tree", None) else []):
                if ad:
                    for fc in ad.drivers:
                        drivers.append({"owner": idb.name, "path": fc.data_path, "index": fc.array_index, "expr": fc.driver.expression,
                                        "valid": fc.driver.is_valid and not fc.mute})
    R["drivers"] = {"count": len(drivers), "broken": [d for d in drivers if not d["valid"]], "list": drivers}
    actions = {}
    for act in bpy.data.actions:
        chans = []
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        chans.append([fc.data_path, fc.array_index, [r(k.co, 6) + r(k.handle_left, 6) + r(k.handle_right, 6) + [k.interpolation] for k in fc.keyframe_points]])
        owners = [o.name for o in bpy.data.objects if o.animation_data and o.animation_data.action == act]
        actions[act.name] = {"owners": owners, "channels": len(chans), "frame_range": r(act.frame_range, 3), "sha256": h(sorted(chans, key=lambda c: (c[0], c[1])))}
    R["actions"] = {"count": len(actions), "inventory": actions, "all_sha256": h(actions)}
    R["rig_keyed_props_frame1"] = {k: a[k] for k in ("listen_L", "listen_R", "chest_intensity", "blink_L", "blink_R", "mouth_smile")}
    cams = {o.name: [r(sum((list(row) for row in o.matrix_world), []), 6), o.data.type, round(o.data.ortho_scale, 6), o.data.lens] for o in bpy.data.objects if o.type == "CAMERA"}
    R["camera_fingerprint"] = h(cams)
    lights = {o.name: [o.data.type, round(o.data.energy, 6), r(o.data.color), round(getattr(o.data, "size", 0), 6), r(sum((list(row) for row in o.matrix_world), []), 6), o.hide_render]
              for o in bpy.data.objects if o.type == "LIGHT"}
    world = bpy.context.scene.world
    wnodes = {n.name: {i.name: (list(i.default_value) if hasattr(i.default_value, "__len__") else i.default_value) for i in n.inputs if hasattr(i, "default_value")} for n in world.node_tree.nodes}
    vs = bpy.context.scene.view_settings
    R["lighting_fingerprint"] = h([lights, wnodes, vs.view_transform, vs.look, vs.exposure, vs.gamma])
    R["lighting"] = {"render_enabled_lights": sorted(n for n, v in lights.items() if not v[5]), "view_transform": vs.view_transform, "look": vs.look}
    # Material Lock --------------------------------------------------------------
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    lock = json.load(open(os.path.join(root, "02_Production", "Visual_Lock", "Ava_Material_Lock_v1.0.json"), encoding="utf-8"))
    def bsdf(m, node=None):
        nt = bpy.data.materials[m].node_tree
        return nt.nodes[node] if node else next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED" and not n.name.startswith("AVA_"))
    checks = {}
    for mat, key in (("MAT_Ava_CeramicWhite", "white_shell"), ("MAT_Ava_Graphite", "graphite"), ("MAT_Ava_AccentGray", "accent_gray")):
        b, l = bsdf(mat), lock[key]
        checks[mat] = {"base_rgb": [r(b.inputs["Base Color"].default_value[:3]), l["base_rgb"]], "metallic": [round(b.inputs["Metallic"].default_value, 6), l["metallic"]],
                       "roughness": [round(b.inputs["Roughness"].default_value, 6), l["roughness"]]}
        if "specular_ior_level" in l:
            checks[mat]["specular_ior_level"] = [round(b.inputs["Specular IOR Level"].default_value, 6), l["specular_ior_level"]]
    for mat in ("MAT_Ava_AmberEmission_C", "MAT_Ava_AmberEmission_L", "MAT_Ava_AmberEmission_R"):
        b = bsdf(mat, "Principled BSDF")
        checks[mat] = {"emission_rgb": [r(b.inputs["Emission Color"].default_value[:3]), lock["amber_emission"]["rgb_linear"]]}
    ok = all(abs(x - y) < 1e-4 for c in checks.values() for got, want in c.values() for x, y in zip(got if isinstance(got, list) else [got], want if isinstance(want, list) else [want]))
    R["material_lock"] = {"all_match": ok, "checks": checks}
    # Legacy render state --------------------------------------------------------
    legacy = {o.name: {"render_enabled": not o.hide_render, "collections": [c.name for c in o.users_collection]} for o in bpy.data.objects if o.name.startswith(LEGACY)}
    R["legacy_render_state"] = {"objects": legacy, "render_enabled_legacy": sorted(n for n, v in legacy.items() if v["render_enabled"] and n not in LIVE_LEGACY_NAMED),
                                "live_objects_with_legacy_prefix": sorted(n for n in LIVE_LEGACY_NAMED if n in legacy)}

    saved = detach_actions()
    reset_pose(a)
    # Finger articulation ---------------------------------------------------------
    arts = {}
    worst = {"rigid_residual": 0, "axis_angle_deg": 0, "knuckle_offset": 0, "segment_gap": 0}
    for side in ("L", "R"):
        for f in FINGERS:
            for deg in (45.0, -30.0):
                rec = {}
                reset_pose(a)
                before = {i: world_verts("Finger_%s%d.%s" % (f, i, side)) for i in (1, 2)}
                heads = {i: bone_world(a, "DEF_%s%d.%s" % (f, i, side)) for i in (1, 2)}
                for i in (1, 2):
                    set_rot(a.pose.bones["DEF_%s%d.%s" % (f, i, side)], deg)
                after = {i: world_verts("Finger_%s%d.%s" % (f, i, side)) for i in (1, 2)}
                for i in (1, 2):
                    bname = "DEF_%s%d.%s" % (f, i, side)
                    head, tail = bone_world(a, bname)
                    # rigid residual: the mesh must move exactly with its bone (bone matrix delta)
                    pb = a.pose.bones[bname]
                    m_after = a.matrix_world @ pb.matrix
                    reset_pose(a); dg()
                    m_before = a.matrix_world @ pb.matrix
                    for j in (1, 2):
                        set_rot(a.pose.bones["DEF_%s%d.%s" % (f, j, side)], deg)
                    dg()
                    delta = m_after @ m_before.inverted()
                    resid = max(((delta @ p0) - p1).length for p0, p1 in zip(before[i], after[i]))
                    c, ax = principal_axis(after[i])
                    bone_dir = (tail - head).normalized()
                    ang = math.degrees(math.acos(min(1.0, abs(ax.dot(bone_dir)))))
                    koff = line_dist(head, c, ax)
                    rec["seg%d" % i] = {"rigid_residual": resid, "axis_angle_deg": ang, "knuckle_offset": koff}
                    worst["rigid_residual"] = max(worst["rigid_residual"], resid)
                    worst["axis_angle_deg"] = max(worst["axis_angle_deg"], ang)
                    worst["knuckle_offset"] = max(worst["knuckle_offset"], koff)
                t1 = bone_world(a, "DEF_%s1.%s" % (f, side))[1]
                h2 = bone_world(a, "DEF_%s2.%s" % (f, side))[0]
                rec["joint_gap"] = (t1 - h2).length
                worst["segment_gap"] = max(worst["segment_gap"], rec["joint_gap"])
                arts["%s.%s @%+.0f deg" % (f, side, deg)] = rec
    reset_pose(a); dg()
    thresholds = {"rigid_residual": 1e-4, "axis_angle_deg": 2.0, "knuckle_offset": 0.01, "segment_gap": 1e-4}
    R["finger_articulation"] = {"method": "Each finger/thumb: both segments rotated about their bone X axis by +45 and -30 degrees (in memory). "
                                          "rigid_residual = max distance between each mesh vertex and the bone's own motion applied to its rest position; "
                                          "axis_angle_deg = angle between the segment mesh principal axis and its bone axis after the curl; "
                                          "knuckle_offset = distance from the bone head (pivot) to the mesh axis line; segment_gap = distance between "
                                          "segment-1 bone tail and segment-2 bone head after the curl.",
                                "thresholds": thresholds, "worst": worst,
                                "pass": all(worst[k] <= thresholds[k] for k in thresholds), "per_test": arts,
                                "returned_to_neutral": all(pb.rotation_euler.to_quaternion().angle < 1e-9 for pb in a.pose.bones)}
    # Arm FK / IK -------------------------------------------------------------------
    arm_tests = {}
    for side in ("L", "R"):
        reset_pose(a); dg()
        wrist0 = bone_world(a, "DEF_Hand." + side)[0]
        shell0 = world_verts("GEO_ForearmShell_" + side)
        set_rot(a.pose.bones["DEF_Forearm." + side], 30.0); dg()
        wrist_fk = bone_world(a, "DEF_Hand." + side)[0]
        pb = a.pose.bones["DEF_Forearm." + side]
        shell1 = world_verts("GEO_ForearmShell_" + side)
        reset_pose(a); dg()
        m0 = a.matrix_world @ pb.matrix
        set_rot(pb, 30.0); dg()
        m1 = a.matrix_world @ pb.matrix
        fk_resid = max((((m1 @ m0.inverted()) @ p0) - p1).length for p0, p1 in zip(shell0, shell1))
        reset_pose(a)
        a["ik_fk_arm_" + side] = 1.0
        dg()
        wrist_ik_rest = bone_world(a, "DEF_Hand." + side)[0]
        ik = a.pose.bones["CTRL_Hand_IK." + side]
        ik.location = (0.0, 0.0, 0.12)
        dg()
        target = (a.matrix_world @ ik.head)
        wrist_ik = bone_world(a, "DEF_Hand." + side)[0]
        arm_tests[side] = {"fk_forearm_30deg_wrist_moved": (wrist_fk - wrist0).length, "fk_forearm_shell_rigid_residual": fk_resid,
                           "ik_enabled_at_rest_wrist_drift": (wrist_ik_rest - wrist0).length,
                           "ik_target_moved_0.12": True, "ik_wrist_to_target_distance": (wrist_ik - target).length,
                           "ik_wrist_moved": (wrist_ik - wrist0).length}
        ik.location = (0, 0, 0)
        a["ik_fk_arm_" + side] = 0.0
        reset_pose(a); dg()
    R["arm_ik_fk"] = {"tests": arm_tests, "pass": all(t["fk_forearm_30deg_wrist_moved"] > 0.1 and t["fk_forearm_shell_rigid_residual"] < 1e-4 and
                                                    t["ik_enabled_at_rest_wrist_drift"] < 0.01 and t["ik_wrist_to_target_distance"] < 0.02 for t in arm_tests.values())}
    # Eye aim ------------------------------------------------------------------------
    eye = {}
    for side in ("L", "R"):
        ctrl = bpy.data.objects["CTRL_EyeAim." + side]
        iris = bpy.data.objects["GEO_CanonicalIris." + side]
        legacy_iris = bpy.data.objects.get("Eye_Iris." + side)
        d = dg(); i0 = iris.evaluated_get(d).matrix_world.translation.copy(); l0 = legacy_iris.evaluated_get(d).matrix_world.translation.copy() if legacy_iris else None
        loc0 = ctrl.location.copy()
        ctrl.location.x += 0.1
        d = dg(); i1 = iris.evaluated_get(d).matrix_world.translation.copy(); l1 = legacy_iris.evaluated_get(d).matrix_world.translation.copy() if legacy_iris else None
        ctrl.location = loc0; dg()
        eye[side] = {"ctrl_moved_x": 0.1, "GEO_CanonicalIris_moved": (i1 - i0).length,
                     "legacy_Eye_Iris_moved": (l1 - l0).length if legacy_iris else None,
                     "GEO_CanonicalIris_parent": iris.parent.name if iris.parent else None}
    R["eye_aim"] = eye
    # Eyelid / blink -----------------------------------------------------------------
    blink = {}
    for side in ("L", "R"):
        lid = bpy.data.objects["CTRL_Eyelid." + side]
        s0 = list(lid.evaluated_get(dg()).matrix_world.to_scale())
        a["blink_" + side] = 1.0
        s1 = list(lid.evaluated_get(dg()).matrix_world.to_scale())
        a["blink_" + side] = 0.0; dg()
        blink[side] = {"scale_neutral": r(s0, 4), "scale_blink_1": r(s1, 4), "driver_responds": any(abs(x - y) > 1e-3 for x, y in zip(s0, s1)),
                       "note": "Driver scales the eyelid control's local Z (inherited v14 semantics); see change log."}
    R["eyelid_blink"] = blink
    # Light controls -----------------------------------------------------------------
    def strength(mat):
        m = bpy.data.materials[mat].evaluated_get(dg())
        return round(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value, 4)
    a["listen_L"], a["listen_R"] = 1.0, 0.0
    lr = {"listen_L=1,listen_R=0": {"L": strength("MAT_Ava_AmberEmission_L"), "R": strength("MAT_Ava_AmberEmission_R")}}
    a["listen_L"], a["listen_R"] = 0.0, 1.0
    lr["listen_L=0,listen_R=1"] = {"L": strength("MAT_Ava_AmberEmission_L"), "R": strength("MAT_Ava_AmberEmission_R")}
    R["listening_ring_independence"] = {"strengths": lr, "independent": lr["listen_L=1,listen_R=0"]["L"] > lr["listen_L=1,listen_R=0"]["R"] and lr["listen_L=0,listen_R=1"]["R"] > lr["listen_L=0,listen_R=1"]["L"],
                                        "rings_use_own_material": {s: bpy.data.objects["GEO_ListeningEmission_" + s].material_slots[0].material.name for s in ("L", "R")}}
    a["chest_intensity"] = 0.0; c0 = strength("MAT_Ava_AmberEmission_C")
    a["chest_intensity"] = 1.0; c1 = strength("MAT_Ava_AmberEmission_C")
    R["chest_light_control"] = {"strength_at_0": c0, "strength_at_1": c1, "responds": c1 > c0,
                                "emitter_objects": [o.name for o in bpy.data.objects if any(s.material and s.material.name == "MAT_Ava_AmberEmission_C" for s in o.material_slots) and not o.hide_render]}
    restore_actions(saved)
    reset_pose(a); dg()
    R["note"] = "In-memory only; actions were detached for the override tests and restored; nothing was saved."
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(R, handle, indent=2, default=str)
    print("RIGQA_OK", json.dumps({"bones": R["rig"]["bone_count"], "drivers": R["drivers"]["count"], "broken_drivers": len(R["drivers"]["broken"]),
                                  "fingers_pass": R["finger_articulation"]["pass"], "arm_pass": R["arm_ik_fk"]["pass"], "matlock": ok}))


main()
