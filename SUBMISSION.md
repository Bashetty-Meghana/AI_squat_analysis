# AI Squat Analysis Application — Submission Package

**Project**: AI Engineer Hiring Assignment — AI Squat Analysis Application  
**Grounding Source**: Mark Rippetoe, *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat)  
**Target Video**: Side-View Barbell Squats (Common Sample: `https://youtube.com/shorts/TRvg083BrXY?si=qXAnreEaVGVgQ_LQ`)  

---

## 📌 Executive Summary of the 5 Required Deliverables

### Requirement 1: Working Application Link & Installable Build
- **Local Application Link**: **`http://localhost:8501`** (Running locally via Streamlit).
- **Constraint / Hosting Rationale**: Due to user video privacy considerations, zero cloud latency requirements, and immediate local GPU/CPU execution, the application is packaged as a reproducible local web build.
- **One-Click Launch**:
  - **Windows**: Run `run.bat` (or `python -m streamlit run app.py --server.port 8501`).
  - **macOS / Linux**: Run `./run.sh` (or `streamlit run app.py --server.port 8501`).
- **Prerequisites**: Python 3.10+ (tested on Python 3.13). Dependencies in `requirements.txt`. No external FFmpeg system installation needed (embedded `imageio-ffmpeg` binary included).

---

### Requirement 2: Source Repository, Document-Derived Skill & Setup Instructions
- **Repository Codebase**:
  - [`app.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/app.py): Consumer-facing interactive Streamlit application.
  - [`analyzer/tracker.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/tracker.py): Vision tracking, orientation detection, and multi-modal barbell sleeve tracking.
  - [`analyzer/biomechanics.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/biomechanics.py): Diagnostic angle math, depth plane margin, midfoot balance axis, and rep segmentation.
  - [`analyzer/evaluator.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/evaluator.py): Standards-grounded rules engine producing structured findings with page citations.
  - [`analyzer/annotator.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/annotator.py): Visual overlay generator and browser-compatible H.264 video writer.
- **Document-Derived Skill**:
  - [`skills/squat_standards.json`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/squat_standards.json): Inspectable, versioned JSON rules citing Reference pages 1–35 (combined PDF pages 4–38).
  - [`skills/squat_coach_skill.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/squat_coach_skill.md): Reusable agent instructions defining biomechanical criteria and boundaries.
- **Required Services & Environment Variables**:
  - Zero external cloud services or paid APIs required ($0 running cost).
  - No secret environment variables needed.
  - Setup: `pip install -r requirements.txt`.

---

### Requirement 3: Build Note (Architecture, Choices, Time, Costs, Trade-offs)
- **Full Document**: [`BUILD_NOTE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/BUILD_NOTE.md)
- **Key Points**:
  - **Architecture**: Decoupled 4-stage pipeline (Vision Tracking $\rightarrow$ Biomechanics $\rightarrow$ Evaluator $\rightarrow$ Annotator).
  - **Model & Tool Choices**: YOLOv8-pose (`yolov8n-pose.pt`) for fast keypoint detection (~80–90ms on CPU); dual-range HSV color + circular Hough transform for barbell sleeve tracking; `imageio_ffmpeg` for browser-native H.264 MP4 streaming; Streamlit for responsive UI.
  - **Actual Time Spent**: **~5 hours 15 minutes** (within the 4–6 hour assignment timebox).
  - **Costs**: Build cost: **$0.00**; Per-video inference cost: **<$0.0005** (half a tenth of a cent on standard CPU/serverless compute).
  - **Key Trade-Offs**: Lightweight YOLOv8-pose over heavy GPU-bound ViTPose; deterministic geometric standards over hallucination-prone free-form vision LLMs; honest 2D single-camera limitations over fabricated 3D numbers.
  - **Known Limitations**: 450mm bumper plate sagittal occlusion of upper back; loose shorts on hip crease; inability to measure coronal variables (stance width, knee valgus) from a 2D side view.

---

### Requirement 4: Account of AI Collaboration & Failure Corrected
- **Full Document**: [`AI_USAGE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/AI_USAGE.md)
- **What Was Delegated**: Document OCR extraction, 2D vector geometry functions, raw FFmpeg piping, and UI scaffolding.
- **What Was Inspected**: Biomechanical definitions against Starting Strength (Figure 2-1 depth plane), frame-by-frame visual overlay precision, and planar feasibility boundaries.
- **Meaningful Failure Caught & Corrected**:
  - *Symptom*: Initial pipeline reported massive horizontal bar drift (>300px), claiming the lifter was completely off-balance.
  - *Root Cause*: The initial tracker anchored the barbell to the shoulder joint. In a pure side view, 450mm bumper plates occlude the shoulder. Occlusion jitter caused the detector to jump onto background gymnastic rings hanging from the ceiling.
  - *Fix*: Restricted the search window to the lifter's torso height and implemented a dedicated barbell sleeve tracker that locks onto the red collar inside the bumper plate hub. Horizontal drift dropped from >300px down to **9.0px**, confirming physical balance over midfoot.

---

### Requirement 5: Empirical Evidence (Common Sample & Unsuitable Recordings)
- **Full Document**: [`EVALUATION_REPORT.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/EVALUATION_REPORT.md)
- **Evidence Summary**:
  1. **Common Sample (`samples/common_sample.mp4`)**:
     - 2 complete repetitions segmented.
     - Rep 1: High squat (`DOES_NOT_MEET_STANDARD`, hip crease remained 10.9px above patella).
     - Rep 2: Depth pass (`MEETS_STANDARD`, hip crease dropped 10.6px below patella).
     - Back Angle: $\sim 56^\circ - 59^\circ$ (`MEETS_STANDARD`).
     - Hip Drive: Strong vertical drive out of turnaround (`MEETS_STANDARD`).
     - Eye Gaze: Upward head tilt $75^\circ-77^\circ$ (`DOES_NOT_MEET_STANDARD`, looking at ceiling/wall instead of floor).
     - Bar Path: Balanced within 9–15px of midfoot axis (`MEETS_STANDARD`).
  2. **Unsuitable Recording 1: Frontal Perspective (`samples/unsuitable_front_view.mp4`)**:
     - System automatically detects non-sagittal angle (`mean_shoulder_width_ratio = 0.68`).
     - Returns `CANNOT_ASSESS` with explicit explanation that depth cannot be resolved from the front, directing the lifter to position the camera at 90° side view.
  3. **Unsuitable Recording 2: Framing Cutoff & Rack Occlusion (`samples/unsuitable_poor_framing_occlusion.mp4`)**:
     - System flags `head_upper_cutoff` and rack safety beam obstruction, returning `CANNOT_ASSESS` on occluded criteria rather than guessing.

---

## 🎯 15-Minute Demonstration Walkthrough

A structured presentation and interview script is available in:  
👉 [`WALKTHROUGH_GUIDE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/WALKTHROUGH_GUIDE.md)

It provides the minute-by-minute talking points for the 5-minute commercial pitch, 10-minute live demonstration, handling live changes to rules in `skills/squat_standards.json`, and answering technical deep-dive questions.
