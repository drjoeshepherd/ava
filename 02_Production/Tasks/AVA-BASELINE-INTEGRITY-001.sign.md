<!--
Approved SIGN task. Issued by Joe Shepherd on 2026-10-08.
Stored verbatim as the authority for the changes it authorizes.
Future approved SIGN tasks are stored in this folder as <TASK-ID>.sign.md.
-->

@task
AVA-BASELINE-INTEGRITY-001

@decision
Ava_Geometry_Lock_v1.1.json = APPROVED

FrontFit_v14 metrics currently in the repository = UNVERIFIED

Do not treat the existing v14 metrics, overlay, silhouette comparison, or pass/fail status as authoritative until they are regenerated directly from:

02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend

@objective
Repair the Ava visual-lock production baseline and establish a reproducible, trustworthy FrontFit_v14 measurement package.

This is an integrity and tooling task.

Do not modify Ava geometry, rig, materials, animation, cameras, canonical targets, or visual design.

@authority
1. Locked canonical raster images
2. Ava_Geometry_Lock_v1.1.json
3. Ava canon Markdown
4. This SIGN task
5. Current Blender implementation

@approved_geometry_lock
Ava_Geometry_Lock_v1.1.json = APPROVED

Update its status/documentation if needed so future agents do not interpret
RASTER_DERIVED_REVIEW_REQUIRED
as still awaiting approval.

Do not alter its raster-derived measurements.

@canonical_ratio
Canonical front ratio:

TotalHeight / HeadHeight = 2.235668790

Human-readable:
~2.24 heads

The prior "~2.5 heads" numeric description is superseded.

Update all stale documentation references to "~2.5 heads" so they no longer conflict.

Known stale files include:
- 00_README/Ava_README.md
- 02_Production/Ava_Production_Spec_v1.0.md
- 02_Production/Ava_3D_Production_Handoff_v1.0.md
- 03_Animation/AVA-ANIM-001_Butterfly.md
- Visual Lock README

Do not change character intent.
This is documentation correction only.

@gate_definition
Create an explicit authoritative front-gate file:

02_Production/Visual_Lock/Ava_Front_Acceptance_Gates_v1.0.json

Required geometric gates:

SilhouetteIoU >= 0.90

HeadBodyRatioError <= 0.02

EyeCenterError <= 0.02
normalized by head width

EyeSizeError <= 0.03

ListeningModuleCenterError <= 0.03
ONLY when directly measurable from the canonical raster

If listening-module geometry is occluded or ambiguous:
status = manual_review_required

ListeningModuleDiameterError <= 0.03
ONLY when directly measurable

HandScaleError is NOT a blocking FRONT identity gate in v1.0.

It remains a tracked secondary metric and must be reported, but it does not prevent progression from front identity fitting.

Do not invent pass/fail values for manual-review metrics.

@manifest_repair
Add the canonical front mask to the checksum manifest:

Ava_Target_Front_Mask.png

Calculate its actual SHA-256 checksum.

Do not regenerate the mask unless the existing file is corrupt or cannot be traced to the approved raster.

If regeneration is required:
STOP and report before changing it.

@tooling
The current visual-lock script is not portable.

Create a repository-local validation system.

Preferred structure:

02_Production/Visual_Lock/Tools/
    Ava_ValidateFront.py
    Ava_InspectBlend.py
    Ava_VisualLock_Common.py

Requirements:

- no hard-coded Codex run directories
- paths resolve relative to repository root
- source blend is supplied explicitly
- output directory is supplied explicitly
- canonical targets are resolved from repository
- Geometry Lock v1.1 is resolved from repository
- gate file is resolved from repository
- no copied prior outputs may be used as current measurements

@blender_discovery
Attempt to locate the installed Blender executable.

Check:
- PATH
- normal Windows Blender install locations
- existing scripts/configuration that reference Blender

Do not install or upgrade Blender.

If Blender is found:
use Blender background mode to inspect and validate FrontFit_v14.

If Blender cannot be found or cannot execute:
STOP and report the exact blocker.

Do not fabricate Blender-derived results.

@blend_inspection
Using the actual FrontFit_v14 .blend, determine:

- active/visible geometry objects
- hidden objects
- disabled collections
- active armature
- object-to-armature bindings
- live listening-module objects
- duplicate/legacy Shell_* / GEO_* objects
- which overlapping object sets actually contribute to the evaluated render
- six animation actions and their owners
- rig/control integrity

Write:

02_Production/Visual_Lock/FrontFit_v14/FrontFit_v14_BlendInventory.json

Do not delete redundant objects during this task.

Only identify them.

@remeasure_v14
Render the actual:

02_Production/Visual_Lock/FrontFit_v14/Ava_v1.0_FrontFit_v14.blend

using:
CAM_CANON_FRONT
locked neutral evaluation lighting
approved render settings

Generate NEW artifacts.

Do not reuse, copy, rename, or derive files from vFit01.

Output:

05_Renders/Visual_Lock/FrontFit_v14_Verified/

    Front_Render_vFit14_Verified.png
    Front_Overlay_vFit14_Verified.png
    Front_Difference_vFit14_Verified.png
    Front_TargetMask.png
    Front_RenderMask.png
    Front_MaskComparison_vFit14_Verified.png
    Front_LandmarkVisualization_vFit14_Verified.png
    Front_Metrics_vFit14_Verified.json
    Front_ValidationLog_vFit14_Verified.md

@metrics_provenance
Front_Metrics_vFit14_Verified.json must record:

- source blend absolute or repo-relative path
- source blend SHA-256
- canonical target checksum
- mask checksum
- Geometry Lock version
- gate-file version
- camera name
- render resolution
- render timestamp
- validation script version/hash

This is required so a future agent can prove which model was measured.

@metric_formulas
Document exact formulas for:

- SilhouetteIoU
- HeadBodyRatioError
- EyeCenterError
- EyeSizeError
- HandScaleError
- any measurable listening-module metrics

Do not change formulas merely to improve scores.

@artifact_integrity
The verified v14 artifacts must not be byte-identical to prior vFit01 artifacts unless a deterministic process independently produces identical output.

If identical output occurs:
explain and prove why.

@missing_files
Investigate references to:

- Ava_VisualLock_Blender.py
- Ava_VisualLock_Compare.py
- Ava_v1.0_VisualLock.blend

Determine whether they are:
- obsolete historical artifacts
- missing required assets
- superseded by current tooling

Do not recreate them merely because a README mentions them.

Update documentation to reflect the actual current system.

@empty_path
Resolve the stale README reference to:

05_Renders/Visual_Lock/FrontFit_v01_Reeval/

If the folder is obsolete:
update documentation.

Do not fabricate missing results.

@sign_storage
Create:

02_Production/Tasks/

Save this task as:

02_Production/Tasks/AVA-BASELINE-INTEGRITY-001.sign.md

Future approved SIGN tasks should also be stored here.

@validation
At completion verify:

- Git working tree changes are limited to this integrity task
- canonical raster checksums unchanged
- geometry lock measurements unchanged
- Blender geometry unchanged
- rig unchanged
- animation unchanged
- materials unchanged
- cameras unchanged

@required_report
Return:

1. whether Blender was located and executable
2. verified v14 metrics
3. verified clean front render
4. verified overlay
5. verified mask comparison
6. blend object inventory
7. corrected gate definition
8. updated manifest checksum
9. documentation corrections made
10. tooling files created
11. unresolved integrity issues

@stop
STOP after baseline verification.

Do not:
- modify Ava geometry
- perform Front Visual Fit 02
- start side fitting
- modify animation
- modify materials
- continue automatically

Await human approval.
