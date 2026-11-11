# Evaluation Report: Empirical Testing & Evidence

This report documents the verification, landmark tracking accuracy, source grounding, and feedback generated across the official benchmark recordings, in compliance with the hiring assignment requirements.

---

## 1. Test Case 1: Official Common Sample Video (`samples/common_sample.mp4`)

### Recording Specifications:
- **Source**: Official hiring assignment YouTube Shorts link (`https://youtube.com/shorts/TRvg083BrXY?si=qXAnreEaVGVgQ_LQ`).
- **Resolution**: $1080 \times 1920$ (Vertical 9:16 mobile capture).
- **Framerate**: 30.00 FPS | **Duration**: 7.87s (236 frames).
- **Perspective**: Left-lateral sagittal side view.
- **Equipment**: Olympic barbell with standard black bumper plates, red collars.

### Landmark Placement & Tracking Verification:
- **Orientation Detected**: Left lateral sagittal view (`is_side_view = True`, `facing = left`).
- **Mean Shoulder Width Ratio**: $0.09$ (confirming pure side-view projection with minimal foreshortening).
- **Confidence Scores**: Hips: $99.3\%$, Knees: $99.4\%$, Ankles: $97.5\%$, Shoulders: $79.4\%$.
- **Barbell Hub Tracking**: Successfully locked onto the red collar sleeve hub at $(576, 1335)$ at bottom turnaround (Frame 187), eliminating occlusion artifacts caused by the 450mm bumper plate.

### Repetition Segmentation:
The pipeline identified **2 complete squat repetitions**:
1. **Repetition 1**: Start: Frame 0 ($0.00$s), Bottom Inflection: Frame 64 ($2.13$s), Lockout: Frame 130 ($4.33$s).
2. **Repetition 2**: Start: Frame 132 ($4.40$s), Bottom Inflection: Frame 187 ($6.23$s), Lockout: Frame 236 ($7.87$s).

### Criteria Evaluation Matrix:

| Criterion | Starting Strength Citation | Rep 1 Observed Result | Rep 2 Observed Result | Grounded Rationale |
|---|---|---|---|---|
| **Squat Depth** | Ref p. 2, Fig 2-1; Ref p. 15 (PDF pp. 5, 18) | **`DOES_NOT_MEET_STANDARD`** (High by $-10.9$px) | **`MEETS_STANDARD`** (Below parallel by $+10.6$px) | In Rep 1, the hip crease remained slightly above the top of the patella. In Rep 2, the hip crease dropped clearly below the patella plane, satisfying full ROM. |
| **Back Angle at Bottom** | Ref p. 9, Fig 2-5; Ref p. 22, Fig 2-13 (PDF pp. 12, 25) | **`MEETS_STANDARD`** ($55.9^\circ$ to horizontal) | **`MEETS_STANDARD`** ($59.3^\circ$ to horizontal) | Torso was inclined at $\sim 56^\circ - 59^\circ$, adhering to the low-bar squat back angle model (nominal $\sim 45^\circ$, acceptable range $32^\circ - 62^\circ$). |
| **Hip Drive Initiation** | Ref p. 1; Ref p. 23, Fig 2-14 (PDF pp. 4, 26) | **`MEETS_STANDARD`** (Hips drove up $+194$px, angle shift $+7.6^\circ$) | **`MEETS_STANDARD`** (Hips drove up $+139$px, angle shift $+1.2^\circ$) | Lifter initiated the turnaround by shoving hips straight up rather than prematurely lifting the chest. |
| **Eye Gaze & Cervical Spine** | Ref pp. 23–25, Fig 2-15 (PDF pp. 26–28) | **`DOES_NOT_MEET_STANDARD`** ($75.8^\circ$ upward head tilt) | **`DOES_NOT_MEET_STANDARD`** ($77.2^\circ$ upward head tilt) | Lifter looked forward/up at wall/ceiling rather than looking down at the floor 4–5 feet in front. Ref p. 23 notes this slacks the hamstrings. |
| **Bar Path Verticality** | Ref p. 6, Ref p. 8, Fig 2-5 (PDF pp. 9, 11) | **`MEETS_STANDARD`** (Balanced over shoe arch) | **`MEETS_STANDARD`** (Balanced over shoe arch) | Bar path stayed vertically aligned within the midfoot corridor ($x_{\text{bar}} = 576$, $x_{\text{midfoot}} = 585$). |

---

## 2. Test Case 2: Unsuitable Recording — Frontal Perspective (`samples/unsuitable_front_view.mp4`)

### Recording Specifications:
- **Source**: Frontal view squat demonstration recording.
- **Resolution**: $1280 \times 720$ | **Framerate**: 29.97 FPS.
- **Perspective**: Frontal (coronal plane) camera angle.

### Automated Detection & System Behavior:
- **Orientation Detected**: Frontal view (`dominant_facing = unknown`, `mean_shoulder_width_ratio = 0.68`).
- **View Classification**: `non_sagittal_or_frontal` (`is_side_view = False`).

### System Output & Honesty:
- The system automatically triggers the `CAMERA_ANGLE_ERROR` alert banner.
- **Reported Outcome for all Sagittal Criteria**: **`CANNOT_ASSESS`**.
- **Explanation**: "Cannot assess sagittal planar biomechanics from a frontal or off-angle view. Plane between hip crease and patella cannot be resolved."
- **Actionable Advice**: "Relocate camera to a pure 90° side view perpendicular to the lifter's stance at hip height."
- **Verification**: Proves that the system avoids invented precision and refuses to hallucinate depth measurements from an invalid camera perspective.

---

## 3. Test Case 3: Unsuitable Recording — Severe Framing Cutoff & Occlusion (`samples/unsuitable_poor_framing_occlusion.mp4`)

### Recording Specifications:
- **Source**: Side-view recording inside a power rack.
- **Resolution**: $640 \times 480$ | **Framerate**: 29.97 FPS.
- **Perspective**: Side view, but with poor camera framing and structural occlusion.

### Automated Detection & System Behavior:
- **Framing Cutoff Detected**: `head_upper_cutoff` (lifter head and upper barbell pass beyond the top frame boundary).
- **Physical Occlusion**: Horizontal steel power rack safety beam directly obstructs the hip and knee joints during descent.

### System Output & Honesty:
- The system flags both framing cutoffs and structural occlusion.
- **Cervical Spine / Eye Gaze**: Reported as **`CANNOT_ASSESS`** ("Lifter head was outside the upper frame boundary").
- **Bar Path**: Reported as **`CANNOT_ASSESS`** ("Barbell path left upper frame boundary during lockout").
- **Actionable Advice**: "Widen camera shot to include the entire lifter from head to feet across full range of motion, and remove or reposition safety bars that occlude the hip joint."

---

## 4. Verification Summary Table

| Test Recording | Camera Suitability | Reps Detected | Depth Assessment | Bar Path Assessment | Grounded Feedback Verified? |
|---|---|---|---|---|---|
| **Common Sample** (`common_sample.mp4`) | ✅ **Valid Sagittal Side View** | 2 | Rep 1: High; Rep 2: Pass | Verified balanced over midfoot | ✅ Yes, cited Ref pp. 1, 2, 8, 9, 23 |
| **Frontal View** (`unsuitable_front_view.mp4`) | ❌ **Invalid (Frontal Angle)** | N/A (Flagged) | `CANNOT_ASSESS` | `CANNOT_ASSESS` | ✅ Yes, prompt alert to fix angle |
| **Framing Cutoff** (`unsuitable_poor_framing.mp4`) | ⚠️ **Invalid (Framing & Occlusion)**| Partial | `CANNOT_ASSESS` | `CANNOT_ASSESS` | ✅ Yes, prompts lifter to fix framing |
