"""Ava FRONT validation: render a .blend through CAM_CANON_FRONT and measure it against the locks.

Created by AVA-BASELINE-INTEGRITY-001.

Run from any folder with system Python (Pillow required):

    py 02_Production/Visual_Lock/Tools/Ava_ValidateFront.py ^
        --blend 02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend ^
        --out 05_Renders/Visual_Lock/FrontFit_v14_Verified ^
        --label vFit14_Verified

Optional: --blender "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe"
(otherwise AVA_BLENDER, PATH, then standard install folders are searched).

What it does:
  1. Verifies every canonical checksum in Ava_Target_Manifest_v1.0.json (including the front mask).
  2. Requires Ava_Geometry_Lock_v1.1.json status APPROVED and the gate file status APPROVED.
  3. Hashes the .blend, renders it in Blender background mode with this same script
     (Blender-side mode below), then hashes the .blend again. The .blend is never saved.
  4. Measures the NEW render only. It never reads, copies or renames an older render.
  5. Writes the review package, a provenance-rich metrics JSON and a validation log.

Blender-side mode (started automatically by step 3):
    blender -b <blend> --factory-startup --python Ava_ValidateFront.py -- --blender-render <png> --info <json>
It sets only in-memory render state (active camera and the locked resolution), checks the locked
camera transform without changing it, renders one still, and exits without saving.

--self-test-image <png> measures an existing image instead of rendering. Its output is marked
SELF_TEST_NOT_A_BASELINE and must never be used as production evidence.
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Ava_VisualLock_Common as common  # noqa: E402

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

CAMERA_NAME = "CAM_CANON_FRONT"
CAMERA_TOLERANCE = 1e-4


# ---------------------------------------------------------------------------
# Blender side
# ---------------------------------------------------------------------------

def blender_render(argv):
    import bpy
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender-render", required=True)
    parser.add_argument("--info", required=True)
    args = parser.parse_args(argv)

    root = common.find_repo_root()
    paths = common.repo_paths(root)
    camera_lock = common.load_json(paths["camera_lock"])
    material_lock = common.load_json(paths["material_lock"])
    locked = camera_lock["cameras"]["Front"]
    scene = bpy.context.scene
    info = {"blender_version": bpy.app.version_string, "blend_filepath": bpy.data.filepath,
            "scene": scene.name, "errors": [], "warnings": [], "in_memory_overrides": {}}

    cam = bpy.data.objects.get(CAMERA_NAME)
    if cam is None or cam.type != "CAMERA":
        info["errors"].append("%s not found or not a camera." % CAMERA_NAME)
    else:
        loc = list(cam.location)
        rot = list(cam.rotation_euler)
        info["camera"] = {"name": cam.name, "location": loc, "rotation_euler": rot,
                          "projection": cam.data.type, "ortho_scale": cam.data.ortho_scale,
                          "use_dof": bool(cam.data.dof.use_dof),
                          "matrix_world": [list(r) for r in cam.matrix_world]}
        checks = {
            "location": max(abs(a - b) for a, b in zip(loc, locked["location"])) <= CAMERA_TOLERANCE,
            "rotation_euler": max(abs(a - b) for a, b in zip(rot, locked["rotation_euler"])) <= CAMERA_TOLERANCE,
            "projection": cam.data.type == locked["projection"][:5],  # ORTHOGRAPHIC -> 'ORTHO'
            "ortho_scale": abs(cam.data.ortho_scale - locked["ortho_scale"]) <= CAMERA_TOLERANCE,
            "no_dof": not cam.data.dof.use_dof,
        }
        info["camera_lock_checks"] = checks
        if not all(checks.values()):
            info["errors"].append("Camera does not match Ava_Camera_Lock_v1.0.json; the camera may not be adjusted during evaluation.")

    render = scene.render
    info["render_settings_in_file"] = {
        "engine": render.engine, "resolution_x": render.resolution_x, "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage, "film_transparent": render.film_transparent,
        "view_transform": scene.view_settings.view_transform, "look": scene.view_settings.look,
        "active_camera": scene.camera.name if scene.camera else None,
    }
    eevee = getattr(scene, "eevee", None)
    if eevee is not None and hasattr(eevee, "use_bloom"):
        info["render_settings_in_file"]["eevee_use_bloom"] = bool(eevee.use_bloom)
        if eevee.use_bloom:
            info["errors"].append("Bloom is enabled in the file; Ava_Material_Lock_v1.0.json forbids bloom for evaluation.")
    if scene.view_settings.view_transform != material_lock["render_evaluation"]["view_transform"]:
        info["errors"].append("View transform %r differs from locked %r." % (scene.view_settings.view_transform, material_lock["render_evaluation"]["view_transform"]))

    lights = []
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            lights.append({"name": obj.name, "light_type": obj.data.type, "energy": obj.data.energy,
                           "hide_render": obj.hide_render, "in_scene": scene.objects.get(obj.name) is not None})
    info["lights"] = lights
    lock_lights = {"LIGHT_KEY", "LIGHT_FILL", "LIGHT_RIM"}
    extra = [l["name"] for l in lights if l["in_scene"] and not l["hide_render"] and l["name"] not in lock_lights]
    missing = [n for n in lock_lights if not any(l["name"] == n and l["in_scene"] and not l["hide_render"] for l in lights)]
    if missing:
        info["errors"].append("Locked evaluation lights not render-enabled: %s" % sorted(missing))
    if extra:
        info["warnings"].append("Non-lock lights are render-enabled in the file and contribute to this render: %s. "
                                "They were left as saved; no lighting was changed." % sorted(extra))

    if info["errors"]:
        with open(args.info, "w", encoding="utf-8") as handle:
            json.dump(info, handle, indent=2)
        sys.exit(2)

    # In-memory only (never saved): locked camera and locked resolution.
    res = camera_lock["resolution"]
    info["in_memory_overrides"] = {"scene.camera": CAMERA_NAME, "resolution": res, "resolution_percentage": 100,
                                   "file_format": "PNG RGB 8-bit"}
    scene.camera = cam
    render.resolution_x, render.resolution_y = res
    render.resolution_percentage = 100
    render.image_settings.file_format = "PNG"
    render.image_settings.color_mode = "RGB"
    render.image_settings.color_depth = "8"
    render.filepath = args.blender_render
    info["render_started_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    bpy.ops.render.render(write_still=True)
    info["render_finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    info["render_output"] = args.blender_render
    with open(args.info, "w", encoding="utf-8") as handle:
        json.dump(info, handle, indent=2)


# ---------------------------------------------------------------------------
# System-Python side
# ---------------------------------------------------------------------------

def tool_hashes(paths):
    names = ["Ava_ValidateFront.py", "Ava_VisualLock_Common.py", "Ava_InspectBlend.py"]
    return {n: common.file_sha256(os.path.join(paths["tools"], n)) for n in names if os.path.isfile(os.path.join(paths["tools"], n))}


def main():
    parser = argparse.ArgumentParser(description="Render and validate Ava FRONT against the visual lock.")
    parser.add_argument("--blend", help="Source .blend (required unless --self-test-image).")
    parser.add_argument("--out", required=True, help="Output directory (created; must be empty unless --overwrite).")
    parser.add_argument("--label", required=True, help="Artifact label, e.g. vFit14_Verified.")
    parser.add_argument("--blender", help="Path to blender executable.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--self-test-image", help="Measure an existing PNG instead of rendering (never a baseline).")
    args = parser.parse_args()

    root = common.find_repo_root()
    paths = common.repo_paths(root)
    out = os.path.abspath(os.path.join(root, args.out) if not os.path.isabs(args.out) else args.out)
    os.makedirs(out, exist_ok=True)
    if os.listdir(out) and not args.overwrite:
        sys.exit("Output directory is not empty: %s (use --overwrite)." % out)
    self_test = bool(args.self_test_image)
    if not self_test and not args.blend:
        sys.exit("--blend is required.")
    if not common.PIL_AVAILABLE:
        sys.exit("Pillow is required for measurement (pip install pillow).")

    log = ["# Ava FRONT validation log — %s" % args.label, ""]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log.append("- Started (UTC): %s" % started)

    manifest_report = common.verify_manifest(paths)
    log.append("- Canonical manifest: all %d checksums match." % len(manifest_report["entries"]))
    lock = common.load_json(paths["geometry_lock"])
    gates = common.load_json(paths["gates"])
    if lock.get("status") != "APPROVED":
        sys.exit("Geometry Lock status is %r, not APPROVED." % lock.get("status"))
    if gates.get("status") != "APPROVED":
        sys.exit("Gate file status is %r, not APPROVED." % gates.get("status"))
    camera_lock = common.load_json(paths["camera_lock"])

    names = {
        "render": "Front_Render_%s.png" % args.label,
        "overlay": "Front_Overlay_%s.png" % args.label,
        "difference": "Front_Difference_%s.png" % args.label,
        "target_mask": "Front_TargetMask.png",
        "render_mask": "Front_RenderMask.png",
        "mask_comparison": "Front_MaskComparison_%s.png" % args.label,
        "landmarks": "Front_LandmarkVisualization_%s.png" % args.label,
        "metrics": "Front_Metrics_%s.json" % args.label,
        "log": "Front_ValidationLog_%s.md" % args.label,
    }
    out_paths = {k: os.path.join(out, v) for k, v in names.items()}

    blender_info, blender_path, blend_rel, blend_before, blend_after = None, None, None, None, None
    if self_test:
        log.append("- MODE: SELF-TEST on existing image `%s`. Not a baseline. No Blender render." % args.self_test_image)
        from PIL import Image
        Image.open(args.self_test_image).convert("RGB").save(out_paths["render"])
    else:
        blend = os.path.abspath(os.path.join(root, args.blend) if not os.path.isabs(args.blend) else args.blend)
        blend_rel = common.rel(root, blend)
        blender_path, searched = common.find_blender(args.blender)
        if not blender_path:
            sys.exit("Blender not found. Searched: %s. Pass --blender or set AVA_BLENDER. Nothing was installed." % searched)
        blend_before = common.file_sha256(blend)
        info_path = os.path.join(out, "_blender_render_info.json")
        cmd = [blender_path, "-b", blend, "--factory-startup", "--python-exit-code", "3",
               "--python", os.path.abspath(__file__), "--", "--blender-render", out_paths["render"], "--info", info_path]
        log.append("- Blender: `%s`" % blender_path)
        log.append("- Command: `%s`" % " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True)
        blend_after = common.file_sha256(blend)
        blender_info = common.load_json(info_path) if os.path.isfile(info_path) else None
        if proc.returncode != 0 or not os.path.isfile(out_paths["render"]):
            with open(out_paths["log"], "w", encoding="utf-8") as handle:
                handle.write("\n".join(log + ["", "## BLENDER FAILURE", "", "Return code: %s" % proc.returncode,
                                               "", "```", (proc.stdout or "")[-6000:], (proc.stderr or "")[-6000:], "```",
                                               "", "Blender info:", "```json", json.dumps(blender_info, indent=2), "```"]))
            sys.exit("Blender render failed (code %s). See %s" % (proc.returncode, out_paths["log"]))
        if blend_before != blend_after:
            sys.exit("Source .blend changed during validation (%s -> %s). Stop and investigate." % (blend_before, blend_after))
        log.append("- Source .blend SHA-256 unchanged before/after render: `%s`" % blend_before)

    from PIL import Image
    target_image = Image.open(paths["target_front"]).convert("RGB")
    render_image = Image.open(out_paths["render"]).convert("RGB")
    expected = tuple(camera_lock["resolution"])
    if render_image.size != expected:
        sys.exit("Render size %s does not match locked resolution %s." % (render_image.size, expected))

    target_mask = common.load_binary_mask(paths["target_front_mask"])
    common.save_mask(target_mask, out_paths["target_mask"])
    render_mask, render_segmentation = common.derive_silhouette(render_image)
    common.save_mask(render_mask, out_paths["render_mask"])
    render_analysis = common.analyze_raster(render_image, render_mask, render_segmentation)
    results, summary = common.compute_front_metrics(lock, gates, target_mask, render_mask, render_analysis, render_segmentation)

    common.save_overlay(target_image, render_image, out_paths["overlay"])
    common.save_difference(target_image, render_image, out_paths["difference"])
    common.save_mask_comparison(target_mask, render_mask, out_paths["mask_comparison"])
    common.save_landmark_visualization(render_image, lock, render_analysis, out_paths["landmarks"], "Ava FRONT %s" % args.label)

    image_outputs = {k: v for k, v in out_paths.items() if k not in ("metrics", "log")}
    identical = common.find_identical_prior_artifacts(root, image_outputs, out)
    # The target mask copy is expected to equal earlier target-mask copies (same canonical pixels).
    identical_render_side = {k: v for k, v in identical.items() if k != "target_mask"}

    status = "SELF_TEST_NOT_A_BASELINE" if self_test else ("INTEGRITY_REVIEW_REQUIRED" if identical_render_side else "VERIFIED_MEASUREMENT_REVIEW_REQUIRED")
    metrics = {
        "schema": "Ava_Front_Validation_v1.0",
        "status": status,
        "label": args.label,
        "provenance": {
            "source_blend": blend_rel,
            "source_blend_sha256_before": blend_before,
            "source_blend_sha256_after": blend_after,
            "self_test_image": args.self_test_image,
            "canonical_raster": {"file": common.rel(root, paths["target_front"]), "sha256": common.file_sha256(paths["target_front"])},
            "canonical_mask": {"file": common.rel(root, paths["target_front_mask"]), "sha256": common.file_sha256(paths["target_front_mask"])},
            "manifest_check": manifest_report,
            "geometry_lock": {"file": common.rel(root, paths["geometry_lock"]), "schema": lock["schema"], "status": lock["status"], "sha256": common.file_sha256(paths["geometry_lock"])},
            "gate_file": {"file": common.rel(root, paths["gates"]), "version": gates["version"], "sha256": common.file_sha256(paths["gates"])},
            "camera": CAMERA_NAME,
            "render_resolution": list(render_image.size),
            "render_timestamp_utc": (blender_info or {}).get("render_finished_utc"),
            "validation_started_utc": started,
            "blender_executable": blender_path,
            "blender_info": blender_info,
            "tool_version": common.TOOL_VERSION,
            "tool_sha256": tool_hashes(paths),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "summary": summary,
        "metrics": results,
        "render_segmentation": render_segmentation,
        "render_landmarks": {k: render_analysis[k] for k in ("character", "head", "eyes", "arms_hands")},
        "artifacts": {k: {"file": names[k], "sha256": common.file_sha256(v)} for k, v in image_outputs.items()},
        "identical_to_prior_artifacts": identical,
        "manual_review_required": lock["manual_review_required"],
        "modified": {"geometry": False, "rig": False, "animation": False, "materials": False, "cameras": False,
                     "evidence": "Source .blend SHA-256 identical before and after; the .blend is never saved." if not self_test else "No .blend opened."},
    }
    with open(out_paths["metrics"], "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    log += ["", "## Result", "", "- Status: **%s**" % status, "- FRONT identity gates: **%s**" % summary["front_identity_gates"], ""]
    log += ["| Metric | Blocking | Status | Value | Rule | Pass |", "|---|---|---|---|---|---|"]
    for name, r in results.items():
        rule = ("%s %s" % (r.get("comparison"), r.get("threshold"))) if r.get("comparison") else ("ref <= %s" % r.get("reference_threshold") if r.get("reference_threshold") else "")
        passed = r.get("pass", r.get("within_reference_threshold"))
        log.append("| %s | %s | %s | %s | %s | %s |" % (name, "yes" if r["blocking"] else "no", r["status"],
                   "" if r["value"] is None else "%.6f" % r["value"], rule, "" if passed is None else passed))
    if blender_info:
        log += ["", "## Blender", "", "- Version: %s" % blender_info.get("blender_version"),
                "- Render settings in file: `%s`" % json.dumps(blender_info.get("render_settings_in_file")),
                "- In-memory overrides (never saved): `%s`" % json.dumps(blender_info.get("in_memory_overrides"))]
        for w in blender_info.get("warnings", []):
            log.append("- WARNING: %s" % w)
    log += ["", "## Artifact integrity", ""]
    if identical:
        for k, v in identical.items():
            log.append("- `%s` is byte-identical to: %s%s" % (names[k], ", ".join(v), " (expected: same canonical mask pixels)" if k == "target_mask" else " — REVIEW REQUIRED"))
    else:
        log.append("- No output is byte-identical to any prior file under 05_Renders/Visual_Lock.")
    log += ["", "## Reminder", "", "Passing metrics is not visual approval. Human review approves character fidelity.", ""]
    with open(out_paths["log"], "w", encoding="utf-8") as handle:
        handle.write("\n".join(log))
    print(json.dumps({"status": status, "summary": summary, "out": out}, indent=2))


if __name__ == "__main__":
    if IN_BLENDER:
        blender_render(common.blender_script_args())
    else:
        main()
