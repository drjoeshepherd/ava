# Ava v1.0 Deterministic Visual Lock

This package establishes an objective comparison system for Ava v1.0. The authoritative source is `Ava v1.0 — Canonical Character Construction Sheet.png`. No mesh fitting or character redesign was performed while creating this lock.

## Locked artifacts

- `Targets/`: immutable direct crops from the canonical turnaround, normalized onto 600 × 800 white canvases.
- `Ava_Target_Manifest_v1.0.json`: SHA-256 identities for the canonical source and all four immutable target crops.
- `Ava_Geometry_Lock_v1.0.json`: normalized target landmarks using total character height = 1.0 and centerline x = 0.
- `Ava_Material_Lock_v1.0.json`: canonical material and amber-emission constraints.
- `Ava_Camera_Lock_v1.0.json`: exact orthographic camera specifications.
- `Ava_v1.0_VisualLock.blend`: evaluation copy containing the existing Ava model plus the locked cameras and neutral studio lights.
- `Tools/Ava_VisualLock_Blender.py`: creates or refreshes the evaluation scene and renders the four fixed views.
- `Tools/Ava_VisualLock_Compare.py`: aligns the rendered figure to each target, generates overlays and differences, and records metrics.

The evaluation collection, camera objects, and light objects carry lock metadata in the Blender file. Camera transforms must not be adjusted during a fitting pass.

## Fixed scene objects

- Cameras: `CAM_CANON_FRONT`, `CAM_CANON_3Q`, `CAM_CANON_SIDE`, `CAM_CANON_BACK`
- Lights: `LIGHT_KEY`, `LIGHT_FILL`, `LIGHT_RIM`
- Collection: `AVA_VISUAL_LOCK`

All views use a 600 × 800 frame, orthographic projection, neutral world lighting, no depth of field, and no bloom or dramatic effects.

## Repeatable evaluation

From the project root:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "outputs\visual-lock-system\Tools\Ava_VisualLock_Blender.py"
py "outputs\visual-lock-system\Tools\Ava_VisualLock_Compare.py"
```

The comparison output is written to `outputs/05_Renders/Visual_Lock/` as `Render`, `Overlay`, and `Difference` images for Front, ThreeQuarter, Side, and Back, plus `Visual_Lock_Metrics.json`.

## Metric policy

The harness calculates silhouette overlap and measurements that can be obtained deterministically from the model and lock data. Semantic mouth, brow, cheek, fringe, palm, and toe-curvature landmarks are explicitly marked as not calculated because object bounds cannot measure them reliably. They must be reviewed visually; the harness does not invent proxy values.

Automatic silhouette masks use sampled neutral-background segmentation. White edge pixels should be visually checked against the overlays if a render setup changes.

## Current baseline

The current implementation is recorded as a failing baseline against the locked thresholds. This is expected: the lock was created before any mesh correction, so later work can be measured against a fixed, auditable starting point.

## v1.1 authority repair

`Ava_Geometry_Lock_v1.1.json` supersedes the numeric geometry measurements in v1.0 for the front view. Every accepted landmark is measured from the immutable `Targets/Ava_Target_Front.png` and records pixel coordinates, normalized coordinates, source, and derivation. Any feature that cannot be isolated unambiguously in the raster is marked `manual_review_required`; no proxy measurement is substituted.

The exact raster-derived proportion is 2.235668790 heads tall. The descriptive canon remains approximately 2.5 heads tall, but it is not used as an exact evaluation constraint.

`Targets/Ava_Target_Front_Mask.png` is the canonical binary silhouette mask. It contains the character in white and the background in black, excluding the floor shadow and glow. Front silhouette IoU is calculated only from this mask and `Front_vFit01_Reeval_RenderMask.png`.

The current front fit was re-evaluated without modifying geometry, rig, controls, materials, or animation. Its review package is in `../05_Renders/Visual_Lock/FrontFit_v01_Reeval/` and includes the render, overlay, difference, mask comparison, render mask, and auditable metrics JSON.

To regenerate the v1.1 measurement and re-evaluation package from the project root:

```powershell
py "outputs\visual-lock-system\Tools\Ava_RebuildVisualLock_v1.1.py"
```

The target checksum is checked before and after processing. The expected SHA-256 is `1C7953A27C24BCD830CE447DC69C76AC71391F39D02743793730952FFC8DDA69`.
