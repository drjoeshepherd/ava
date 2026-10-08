# Ava v1.0 — FRONT Fit v14 Change Log

## Lock basis

- Geometry lock: `Ava_Geometry_Lock_v1.1.json`
- Canonical raster: `Ava_Target_Front.png`
- Canonical silhouette: `Ava_Target_Front_Mask.png`
- Target SHA-256: `1C7953A27C24BCD830CE447DC69C76AC71391F39D02743793730952FFC8DDA69`
- Locked front camera and evaluation lights: unchanged
- Rig hierarchy, control names, emotional-light controls, and animation data: preserved

## Geometry changes

- Refit the outer head and broad bob silhouette with height-weighted crown shaping.
- Extended the existing lower bob curls only enough to restore the canonical cheek-line silhouette and locked head/body contraction.
- Enlarged and lowered the eye assembly in measured stages; retained eye-aim parenting and independent eyelid controls.
- Expanded the existing forearm shells from fixed inner edges while preserving their bone parents.
- Restored compact foot-pod height and added shallow, bone-parented ceramic vamps across the lower boot-front split.
- Preserved the approved listening-module design and amber material system; no new design language was introduced.

## Locked front results

- Silhouette IoU: `0.9115882579711777` — PASS (`>= 0.90`)
- Head/body ratio error: `0.0%` — PASS (`<= 2%`)
- Eye-center error: `0.13030699169579195%` of head width — PASS (`<= 2%`)
- Eye-size error: `0.7830954092636335%` — PASS (`<= 3%`)
- Canonical measured ratio: `2.2356687898089174` heads tall

## Manual review remains required

- Listening-module centers and diameters: the canonical hair occludes the complete circles, so no numerical pass value is asserted.
- Brow and side-hair landmarks.
- Shoulder, torso, arm-joint, thigh, lower-leg, and foot boundaries where the raster does not expose an unambiguous boundary.
- Hand scale is reported by the evaluator at `3.4027046013347384%`; hand scale is not one of the approved FRONT gate metrics and was not changed after the required gates passed.

No side, three-quarter, or back fitting was started. No butterfly animation data was modified.
