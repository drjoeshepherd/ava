<!--
PROPOSED SIGN task — NOT APPROVED. Drafted by Claude Code under AVA-FIT-FRONT-03 section 1, 2026-10-08.
If approved, store as 02_Production/Tasks/AVA-EYE-MEASUREMENT-vNext.sign.md.
-->

@task
AVA-EYE-MEASUREMENT-vNext (proposal)

@status
PROPOSED — awaiting Joe Shepherd's approval

@problem
The approved front eye gates (Ava_Front_Acceptance_Gates_v1.0.json: EyeSizeError, EyeCenterError) measure a box
of "dark or strongly chromatic" pixels inside a window around the amber iris. On the canonical raster that box is
set by warm skin, blush, the mouth and hair shadow, not by the eye:

- left eye: top edge = hair-strand shading, bottom edge = hair shadow, inner edge = skin (chroma > 40)
- right eye: top and outer edges = skin, bottom edge = the mouth

A warm-white ceramic face has no such pixels, so the v1.0 gates can only be met with non-canonical geometry
(v14 goggle ring, v02 socket seam) or a skin-toned face. With the seam removed (FrontVisualFit_v03) both v1.0 eye
gates fail on the left eye although the eye itself matches the canon.

@proposal
Add anatomical eye gates, measured by the same code on the canonical raster and the render:

| Gate | Threshold | Measures |
|---|---|---|
| IrisCenterError | 0.02 head width | centre of a circle of the measured iris width tangent to the lowest amber row |
| IrisDiameterError | 6 % | horizontal width of the amber iris (vertical extent is lid-occluded in the canon) |
| PupilCenterError | 0.03 head width | centroid of luminance < 70 pixels inside the iris box |
| UpperLashSpanError | 10 % | width of the dark upper-lash component (outside the iris circle, above its centre) |
| UpperLashTopError | 0.02 head width | top row of the upper lash |
| EyeOpeningSizeError | 6 % | lash corners and lash top down to the lowest iris row |
| EyeOpeningCenterError | 0.02 head width | centre of that opening box |
| IrisSymmetryError | 5 % | left/right iris-width ratio versus the canonical ratio |

Head width = Geometry Lock head.max_width_row (429 px), as in the approved EyeCenterError. No feature uses skin
colour, blush, cheek warmth, under-eye shading or a socket outline; the canonical lower lid is skin-toned and is
deliberately not read. Thresholds were set before measuring FrontVisualFit_v03 and are not tuned to it.

@files (new, versioned; nothing existing is changed)
- 02_Production/Visual_Lock/Ava_Front_EyeAnatomy_Gates_vNext_PROPOSED.json — gates, formulas, rationale
- 02_Production/Visual_Lock/Tools/Ava_EyeAnatomy_vNext.py — measurement tool
- Unchanged: Ava_Front_Acceptance_Gates_v1.0.json, Ava_ValidateFront.py, Ava_VisualLock_Common.py, Targets/*

@decision_requested
1. Replace v1.0 EyeSizeError with the eight gates above (or a subset).
2. Replace v1.0 EyeCenterError with IrisCenterError + EyeOpeningCenterError (2026-10-08 interim decision for v03:
   v1.0 EyeCenterError is reported only).
3. If approved: version the gate file (v1.1), add the tool to Ava_ValidateFront.py under a new tool version, and
   keep reporting the v1.0 values for traceability.

@results (EyeMeasurement_OldVsNew.json)

| Model | v1.0 EyeCenter (worst eye) | v1.0 EyeSize (worst eye) | vNext all gates |
|---|---|---|---|
| Canonical raster vs itself | — | — | PASS (all 0; self-consistency check of the tool) |
| FrontVisualFit_v02 (with socket seam) | 0.0026 PASS | 0.0148 PASS | FAIL — opening size 0.108, lash top 0.019 OK, opening centre 0.020 FAIL |
| FrontVisualFit_v03 (no ring) | 0.0314 FAIL | 0.2858 FAIL | PASS — iris centre 0.004, diameter 0.021, pupil 0.012, lash span 0.041, lash top 0.002, opening size 0.027, opening centre 0.003, symmetry 0.021 |

The comparison shows the v1.0 gates rewarded the non-canonical seam (v02 passed while its lash sat ~8 px high and
its inner lash ran ~11 px long), and penalise the anatomically corrected eye.
