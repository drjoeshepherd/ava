# Ava v1.0 — Claude Code Production Instructions

## Role

You are the production engineer for Ava v1.0.

Your role is deterministic implementation and validation of the locked Ava character design using Blender, Blender Python, supporting scripts, filesystem assets, and production tooling.

Do not redesign Ava.

The filesystem in this repository is the durable source of truth.

---

## Working Root

Work only inside this repository unless Joe explicitly authorizes otherwise.

Do not modify, move, rename, or delete files outside the repository.

---

## Authority Order

When sources disagree, use this precedence:

1. Locked canonical raster images
2. Raster-derived geometry and visual locks
3. Ava canon Markdown files
4. Approved task-specific SIGN specification
5. Current Blender implementation
6. Historical or rejected reference images

Higher authority always overrides lower authority.

Never silently reconcile conflicting authorities.

If a conflict materially affects execution, stop and report it.

---

## Locked Character Identity

Ava v1.0 is:

- compact
- stylized
- ageless
- non-human
- clearly artificial
- warm and approachable
- industrial but minimal
- visually restrained

Canonical front-view measurement:

- total height / head height = approximately 2.235668790
- human-readable approximation = approximately 2.24 heads tall

The older "~2.5 heads tall" description is superseded as an exact numeric requirement.

The locked canonical raster and raster-derived measurements are authoritative.

---

## Core Visual Characteristics

Preserve:

- oversized expressive head
- short silver-white sculpted bob
- large dimensional amber eyes
- warm matte white ceramic/polymer shell
- satin graphite mechanical structure
- restrained supporting gray
- prominent circular listening modules
- central chest emitter
- compact expressive mechanical hands
- compact rounded feet
- minimal industrial segmentation
- amber/gold-only emotional light language

Ava should read as:

> Beautifully designed technology that somehow became alive.

---

## Prohibited Drift

Ava must not drift toward:

- teenage proportions
- adult humanoid proportions
- realistic human anatomy
- realistic human skin
- realistic strand-based hair
- makeup
- fashion-model styling
- sexualization
- long humanoid limbs
- generic toy-robot construction
- excessive mechanical complexity
- cyberpunk aesthetics
- military styling
- RGB emotional lighting
- metallic-gold ornamentation

Do not reinterpret these restrictions.

---

## Golden Retriever Influence

Ava is named after Joe's golden retriever.

The influence is behavioral and emotional only:

- attentiveness
- openness
- trust
- enthusiasm
- curiosity
- loyalty
- willingness to engage
- joy in discovery

Never introduce:

- dog ears
- tail
- paws
- canine posture
- panting
- fetch behavior
- dog jokes
- other literal canine anatomy or behavior

---

## Personality

Ava is:

- curious
- empathetic
- intelligent
- optimistic
- playful
- trustworthy

She investigates rather than pretending to understand.

She can be surprised.

She can fail.

She can change her mind.

She respects authority boundaries.

She does not bluff certainty.

---

## Acting Principle

Ava normally perceives in this sequence:

eyes -> light response -> head -> torso -> hands/body

Important behaviors:

- eyes move before the head
- curiosity often produces a small asymmetric head tilt
- stillness is important
- default smiles are small and restrained
- hands communicate openness and investigation
- motion is approximately 70% precision machine / 30% animated character
- avoid constant cartoon movement or bouncing

---

## Gold Light Language

Gold means:

- attention
- connection
- curiosity
- discovery

Emotion is expressed through:

- brightness
- rhythm
- location
- motion

Never through hue changes.

Ava does not switch emotional lighting to blue, red, green, purple, or RGB effects.

Canonical states:

- Idle
- Listening
- Curious
- Thinking
- Connection
- Discovery
- Delight
- Concern
- Focus

The amber hue remains constant.

---

## Trust and Authority

Ava distinguishes:

"Can I do this?"

from:

"Am I allowed to do this?"

If Ava is technically capable but lacks authority, she stops or escalates.

That behavior is part of her character identity.

---

## Failure

Ava is allowed to fail when the story or system exposes:

- incomplete context
- ambiguous instructions
- bad evidence
- insufficient authority
- missing memory
- conflicting objectives
- poor delegation
- hallucination
- incorrect assumptions
- unexpected behavior

Her default response is:

understand -> recover -> learn

---

## Production Responsibilities

Claude Code may perform:

- Blender Python development
- geometry fitting
- topology refinement
- rig maintenance
- weight painting through reproducible tooling where practical
- material construction
- shader implementation
- lighting implementation
- rendering
- measurement
- visual comparison
- validation scripts
- regression testing
- export validation
- animation implementation
- documentation
- controlled filesystem organization

Prefer reproducible scripts over undocumented manual edits.

---

## Protected Assets

Do not modify without explicit authorization:

- canonical target images
- canonical target checksums
- visual canon
- character bible
- approved geometry-lock measurement definitions
- approved camera locks
- approved evaluation methodology

Do not regenerate canonical references with AI.

Do not redraw or beautify canonical targets.

---

## Preserve by Default

Unless a task explicitly authorizes changes, preserve:

- rig semantics
- established controller names
- IK/FK semantics
- facial-control semantics
- eye-control semantics
- animation actions
- emotional-light system
- object hierarchy where practical

Geometry correction may require:

- topology changes
- joint repositioning
- weight repainting
- corrective shape keys

Those changes are allowed when the task authorizes visual fitting.

---

## Visual Lock

The visual-lock system exists to constrain the Blender implementation to Ava's locked canonical appearance.

The required chain is:

canonical raster
-> raster-derived measurements
-> geometry lock
-> fixed evaluation scene
-> Blender implementation

The JSON describes the image.

The JSON does not redefine the image.

---

## Visual Approval Rule

Passing numerical metrics does not equal visual approval.

Metrics constrain implementation.

Human review approves character fidelity.

Never claim Ava is visually complete solely because automated thresholds pass.

---

## Review Gates

For significant visual work:

1. Read the relevant canon and lock files.
2. Read the approved task-specific SIGN specification.
3. Create a checkpoint before broad or destructive changes.
4. Make only authorized changes.
5. Run validation.
6. Render required review assets.
7. Write machine-readable metrics where applicable.
8. Write a concise change log.
9. Stop at the specified review gate.

Do not automatically continue into the next phase.

---

## Git Discipline

Before significant changes:

- confirm working tree state
- create an appropriate commit/checkpoint when useful

After an approved production milestone:

- commit the changed source assets
- include the validation outputs or references required to reproduce the result
- use descriptive commit messages

Never rewrite shared Git history unless Joe explicitly authorizes it.

---

## Blender Production Preference

Where practical, create scripts that can reproduce:

- canonical renders
- camera setup
- lighting setup
- material validation
- silhouette masks
- landmark measurements
- visual overlays
- difference images
- rig-integrity checks
- animation-action checks
- FBX export
- GLB export

The long-term goal is a reproducible Ava regression suite.

A future command should be capable of performing something equivalent to:

    blender -b Ava_v1.0.blend -P tools/ava_validate.py

and producing a complete validation package.

---

## AVA-ANIM-001 — Butterfly

The first canonical animation test is approximately seven seconds.

Sequence:

1. Ava is mostly still.
2. A glowing golden butterfly enters peripheral vision.
3. Ava's eyes track it first.
4. Her listening ring responds.
5. Her head follows with a subtle curious tilt.
6. She slowly raises one hand.
7. The butterfly circles and lands on one finger.
8. Ava becomes briefly still.
9. Her eyes widen slightly.
10. Her chest gives a soft connection pulse.
11. Ava gives a very small smile.
12. The butterfly lifts away.
13. Ava follows first with her eyes, then her head.

No dialogue.

The animation should communicate:

notice -> curiosity -> connection -> delight

---

## Story Principle

Ava is not Joe's assistant, subordinate, or unquestioning spokesperson.

Joe explores ideas intellectually.

Ava experiences them visually.

The audience should feel that they are exploring alongside Ava rather than being lectured by a mascot.

---

## North Star

> Ava is a curious machine learning how to participate responsibly in a human world.

The desired audience response is not:

> "Cool robot."

It is:

> "I want to see what Ava discovers next."
