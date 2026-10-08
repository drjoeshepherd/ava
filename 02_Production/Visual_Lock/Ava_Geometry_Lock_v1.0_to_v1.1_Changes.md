# Ava Geometry Lock v1.0 → v1.1 Changes

## Authority repair

Version 1.1 is derived directly from `Ava_Target_Front.png`. It does not reuse conflicting v1.0 numeric geometry. The canonical raster now overrides v1.0, the approximate `~2.5 heads` prose, and the Blender implementation.

The canonical image SHA-256 remains `1C7953A27C24BCD830CE447DC69C76AC71391F39D02743793730952FFC8DDA69`.

## Replaced values

| Measurement | v1.0 value | v1.1 raster-derived value | Resolution |
|---|---:|---:|---|
| Head height / character height | `0.4` | `0.447293447` (314 px) | Replaced with mask-derived head contraction boundary. |
| Heads tall | `2.5` | `2.235668790` | Exact raster ratio replaces approximate prose. |
| Image-left eye center | `[-0.103, 0.79]` | `[-0.0933048433048433, 0.6809116809116809]` | Replaced with local eye-feature bbox center. |
| Image-right eye center | `[0.103, 0.79]` | `[0.0868945868945869, 0.6915954415954416]` | Replaced with local eye-feature bbox center. |
| Eye bounds | width `0.1`, height `0.112` | left `{'xmin': -0.1574074074074074, 'xmax': -0.0292022792022792, 'ymin': 0.6054131054131054, 'ymax': 0.7564102564102564}`, right `{'xmin': 0.02492877492877493, 'xmax': 0.14886039886039887, 'ymin': 0.6210826210826211, 'ymax': 0.7621082621082621}` | Replaced with raster feature bounds. |
| Listening-module center/diameter | centers `[-0.242, 0.786]`, `[0.242, 0.786]`; diameter `0.132` | `manual_review_required` | Full circles are occluded by hair; v1.0 exact values were unsupported. |
| Torso/waist/pelvis exact widths | v1.0 numeric estimates | `manual_review_required` | Touching/overlapping raster shells prevent unambiguous isolation. |
| Joint centers and segment lengths | v1.0 numeric estimates | `manual_review_required` | Joint centers are visually occluded and cannot be stored as exact raster measurements. |
| Foot dimensions | v1.0 numeric estimates | `manual_review_required` | Foot/shin boundary and floor contact require human annotation. |

## Metric changes

- Silhouette comparison now uses `Ava_Target_Front_Mask.png` against `Front_vFit01_Reeval_RenderMask.png`; RGB difference is not used for IoU.
- Eye-center error is normalized by raster-derived head width.
- Eye-size error is normalized independently by target eye width and height.
- Body landmark errors use canonical character height.
- Ambiguous targets have no pass/fail result.

## Remaining human review

- `face.brow_landmarks`
- `hair.side_silhouette_landmarks`
- `listening_modules.left center/outer diameter/inner diameter`
- `listening_modules.right center/outer diameter/inner diameter`
- `torso.shoulder_centers/widest_points/waist_extents/pelvis_extents`
- `arms_hands.shoulder/elbow/wrist`
- `legs_feet.hip/knee/ankle/thigh_width/lower_leg_width/foot_bounding_boxes`
