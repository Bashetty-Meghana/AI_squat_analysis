# Account of AI Collaboration & Engineering Verification

This document provides a transparent, defensible account of how AI assistance was utilized during the development, audit, and enhancement of the AI Squat Analysis Application, adhering to all hiring assignment guidelines and engineering ethics.

---

## 1. What Was Delegated to AI

1. **Document Knowledge Extraction**:
   - Parsing the 35 pages of *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat, Ref pp. 1–35, combined PDF pages 4–38).
   - Extracting core biomechanical rules (depth landmarks, bar-path balance axis, low-bar torso inclination, hip drive mechanics, eye gaze direction, knee forward travel).
   - Mapping each standard to exact source sections, reference pages (**Ref pp. 1–35**), combined PDF page numbers (**PDF pp. 4–38**), and textbook figures (**Figs 2-1 to 2-22**).
2. **Boilerplate Architecture & Mathematical Utilities**:
   - Synthesizing 2D vector geometry calculations: angle at vertex ($p_1, p_2, p_3$), torso angle relative to horizontal ground, and head tilt relative to the torso axis.
   - Scaffolding the decoupled pipeline modules (`tracker.py`, `biomechanics.py`, `evaluator.py`, `annotator.py`, `validator.py`, and `app.py`).
3. **Encoding & Piping Pipelines**:
   - Generating FFmpeg raw video streaming commands with `imageio_ffmpeg` to output browser-ready H.264 MP4 streams with `yuv420p` pixel format and `+faststart` moov atom flags.
   - Exporting synchronized JSON overlay tracks (`output/*_overlay_track.json`) for web canvas rendering.

---

## 2. What Was Inspected and Verified by the Senior Engineer

1. **Biomechanical Ground Truth vs. Document Claims**:
   - Inspected Mark Rippetoe's depth definition on Reference Page 2 (Figure 2-1) and Reference Page 15: *"The top of the patella (A) and the hip joint, as identified by the apex in the crease of the shorts (B). The B side of the plane formed by these two points must drop below parallel with the ground."*
   - Verified that the code implemented this as a vertical plane check: $y_{\text{hip\_crease}} > y_{\text{patella\_top}}$ in downward-positive image coordinates, rather than an arbitrary knee angle threshold (e.g. 90 degrees), which is explicitly rejected by *Starting Strength*.
2. **Visual Verification of Keyframe Overlays**:
   - Extracted and verified 24 audit verification frames across all 3 sample clips into `evidence/audit_frames/` with `evidence/audit_frames_summary.json`.
   - Inspected bottom-position frame grabs to verify skeleton alignment, patella plane placement, and barbell sleeve tracking.
3. **Camera Angle & Feasibility Boundaries**:
   - Audited the criteria catalog to ensure no coronal/transverse planar requirements (such as stance width, toe angle, or lateral knee valgus) were falsely claimed as assessable from a sagittal side view.
   - Verified that frontal recordings trigger `CANNOT_ASSESS` across all sagittal criteria.

---

## 3. Real Bugs Caught and Resolved

### Bug 1: Barbell Tracker Occlusion & Ceiling False Positives
- **Failure**: During initial runs on `samples/common_sample.mp4`, the barbell trail erratically jumped upwards toward the ceiling (tracking background gymnast rings and pull-up ropes), rendering the barbell position marker near the lifter's tricep and producing an absurd $>300$px horizontal bar drift!
- **Root Cause**: Standard 450mm Olympic bumper plates occlude the shoulder joint in a side view. YOLO shoulder keypoint jitter caused the unconstrained Hough circle detector to latch onto high-contrast rings in the gym ceiling.
- **Correction**: Rewrote `_track_barbell_sleeve` in `analyzer/tracker.py` to:
  1. Restrict candidate search strictly within the lifter's upper-body spatial bounding box.
  2. Implement dual-range HSV color filtering for red Olympic collar / sleeve hubs.
  3. Enforce temporal velocity gating: displacement between adjacent frames is capped at $80\text{ px/frame}$; outliers are rejected.
  4. Fallback to shoulder proxy only if explicitly tagged `ESTIMATED`; refuse to draw a trail when tracking is `LOST`.
- **Outcome**: Barbell tracking remained glued to the sleeve collar at $(576, 1335)$ throughout turnaround.

### Bug 2: Depth Landmark Approximation & False-Confident Boundary Decisions
- **Failure**: The original prototype treated the raw COCO hip landmark as the exact crease of the shorts, outputting a confident binary pass/fail on Rep 2 of `common_sample.mp4` even though the margin was only $-0.3\text{ cm}$ (fractions of a millimeter).
- **Root Cause**: In 2D pose estimation (COCO keypoint 11/12), the detector predicts the internal skeletal hip joint center (greater trochanter proxy), whereas *Starting Strength* Figure 2-1 specifies Point B as the external anatomical *apex of the crease of the shorts*. A 2D joint center is an approximation with physical uncertainty of $\pm 0.5 - 1.0\text{ cm}$.
- **Correction**: Implemented the low-margin boundary rule in `analyzer/biomechanics.py` and `analyzer/evaluator.py`:
  - When the measured depth margin is within $\pm 0.8\text{ cm}$ (approx. $\pm 4$ pixels), the result is flagged as `is_borderline = True`.
  - The evaluator outputs `CANNOT_ASSESS` with an explicit disclosure: `[ASSUMPTION: Margin within +/-0.8cm boundary uncertainty. Hip joint keypoint is an anatomical proxy for crease apex B]`.
- **Outcome**: Eliminates false confidence on borderline squats, prompting lifters to squat 1–2 inches deeper to remove all doubt.

### Bug 3: Textbook Citation Drift in Original Schema
- **Failure**: The original `squat_standards.json` contained multiple misaligned figure and page citations:
  - Fig 2-10 was cited on Ref p. 16 (actually Fig 2-9; Fig 2-10 is on Ref p. 17 / PDF p. 20).
  - Fig 2-7 was cited on Ref p. 11 (actually on Ref p. 12 / PDF p. 15).
  - Figs 2-19 and 2-20 were cited on Ref p. 29 (actually on Ref pp. 30–31 / PDF pp. 33–34).
  - Fig 2-21 was cited on Ref p. 30 (actually on Ref p. 31 / PDF p. 34).
- **Correction**: Audited every page and figure citation directly against the extracted 35-page text of `docs/reference.pdf`. Fixed all citations in `skills/squat_standards.json` and validated them via `skills/validator.py`.

### Bug 4: Camera-Facing Side Flipping on New Uploads
- **Failure**: When testing the fresh user upload (`uploaded_4921641-hd_1066_1920_25fps.mp4`), the lifter faced right instead of left. The hardcoded left-side tracker tracked the occluded far-side leg, leading to erratic angle calculations.
- **Correction**: In `analyzer/tracker.py`, implemented cumulative confidence side scoring across all detected frames:
  $$\text{Score}_{\text{side}} = \sum (\text{conf}_{\text{shoulder}} + \text{conf}_{\text{hip}} + \text{conf}_{\text{knee}} + \text{conf}_{\text{ankle}})$$
  Automatically selected the primary camera-facing side (`right` for the new upload, `left` for common sample) and reported `camera_facing_side` in the output JSON.

### Bug 5: Temporal Jitter in Velocity & Angles
- **Failure**: High-frequency detection jitter ($\pm 2-3$ px) caused derivative spike noise in peak concentric velocity and early ascent angle slope calculations.
- **Correction**: Implemented an adaptive `OneEuroFilter` (Casiez et al., CHI 2012) in `analyzer/tracker.py`. Low cutoff at rest suppresses stationary jitter; dynamic cutoff during rapid descent/ascent prevents lag.

---

## 4. Prompts & Interaction Summary

1. **System Prompt & Audit**:
   - Directed the model to read `docs/assignment.md` and `docs/reference.pdf` completely before modifying code.
   - Mandated non-destructive enhancement: keep the Streamlit app runnable at all times and list every change in `docs/CHANGELOG.md`.
2. **Decoupled Architecture**:
   - Enforced that changing rules in `skills/squat_standards.json` dynamically alters the evaluation findings without any code edits or video reprocessing (proven via `demo_rule_change.py`).
3. **Consumer & Pro Duality**:
   - Directed the creation of a dual-mode interface: simple 0–100 score with plain English action cues for beginners, and deep VBT/diagnostic angle analytics for coaches.
