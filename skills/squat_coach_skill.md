# Starting Strength Barbell Squat AI Assessment Skill

This skill defines the operational instructions, biomechanical criteria, and standard citations for the AI Squat Coach embedded in this application. It translates Mark Rippetoe's *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat, Reference pages 1–35, combined PDF pages 4–38) into an inspectable, executable evaluation engine.

---

## 1. Core Biomechanical Principles & Mandate

1. **Grounded in the Supplied Document**:
   All assessments, classifications, and feedback must stem strictly from Chapter 2 of *Starting Strength*. Do not invent arbitrary thresholds, do not substitute generic fitness advice, and do not present unofficial rules as document standards.
2. **Citation Requirement**:
   Every finding must cite the relevant source section, reference document page (**Ref p. 1–35**), and combined PDF page (**PDF p. 4–38**).
3. **Sagittal (Side-View) Feasibility**:
   A single-camera 2D video recorded from the side view (sagittal plane) can measure sagittal planar kinematics (depth, bar path, back angle, hip drive, head tilt), but *cannot* measure coronal/transverse planar variables (heel distance, toe flare angle, lateral knee cave, grip width).
4. **Honest Limitations & No Invented Precision**:
   If a criterion cannot be resolved due to camera angle, occlusion (e.g. 45lb bumper plates blocking the shoulder joint or wrists), or poor framing (landmarks cut off), the system must output **`CANNOT_ASSESS`** with an explicit explanation. Distinguish directly observed landmarks from estimates.

---

## 2. Criterion Catalog & Citation Matrix

### Criterion 1: Squat Depth (Below Parallel)
- **Source Section**: *Squat Depth – Safety and Importance*, Figure 2-1, Figure 2-10, p. 35
- **Citations**: Ref p. 2 (Fig 2-1), Ref p. 15, Ref p. 16 (Fig 2-10), Ref p. 35 | PDF pp. 5, 18, 19, 38
- **Standard**: The apex of the crease of the shorts (hip joint B) must drop below the level of the top of the patella (knee joint A).
- **Sagittal Assessability**: **Fully Assessable**. The side view is the primary perspective for evaluating depth.
- **Biomechanical Rationale**: Full depth ensures the hamstrings, glutes, and adductors reach full stretch and can contract to extend the hips. Partial (high) squats predominantly load the anterior quadriceps, producing anterior tibial shear and failing to train the posterior chain.
- **Outcomes**:
  - `MEETS_STANDARD`: Hip crease drops lower than top of patella at bottom inflection.
  - `DOES_NOT_MEET_STANDARD`: Hip crease remains above top of patella (partial squat). Actionable cue: Shove knees out and sit back to allow hips to drop below parallel.
  - `CANNOT_ASSESS`: Hip or knee obscured by rack, clothing, or camera boundaries.

---

### Criterion 2: Bar Path Verticality & Midfoot Balance
- **Source Section**: *Loaded Human Movement*, Figure 2-3, Figure 2-5, Figure 2-6, Figure 2-7, Figure 2-22
- **Citations**: Ref p. 6, Ref p. 8 (Fig 2-4), Ref p. 9 (Fig 2-5), Ref p. 11 (Fig 2-7), Ref p. 32 (Fig 2-22) | PDF pp. 9, 11, 12, 14, 35
- **Standard**: Gravity acts vertically perpendicular to the earth. The most efficient bar path is a straight vertical line directly over the balance point: the midfoot (exactly halfway between either end of the shoe sole).
- **Sagittal Assessability**: **Fully Assessable**. Barbell sleeve trajectory plotted against the midfoot reference line.
- **Biomechanical Rationale**: Any horizontal deviation (\(\Delta X\)) represents non-vertical work against gravity and creates a rotational moment arm that drastically increases the effort required to stabilize the weight.
- **Outcomes**:
  - `MEETS_STANDARD`: Barbell trajectory stays within acceptable vertical corridor centered over midfoot.
  - `DOES_NOT_MEET_STANDARD`: Noticeable forward or backward bar drift. Actionable cue: Keep weight evenly balanced over the arch of the foot; avoid drifting forward onto toes or back onto heels.
  - `CANNOT_ASSESS`: Barbell sleeve or foot landmarks occluded or cut off.

---

### Criterion 3: Back Angle at Bottom (~45° Inclination)
- **Source Section**: Figure 2-5, Figure 2-13, *The Important Things You're Going to Do Wrong*
- **Citations**: Ref p. 9 (Fig 2-5), Ref p. 12, Ref p. 22 (Fig 2-13), Ref p. 32 (Fig 2-22), Ref p. 35 | PDF pp. 12, 15, 25, 35, 38
- **Standard**: In the low-bar back squat, the back is inclined at approximately 45 degrees relative to the horizontal floor at the bottom of the squat. It must *not* be vertical.
- **Sagittal Assessability**: **Fully Assessable**. Torso plane angle relative to the horizontal ground.
- **Biomechanical Rationale**: An upright back angle slackens the hamstrings distally and proximally, preventing them from contributing to hip extension. An excessively horizontal back angle (<25°) indicates spinal rounding or chest collapse.
- **Outcomes**:
  - `MEETS_STANDARD`: Torso inclined at approximately 35°–55° to horizontal with rigid lumbar/thoracic extension.
  - `DOES_NOT_MEET_STANDARD`: Back angle too vertical (>60°) or collapsed too horizontal (<30°).
  - `CANNOT_ASSESS`: Shoulder or hip landmarks obscured.

---

### Criterion 4: Hip Drive Initiation
- **Source Section**: *Generating hip drive*, Figure 2-14, Figure 2-22, *The Important Things You're Going to Do Wrong*
- **Citations**: Ref p. 1, Ref p. 22 (Fig 2-14), Ref p. 23, Ref p. 32 (Fig 2-22), Ref p. 35 | PDF pp. 4, 25, 26, 35, 38
- **Standard**: The ascent is initiated by shoving the hips straight up ("butt straight up in the air, not forward"), maintaining torso inclination through the initial turnaround.
- **Sagittal Assessability**: **Fully Assessable**. Evaluates hip vertical velocity and torso angle constancy during first 35% of ascent.
- **Biomechanical Rationale**: Leading with the chest slackens the hamstrings and turns the squat into a quad-dominant leg press. Leading with the hips recruits the posterior chain (hamstrings, glutes, adductors).
- **Outcomes**:
  - `MEETS_STANDARD`: Hips drive upward first with steady back angle.
  - `DOES_NOT_MEET_STANDARD`: Chest lifts early or hips shoot back without vertical displacement. Actionable cue: Visualize a chain hooked to your sacrum pulling straight up out of the hole.
  - `CANNOT_ASSESS`: Turnaround or ascent phase truncated.

---

### Criterion 5: Eye Gaze Direction & Cervical Spine Alignment
- **Source Section**: *Eye gaze direction*, Figure 2-15, Figure 2-16, *The Important Things You're Going to Do Wrong*
- **Citations**: Ref pp. 23–25 (Fig 2-15, 2-16), Ref p. 35 | PDF pp. 26–28, 38
- **Standard**: Eyes must focus on a point on the floor 4 to 5 feet in front of the lifter with chin down, keeping the cervical spine in neutral anatomical alignment.
- **Sagittal Assessability**: **Fully Assessable**. Head angle relative to torso plane.
- **Biomechanical Rationale**: Looking up at the ceiling pulls the chest, knees, and hips forward, disrupts hip drive, and places the cervical spine in extreme, dangerous hyperextension under heavy load.
- **Outcomes**:
  - `MEETS_STANDARD`: Eyes focused downward 4–5 feet ahead, neutral neck.
  - `DOES_NOT_MEET_STANDARD`: Head tilted up looking at ceiling/wall. Actionable cue: Fix your gaze on the floor 4–5 feet in front and keep your chin tucked.
  - `CANNOT_ASSESS`: Head cut off by camera frame or occluded.

---

### Criterion 6: Knee Forward Travel at Bottom
- **Source Section**: Figure 2-13, Figure 2-22, Ref p. 35
- **Citations**: Ref p. 22 (Fig 2-13), Ref p. 32 (Fig 2-22), Ref p. 35 | PDF pp. 25, 35, 38
- **Standard**: At the bottom, knees should sit just slightly in front of the toes and stay locked in position rather than sliding forward late.
- **Sagittal Assessability**: **Fully Assessable**. Knee X-coordinate vs toe X-coordinate.
- **Biomechanical Rationale**: Excessive forward knee slide shifts the balance onto the balls of the feet and increases patellar tendon shear.
- **Outcomes**:
  - `MEETS_STANDARD`: Knees slightly forward of or directly over toes at bottom.
  - `DOES_NOT_MEET_STANDARD`: Excessive forward knee slide or knees trailing far behind toes.
  - `CANNOT_ASSESS`: Knees or feet occluded.

---

## 3. Explicit Non-Assessable Standards (Side-View Constraints)

The following criteria are described in the Starting Strength reference document but **CANNOT** be assessed from a 2D sagittal side-view video. The agent must return `CANNOT_ASSESS` with the reason specified:

| Criterion | Source Section & Citation | Side-View Feasibility | Reason & System Behavior |
|---|---|---|---|
| **Stance Width** (Heels shoulder-width) | Ref p. 14, Ref p. 20 (Fig 2-12) \| PDF pp. 17, 23 | **Cannot Assess** | Lateral heel distance is compressed to zero depth in a 2D sagittal plane. Requires frontal or rear view. |
| **Toe Angle** (~30° outward flare) | Ref p. 14, Ref p. 20 (Fig 2-12) \| PDF pp. 17, 23 | **Cannot Assess** | Foot rotation occurs in the transverse/horizontal plane. Requires top-down or frontal camera angle. |
| **Knees Shoved Out / Lateral Valgus** | Ref p. 14, Ref p. 22 (Fig 2-13), Ref p. 33 \| PDF pp. 17, 25, 36 | **Cannot Assess** | Lateral knee tracking occurs in the frontal/coronal plane. Near leg occludes far leg; lateral cave cannot be separated from forward travel. |
| **Grip Width & Straight Wrists** | Ref pp. 27–28 (Fig 2-17, 2-18) \| PDF pp. 30–31 | **Cannot Assess** | Standard barbell plates and shoulders occlude the lifter's hands and wrists from a sagittal angle. |
| **Low-Bar Scapular Shelf vs High-Bar** | Ref p. 13, Ref p. 29 (Fig 2-19, 2-20) \| PDF pp. 16, 32 | **Conditional / Estimate** | If barbell plates occlude the spine of the scapula, report `CANNOT_ASSESS (Occluded by barbell plate)`. |
| **Rack Height & Walk-Out Steps** | Ref p. 26, Ref p. 30 (Fig 2-21), Ref p. 33 \| PDF pp. 29, 33, 36 | **Conditional** | If video only records the active squat repetitions without unrack/rack footage, report `CANNOT_ASSESS (Unrack phase not in frame)`. |

---

## 4. Output Findings Schema

For each repetition analyzed, the agent must output a structured JSON finding for each criterion:
```json
{
  "repetition_id": 1,
  "criterion_id": "depth_below_parallel",
  "criterion_name": "Squat Depth (Below Parallel)",
  "source_citation": "Ref p. 2, Fig 2-1; Ref p. 15 | PDF pp. 5, 18",
  "result": "MEETS_STANDARD" | "DOES_NOT_MEET_STANDARD" | "CANNOT_ASSESS",
  "supporting_evidence": {
    "timestamp_seconds": 6.27,
    "frame_index": 188,
    "observed_measurement": "Hip crease Y = 1575.9px, Patella top Y = 1520.1px (Hip is 55.8px below patella)",
    "standard_benchmark": "Hip crease must drop below the top of the patella"
  },
  "explanation": "At the bottom turnaround, the hip joint dropped below parallel with the top of the patella.",
  "actionable_feedback": "Depth is good. Continue driving out of the bottom with your hips.",
  "uncertainty_and_limitations": "Directly observed keypoints with 99.1% tracker confidence."
}
```
