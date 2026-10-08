# FrontVisualFit_v03 — change log

Task: `02_Production/Tasks/AVA-FIT-FRONT-03.sign.md` (approved 2026-10-08).
Status: **review package ready for human visual approval. Not self-approved.**

## Provenance

| Item | Value |
|---|---|
| Baseline (read only, unchanged) | `FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend` — `E9886775…AC03957` before and after |
| New checkpoint | `02_Production/Visual_Lock/FrontVisualFit_v03/Ava_v1.0_FrontVisualFit_v03.blend` — `0B780DC37A43EBA4F5B34D7C976F94B0C0C173D66FE8FDFE96EA6F71997501E8` |
| Build script | `Tools/Ava_FrontVisualFit_v03_Build.py` — `DBC89EC5…99D954` (loads the unchanged v02 builder's helpers, hash-checked) |
| Eye measurement (proposal) | `Tools/Ava_EyeAnatomy_vNext.py` — `A0F2034E…23FF84`; gates `Ava_Front_EyeAnatomy_Gates_vNext_PROPOSED.json` — `73156FE1…935876` |
| Rig QA tool | `Tools/Ava_RigQA.py` — `1B39C0CB…28A2BF` |
| Build report / inventory | `02_Production/Visual_Lock/FrontVisualFit_v03/FrontVisualFit_v03_BuildReport.json`, `…_BlendInventory.json` |
| Official validation | `Validation/` (Ava_ValidateFront.py, unchanged, on the saved checkpoint); target and mask checksums all match |

`Front_Clean.png`, `Front_Overlay.png`, `Front_MaskComparison.png`, `Front_Metrics.json` are byte copies of the
matching `Validation/` files.

Rebuild: `blender -b 02_Production/Visual_Lock/FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend --factory-startup --python 02_Production/Visual_Lock/Tools/Ava_FrontVisualFit_v03_Build.py -- --save <out.blend>`

## Decisions taken with Joe during the task (2026-10-08)

1. **v1.0 EyeCenterError is report-only**, like v1.0 EyeSizeError: both are set by skin/blush pixels in the
   canonical raster. The proposed IrisCenterError and EyeOpeningCenterError carry the eye-position gate.
2. **SilhouetteIoU is gated at the final validation.** Categories 5 and 6 measured below 0.90 (see table): the
   canonical arm pose opens a real gap between elbow and waist that the canonical mask counts as silhouette (soft
   shadow on white), and the locked grey world renders no shadow there. No non-canonical bulk was added to hide it.

## Front gates (final, official checkpoint)

| Gate | v02 | v03 | Rule | Result |
|---|---|---|---|---|
| SilhouetteIoU | 0.9133 | **0.9142** | >= 0.90 | PASS |
| HeadBodyRatioError | 0.0112 | **0.0049** | <= 0.02 | PASS |
| Proposed eye-anatomy gates (8) | FAIL (opening size 0.108, opening centre 0.020) | **all PASS** | see proposal | PASS |
| ListeningModule Center / Diameter | manual review | manual review | — | not measurable |
| v1.0 EyeCenterError (worst eye) — report only | 0.0026 | 0.0314 | <= 0.02 | reported |
| v1.0 EyeSizeError (worst eye) — report only | 0.0148 | 0.2858 | <= 0.03 | reported |
| HandScaleError (secondary) | 0.1400 | 0.0683 | — | reported |

Ava_ValidateFront.py (v1.0 gate file) therefore prints `front_identity_gates: FAIL` with failing gates
EyeCenterError and EyeSizeError only. Details: `EyeMeasurement_OldVsNew.json`, `EyeMeasurement_vNext_SIGN.md`.

## Metrics after each correction category

Cumulative builds (that category plus every earlier one), CAM_CANON_FRONT, locked lights; self-test mode except
the final official row above.

| # | Category | IoU | Head ratio | vNext eye gates | Iris centre | Opening size | Opening centre | v1.0 EyeCenter | Hand scale |
|---|---|---|---|---|---|---|---|---|---|
| — | v02 baseline | 0.9133 | 0.0112 | FAIL | 0.0000 | 0.1077 | 0.0204 | 0.0026 | 0.1400 |
| 1 | eye measurement contract | — (no model change) | | | | | | | |
| 2 | eyes and face | 0.9139 | 0.0112 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.1400 |
| 3 | amber shader | 0.9139 | 0.0112 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.1400 |
| 4 | neutral arm pose | 0.9000 | 0.0174 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.1197 |
| 5 | hand / finger alignment | **0.8959** | 0.0174 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |
| 6 | hair | **0.8936** | 0.0049 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |
| 7 | pelvis and legs | 0.9131 | 0.0049 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |
| 8 | feet | 0.9137 | 0.0049 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |
| 9 | listening modules | 0.9143 | 0.0049 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |
| 10 | final validation (official) | 0.9142 | 0.0049 | PASS | 0.0037 | 0.0269 | 0.0026 | 0.0314 | 0.0683 |

## What changed

1. **Eye measurement contract.** New versioned proposal (tool + gate file + SIGN draft). Existing evaluator and
   gate files untouched.
2. **Eyes and face.** Socket seam removed (`GEO_EyeRim.L/R` render-disabled, kept). Eye opening is an almond
   sclera shaped by the lash and lower-lid curves; strong canonical upper lash back at its canonical bounds
   (v02 had raised it ~8 px for the old metric); short subtle lower lid; iris sized to the canonical width and tucked
   under the lash; dark pupil zone and one catchlight unchanged in kind. Cheek and lower-face fullness restored;
   warm ivory base; localized cheek warmth in head space (follows head motion). Nose and smile re-seated. Eye-aim
   objects, eyelid controls and their drivers unchanged.
3. **Amber.** Locked emission colour (1.0, 0.43, 0.008) restored on the three driven materials; v14 base values
   restored on the driven node; drivers and keyed strengths untouched. The driven node is blended over a
   non-emissive gold substrate (locked hue, low value) by a view-facing response mask: bright along the
   camera-facing core, deep gold at the edges. No Material Lock change.
4. **Neutral arm pose (rig rest pose).** Elbows and wrists moved to the canonical joint positions measured from the
   raster's dark joint components (elbow px 190.5/409.5, y 449.5; wrist 117/483, y 515; shoulders unchanged).
   Bones re-aimed with roll-preserving rotations; hand and finger bones moved rigidly; CTRL_Hand_IK and
   CTRL_ElbowPole moved to the new wrist/elbow. Names, hierarchy, constraints and drivers unchanged. Arm shells
   rebuilt at canonical size along the new bones (no inflation), with graphite gaps; shoulder socket at its
   canonical size.
5. **Hands and fingers.** Finger and thumb rest bones laid out on a canonical back-of-hand: knuckle line across the
   palm, slight fan, relaxed curl, thumb on the body side; roll aligned to the back-of-hand normal. Every finger
   segment is a capsule exactly on its own bone. Compact palm. Articulation QA passes (below).
6. **Hair.** Graphite crown band and parting added (`GEO_CrownBand_C`, new, on DEF_Head). Fringes re-cut to start
   below the band so the parting opens; sharper, thinner lens sections; softer cavity shading; subtle fibre bump;
   lower bob tips curl inward; crown cap re-centred on the canonical crown. All masses keep their SEC_Hair parents.
7. **Pelvis and legs.** Compact rounded graphite core; integrated hip blocks at canonical size; thighs slanted and
   rounded (inner tops cut back as in the canon); shins compact bells meeting at their widest row; knees unchanged
   as visible joints; height unchanged.
8. **Feet.** Domed white upper with rounded corners, graphite toe-cap arc under the shin, graphite sole tray;
   bottom row kept at the v14 floor contact (character height unchanged, 703 px).
9. **Listening modules.** Same concept, scale, placement and driven materials; fuller luminous ring, thin restrained
   gasket, graphite core.

## Required QA (RigArticulation_QA.json)

| Check | Result |
|---|---|
| Rig bones | 52 |
| Constraints / broken | 4 / 0 |
| Drivers / broken | 24 / 0 (counts object and node-tree driver records) |
| Actions | 6, owners unchanged; **animation data identical to v02** (keyframe hash) |
| Camera fingerprint | identical to v02 |
| Lighting fingerprint (lights, world, colour management) | identical to v02; only KEY/FILL/RIM render |
| Material Lock values | white, graphite, accent grey, amber emission all match exactly |
| Target and mask checksums | all match (validation manifest check) |
| Legacy render state | no Shell_/Canon_/HairShell_/HairGroup_/RETIRED_ object renders, except the live Shell_Head and Shell_Hand.L/R (live since v14) |
| Finger articulation (+45 / -30 deg, every finger and thumb, both hands) | PASS — worst rigid residual 7e-7, axis drift 0.03 deg, knuckle offset 1e-6, joint gap 0 (v02: 26.7 deg, 0.36 units); returned to neutral |
| Arm FK / IK | PASS — FK moves the wrist, shells rigid; IK on at rest drifts 1e-6; IK wrist reaches a moved target within 1e-6 |
| Eye aim | **finding**: CTRL_EyeAim drives only the hidden legacy Eye_Iris; the live GEO_CanonicalIris (on an undriven MCH_EyeAim empty) does not move. Same in v02. Not changed. |
| Eyelid / blink | driver responds (scale Z 1.0 → 0.18) but the axis is depth, so the lash does not close the eye. Same in v02. Not changed. |
| Listening rings | independent (L 7.2 / R 0.2 and the reverse), each on its own driven material |
| Chest light | responds (0.2 → 7.2) |

Override tests detach the actions in memory only; nothing was saved.

## Open items for review

1. **Approve or amend the eye-measurement proposal** (`EyeMeasurement_vNext_SIGN.md`).
2. **IoU dip during categories 5–6** recorded above; final 0.9142.
3. **Eye aim and blink** do not move/close the live eye (pre-existing). Fixing needs a rig/driver task.
4. **Amber brightness ceiling.** Under the locked AgX view the locked hue cannot reach the canon's bright saturated
   amber; the response shader keeps it gold rather than peach at the neutral state. At high light states (strength
   up to 7.2) the camera-facing core will brighten toward pale gold.
5. **Existing animation now deforms differently** for the arm channels keyed in RIG_Ava_MasterAction (new rest
   pose), as the SIGN allows. Not polished.
6. **Sclera** reads only faintly beside the large irises under the flat locked lighting.
7. Construction sheet text says "2.5 heads"; the Geometry Lock ratio (2.2357) governs and was not changed.

## Stop

Stopped after the FRONT v03 review package. No side/three-quarter/back fitting, no canon, target, camera or
lighting change, no animation polish, nothing committed.
