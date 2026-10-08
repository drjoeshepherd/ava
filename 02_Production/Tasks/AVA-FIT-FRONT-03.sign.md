<!--
Approved SIGN task. Issued by Joe Shepherd on 2026-10-08.
Stored verbatim as the authority for the changes it authorizes.
-->

@task
AVA-FIT-FRONT-03 — Canonical Visual and Rig-Fit Correction
@status
AUTHORIZED FOR FRONT-ONLY CORRECTION
@source
Use this checkpoint as the implementation baseline:
02_Production\Visual_Lock\FrontVisualFit_v02\Ava_v1.0_FrontVisualFit_v02.blend
Preserve FrontVisualFit_v02 unchanged.
@authoritative_references

* Ava_Target_Front.png
* Ava_Target_Front_Mask.png
* Ava_Geometry_Lock_v1.1.json
* Ava_Material_Lock_v1.0.json
* Ava_Camera_Lock_v1.0.json
* Ava v1.0 — Canonical Character Construction Sheet.png

Canon, target rasters, cameras, evaluation lighting and canonical proportions remain immutable.
@visual_review_decision
FrontVisualFit_v02 is accepted as the new implementation baseline but is NOT approved as the canonical front visual lock.
Its large-scale envelope is viable. The remaining visual and rig-fit blockers must be corrected before SIDE fitting begins.
Numerical gates do not override visual fidelity.
@required_order
Perform corrections in this order:

1. eye measurement contract
2. eyes and face
3. amber shader response
4. canonical neutral arm pose
5. hand and finger rig alignment
6. hair refinement
7. pelvis and leg refinement
8. foot refinement
9. listening-module presentation
10. final FRONT validation

Do not proceed to the next category if a previously passing required gate fails.
@1_eye_measurement_contract
The current EyeSize metric is partly driven by warm skin and blush pixels surrounding the canonical eye. This forces non-canonical dark geometry onto Ava's ceramic face.
Create a versioned SIGN proposal for an EyeSize measurement that evaluates actual eye anatomy:

* visible eye-opening bounds
* upper-lash bounds
* iris diameter
* iris center
* pupil center
* left/right symmetry where appropriate

The new measurement must not depend on blush, skin warmth, under-eye shading or a continuous socket outline.
Do not modify the canonical raster.
Preserve the existing evaluator and gate files unchanged. Create new versioned files for the proposed measurement.
Document old-versus-new results on v02 and the corrected model.
@2_eyes_and_face
Remove the thin circular line beneath each eye.
It currently reads as spectacles or a residual goggle/socket ring.
Required eye treatment:

* no full or nearly full eye-outline ring
* strong canonical upper lash line
* short, subtle lower-lid indication only
* large soft amber irises
* dark pupil zone
* controlled catchlight
* eye opening shaped by lids rather than a circular mechanical border
* retain eye-aim and independent eyelid semantics

Face requirements:

* restore soft cheek and lower-face fullness
* add subtle localized cheek warmth
* retain a warm ivory ceramic/polymer base
* do not turn the entire face into realistic skin
* keep the small dimensional nose and restrained smile
* avoid makeup, fashion lashes and teenage/adult facial anatomy

Do not deform the face merely to pass the old EyeSize metric.
@3_amber_shader_response
The v02 change to amber value 0.26 is NOT approved.
Ava_Material_Lock_v1.0.json remains immutable.
Restore the locked amber material color values.
Correct peach clipping and dull ochre appearance through shader construction without changing:

* locked amber color numbers
* emotional-light control semantics
* keyed light strengths
* animation timing
* locked color management
* evaluation lighting

Preferred approach:

* separate visible amber/gold substrate from driven emission response
* preserve the locked hue
* retain readable gold when emission is low
* produce a clear amber-gold glow at the locked neutral state
* prevent the illuminated region from washing out to peach or white

Do not create a new Material Lock version unless the locked values prove technically impossible. If so, stop and document the conflict rather than changing the lock.
@4_canonical_neutral_arm_pose
The current approximately 30-degree arm splay is not canonical.
Correct the neutral rest/bind pose so the arms sit closer to the torso, matching Ava_Target_Front.png.
Allowed:

* reposition shoulder, elbow and wrist joints
* update the bind/rest pose
* repaint affected weights
* add corrective shape keys
* adjust shells after the joint correction

Required:

* preserve established rig-control names
* preserve IK/FK semantics
* preserve existing animation actions
* do not fake the canonical arm line by inflating the arm shells
* maintain clear joint gaps and rounded product-designed limbs

Existing animation may temporarily deform incorrectly. Canonical geometry and correct joint alignment take precedence. Do not polish or retime animation in this task.
@5_hand_and_finger_rig_alignment
Correct the pre-existing mismatch between hand geometry and finger bones.
Every finger and thumb segment must align with its corresponding bone axis and pivot.
Requirements:

* four fingers plus thumb remain independently articulated
* compact rounded canonical hand proportions
* reduce the current long, flat, fanned appearance
* natural relaxed neutral curl
* readable palm volume
* correct knuckle spacing
* clean wrist transition
* no mitten shape
* no human-realistic slender fingers

Perform a temporary articulation test for every finger and thumb, then return the rig to the canonical neutral pose.
The test must demonstrate that curls bend around the intended knuckles without translation, separation or axis drift.
The hand's visual scale must move materially closer to the canonical reference. HandScaleError is secondary, but the hand must pass visual review and articulation QA.
@6_hair_refinement
Retain the broad sculpted-shell approach, but refine the v02 hair.
Current problems:

* masses read as padded bands
* crown reads too helmet-like
* parting lacks definition
* lower bob lacks the canonical layered inward curl

Required:

* overlapping broad sculpted bob forms
* clear asymmetric sweeping fringe
* controlled side and back volume
* layered inward-curled lower silhouette
* soft manufactured fiber/shell character
* no strand simulation
* no chunky plastic locks

Add the graphite crown/parting structure visible in the canonical reference. This is an existing canonical element, not a new design concept.
Preserve secondary-motion hair-group semantics.
@7_pelvis_and_leg_refinement
The current pelvis plate is too large and triangular.
Refine it toward the canonical compact graphite core:

* smaller central graphite pelvis
* cleaner transition into the torso
* integrated hip structure
* no superhero-brief or oversized armor reading

Refine the legs:

* thighs should be rounded and tapered, not rectangular
* knees should remain visible mechanical joints
* shins should have compact bell-like product forms
* maintain short non-human proportions
* do not increase total character height

@8_foot_refinement
The current feet are too flat and box-like.
Create compact rounded canonical foot pods with:

* softly domed white upper shells
* clear graphite toe-cap transition
* stable graphite soles
* rounded outer corners
* restrained seam language
* unchanged floor contact and total height

Do not introduce sneaker, boot or fashion-footwear styling.
@9_listening_modules
Preserve the approved module concept, scale and placement.
Improve presentation only:

* restore clearly luminous locked amber rings
* maintain clean circular mechanical construction
* retain graphite core and restrained gasket
* preserve left/right independent control
* keep intentional hair overlap without obscuring module identity

Module measurements remain manual review because the canonical raster occludes the complete circles. Do not invent numerical values.
@rig_and_animation_preservation
Preserve:

* RIG_Ava_Master
* established control names
* IK/FK control semantics
* eye-aim controls
* eyelid controls
* emotional-light controls
* all six animation actions
* all working drivers and constraints
* butterfly objects and animation data
* v14 and v02 source files

Do not delete retired or legacy objects. Keep them hidden and non-rendering.
Do not modify butterfly timing or polish any animation.
@front_gates
Required numerical gates:

* SilhouetteIoU >= 0.90
* HeadBodyRatioError <= 0.02
* EyeCenterError <= 0.02 of head width
* new versioned eye-opening/iris gates must pass their documented thresholds
* ListeningModule Center/Diameter remain manual review

The obsolete skin-dependent EyeSize result must still be reported for comparison but must not drive non-canonical geometry.
@visual_acceptance
The clean front render must visually read as canonical Ava:

* soft broad face with localized cheek warmth
* large expressive amber eyes without goggle/socket rings
* sculpted silver-white bob with clear parting
* prominent integrated listening modules
* compact rounded industrial body
* arms close to the torso
* compact functional articulated hands
* rounded tapered legs and stable foot pods
* warm matte ceramic/polymer
* satin graphite
* luminous amber-gold rather than mustard, peach or white

A passing silhouette score is insufficient if these qualities are absent.
@required_qa
Verify and report:

* rig bone count
* driver count and broken-driver count
* constraint count and broken-constraint count
* action inventory
* camera fingerprint
* lighting fingerprint
* Material Lock values
* target and mask checksums
* legacy render-state audit
* finger articulation test
* arm IK/FK sanity test
* eye-aim test
* eyelid/blink test
* listening-ring left/right independence
* chest-light control
* no animation data changed

@required_outputs
Create a new checkpoint without overwriting v02:
02_Production\Visual_Lock\FrontVisualFit_v03\Ava_v1.0_FrontVisualFit_v03.blend
Also return:

* FrontVisualFit_v03_ChangeLog.md
* Front_Clean.png
* Front_Overlay.png
* Front_MaskComparison.png
* Front_Metrics.json
* Canon_vs_Render_Face.png
* Canon_vs_Render_Eyes.png
* Canon_vs_Render_Hair.png
* Canon_vs_Render_ListeningModule.png
* Canon_vs_Render_Hand.png
* Canon_vs_Render_Torso.png
* Canon_vs_Render_Hip.png
* Canon_vs_Render_Foot.png
* EyeMeasurement_vNext_SIGN.md
* EyeMeasurement_OldVsNew.json
* RigArticulation_QA.json
* FrontVisualFit_v03_BuildReport.json
* FrontVisualFit_v03_BlendInventory.json
* reproducible build script

Include a concise table showing metrics after each correction category.
@stop
STOP after the FRONT v03 review package is complete.
Do not:

* begin side, three-quarter or back fitting
* modify canonical targets or masks
* change locked cameras or evaluation lighting
* approve the visual result yourself
* modify or polish the butterfly animation
* overwrite v14 or v02
* commit changes

Return the package for human visual approval.
