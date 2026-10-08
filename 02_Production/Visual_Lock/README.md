# Ava v1.0 Deterministic Visual Lock

This folder holds the objective comparison system for Ava v1.0. The authoritative source is `Ava v1.0 — Canonical Character Construction Sheet.png` (repository root). The lock describes the image. It does not redefine it.

Last corrected by `02_Production/Tasks/AVA-BASELINE-INTEGRITY-001.sign.md` (2026-10-08).

## Authority order

1. Locked canonical raster images (`Targets/`, checksums in the manifest)
2. `Ava_Geometry_Lock_v1.1.json` — **APPROVED** by Joe on 2026-10-08
3. Ava canon Markdown
4. The approved task-specific SIGN spec (`02_Production/Tasks/`)
5. Current Blender implementation

## Locked artifacts (present in this repository)

| File | Role |
|---|---|
| `Targets/Ava_Target_Front.png`, `_ThreeQuarter`, `_Side`, `_Back` | Immutable direct crops from the canonical sheet, 600 × 800 white canvases. |
| `Targets/Ava_Target_Front_Mask.png` | Canonical binary front silhouette (character white, background black, no floor shadow or glow). Traced to `Ava_Target_Front.png` with 0 pixel mismatches on 2026-10-08. |
| `Ava_Target_Manifest_v1.0.json` | SHA-256 for the canonical sheet, the four crops, and (since 2026-10-08) the front mask. |
| `Ava_Geometry_Lock_v1.1.json` | Approved raster-derived front landmarks. Status `APPROVED`. Entries marked `manual_review_required` are unmeasured raster features that need human annotation; they are not waiting on approval of the lock. |
| `Ava_Geometry_Lock_v1.0_to_v1.1_Changes.md` | Why v1.1 replaced v1.0's numbers. |
| `Ava_Front_Acceptance_Gates_v1.0.json` | Authoritative FRONT gates: which metrics block, thresholds, exact formulas, manual-review rule. |
| `Ava_Camera_Lock_v1.0.json` | Locked orthographic cameras. Camera transforms must not change during a fitting pass. |
| `Ava_Material_Lock_v1.0.json` | Material and amber-emission constraints, and evaluation render rules (AgX, no bloom, no DOF). |
| `Ava_Target_Front_Landmarks_v1.1.png` | Visualization of the v1.1 target landmarks. |

## Canonical proportion

TotalHeight / HeadHeight = **2.235668790** (approximately 2.24 heads tall), measured from `Ava_Target_Front.png`. The earlier "~2.5 heads" wording is superseded and is not an evaluation constraint.

## FRONT gates (summary — the JSON file is authoritative)

Blocking: SilhouetteIoU ≥ 0.90, HeadBodyRatioError ≤ 0.02, EyeCenterError ≤ 0.02 (normalized by head width), EyeSizeError ≤ 0.03, ListeningModuleCenterError ≤ 0.03 and ListeningModuleDiameterError ≤ 0.03 only when the target modules are directly measurable (today they are `manual_review_required` because hair occludes them).

Secondary, never blocking: HandScaleError (reported, reference 0.03), TorsoWidthError, ThighWidthError, FootWidthError.

Passing metrics is not visual approval. Human review approves character fidelity.

## Current tooling (`Tools/`)

| Script | Purpose |
|---|---|
| `Ava_VisualLock_Common.py` | Shared library: repo-relative paths, checksum checks, Blender discovery, and the raster measurement functions copied verbatim from the superseded rebuild script, plus metrics, gates and review images. |
| `Ava_ValidateFront.py` | Renders a given `.blend` through `CAM_CANON_FRONT` in Blender background mode and measures the new render against the lock and gates. Writes a provenance-rich metrics JSON and validation log. Never saves the `.blend`. |
| `Ava_InspectBlend.py` | Read-only inventory of a `.blend`: visible/hidden objects, collections, rig bindings, duplicate families, front-ray contribution, actions and owners, and fingerprints of geometry, rig, animation, materials and cameras. |
| `Ava_RebuildVisualLock_v1.1.py` | **Historical. Do not run.** It hard-codes a Codex run directory, overwrites `Ava_Geometry_Lock_v1.1.json` and the front mask, and copies an earlier render as its "measurement". Kept only as the record of how v1.1 was derived. |

Run from the repository root on the Windows machine that has Blender (PowerShell; Pillow required):

```powershell
py 02_Production\Visual_Lock\Tools\Ava_InspectBlend.py `
   --blend 02_Production\Visual_Lock\FrontFit_v14\Ava_v1.0_FrontFit_v14.blend `
   --out 02_Production\Visual_Lock\FrontFit_v14\FrontFit_v14_BlendInventory.json `
   --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

py 02_Production\Visual_Lock\Tools\Ava_ValidateFront.py `
   --blend 02_Production\Visual_Lock\FrontFit_v14\Ava_v1.0_FrontFit_v14.blend `
   --out 05_Renders\Visual_Lock\FrontFit_v14_Verified `
   --label vFit14_Verified `
   --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

`--blender` may be omitted when Blender is on PATH, in `AVA_BLENDER`, or in a standard install folder.

## Files referenced by earlier docs that are not in this repository

| Name | Finding | Status |
|---|---|---|
| `Tools/Ava_VisualLock_Blender.py` | Lived in the original Codex run folder (`outputs\visual-lock-system\Tools\`). Never committed here. | Obsolete. Superseded by `Ava_ValidateFront.py` (render) and `Ava_InspectBlend.py`. Not recreated. |
| `Tools/Ava_VisualLock_Compare.py` | Same origin. Never committed here. | Obsolete. Superseded by `Ava_ValidateFront.py` + `Ava_VisualLock_Common.py`. Not recreated. |
| `Ava_v1.0_VisualLock.blend` | Evaluation copy of an earlier model with the locked cameras and lights. Never committed here. | Obsolete historical artifact. `FrontFit_v14/Ava_v1.0_FrontFit_v14.blend` already contains `CAM_CANON_*`, `LIGHT_KEY/FILL/RIM`, and the `AVA_VISUAL_LOCK` collection. |
| `Ava_Geometry_Lock_v1.0.json` | Superseded by v1.1. Never committed here. | Historical only. Its values are summarized in the v1.0 → v1.1 change notes. |
| `05_Renders/Visual_Lock/FrontFit_v01/`, `FrontFit_v01_Reeval/` results | The v01 re-evaluation files were committed inside `05_Renders/Visual_Lock/FrontFit_v14/` under `Front_vFit01_Reeval_*` names. The `FrontFit_v01_Reeval/` folder in the working copy is empty and untracked. | Obsolete path. No results were fabricated for it. |

## FrontFit_v14 measurement status

The metrics and images in `05_Renders/Visual_Lock/FrontFit_v14/` are **UNVERIFIED** (decision in AVA-BASELINE-INTEGRITY-001). The `vFit14` and `vFit01_Reeval` files there are byte-identical pairs, and the metrics JSON was produced by the historical rebuild script. Do not treat them as authoritative. The authoritative v14 package is `05_Renders/Visual_Lock/FrontFit_v14_Verified/`, produced on 2026-10-08 by `Ava_ValidateFront.py` with Blender 5.2.2 from the committed `.blend` (SHA-256 `D9BD100D…A4D960`). It reproduces the earlier numbers. The read-only inventory is `02_Production/Visual_Lock/FrontFit_v14/FrontFit_v14_BlendInventory.json`.

## Fixed scene objects

- Cameras: `CAM_CANON_FRONT`, `CAM_CANON_3Q`, `CAM_CANON_SIDE`, `CAM_CANON_BACK`
- Lights: `LIGHT_KEY`, `LIGHT_FILL`, `LIGHT_RIM`
- Collection: `AVA_VISUAL_LOCK`

All views use a 600 × 800 frame, orthographic projection, neutral lighting, no depth of field, and no bloom.

## Metric policy

Silhouette IoU uses only the canonical mask file and the render mask. Semantic mouth, brow, cheek, fringe, palm, toe, joint, and listening-module landmarks that the raster does not expose unambiguously are `manual_review_required`. Tools never invent a proxy value or a pass/fail result for them.

The front target SHA-256 is `1C7953A27C24BCD830CE447DC69C76AC71391F39D02743793730952FFC8DDA69`. The front mask SHA-256 is `0232CE4979A936501E8E203D829010AC82368495EF426A4551912374F2813E95`.
