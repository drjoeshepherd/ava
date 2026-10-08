# Ava FRONT validation log — vFit14_Verified

- Started (UTC): 2026-10-08T20:17:23.552376+00:00
- Canonical manifest: all 6 checksums match.
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Command: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe -b C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\FrontFit_v14\Ava_v1.0_FrontFit_v14.blend --factory-startup --python-exit-code 3 --python C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\02_Production\Visual_Lock\Tools\Ava_ValidateFront.py -- --blender-render C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontFit_v14_Verified\Front_Render_vFit14_Verified.png --info C:\Users\joesh\OneDrive - Dr. Joe Shepherd\6.Content\Ava\05_Renders\Visual_Lock\FrontFit_v14_Verified\_blender_render_info.json`
- Source .blend SHA-256 unchanged before/after render: `D9BD100D7AFEAEA4351F74DD4DF28CA80985D1EC3BDCC8D9AC878FB794A4D960`

## Result

- Status: **INTEGRITY_REVIEW_REQUIRED**
- FRONT identity gates: **PASS**

| Metric | Blocking | Status | Value | Rule | Pass |
|---|---|---|---|---|---|
| SilhouetteIoU | yes | calculated | 0.911588 | >= 0.9 | True |
| HeadBodyRatioError | yes | calculated | 0.000000 | <= 0.02 | True |
| EyeCenterError | yes | calculated | 0.001303 | <= 0.02 | True |
| EyeSizeError | yes | calculated | 0.007831 | <= 0.03 | True |
| ListeningModuleCenterError | yes | manual_review_required |  | <= 0.03 |  |
| ListeningModuleDiameterError | yes | manual_review_required |  | <= 0.03 |  |
| HandScaleError | no | calculated | 0.034027 | ref <= 0.03 | False |
| TorsoWidthError | no | manual_review_required |  |  |  |
| ThighWidthError | no | manual_review_required |  |  |  |
| FootWidthError | no | manual_review_required |  |  |  |

## Blender

- Version: 5.2.2 LTS
- Render settings in file: `{"engine": "BLENDER_EEVEE", "resolution_x": 600, "resolution_y": 800, "resolution_percentage": 100, "film_transparent": false, "view_transform": "AgX", "look": "None", "active_camera": "CAM_CANON_FRONT"}`
- In-memory overrides (never saved): `{"scene.camera": "CAM_CANON_FRONT", "resolution": [600, 800], "resolution_percentage": 100, "file_format": "PNG RGB 8-bit"}`

## Artifact integrity

- `Front_RenderMask.png` is byte-identical to: 05_Renders/Visual_Lock/FrontFit_v14/Front_vFit01_Reeval_RenderMask.png — REVIEW REQUIRED
- `Front_MaskComparison_vFit14_Verified.png` is byte-identical to: 05_Renders/Visual_Lock/FrontFit_v14/Front_SilhouetteComparison_vFit14.png, 05_Renders/Visual_Lock/FrontFit_v14/Front_vFit01_Reeval_MaskComparison.png — REVIEW REQUIRED

## Reminder

Passing metrics is not visual approval. Human review approves character fidelity.
