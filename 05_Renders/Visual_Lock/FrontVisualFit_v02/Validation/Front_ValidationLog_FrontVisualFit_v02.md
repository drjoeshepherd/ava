# Ava FRONT validation log — FrontVisualFit_v02

- Started (UTC): 2026-10-08T21:32:31.818699+00:00
- Canonical manifest: all 6 checksums match.
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Command: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe -b C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\FrontVisualFit_v02\Ava_v1.0_FrontVisualFit_v02.blend --factory-startup --python-exit-code 3 --python C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\Tools\Ava_ValidateFront.py -- --blender-render C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontVisualFit_v02\Validation\Front_Render_FrontVisualFit_v02.png --info C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontVisualFit_v02\Validation\_blender_render_info.json`
- Source .blend SHA-256 unchanged before/after render: `E9886775D75A5A66EEB771E3D1AFBDFD5DBC09F062A4BD48E39FA3378AC03957`

## Result

- Status: **VERIFIED_MEASUREMENT_REVIEW_REQUIRED**
- FRONT identity gates: **PASS**

| Metric | Blocking | Status | Value | Rule | Pass |
|---|---|---|---|---|---|
| SilhouetteIoU | yes | calculated | 0.913350 | >= 0.9 | True |
| HeadBodyRatioError | yes | calculated | 0.011172 | <= 0.02 | True |
| EyeCenterError | yes | calculated | 0.002127 | <= 0.02 | True |
| EyeSizeError | yes | calculated | 0.012761 | <= 0.03 | True |
| ListeningModuleCenterError | yes | manual_review_required |  | <= 0.03 |  |
| ListeningModuleDiameterError | yes | manual_review_required |  | <= 0.03 |  |
| HandScaleError | no | calculated | 0.139999 | ref <= 0.03 | False |
| TorsoWidthError | no | manual_review_required |  |  |  |
| ThighWidthError | no | manual_review_required |  |  |  |
| FootWidthError | no | manual_review_required |  |  |  |

## Blender

- Version: 5.2.2 LTS
- Render settings in file: `{"engine": "BLENDER_EEVEE", "resolution_x": 600, "resolution_y": 800, "resolution_percentage": 100, "film_transparent": false, "view_transform": "AgX", "look": "None", "active_camera": "CAM_CANON_FRONT"}`
- In-memory overrides (never saved): `{"scene.camera": "CAM_CANON_FRONT", "resolution": [600, 800], "resolution_percentage": 100, "file_format": "PNG RGB 8-bit"}`

## Artifact integrity

- `Front_TargetMask.png` is byte-identical to: 05_Renders/Visual_Lock/FrontFit_v14_Verified/Front_TargetMask.png (expected: same canonical mask pixels)

## Reminder

Passing metrics is not visual approval. Human review approves character fidelity.
