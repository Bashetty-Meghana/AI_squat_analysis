# System Audit & Assignment Compliance Report

**Date**: 2026-11-12  
**Target Repository**: [AI_squat_analysis](https://github.com/Bashetty-Meghana/AI_squat_analysis)  
**Primary Standards Document**: Mark Rippetoe, *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat; Ref pp. 1–35, Combined PDF pp. 4–38).  
**Assignment Reference**: `/docs/assignment.md` (Extracted from `AI_Engineer_Hiring_Assignment.pdf`).

---

## 1. Assignment Requirements Compliance Scorecard

| Assignment Requirement | Status | Relevant File Paths | Empirical Evidence & Findings |
|---|---|---|---|
| **1. Document-Derived Skill** | **Partial** | `skills/squat_standards.json`<br>`skills/squat_coach_skill.md` | Skill exists as JSON + Markdown. However: citations contain minor figure/page misalignments (e.g. Fig 2-10 on p. 17 cited as p. 16; Fig 2-7 on p. 12 cited as p. 11). Eye gaze & hip drive are optimistically classified as "fully assessable" when 2D tracking can only partially assess them. Missing runtime schema validation. |
| **2. Accept & Process Video** | **Done** | `app.py`<br>`analyzer/tracker.py` | Drag-and-drop file uploader and sample video loaders work for MP4, MOV, AVI, WEBM. Real-time progress bar reports tracking, biomechanics, evaluation, and video encoding stages. |
| **3. Movement & Barbell Annotation** | **Partial** | `analyzer/tracker.py`<br>`analyzer/annotator.py` | Pose estimation uses lightweight `yolov8n-pose.pt`. Bar sleeve detection combines red color masking and Hough circles. Repetition segmentation detects peaks. Output video encoded to H.264. Missing: JSON overlay track export for interactive UI canvases, temporal One-Euro smoothing, and observed/estimated/lost tagging per landmark. |
| **4. Standards-Grounded Assessment** | **Partial** | `analyzer/evaluator.py`<br>`skills/squat_standards.json` | Generates structured findings with status badges, citations, and explanations. Fails gracefully with `CANNOT_ASSESS` on unsuitable perspectives. Missing: LLM agent evaluation layer with deterministic fallback, guardrails rejecting unknown criterion IDs, and explicit ASSUMPTION labeling on app tolerances. |
| **5. Consumer-Grade Experience** | **Done** | `app.py` | Simple Form Score (0–100), plain-English action cards ("Squat 2 inches deeper"), traffic-light checklist, bottom turnaround photo inspection, and a Pro/Coach mode toggle. |
| **6. Submission Deliverables & Testing** | **Partial** | `BUILD_NOTE.md`<br>`EVALUATION_REPORT.md`<br>`test_pipeline.py` | Automated pipeline script runs end-to-end. Benchmark outputs exist. Missing: formal pytest suite, schema validation tests, and "change-the-rule" live demo script. |

---

## 2. Page & Figure Citation Verification (`reference.pdf` Audit)

Every citation in `skills/squat_standards.json` and the README was checked against the 35 pages of the squat chapter in `docs/reference.pdf` (Ref pp. 1–35, corresponding to combined PDF pp. 4–38).

| Criterion ID | Document Section | Document Citation in Skill | Actual Page / Figure in `reference.pdf` | Discrepancy & Required Fix |
|---|---|---|---|---|
| `depth_below_parallel` | *Squat Depth – Safety and Importance* | Ref p. 2, Fig 2-1; Ref p. 15; Ref p. 16, Fig 2-10; Ref p. 35 | Ref p. 2 (Fig 2-1), Ref p. 15, **Ref p. 17 (Fig 2-10)**, Ref p. 35 | **Discrepancy**: Figure 2-10 is on **Ref p. 17** (PDF p. 20), not Ref p. 16 (which contains Fig 2-9). Correct to Ref p. 17. |
| `bar_path_verticality_midfoot` | *Loaded Human Movement* | Ref p. 6; Ref p. 8, Fig 2-5; Ref p. 9, Fig 2-6; Ref p. 11, Fig 2-7; Ref p. 32, Fig 2-22 | Ref p. 6; Ref p. 8 (Fig 2-5); Ref p. 9 (Fig 2-6); **Ref p. 12 (Fig 2-7)**; Ref p. 32 (Fig 2-22) | **Discrepancy**: Figure 2-7 is on **Ref p. 12** (PDF p. 15), not Ref p. 11. Correct to Ref p. 12. |
| `back_angle_inclination` | *Diagnostic Angles & Common Faults* | Ref p. 9, Fig 2-5; Ref p. 12; Ref p. 22, Fig 2-13; Ref p. 32, Fig 2-22; Ref p. 35 | Ref p. 9 (Fig 2-5); Ref p. 12; Ref p. 21–22 (Fig 2-13); Ref p. 32 (Fig 2-22); Ref p. 35 | **Verified**: Correct. |
| `hip_drive_initiation` | *Generating Hip Drive* | Ref p. 1; Ref p. 22, Fig 2-14; Ref p. 23; Ref p. 32, Fig 2-22; Ref p. 35 | Ref p. 1; Ref p. 22–23 (Fig 2-14); Ref p. 32 (Fig 2-22); Ref p. 35 | **Verified**: Correct. |
| `eye_gaze_cervical_spine` | *Eye Gaze Direction* | Ref pp. 23-25, Fig 2-15, Fig 2-16; Ref p. 35 | Ref pp. 23–26, Fig 2-15 (Ref p. 25), Fig 2-16 (Ref p. 26); Ref p. 35 | **Verified**: Correct. |
| `knee_forward_travel_at_bottom` | *Figure 2-13 & Figure 2-22* | Ref p. 22, Fig 2-13; Ref p. 32, Fig 2-22; Ref p. 35 | Ref pp. 21–22 (Fig 2-13); Ref p. 32 (Fig 2-22); Ref p. 35 | **Verified**: Correct. |
| `bar_placement_scapula_shelf` | *Bar Placement & Adding the Bar* | Ref p. 13, Fig 2-8; Ref p. 29, Fig 2-19, Fig 2-20; Ref p. 35 | Ref p. 13 (Fig 2-8); **Ref p. 30 (Fig 2-19)**; **Ref p. 31 (Fig 2-20)**; Ref p. 35 | **Discrepancy**: Fig 2-19 is on **Ref p. 30**, Fig 2-20 is on **Ref p. 31**, not Ref p. 29 (which contains Fig 2-18). Correct to Ref pp. 30–31. |
| `rack_height_and_unrack` | *Adding the Bar & Unracking* | Ref p. 26; Ref p. 30, Fig 2-21; Ref p. 33; Ref p. 35 | Ref p. 26; **Ref p. 31 (Fig 2-21)**; Ref p. 33; Ref p. 35 | **Discrepancy**: Figure 2-21 is on **Ref p. 31**, not Ref p. 30. Correct to Ref p. 31. |

---

## 3. Assumptions vs. Document Requirements Analysis

A critical assignment guardrail is:  
> *"Do not add unsupported thresholds or rules and present them as document requirements."*

The audit identified where the application applied numerical thresholds that are **Engineering Assumptions** rather than document mandates:

1. **Squat Depth Boundary**:
   - *Document Requirement*: Hip crease (B) must drop below the top of the patella (A) (Figure 2-1). The document provides **zero** pixel or millimeter tolerances.
   - *App Assumption*: `depth_margin_ratio_target: 0.0`, `acceptable_tolerance_margin: -0.015`. Boundary cases within $\pm 1.0\text{ cm}$ should be classified as `LOW_MARGIN_UNCERTAIN` rather than definitive pass/fail.
   - *Action*: Tag `document_gives_numeric_threshold: false`, flag tolerance as `[ASSUMPTION]`.
2. **Back Angle at Bottom**:
   - *Document Requirement*: "approximately a 45-degree angle" (Ref p. 22 Fig 2-13, Ref p. 9 Fig 2-5). The text does not provide strict angular boundaries.
   - *App Assumption*: Acceptable range `[32.0°, 62.0°]`.
   - *Action*: Tag `document_gives_numeric_threshold: false`, explicitly label the range as `[ASSUMPTION: ±15° tolerance around 45° benchmark]`.
3. **Bar Path Horizontal Drift**:
   - *Document Requirement*: "Straight vertical line directly over midfoot" (Ref p. 8 Fig 2-5, Ref p. 12 Fig 2-7).
   - *App Assumption*: Maximum allowable horizontal drift $\le 0.16$ of shank length ($\approx 3.5\text{ cm}$).
   - *Action*: Tag `document_gives_numeric_threshold: false`, label as `[ASSUMPTION: Engineering drift tolerance]`.
4. **Hip Drive Torso Angle Deviation**:
   - *Document Requirement*: Torso angle must not become more vertical early in ascent (lead with chest) and hips must not shoot backward without vertical progress.
   - *App Assumption*: Early ascent window = first 35% of ascent; torso angle opening $> 12.0^\circ$ = chest leading; torso angle closing $< -10.0^\circ$ = hips shoot back.
   - *Action*: Tag as `[ASSUMPTION: Discrete kinematic window thresholds]`.
5. **Toe Angle**:
   - *Document Requirement*: "approximately 30 degrees" (Ref p. 14, Ref p. 20 Fig 2-12).

---

## 4. Sagittal Assessability Honesty Check

The assignment strictly penalizes invented precision. We audited the 2D sagittal feasibility classifications:

| Criterion | Original Classification | Audit Finding | Revised Honest Classification |
|---|---|---|---|
| **Squat Depth** | Fully Assessable | **Assessable (with uncertainty disclosure)**: The hip joint from 2D pose is an approximation of the anatomical crease apex (point B, Figure 2-1). Boundary results ($\pm 1\text{ cm}$) must disclose clothing/landmark uncertainty. | **Assessable (Subject to Margin of Error)** |
| **Bar Path & Midfoot** | Fully Assessable | **Assessable**: Midfoot horizontal axis and bar sleeve verticality can be measured from side view if shoes/heels are in frame. | **Fully Assessable** |
| **Back Angle** | Fully Assessable | **Assessable**: Torso inclination relative to floor is purely sagittal. | **Fully Assessable** |
| **Hip Drive** | Fully Assessable | **Downgraded to Partial**: 2D pose measures 2D hip elevation and torso angle shift, but cannot observe lumbar lordosis maintenance or 3D hip rotation. | **Partially Assessable (Sagittal Proxy)** |
| **Eye Gaze** | Fully Assessable | **Downgraded to Partial**: 2D side view tracks head tilt angle (ear-to-eye vector vs torso), but **cannot track eye pupils** or gaze fixation point directly. Upward head tilt is a proxy for cervical hyperextension, not direct eye tracking. | **Partially Assessable (Head Tilt Proxy)** |
| **Knee Position at Bottom** | Fully Assessable | **Partially Assessable**: Forward knee position relative to toes is sagittal, but lateral knee tracking (knees out vs valgus) is invisible from the side. | **Partially Assessable** |
| **Stance Width & Toe Flare** | Non-Assessable | **Correctly Non-Assessable**: Coronal/transverse plane variables. | **Non-Assessable (Front/Top View Required)** |
| **Knee Valgus (Knee Cave)**| Non-Assessable | **Correctly Non-Assessable**: Requires frontal or rear camera view. | **Non-Assessable (Front View Required)** |
| **Bar Placement on Scapula**| Non-Assessable | **Correctly Non-Assessable**: Standard 450mm bumper plates occlude the spine of the scapula. | **Non-Assessable (Occluded by Plates)** |

---

## 5. Movement Tracking & Bar Path Verification (24 Audit Frames)

We extracted 8 equidistant frames across all 3 sample videos (`evidence/audit_frames/`, summarized in `evidence/audit_frames_summary.json`):

1. **Common Sample (`samples/common_sample.mp4`, 236 frames)**:
   - **Lifter Orientation**: Accurately detected as `facing: left`, `primary_side: left`.
   - **Keypoint Stability**: Hip, knee, ankle, shoulder landmarks track with high confidence across both reps.
   - **Barbell Hub Tracker**: Successfully tracks the red collar inside the bumper plate hub across all frames (`y=975` lockout $\rightarrow$ `y=1415` bottom rep 1 $\rightarrow$ `y=970` lockout $\rightarrow$ `y=1420` bottom rep 2).
   - **Misalignments Caught**: Around turnaround frame 64 and frame 187, slight camera shake occurs; raw pixel drift must be smoothed to avoid artificial acceleration spikes.
2. **Front View Unsuitable Sample (`samples/unsuitable_front_view.mp4`, 180 frames)**:
   - **Flips & Jitter**: Primary side flips between `left` and `right` repeatedly (frame 0 = left, frame 22 = right, frame 66 = left, frame 88 = right).
   - **System Behavior**: Correctly flags `view_classification: non_sagittal_or_frontal` and returns `CANNOT_ASSESS` on depth and bar path.
3. **Poor Framing & Occlusion Sample (`samples/unsuitable_poor_framing_occlusion.mp4`, 300 frames)**:
   - **Occlusions**: Frames 0–74 report `bar_detected: false` because safety spotter bars obstruct the collar.
   - **Framing Cutoff**: At frame 148 and 185, detected bar position jumps to `y=25` (top 2% of frame). Correctly triggers `head_upper_cutoff` and `feet_lower_cutoff`.

---

## 6. Fresh Upload Verification

- Verified with `uploaded_4921641-hd_1066_1920_25fps.mp4`:
  - Path is fully dynamic: saved to `$env:TEMP` or selected path.
  - Video properties (`1080x1920`, `25.0 FPS`, `15.0s duration`) extracted dynamically via OpenCV.
  - No hardcoded frame counts, indices, or cached outputs.

---

## 7. Prioritized Implementation Plan

Based on the audit findings, here is the prioritized execution roadmap:

1. **Phase 1: Skill Engine Hardening (`skills/`)**:
   - Fix page and figure citations in `squat_standards.json` (Fig 2-10 $\rightarrow$ p. 17; Fig 2-7 $\rightarrow$ p. 12; Figs 2-19/20 $\rightarrow$ pp. 30–31; Fig 2-21 $\rightarrow$ p. 31).
   - Add schema validator and runtime loader.
   - Add missing criteria: `back_flatness_lumbar_extension`, `feet_flat_heels_down`, `unrack_rack_safety`.
   - Add explicit "do NOT assess / narrative only" catalog.
   - Label all application tolerances explicitly as `[ASSUMPTION]`.
2. **Phase 2: Vision & Bar Tracker Upgrade (`analyzer/`)**:
   - Model upgrade evaluation: compare `yolov8n-pose` vs `yolov8m-pose` / heavy model on accuracy and latency.
   - Implement One-Euro temporal smoothing on landmarks.
   - Explicit landmark status tagging: `OBSERVED`, `ESTIMATED`, `LOST`.
   - Low-margin threshold: depth margin within $\pm 0.8\text{ cm}$ marked as uncertain.
   - Generate synchronized JSON overlay track (`output/overlay_track.json`).
3. **Phase 3: Assessment Engine & Guardrails (`analyzer/evaluator.py`)**:
   - Strict skill guardrails: reject unknown criteria and ungrounded numeric thresholds.
   - LLM Agent assessment adapter with automatic deterministic fallback.
4. **Phase 4: UI Refinement (`app.py`)**:
   - Retain the dual-tier design: simple beginner-friendly score & plain-English fixes by default, with full Pro/Coach inspection mode.
   - Add interactive canvas overlay synchronization and frame-stepping.
5. **Phase 5: Verification, Tests & Rule-Change Demo**:
   - Automated pytest test suite (`test_standards_validation.py`, `test_biomechanics_math.py`).
   - "Change-the-rule" live script demonstrating decoupled skill behavior.
   - Log real bug fixes in `AI_USAGE.md`.
6. **Phase 6: Repository Hygiene & Packaging**:
   - Update `.gitignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`.
   - Finalize `BUILD_NOTE.md`, `README.md`, `DEMO_SCRIPT.md`.
