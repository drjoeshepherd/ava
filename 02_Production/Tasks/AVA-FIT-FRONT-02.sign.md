<!--
Approved SIGN task. Issued by Joe Shepherd on 2026-10-08.
Stored verbatim as the authority for the changes it authorizes.
-->

@task
AVA-FIT-FRONT-02

@status
Front geometric baseline = VERIFIED
Front geometric gates = PASS
Front visual fidelity = NOT APPROVED

@baseline
Use:

02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend

Use only the live GEO_* implementation unless a change explicitly requires otherwise.

Do not reactivate legacy Shell_*, Canon_*, HairShell_*, or HairGroup_* geometry.

@authority
Canonical raster images > raster-derived geometry locks > Ava canon > this SIGN task > current Blender implementation

@objective
Make the verified v14 front-view model visually read as the locked canonical Ava while preserving the currently passing front geometry gates.

This is a visual-construction refinement task.

It is NOT a redesign.

@hard_preserve
Maintain:

SilhouetteIoU >= 0.90
HeadBodyRatioError <= 2%
EyeCenterError <= 2%
EyeSizeError <= 3%

Preserve:
- rig semantics
- 52-bone rig
- controller names
- six animation actions
- emotional-light infrastructure
- canonical cameras
- canonical lights
- target images
- target masks
- measurement definitions

If a proposed visual improvement would break a passing identity metric:
prefer the canonical raster
make the smallest geometry change necessary
re-run metrics immediately

@current_visual_failures

HAIR:
Current hair reads as soft white blobs / helmet-like masses.

Canonical target requires:
- short silver-white bob
- clearly designed silhouette
- broad sculpted overlapping sections
- visible separation between major hair forms
- controlled taper around cheeks
- intentional back/side volume
- no realistic strands
- no amorphous blobs
- no spiky plastic chunks

Create approximately 5-9 visually meaningful major hair masses.
Do not create dozens of strands.

EYES:
Current eyes have heavy dark perimeter rings that read like glasses/goggles.

Canonical target requires:
- large dimensional amber eyes
- dark rim visually subordinate to iris
- visible iris depth
- visible pupil
- subtle off-white sclera
- controlled catchlight
- warm synthetic expression

Reduce apparent dark eye-ring thickness substantially.

The eye should read first as:
AMBER EYE

not:
BLACK RING WITH AMBER CENTER

FACE:
Current face lacks canonical cheek volume and softness.

Target:
- broad soft cheeks
- small lower face
- minimal nose
- small subtle mouth
- synthetic rather than human anatomy
- no makeup cues
- no teenage-girl read

Mouth should be dimensional geometry, not a drawn line.

GRAPHITE STRUCTURE:
Current render hides too much of Ava's graphite mechanical structure.

Canonical Ava visibly uses graphite at functional articulation points.

Restore clearly readable graphite at:
- neck interface
- shoulder articulation
- elbows
- wrists
- waist/core transition
- hips/pelvis articulation
- knees
- ankles
- foot/leg interface where supported by canon

Do not add decorative graphite panels.

Graphite must explain structure.

TORSO:
Current torso reads too monolithic.

Target:
- smooth warm white shell
- subtle graphite core/waist structure
- integrated chest emitter
- minimal but readable mechanical construction

Avoid:
- stacked cylinders
- action-figure armor
- decorative seams

HANDS:
Current hands read as dark mitts.

Canonical requirement:
- visible palm form
- individually readable fingers
- readable thumb
- compact scale
- suitable for:
  - pointing
  - reaching
  - open palm
  - gentle grasp

Preserve articulation.

Hands must remain mechanically simple but visually legible.

ARMS / LEGS:
Keep compact proportions.

Improve:
- white shell continuity
- deliberate graphite articulation
- rounded product-design forms

Avoid:
- toy cylinders
- long human limbs
- excessive panel breaks

FEET:
Target:
- rounded
- compact
- stable
- integrated into lower-leg construction

Avoid:
- shoes
- sneakers
- rectangular blocks

LISTENING MODULES:
Current underlying concept is accepted.

Improve only:
- integration with hair/head
- gasket/housing transition
- graphite core readability
- amber emission cleanliness

Do not redesign the module.

MATERIALS:
WHITE:
warm matte ceramic/polymer
not glossy plastic

GRAPHITE:
satin
not black rubber
not chrome

AMBER:
emission
warm gold
constant hue

Prohibited:
- pink
- peach
- red-orange
- metallic gold trim

@regional_visual_checks

For review, create canonical-vs-render crops for:

1. hair
2. eyes
3. face
4. listening module
5. torso/waist
6. hand
7. pelvis/hip
8. foot

Each crop must show:

LEFT = canonical raster
RIGHT = Blender render

Same approximate scale and framing.

Do not use regenerated reference artwork.

@implementation_rule
Prefer modifying the live GEO_* geometry and materials.

Do not resurrect legacy object sets as shortcuts.

If a live GEO_* object cannot achieve the canonical design cleanly:
replace that specific object with a new production object
preserve naming semantics where practical
document replacement

@validation_loop
After every major category:

1. render front
2. run front metrics
3. confirm geometric gates remain passing
4. visually compare affected region against canonical raster

Suggested order:

1. eyes
2. hair
3. face
4. graphite structure
5. hands
6. torso
7. limbs
8. feet
9. materials
10. listening-module integration

Do not change all categories in one blind pass.

@required_outputs

05_Renders/Visual_Lock/FrontVisualFit_v02/

- Front_Clean.png
- Front_Overlay.png
- Front_MaskComparison.png
- Front_Metrics.json
- Canon_vs_Render_Hair.png
- Canon_vs_Render_Eyes.png
- Canon_vs_Render_Face.png
- Canon_vs_Render_ListeningModule.png
- Canon_vs_Render_Torso.png
- Canon_vs_Render_Hand.png
- Canon_vs_Render_Hip.png
- Canon_vs_Render_Foot.png
- FrontVisualFit_v02_ChangeLog.md

Save updated Blender checkpoint as:

02_Production/Visual_Lock/FrontVisualFit_v02/Ava_v1.0_FrontVisualFit_v02.blend

@acceptance
Automated front geometry gates must remain passing.

Visual approval additionally requires that a human reviewer can clearly see:

- canonical bob rather than blob/helmet hair
- amber eyes rather than black-ring/goggle eyes
- soft canonical face
- readable graphite articulation
- real fingers rather than mitts
- rounded premium body construction
- canonical Ava product-design language

Numerical metrics alone cannot approve this task.

@stop
STOP after the review package.

Do not:
- begin side fitting
- modify butterfly animation
- retime animations
- create new Ava designs
- alter canon
- merge legacy geometry
- continue automatically

Await human visual approval.
