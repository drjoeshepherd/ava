"""Ava .blend inventory (read-only). Created by AVA-BASELINE-INTEGRITY-001.

Run with system Python (it starts Blender in background mode for you):

    py 02_Production/Visual_Lock/Tools/Ava_InspectBlend.py ^
        --blend 02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend ^
        --out 02_Production/Visual_Lock/FrontFit_v14/FrontFit_v14_BlendInventory.json

Optional: --blender <path>. The .blend is hashed before and after and is never saved.
Nothing is deleted, renamed or edited. Redundant objects are only identified.

Reports: visible / hidden objects, disabled collections, armatures and the active rig,
object-to-armature bindings, listening-module objects, duplicate/legacy families
(Shell_*, GEO_*, Canon_* ...), which objects are actually hit by camera rays from
CAM_CANON_FRONT (front-render contribution), actions and their owners, rig/control
integrity, and content fingerprints (geometry, rig, animation, materials, cameras)
that a later run can compare to prove nothing changed.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Ava_VisualLock_Common as common  # noqa: E402

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

RAY_STRIDE = 2  # one ray per 2x2 pixel block of the 600x800 front frame
FAMILY_PREFIXES = ("GEO_", "Shell_", "Canon_", "HairShell_", "HairGroup_")


def _r(v, n=6):
    return round(float(v), n)


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest().upper()


# ---------------------------------------------------------------------------
# Blender side
# ---------------------------------------------------------------------------

def collection_chains(bpy):
    """Map collection name -> layer-collection state, including inherited exclusion/hiding."""
    states = {}

    def walk(layer_coll, excluded, hidden_render, hidden_viewport, path):
        coll = layer_coll.collection
        ex = excluded or layer_coll.exclude
        hr = hidden_render or coll.hide_render
        hv = hidden_viewport or coll.hide_viewport or layer_coll.hide_viewport
        states[coll.name] = {"path": path + [coll.name], "exclude": layer_coll.exclude, "hide_render": coll.hide_render,
                             "hide_viewport": coll.hide_viewport, "layer_hide_viewport": layer_coll.hide_viewport,
                             "effective_render_enabled": not ex and not hr, "effective_viewport_visible": not ex and not hv}
        for child in layer_coll.children:
            walk(child, ex, hr, hv, path + [coll.name])

    walk(bpy.context.view_layer.layer_collection, False, False, False, [])
    return states


def action_fcurves(action, slot=None):
    """F-curves across Blender versions (legacy action.fcurves or layered/slotted actions)."""
    curves = []
    if hasattr(action, "fcurves"):
        try:
            return list(action.fcurves)
        except Exception:
            pass
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for bag in getattr(strip, "channelbags", []):
                if slot is None or getattr(bag, "slot", None) == slot:
                    curves.extend(bag.fcurves)
    return curves


def front_ray_contribution(bpy, render_enabled):
    """Cast orthographic rays from CAM_CANON_FRONT. A hit on a non-render object continues behind it.
    Counts the first render-enabled object hit per ray. Limits: material transparency/alpha is ignored,
    and objects hidden in the viewport are invisible to scene.ray_cast (listed separately)."""
    from mathutils import Vector
    scene = bpy.context.scene
    cam = bpy.data.objects.get("CAM_CANON_FRONT")
    if cam is None:
        return {"error": "CAM_CANON_FRONT not found"}
    depsgraph = bpy.context.evaluated_depsgraph_get()
    frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=scene)]  # tr, br, bl, tl
    tr, br, bl, tl = frame
    direction = (cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))).normalized()
    width, height = 600, 800
    counts, total = {}, 0
    for py in range(0, height, RAY_STRIDE):
        v = (py + 0.5) / height
        left = tl.lerp(bl, v)
        right = tr.lerp(br, v)
        for px in range(0, width, RAY_STRIDE):
            u = (px + 0.5) / width
            origin = left.lerp(right, u) - direction * 1.0
            total += 1
            for _ in range(32):
                hit, loc, _n, _i, obj, _m = scene.ray_cast(depsgraph, origin, direction)
                if not hit:
                    break
                name = obj.original.name if obj.original else obj.name
                if render_enabled.get(name, False):
                    counts[name] = counts.get(name, 0) + 1
                    break
                origin = loc + direction * 1e-4
    return {"camera": cam.name, "rays": total, "stride_px": RAY_STRIDE,
            "first_hit_ray_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1]))}


def family_key(name):
    base = name
    for prefix in FAMILY_PREFIXES:
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
    side = ""
    m = re.search(r"[._](L|R|C)$", base)
    if m:
        side, base = m.group(1), base[:m.start()]
    return re.sub(r"[^a-z0-9]", "", base.lower()) + ("|" + side if side else "")


def blender_inspect(argv):
    import bpy
    from mathutils import Vector
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender-out", required=True)
    args = parser.parse_args(argv)
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    coll_states = collection_chains(bpy)

    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    objects = {}
    render_enabled = {}
    for obj in bpy.data.objects:
        in_scene = scene.objects.get(obj.name) is not None
        colls = [c.name for c in obj.users_collection]
        coll_render = any(coll_states.get(c, {}).get("effective_render_enabled", False) for c in colls)
        renders = in_scene and not obj.hide_render and coll_render
        render_enabled[obj.name] = renders
        arm_mods = [{"modifier": m.name, "object": m.object.name if m.object else None, "show_render": m.show_render}
                    for m in obj.modifiers if m.type == "ARMATURE"]
        entry = {
            "type": obj.type, "in_scene": in_scene, "collections": colls,
            "hide_render": obj.hide_render, "hide_viewport": obj.hide_viewport,
            "hidden_in_view_layer": obj.hide_get() if in_scene else None,
            "visible_in_viewport": obj.visible_get() if in_scene else False,
            "render_enabled": renders,
            "parent": obj.parent.name if obj.parent else None, "parent_type": obj.parent_type,
            "parent_bone": obj.parent_bone or None,
            "armature_modifiers": arm_mods,
            "materials": [s.material.name if s.material else None for s in obj.material_slots],
        }
        if obj.parent and obj.parent.type == "ARMATURE" and obj.parent_type == "BONE":
            entry["parent_bone_exists"] = obj.parent_bone in obj.parent.data.bones
        if obj.type == "MESH":
            me = obj.data
            entry["mesh"] = {"data": me.name, "vertices": len(me.vertices), "polygons": len(me.polygons),
                             "vertex_groups": [g.name for g in obj.vertex_groups]}
            entry["world_bbox"] = [[_r(c) for c in (obj.matrix_world @ Vector(b))] for b in obj.bound_box]
        objects[obj.name] = entry

    # Active armature = the one most referenced by bindings.
    refs = {}
    for e in objects.values():
        if e["parent"] and objects.get(e["parent"], {}).get("type") == "ARMATURE":
            refs[e["parent"]] = refs.get(e["parent"], 0) + 1
        for m in e["armature_modifiers"]:
            if m["object"]:
                refs[m["object"]] = refs.get(m["object"], 0) + 1
    active_rig = max(refs, key=refs.get) if refs else (armatures[0].name if armatures else None)

    rig = {}
    for arm in armatures:
        bones = {}
        for b in arm.data.bones:
            bones[b.name] = {"deform": b.use_deform, "parent": b.parent.name if b.parent else None,
                             "head_local": [_r(c) for c in b.head_local], "tail_local": [_r(c) for c in b.tail_local]}
        constraints, invalid = [], []
        for pb in arm.pose.bones:
            for c in pb.constraints:
                rec = {"bone": pb.name, "name": c.name, "type": c.type, "is_valid": c.is_valid, "mute": c.mute,
                       "target": getattr(getattr(c, "target", None), "name", None), "subtarget": getattr(c, "subtarget", None),
                       "pole_target": getattr(getattr(c, "pole_target", None), "name", None), "pole_subtarget": getattr(c, "pole_subtarget", None)}
                constraints.append(rec)
                if not c.is_valid:
                    invalid.append(rec)
        rig[arm.name] = {"armature_data": arm.data.name, "bone_count": len(bones), "bones": bones,
                         "deform_bones": sorted(n for n, b in bones.items() if b["deform"]),
                         "control_bones": sorted(n for n in bones if n.startswith("CTRL_")),
                         "pose_constraints": constraints, "invalid_constraints": invalid,
                         "pose_position": arm.data.pose_position}

    # Object-level constraints on control objects.
    object_constraints = {}
    for obj in bpy.data.objects:
        if obj.constraints:
            object_constraints[obj.name] = [{"name": c.name, "type": c.type, "is_valid": c.is_valid, "mute": c.mute,
                                             "target": getattr(getattr(c, "target", None), "name", None),
                                             "subtarget": getattr(c, "subtarget", None)} for c in obj.constraints]

    # Drivers anywhere.
    drivers, invalid_drivers = [], []
    id_collections = ["objects", "meshes", "armatures", "materials", "shape_keys", "cameras", "lights", "worlds",
                      "scenes", "node_groups", "curves"]
    for coll_name in id_collections:
        for idb in getattr(bpy.data, coll_name, []):
            ad = getattr(idb, "animation_data", None)
            if ad:
                for d in ad.drivers:
                    rec = {"id": "%s:%s" % (coll_name, idb.name), "data_path": d.data_path, "index": d.array_index,
                           "valid": d.driver.is_valid}
                    drivers.append(rec)
                    if not d.driver.is_valid:
                        invalid_drivers.append(rec)

    # Actions and owners.
    owners = {}

    def add_owner(action, owner, how):
        if action:
            owners.setdefault(action.name, []).append({"owner": owner, "via": how})

    def scan_animdata(label, idb):
        ad = getattr(idb, "animation_data", None)
        if not ad:
            return
        add_owner(ad.action, label, "active action" + (" (slot %s)" % ad.action_slot.name_display if getattr(ad, "action_slot", None) else ""))
        for track in ad.nla_tracks:
            for strip in track.strips:
                add_owner(strip.action, label, "NLA %s/%s" % (track.name, strip.name))

    for coll_name in id_collections:
        for idb in getattr(bpy.data, coll_name, []):
            scan_animdata("%s:%s" % (coll_name, idb.name), idb)
            nt = getattr(idb, "node_tree", None)
            if nt is not None:
                scan_animdata("%s:%s.node_tree" % (coll_name, idb.name), nt)
    actions = {}
    for act in bpy.data.actions:
        curves = action_fcurves(act)
        keys = [[c.data_path, c.array_index, [[_r(k.co[0]), _r(k.co[1])] for k in c.keyframe_points]] for c in curves]
        actions[act.name] = {"users": act.users, "use_fake_user": act.use_fake_user,
                             "frame_range": [_r(v) for v in act.frame_range],
                             "slots": [s.name_display for s in getattr(act, "slots", [])],
                             "fcurve_count": len(curves), "keyframe_count": sum(len(k[2]) for k in keys),
                             "owners": owners.get(act.name, []), "content_sha256": _hash(keys)}

    # Duplicate / legacy families.
    families = {}
    for name, e in objects.items():
        if e["type"] in ("MESH", "CURVE", "SURFACE", "META", "FONT"):
            families.setdefault(family_key(name), []).append(name)
    contribution = front_ray_contribution(bpy, render_enabled)
    hits = contribution.get("first_hit_ray_counts", {})
    duplicate_families = {}
    for key, names in families.items():
        if len(names) > 1:
            duplicate_families[key] = [{"object": n, "render_enabled": objects[n]["render_enabled"],
                                        "visible_in_viewport": objects[n]["visible_in_viewport"],
                                        "front_ray_hits": hits.get(n, 0),
                                        "collections": objects[n]["collections"]} for n in sorted(names)]

    listening = {n: {"render_enabled": e["render_enabled"], "visible_in_viewport": e["visible_in_viewport"],
                     "front_ray_hits": hits.get(n, 0), "parent": e["parent"], "parent_bone": e["parent_bone"],
                     "materials": e["materials"]}
                 for n, e in objects.items() if "listening" in n.lower()}

    geometry_objects = [n for n, e in objects.items() if e["type"] in ("MESH", "CURVE", "SURFACE", "META", "FONT")]
    render_but_viewport_hidden = [n for n in geometry_objects if objects[n]["render_enabled"] and not objects[n]["visible_in_viewport"]]

    # Fingerprints for later "unchanged" proofs.
    geo_fp = {}
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            me = obj.data
            geo_fp[obj.name] = _hash({"co": [[_r(c, 5) for c in v.co] for v in me.vertices],
                                      "polys": [list(p.vertices) for p in me.polygons],
                                      "matrix": [[_r(c, 6) for c in row] for row in obj.matrix_world]})
    mat_fp = {}
    for mat in bpy.data.materials:
        nodes = []
        if mat.node_tree:
            for node in mat.node_tree.nodes:
                vals = {}
                for inp in node.inputs:
                    dv = getattr(inp, "default_value", None)
                    try:
                        vals[inp.identifier] = [_r(x) for x in dv]
                    except TypeError:
                        vals[inp.identifier] = _r(dv) if isinstance(dv, (int, float)) else str(dv)
                nodes.append([node.name, node.bl_idname, vals])
            links = [[l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier] for l in mat.node_tree.links]
        else:
            links = []
        mat_fp[mat.name] = _hash({"nodes": sorted(nodes, key=lambda n: n[0]), "links": sorted(links)})
    cam_fp = {o.name: _hash({"matrix": [[_r(c) for c in row] for row in o.matrix_world], "type": o.data.type,
                             "ortho_scale": _r(o.data.ortho_scale), "lens": _r(o.data.lens), "dof": o.data.dof.use_dof})
              for o in bpy.data.objects if o.type == "CAMERA"}

    controls = sorted(n for n in objects if n.startswith(("CTRL_", "MCH_")))
    report = {
        "schema": "Ava_BlendInventory_v1.0",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "blend_filepath": bpy.data.filepath,
        "scene": scene.name, "view_layer": view_layer.name,
        "render_engine": scene.render.engine,
        "summary": {
            "objects_total": len(objects),
            "geometry_objects_total": len(geometry_objects),
            "geometry_render_enabled": sorted(n for n in geometry_objects if objects[n]["render_enabled"]),
            "geometry_not_render_enabled": sorted(n for n in geometry_objects if not objects[n]["render_enabled"]),
            "geometry_render_enabled_but_viewport_hidden": render_but_viewport_hidden,
            "geometry_contributing_to_front_render": sorted(hits),
            "geometry_render_enabled_but_not_hit_from_front": sorted(n for n in geometry_objects if objects[n]["render_enabled"] and n not in hits),
            "disabled_collections": sorted(n for n, s in coll_states.items() if not s["effective_render_enabled"]),
            "armatures": [a.name for a in armatures],
            "active_armature": active_rig,
            "actions": sorted(actions),
            "control_objects": controls,
            "invalid_constraints": sum(len(r["invalid_constraints"]) for r in rig.values()) + sum(1 for cs in object_constraints.values() for c in cs if not c["is_valid"]),
            "invalid_drivers": len(invalid_drivers),
        },
        "collections": coll_states,
        "objects": objects,
        "front_render_contribution": contribution,
        "duplicate_or_legacy_families": duplicate_families,
        "listening_module_objects": listening,
        "rig": rig,
        "object_constraints": object_constraints,
        "drivers": {"count": len(drivers), "invalid": invalid_drivers},
        "actions": actions,
        "fingerprints": {
            "geometry_per_mesh_object": geo_fp, "geometry_all": _hash(geo_fp),
            "rig_all": _hash({k: {"bones": v["bones"], "constraints": v["pose_constraints"]} for k, v in rig.items()}),
            "animation_all": _hash({k: v["content_sha256"] for k, v in actions.items()}),
            "materials_per_material": mat_fp, "materials_all": _hash(mat_fp),
            "cameras_per_camera": cam_fp, "cameras_all": _hash(cam_fp),
        },
        "notes": [
            "Read-only inspection. Nothing was deleted, renamed, or saved.",
            "front_render_contribution uses geometric ray casts from CAM_CANON_FRONT: material transparency/alpha is ignored, "
            "and objects hidden in the viewport are not hit by scene.ray_cast (see geometry_render_enabled_but_viewport_hidden).",
        ],
    }
    with open(args.blender_out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


# ---------------------------------------------------------------------------
# System-Python side
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Read-only inventory of an Ava .blend.")
    parser.add_argument("--blend", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--blender")
    args = parser.parse_args()
    root = common.find_repo_root()
    blend = os.path.abspath(os.path.join(root, args.blend) if not os.path.isabs(args.blend) else args.blend)
    out = os.path.abspath(os.path.join(root, args.out) if not os.path.isabs(args.out) else args.out)
    blender, searched = common.find_blender(args.blender)
    if not blender:
        sys.exit("Blender not found. Searched: %s. Nothing was installed." % searched)
    before = common.file_sha256(blend)
    tmp = out + ".partial"
    cmd = [blender, "-b", blend, "--factory-startup", "--python-exit-code", "3",
           "--python", os.path.abspath(__file__), "--", "--blender-out", tmp]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    after = common.file_sha256(blend)
    if proc.returncode != 0 or not os.path.isfile(tmp):
        sys.stderr.write((proc.stdout or "")[-6000:] + (proc.stderr or "")[-6000:])
        sys.exit("Blender inspection failed (code %s)." % proc.returncode)
    report = common.load_json(tmp)
    report["provenance"] = {"source_blend": common.rel(root, blend), "source_blend_sha256_before": before,
                            "source_blend_sha256_after": after, "unchanged": before == after,
                            "blender_executable": blender, "command": cmd, "tool_version": common.TOOL_VERSION,
                            "tool_sha256": common.file_sha256(os.path.abspath(__file__))}
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    try:
        os.remove(tmp)
    except OSError:
        pass
    if before != after:
        sys.exit("Source .blend changed during inspection. Stop and investigate.")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    if IN_BLENDER:
        blender_inspect(common.blender_script_args())
    else:
        main()
