# UNVERIFIED — do not use these FrontFit_v14 measurements as authoritative

Decision: `02_Production/Tasks/AVA-BASELINE-INTEGRITY-001.sign.md` (Joe Shepherd, 2026-10-08).

Facts found on 2026-10-08:

- Each `Front_*_vFit14.*` file here is byte-identical to a `Front_vFit01_Reeval_*` file in this folder (render, overlay, mask comparison, metrics).
- `Front_Metrics_vFit14.json` uses the schema `Ava_Front_vFit01_Reevaluation_v1.1` and states `geometry_modified: false`, while `Front_ChangeLog_vFit14.md` lists geometry changes. It was written by the historical `Ava_RebuildVisualLock_v1.1.py`, which copies an input render rather than rendering a .blend.
- The PNG metadata stamped by Blender in `Front_Render_vFit14.png` names `...\outputs\front-fit-v14\Ava_v1.0_FrontFit_v14.blend`, camera `CAM_CANON_FRONT`, rendered 2026/10/08 14:42:25. This suggests the render came from a v14 file, but it does not prove it came from the exact .blend committed in this repository.
- Re-measuring `Front_Render_vFit14.png` with the new `Ava_ValidateFront.py --self-test-image` reproduces the same numbers exactly. That confirms the formulas match, not the source model.

Update 2026-10-08: the authoritative package now exists in `../FrontFit_v14_Verified/`, rendered by Blender 5.2.2 from the committed .blend. It reproduces these numbers (see `../FrontFit_v14_Verified/Integrity_Explanation_vFit14_Verified.md`). Cite the verified package, not this folder.

The files in this folder are kept unchanged as history.
