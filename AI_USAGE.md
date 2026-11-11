# Account of AI Collaboration & Verification

This document provides a transparent, defensible account of how AI agents were utilized during the design, development, and testing of the AI Squat Analysis Application, adhering to the hiring assignment specifications.

---

## 1. What Was Delegated to AI

1. **Document Knowledge Extraction**:
   - Parsing the 35 pages of *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat, combined PDF pages 4–38).
   - Extracting core biomechanical rules (depth landmarks, bar-path balance axis, low-bar torso inclination, hip drive mechanics, eye gaze direction, knee forward travel).
   - Mapping each standard to exact source sections, reference pages (**Ref pp. 1–35**), and combined PDF page numbers (**PDF pp. 4–38**).
2. **Boilerplate Architecture & Mathematical Utilities**:
   - Synthesizing 2D vector geometry calculations: angle at vertex ($p_1, p_2, p_3$), torso angle relative to horizontal ground, and head tilt relative to the torso axis.
   - Scaffolding the pipeline skeleton (`tracker.py`, `biomechanics.py`, `evaluator.py`, `annotator.py`, and `app.py`).
3. **Encoding & Piping Pipelines**:
   - Generating the FFmpeg raw video streaming command with `imageio_ffmpeg` to output browser-ready H.264 MP4 streams with `yuv420p` pixel format and `+faststart` moov atom flags.

---

## 2. What Was Inspected and Verified by the Engineer

1. **Biomechanical Ground Truth vs. Document Claims**:
   - Inspected Mark Rippetoe's depth definition on Reference Page 2 (Figure 2-1) and Reference Page 15: "The top of the patella (A) and the hip joint, as identified by the apex in the crease of the shorts (B). The B side of the plane formed by these two points must drop below parallel with the ground."
   - Verified that the code implemented this as a vertical plane check: $y_{\text{hip\_crease}} > y_{\text{patella\_top}}$ in inverted image coordinates, rather than an arbitrary knee angle threshold (e.g. 90 degrees), which is explicitly rejected by *Starting Strength*.
2. **Visual Verification of Annotated Frames**:
   - Manually inspected keyframes extracted from the video pipeline (e.g. `annotated_frame_187.jpg`) to verify landmark overlay precision, depth plane accuracy, and HUD readability.
3. **Camera Angle & Feasibility Boundaries**:
   - Audited the criteria catalog to ensure no coronal/transverse planar requirements (such as stance width, toe angle, or lateral knee valgus) were falsely claimed as assessable from a sagittal side view.

---

## 3. Meaningful Mistake Caught and Corrected

### The Failure:
During the initial end-to-end run on the common sample video (`samples/common_sample.mp4`), the automated evaluation reported:
```
[DOES_NOT_MEET_STANDARD] Bar Path Verticality & Midfoot Balance ->
Excessive horizontal bar drift (318.5px, drift ratio: 1.31) observed relative to midfoot.
```
Upon inspecting the annotated video keyframe (`annotated_frame_187.jpg`), we observed that the barbell trajectory trail was erratically jumping upwards toward the ceiling (tracking background gymnast rings and pull-up ropes), and the barbell position marker was rendered near the lifter's tricep rather than on the barbell.

### Root Cause Analysis:
The AI-generated tracker attempted to locate the barbell by using the lifter's shoulder joint as a spatial anchor and searching for dark circular contours nearby. However:
1. In a pure sagittal side view, standard 450mm Olympic bumper plates completely occlude the shoulder joint and spine of the scapula.
2. The YOLO keypoint detector's shoulder estimate experienced occlusion jitter, causing the circular Hough transform to pick up high-contrast circular objects in the gym ceiling (gymnastic wooden rings and rope knots).
3. This produced a completely fictitious horizontal bar drift measurement (>300 pixels), which wrongly failed the lifter on midfoot balance!

### The Correction:
1. We inspected the high-resolution frame of the common sample video and observed that while the shoulder was occluded, the physical center of the barbell (the sleeve hub with its bright red collar) was clearly visible in the center of the black bumper plate.
2. We rewrote `_track_barbell_sleeve` in `analyzer/tracker.py` to:
   - Restrict the search window strictly to the lifter's bounding box (between upper torso and hip height, never above the head or near the ceiling).
   - Detect the red collar / sleeve hub using dual-range HSV color masks and circular contour enclosing circles.
   - Implement temporal smoothing and optical flow tracking.
3. **Result After Fix**:
   - The barbell tracker locked onto the red sleeve collar at $(576, 1335)$.
   - Midfoot was located at $x = 585$.
   - Horizontal deviation dropped from >300px down to **9.0 pixels** (within 1.5% of the lifter's shank length), confirming that the lifter was actually maintaining a balanced bar path directly over the midfoot, exactly as physical mechanics require!

---

## 4. Selected Agent Prompts & Engineering Traces

### Prompt Delegating Biomechanical Rule Formalization:
> *"Extract all assessable and non-assessable criteria from Starting Strength Chapter 2 (Reference pages 1-35 / PDF pages 4-38). Formulate a machine-readable JSON schema with exact section names, page citations, measurable parameters, and feedback messages. Ensure that criteria requiring frontal or transverse views are explicitly marked as CANNOT_ASSESS from a side view."*

### Engineering Prompt Correcting the Barbell Tracker:
> *"Inspection of annotated_frame_187.jpg shows the barbell marker drifting onto background gymnast rings due to shoulder occlusion from the 45lb bumper plate. Redesign `_track_barbell_sleeve` to isolate the barbell sleeve inside the bumper plate using the red collar contour and spatial constraints bounded within the lifter's torso height, preventing ceiling fixture false positives."*
