# Why two verified files are byte-identical to older files

Written under AVA-BASELINE-INTEGRITY-001 (@artifact_integrity), 2026-10-08.

`Ava_ValidateFront.py` flagged two byte-identical outputs:

- `Front_RenderMask.png` = `../FrontFit_v14/Front_vFit01_Reeval_RenderMask.png`
- `Front_MaskComparison_vFit14_Verified.png` = `../FrontFit_v14/Front_SilhouetteComparison_vFit14.png` and `../FrontFit_v14/Front_vFit01_Reeval_MaskComparison.png`

## Proof that they were produced independently

1. The new render was made by Blender 5.2.2 LTS (EEVEE) from `02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend`, SHA-256 `D9BD100D7AFEAEA4351F74DD4DF28CA80985D1EC3BDCC8D9AC878FB794A4D960`, unchanged before and after. Its PNG stamp names that repository file and the time 2026/10/08 15:17:29 local.
2. The new render is **not** byte-identical to the old one. It is RGB, the old one RGBA (alpha 255 everywhere), and the stamps differ.
3. Pixel comparison of new vs old render (RGB): 11 of 480,000 pixels differ, each by at most 1 level out of 255. This is normal GPU rendering noise.
4. Silhouette segmentation uses a background tolerance of 3 levels on a flood fill from the border. A change of 1 level on 11 pixels does not move any pixel across that tolerance, so the render mask comes out identical.
5. Pillow writes the same PNG bytes for the same mask pixels, so the mask file and the mask-comparison file are byte-identical.

## Conclusion

The identical files come from a deterministic process run on an independently rendered image of the committed .blend. They are not copies. The earlier `FrontFit_v14` numbers are now reproduced from the actual committed .blend:
SilhouetteIoU 0.911588, HeadBodyRatioError 0.0, EyeCenterError 0.001303, EyeSizeError 0.007831, HandScaleError 0.034027.

The tool status `INTEGRITY_REVIEW_REQUIRED` in the metrics JSON is the automatic flag. This file is the review. Visual approval is still pending human review.
