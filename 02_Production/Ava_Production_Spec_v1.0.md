# Ava Production Specification v1.0

**Status: LOCKED production target**  
**Visual authority:** `Ava v1.0 — Canonical Character Construction Sheet.png`

## Production objective

Build a reusable, animation-ready Ava v1.0 master that reproduces the locked approximately 2.5-head design and supports subtle character acting. The movement target is approximately **70% precision machine / 30% animated character**: designed, intentional, balanced motion with enough softness and timing variation to feel alive.

## Model hierarchy

Use a clean hierarchy that separates deformation, rigid mechanical parts, controls, and emissions:

```text
AVA_v1_0_MASTER
├── GEO
│   ├── HEAD / FACE / EYES / HAIR
│   ├── LISTENING_MODULE_L / LISTENING_MODULE_R
│   ├── TORSO / CHEST_EMITTER
│   ├── ARM_L / ARM_R / HAND_L / HAND_R
│   └── LEG_L / LEG_R / FOOT_L / FOOT_R
├── RIG
├── CONTROLS
├── LIGHTS_EMISSIVE
└── EXPORT
```

The final hierarchy may adapt to the production pipeline, but names, left/right identity, materials, emission controls, and export meshes must remain unambiguous.

## Geometry and topology

- Match the canonical turnaround before adding detail.
- Preserve the approximately 2.5-head silhouette from all primary views.
- Use clean, animation-ready topology with predictable deformation and no unnecessary density.
- Keep rigid shell elements mechanically legible; do not make hard components deform like flesh.
- Provide adequate deformation loops at neck, shoulders, elbows, wrists, hips, knees, ankles, eyelids, brows, and mouth.
- Separate intersecting mechanical components where articulation requires controlled overlap.
- Avoid excessive panel lines, greebles, vents, exposed internals, or invented functional details.
- Maintain symmetry in the base mesh where practical, while allowing asymmetry in posing and animation.
- Use production-safe normals, UVs, scale, pivots, transforms, and non-overlapping naming.

## Materials

- `MAT_Ava_CeramicWhite` — premium white ceramic/polymer shell with soft controlled reflections.
- `MAT_Ava_Graphite` — dark structural joints, interfaces, hands, and selected mechanical elements.
- `MAT_Ava_AccentGray` — restrained neutral support material.
- `MAT_Ava_Eye` — amber eye system with depth and controlled highlights.
- `MAT_Ava_AmberEmission` — the single amber/gold emissive family for listening rings and chest light.
- Hair materials that create a silver-white sculpted fiber/shell appearance without realistic strand rendering.

No emotional state may swap the amber emission to another hue.

## Rig and articulation

- Fully articulated neck/head, shoulders, elbows, wrists, hips, knees, and ankles.
- IK/FK systems for arms and legs with animator-safe switching and matching.
- Stable foot controls, pole vectors, root/global controls, and center-of-mass control.
- Compact mechanical hands with articulated fingers and thumb; support open, relaxed, point, gentle reach, and careful object-contact poses.
- Eye-aim control with target and local/manual options.
- Independent eyelid controls and reliable blinks over eye rotation.
- Restrained facial controls matching the approved expression set; do not build a realistic human facial rig that invites off-model performance.
- Dedicated head-tilt control supporting Ava's subtle asymmetric tilt without breaking neck construction.
- Hair rig organized into broad secondary-motion groups; no realistic strand simulation.
- Independent left and right listening-ring emission controls.
- Chest-light emission and intensity control.
- Reusable emotional-light presets for all canonical states.

## Approved facial control set

Eye aim, blink, widen, squint, brows, soft smile, broad smile, concern, thoughtful compression, open mouth, small surprised “o,” and subtle cheek raise.

Controls may be technically decomposed into left/right components, but the animation interface should keep this approved vocabulary easy to use and discourage realistic facial overacting.

## Hair controls

- Rig broad sculpted groups for controlled overlap and settle.
- Provide modest follow-through for front, side, and rear masses.
- Maintain the short bob silhouette and keep listening modules readable.
- Prevent obvious penetration during standard head turns and tilts.
- Avoid high-frequency flutter and realistic loose-strand behavior.

## Light controls and presets

Expose at minimum `listen_L_intensity`, `listen_R_intensity`, left/right animatable pattern controls, `chest_intensity`, a chest pulse/scale control, and a master amber emission multiplier.

Create reusable presets for `Idle`, `Listening`, `Curious`, `Thinking`, `Connection`, `Discovery`, `Delight`, `Concern`, and `Focus`. Presets control intensity, timing, spatial emphasis, and motion only. Hue remains locked.

## Canonical neutral pose

Provide a neutral standing pose that matches the canonical sheet, reads at approximately 2.5 heads tall, keeps the head level and gaze present, uses relaxed shoulders and compact limb placement, keeps hands open and restrained, distributes weight evenly without stiffness, and shows all signature elements clearly.

Also deliver a clean bind/rest pose suitable for rig maintenance. The bind pose is a technical artifact and must not replace the canonical neutral pose in reviews.

## Naming conventions

- Character prefix: `AVA_`
- Version token: `v1_0`
- Side suffixes: `_L`, `_R`, `_C`
- Geometry prefix: `GEO_`
- Rig/bone prefix: `RIG_` or pipeline-approved equivalent
- Control prefix: `CTRL_`
- Material prefix: `MAT_`
- Texture prefix: `TEX_`
- Emission controls/presets: `EMIT_` and `STATE_`
- Animation clips: `AVA-ANIM-###_DescriptiveName`

Use stable ASCII names inside production files. Never use unnamed duplicates such as `.001` as final production identifiers.

## Master and exports

Deliver:

1. **Blender master** (`.blend`) containing the authoritative model, materials, rig, controls, presets, canonical neutral pose, and organized collections.
2. **FBX export** with validated skeletal hierarchy, mesh deformation, material assignment, and scale.
3. **GLB export** with validated geometry, materials, emissions, transforms, and intended animation clips where applicable.

Validate exports by reimporting them into a clean scene and checking scale, orientation, material slots, emission appearance, skinning, eye direction, finger articulation, and at least one light-state animation.

## Review gates

1. **Silhouette/proportion gate** — grayscale turnaround matches the canonical 2.5-head sheet.
2. **Construction/material gate** — materials and mechanical articulation are legible without excess detail.
3. **Rig gate** — approved controls work cleanly across representative poses.
4. **Acting gate** — subtle eye-first performance and stillness are achievable.
5. **Export gate** — Blender, FBX, and GLB pass reimport validation.

Stop for review if any source image suggests conflicting proportions or design features. Never average the canonical sheet with rejected references.
