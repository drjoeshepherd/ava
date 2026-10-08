# Ava FRONT validation log — FrontVisualFit_v03

- Started (UTC): 2026-10-08T22:31:41.438929+00:00
- Canonical manifest: all 6 checksums match.
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Command: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe -b C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\FrontVisualFit_v03\Ava_v1.0_FrontVisualFit_v03.blend --factory-startup --python-exit-code 3 --python C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\Tools\Ava_ValidateFront.py -- --blender-render C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontVisualFit_v03\Validation\Front_Render_FrontVisualFit_v03.png --info C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontVisualFit_v03\Validation\_blender_render_info.json`
- Source .blend SHA-256 unchanged before/after render: `0B780DC37A43EBA4F5B34D7C976F94B0C0C173D66FE8FDFE96EA6F71997501E8`

## Result

- Status: **VERIFIED_MEASUREMENT_REVIEW_REQUIRED**
- FRONT identity gates: **FAIL**

| Metric | Blocking | Status | Value | Rule | Pass |
|---|---|---|---|---|---|
| SilhouetteIoU | yes | calculated | 0.914249 | >= 0.9 | True |
| HeadBodyRatioError | yes | calculated | 0.004914 | <= 0.02 | True |
| EyeCenterError | yes | calculated | 0.016504 | <= 0.02 | False |
| EyeSizeError | yes | calculated | 0.148249 | <= 0.03 | False |
| ListeningModuleCenterError | yes | manual_review_required |  | <= 0.03 |  |
| ListeningModuleDiameterError | yes | manual_review_required |  | <= 0.03 |  |
| HandScaleError | no | calculated | 0.068343 | ref <= 0.03 | False |
| TorsoWidthError | no | manual_review_required |  |  |  |
| ThighWidthError | no | manual_review_required |  |  |  |
| FootWidthError | no | manual_review_required |  |  |  |

## Blender

- Version: 5.2.2 LTS
- Render settings in file: `{"engine": "BLENDER_EEVEE", "resolution_x": 600, "resolution_y": 800, "resolution_percentage": 100, "film_transparent": false, "view_transform": "AgX", "look": "None", "active_camera": "CAM_CANON_FRONT"}`
- In-memory overrides (never saved): `{"scene.camera": "CAM_CANON_FRONT", "resolution": [600, 800], "resolution_percentage": 100, "file_format": "PNG RGB 8-bit"}`

## Artifact integrity

- `Front_TargetMask.png` is byte-identical to: 05_Renders/Visual_Lock/FrontFit_v14_Verified/Front_TargetMask.png, 05_Renders/Visual_Lock/FrontVisualFit_v02/Validation/Front_TargetMask.png (expected: same canonical mask pixels)

## Reminder

Passing metrics is not visual approval. Human review approves character fidelity.
