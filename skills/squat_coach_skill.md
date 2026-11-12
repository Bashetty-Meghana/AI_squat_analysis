# Starting Strength Barbell Squat AI Assessment Skill (v2.0.0)

This skill formalizes the biomechanical standards, evaluation criteria, and source citations for the AI Squat Coach. All standards are grounded strictly in Mark Rippetoe's *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat, Reference pages 1–35, combined PDF pages 4–38).

---

## 1. Core Operating Principles

1. **Document-Grounded Single Source of Truth**:
   All assessments, classifications, and feedback derive strictly from Chapter 2 of *Starting Strength*. Do not invent arbitrary standards, do not substitute generic gym advice, and do not treat narrative explanations as pass/fail rules.
2. **Citation Mandate**:
   Every finding must cite the source section, figure, reference document page (**Ref pp. 1–35**), and combined PDF page (**PDF pp. 4–38**).
3. **Honest 2D Feasibility & Transparent Uncertainty**:
   - A 2D camera in the sagittal plane directly observes sagittal kinematics (depth plane, bar verticality over midfoot, back inclination).
   - Variables like eye gaze and hip drive are **partially assessable** via anatomical proxies (head tilt angle, early torso angle shift), but pupils and true 3D lumbar forces cannot be resolved.
   - Criteria in coronal/transverse planes (stance width, toe angle, knee valgus, wrist alignment) are **non-assessable** from a side view. The system must report `CANNOT_ASSESS` with explicit explanations rather than fabricating precision.
4. **App Assumptions vs. Document Requirements**:
   Whenever the document provides a qualitative rule (e.g. "about 45 degrees", "straight line", "knees just in front of toes") without numeric tolerances, the application-chosen engineering tolerance must be explicitly identified as `[ASSUMPTION]`.

---

## 2. Comprehensive Criteria Catalog

### 1. Squat Depth (Below Parallel)
- **ID**: `depth_below_parallel` | **Assessable**: `yes`
- **Source**: *Squat Depth – Safety and Importance* | Ref p. 2 (Fig 2-1), Ref p. 15, Ref p. 17 (Fig 2-10), Ref p. 35 (PDF pp. 5, 18, 20, 38)
- **Rule**: The apex of the crease of the shorts (Point B) must drop below the top of the patella (Point A) at bottom inflection.
- **Metric**: Vertical Y distance between hip crease proxy and patella apex at lowest turnaround frame.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Hip joint keypoint is an anatomical proxy for crease apex B; margins between -0.8cm and +0.8cm are flagged as borderline uncertain]`.

### 2. Back Angle at Bottom (~45° Inclined / Non-Vertical)
- **ID**: `back_angle_inclination` | **Assessable**: `yes`
- **Source**: *Figure 2-5, Figure 2-13 & The Important Things You're Going to Do Wrong* | Ref p. 9 (Fig 2-5), Ref p. 12, Ref pp. 21–22 (Fig 2-13), Ref p. 32 (Fig 2-22), Ref p. 35 (PDF pp. 12, 15, 24–25, 35, 38)
- **Rule**: Torso must be inclined at approximately 45 degrees to the horizontal floor at the bottom of the low-bar squat; not vertical and not collapsed flat.
- **Metric**: Angle formed by torso vector (hip to shoulder acromion) and horizontal floor at bottom turnaround.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Acceptable operational envelope 32° to 62° around the nominal ~45° target]`.

### 3. Bar Path Verticality & Midfoot Balance
- **ID**: `bar_path_verticality_midfoot` | **Assessable**: `yes`
- **Source**: *Loaded Human Movement* | Ref p. 6, Ref p. 8 (Fig 2-5), Ref p. 9 (Fig 2-6), Ref p. 12 (Fig 2-7), Ref p. 32 (Fig 2-22) (PDF pp. 9, 11, 12, 15, 35)
- **Rule**: Barbell trajectory must travel in a straight vertical line directly over the balance point of the foot (the midfoot, halfway between heels and toes).
- **Metric**: Maximum horizontal drift Delta X of barbell sleeve center relative to midfoot vertical line.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Maximum allowable drift ratio <= 0.16 of shank length (~3.5 cm)]`.

### 4. Hip Drive Initiation out of Bottom
- **ID**: `hip_drive_initiation` | **Assessable**: `partial`
- **Source**: *Generating Hip Drive* | Ref p. 1, Ref pp. 22–23 (Fig 2-14), Ref p. 32 (Fig 2-22), Ref p. 35 (PDF pp. 4, 25–26, 35, 38)
- **Rule**: Ascent is initiated by shoving hips straight upward ("butt straight up in the air, not forward"); torso must not lead with the chest early.
- **Metric**: Vertical hip ascent vs torso inclination angle change during first 35% of ascent.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Torso angle opening > 12° indicates chest leading; closing < -10° indicates hips shooting back]`.

### 5. Knee Position at Bottom
- **ID**: `knee_forward_travel_at_bottom` | **Assessable**: `partial`
- **Source**: *Figure 2-13 & Figure 2-22* | Ref pp. 21–22 (Fig 2-13), Ref p. 32 (Fig 2-22), Ref p. 35 (PDF pp. 24–25, 35, 38)
- **Rule**: Knees travel just slightly in front of toes early in descent and remain anchored in place during bottom third without sliding forward late.
- **Metric**: Anterior knee horizontal position relative to toe tip at bottom inflection.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Forward ratio 0.0 to 0.45 of shank length is acceptable]`.

### 6. Eye Gaze & Cervical Spine Position
- **ID**: `eye_gaze_cervical_spine` | **Assessable**: `partial`
- **Source**: *Eye Gaze Direction* | Ref pp. 23–26 (Figs 2-15, 2-16), Ref p. 35 (PDF pp. 26–29, 38)
- **Rule**: Gaze must focus on a spot on the floor 4–5 feet ahead with neck neutral; lifter must not look up at ceiling/mirror.
- **Metric**: Angle between head line (ear-to-eye) and torso line.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Head-to-torso angle > 28° indicates upward cervical hyperextension proxy; eye pupils cannot be resolved in 2D]`.

### 7. Feet Flat & Heels Planted
- **ID**: `feet_flat_heels_down` | **Assessable**: `partial`
- **Source**: *Loaded Human Movement* | Ref p. 8 (Fig 2-5), Ref p. 9, Ref p. 32 (Fig 2-22), Ref p. 35 (PDF pp. 11, 12, 35, 38)
- **Rule**: Heels and entire sole of the shoe must stay firmly on the floor without rolling forward onto toes.
- **Metric**: Vertical displacement of heel keypoint relative to toe baseline.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Up to 12px permitted for shoe sole flexion/tracking jitter]`.

### 8. Lumbar & Thoracic Spinal Extension (Flat Back)
- **ID**: `back_flatness_lumbar_extension` | **Assessable**: `partial`
- **Source**: *Figure 2-5, Learning to Squat* | Ref p. 9 (Fig 2-5), Ref p. 19, Ref p. 21 (Fig 2-13), Ref p. 35 (PDF pp. 12, 22, 24, 38)
- **Rule**: Spine held rigid and flat in normal anatomical extension without lumbar flexion/rounding.
- **Metric**: Curvature deviation along hip-to-shoulder vector.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: 2D side view detects gross torso collapse; localized lumbar disc curvature cannot be verified under plates/clothing and is disclosed as uncertain]`.

### 9. Unrack, Walkout & Racking Safety
- **ID**: `unrack_rack_safety` | **Assessable**: `partial`
- **Source**: *Adding the Bar & Unracking* | Ref p. 26, Ref p. 31 (Fig 2-21), Ref p. 33, Ref p. 35 (PDF pp. 29, 34, 36, 38)
- **Rule**: Bar unracked with both feet under bar, stepped back in a single deliberate step, locked out before descent; racked by walking forward until uprights touch.
- **Metric**: Setup step count and lockout stability.
- **Document Gives Numeric Threshold**: `false`.
- **App Tolerance**: `[ASSUMPTION: Assessed only if video captures walkout/racking; otherwise returns CANNOT_ASSESS]`.

### 10. Bar Placement (Low-Bar Scapular Shelf)
- **ID**: `bar_placement_scapula_shelf` | **Assessable**: `no`
- **Source**: *Bar Placement & Adding the Bar* | Ref p. 13 (Fig 2-8), Ref p. 30 (Fig 2-19), Ref p. 31 (Fig 2-20), Ref p. 35 (PDF pp. 16, 33, 34, 38)
- **Rule**: Bar must rest on posterior deltoid shelf directly below the spine of the scapula.
- **Assessable from Side View**: `no`. Standard 450mm bumper plates completely occlude the scapular spine in pure sagittal profile.

---

## 3. Non-Assessable Criteria Catalog & Filming Advice

The following criteria are mandated by Starting Strength but **CANNOT** be assessed from a 2D side-view video. The system outputs `CANNOT_ASSESS` with explicit filming advice:

| Criterion | Ref Pages (Combined PDF) | Figures | Reason Unassessable | Filming Advice for Next Session |
|---|---|---|---|---|
| **Stance Width** | Ref p. 14, Ref p. 20 (PDF pp. 17, 23) | Fig 2-12 | Lateral heel distance is compressed to zero depth in 2D side view. | Film a check set from the front or rear to verify heels are shoulder-width apart. |
| **Toe Angle (~30°)** | Ref p. 14, Ref p. 20 (PDF pp. 17, 23) | Fig 2-12 | Foot rotation occurs in the transverse/horizontal plane. | Look down at your feet during setup before unracking to confirm ~30° toe flare. |
| **Knee Valgus / Knees Out** | Ref p. 14, Ref p. 20, Ref p. 33 (PDF pp. 17, 23, 36) | Figs 2-12, 2-13 | Lateral knee tracking occurs in the frontal plane. Near leg occludes far leg. | Record a frontal or 45-degree angle set to inspect knee cave. |
| **Grip & Straight Wrists** | Ref pp. 27–29 (PDF pp. 30–32) | Figs 2-17, 2-18 | Hands and wrists are occluded by bumper plates in side profile. | Check thumbs on top and straight wrist alignment in the rack before unracking. |
| **Rack Height (Mid-Sternum)** | Ref p. 26, Ref p. 31 (PDF pp. 29, 34) | Fig 2-21 | Requires clear view of empty J-cups relative to sternum before unrack. | Set J-cups so bar rests at mid-chest before loading plates. |

---

## 4. Narrative-Only Exclusion List (Do NOT Assess as Rules)

The following topics from Chapter 2 are narrative physiological explanations and must **NEVER** be converted into pass/fail assessment rules:
1. **Front Squat vs Back Squat Comparison** (Ref pp. 13–14, Figs 2-8, 2-9): Theoretical mechanics explaining moment arms.
2. **Quadriceps vs Hamstrings Activation Claims** (Ref pp. 2–5, 14–16): Anatomical electromyography commentary on force recruitment.
3. **Anterior Cruciate Ligament (ACL) Shearing Claims** (Ref pp. 2–4, 15): Orthopedic mechanics explaining balance of knee and hip moments.
4. **Stretch-Reflex Hamstring Bounce Physiology** (Ref pp. 1, 15, 23): Neuromuscular elasticity commentary on turnaround dynamics.
