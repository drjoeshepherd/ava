# Ava 3D Production Handoff v1.0

## Assignment

Create a production-ready 3D model and rig of **Ava v1.0** in Blender, then provide validated FBX and GLB exports. This brief is self-contained; the original design conversation is not required.

**Do not redesign Ava.** The task is faithful translation of a locked character into an animation-ready asset.

## Source authority

The local Ava folder contains image references. Their authority is not equal.

- **Authoritative:** `Ava v1.0 — Canonical Character Construction Sheet.png`. This is the final approximately 2.5-head construction sheet and the primary visual source for modeling, proportions, silhouette, materials, details, and turnaround.
- **Non-canonical:** `Ava v1.0.png`. This earlier development sheet includes an approximately 3.5-head proportion and rejected/development imagery. Do not model from it.
- **Non-canonical:** `Ava.png`. This is an early concept/brand sheet. It may explain thematic history, but it is not geometry or proportion authority.
- **Non-canonical:** `AVA_ A Brighter Tomorrow.png`. This is an earlier concept/brand sheet with a taller, more humanoid construction and scenario poses. Do not model from it.
- **Non-canonical:** `Robot Girl Reaching for a Butterfly.png`. This is scene/mood art only. It may support the curiosity/discovery tone, but it is not construction, proportion, topology, rig, or facial-style authority.

If other images are added later and are not explicitly marked canonical, treat them as unverified references. Do not infer a redesign by averaging or combining earlier rejected images with the final sheet. If the final sheet and any other reference conflict, follow the final sheet and flag the conflict.

## Locked character definition

Ava is compact, stylized, ageless, and non-human; approximately 2.5 heads tall; built around an oversized head and compact rounded body; designed with a short silver-white bob and large amber eyes; surfaced with a white ceramic/polymer exterior; structured with graphite mechanical joints and components; equipped with signature circular listening modules and a central circular chest emitter; built with compact mechanical hands and feet; and minimally detailed in an industrial/product-design language.

Her emotional lighting is amber/gold only.

## Meaning and performance target

Ava is the recurring animated face of Joe Shepherd's work on AI, agents, technology, and the future of work.

North star: **“Ava is a curious machine learning how to participate responsibly in a human world.”**

She is curious, empathetic, intelligent, optimistic, playful, and trustworthy. Her movement target is approximately **70% precision machine / 30% animated character**. She should be capable of quiet attention, visible thought, small discovery, careful uncertainty, and warm connection.

The golden-retriever influence is behavioral only: attentiveness, openness, trust, enthusiasm, curiosity, loyalty, willingness to engage, and joy in discovery. It must never produce canine anatomy or behavior.

## Non-negotiable anti-drift rules

Do not introduce teenage or adult humanoid proportions, realistic human skin, realistic hairstyles or strand-heavy hair simulation, makeup or fashion-model styling, sexualization, long humanoid limbs, excessive mechanical complexity or ornamental greebling, cyberpunk styling, RGB or multicolor emotional lighting, canine anatomy or behavior, or superhero/weapon/combat design language.

## Modeling requirements

- Match the final sheet's front, three-quarter, side, three-quarter-back, and back views.
- Lock the approximately 2.5-head height and oversized-head silhouette before refinement.
- Use clean animation-ready topology.
- Keep rigid shell elements distinct from deforming interfaces.
- Model articulated shoulders, elbows, wrists, hips, knees, and ankles with plausible clearances.
- Build compact articulated fingers and thumb for restrained gestures.
- Preserve smooth rounded construction and minimal industrial detail.
- Organize the silver-white bob into broad sculpted groups suitable for controlled secondary motion.
- Keep listening modules visible and structurally integrated.
- Maintain clean UVs, normals, transforms, scale, origins, and production names.

## Material requirements

- White ceramic/polymer primary shell.
- Graphite mechanical structure, interfaces, joints, and hands.
- Restrained neutral gray support accents.
- Amber eyes with controlled depth and reflection.
- One amber/gold emissive family for listening rings and chest emitter.
- Silver-white designed hair/fiber-shell material.

The look should be clean, tactile, understandable, and slightly magical—more industrial/product design than science fiction.

## Rigging requirements

- Production-ready root/global and center-of-mass controls.
- IK/FK arms and legs with stable switching and matching.
- Articulated fingers and thumb.
- Eye aim with independent eye control.
- Independent eyelids and reliable blinks.
- Restrained facial controls for eye aim, blink, widen, squint, brows, soft smile, broad smile, concern, thoughtful compression, open mouth, small surprised “o,” and subtle cheek raise.
- Dedicated subtle asymmetric head-tilt control.
- Broad-group secondary-motion hair rig; no realistic strand simulation.
- Independent left/right listening-ring emission controls.
- Chest emission/intensity and pulse control.
- Reusable light-state presets: Idle, Listening, Curious, Thinking, Connection, Discovery, Delight, Concern, and Focus.

## Emotional-light rules

Gold communicates attention, connection, curiosity, and discovery. Emotion changes through brightness, rhythm, location, and motion—never through hue.

Listening rings may act independently when attention is directional, then synchronize when recognition or connection resolves. The chest emitter may softly pulse or expand. Keep all emission subordinate to the eyes and performance.

## Acting proof required

The rig must support this order: eyes → light response → head → torso → hands/body. Eyes move before the head. Stillness matters. Gestures are open, small, and restrained. Ava uses a subtle asymmetric head tilt. Avoid frantic cartoon motion.

Demonstrate the rig with the canonical neutral pose and a short proof based on `03_Animation/AVA-ANIM-001_Butterfly.md` or an equivalent eye-first attention test.

## Deliverables

- `AVA_v1_0_MASTER.blend`
- validated `AVA_v1_0.fbx`
- validated `AVA_v1_0.glb`
- organized relative-path textures
- canonical neutral pose
- approved facial-control test
- emotional-light preset test
- turnaround review renders aligned to the construction sheet
- short rig/readme note describing controls, dependencies, export settings, and known limitations

## Acceptance criteria

- Silhouette and primary views match the final 2.5-head construction sheet.
- No rejected 3.5-head or earlier-concept features drift into the model.
- The face remains stylized, ageless, non-human, and non-sexualized.
- Materials read as ceramic/polymer, graphite structure, silver-white hair, and amber-only emission.
- The rig supports precise mechanical articulation plus restrained character performance.
- Eye-first acting, asymmetric head tilt, stillness, hands, hair follow-through, listening rings, and chest pulse work cleanly.
- Blender, FBX, and GLB pass clean-scene reimport checks.

When uncertain, stop and request a decision. Do not solve ambiguity by inventing new character design.
