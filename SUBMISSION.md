# AI Squat Analysis Application — Submission Package

**Project**: AI Engineer Hiring Assignment — AI Squat Analysis Application  
**Grounding Source**: Mark Rippetoe, *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat, Ref pp. 1–35 / PDF pp. 4–38)  
**Target Video**: Side-View Barbell Squats (Common Sample: `https://youtube.com/shorts/TRvg083BrXY?si=qXAnreEaVGVgQ_LQ`)  

---

## 📌 Executive Summary of the 5 Required Deliverables

### Requirement 1: Working Application Link & Installable Build
- **Local Application Link**: **`http://localhost:8501`** (Running locally via Streamlit).
- **One-Click Launch**:
  - **Windows**: Double-click `run.bat` (or execute `run.bat` in Command Prompt).
  - **macOS / Linux**: Run `./run.sh`.
  - **Docker**: `docker compose up --build`.
- **Dual-Mode User Experience**:
  - **Consumer Mode (Default)**: Simple Form Score (0–100), traffic-light checklist (Depth, Head Position, Back Support, Foot Balance), and actionable plain-English next-set cues.
  - **Pro / Coach Mode (1-Click Toggle)**: Velocity-Based Training (VBT) KPIs ($V_{\text{mean}}$, $V_{\text{peak}}$, tempo, velocity loss %), Starting Strength textbook citations, diagnostic angles, and synchronized JSON overlay tracks.

---

### Requirement 2: Source Repository, Document-Derived Skill & Setup Instructions
- **Repository Architecture**:
  - [`app.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/app.py): Dual-mode consumer and coach dashboard.
  - [`analyzer/tracker.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/tracker.py): YOLOv8s-pose model with 1-Euro adaptive temporal filter, automated camera-facing side selection, and velocity-gated multi-modal barbell tracking.
  - [`analyzer/biomechanics.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/biomechanics.py): Starting Strength diagnostic angles, low-margin boundary uncertainty rule ($\pm 0.8$ cm), midfoot balance axis, rep segmentation with hysteresis, and VBT velocity engine.
  - [`analyzer/evaluator.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/evaluator.py): Standards-grounded rules engine with schema guardrails, non-sagittal gating, and LLM agent adapter layer.
  - [`analyzer/annotator.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/analyzer/annotator.py): Telemetry HUD overlay, browser-native H.264 MP4 writer, and synchronized JSON overlay track generator (`output/*_overlay_track.json`).
- **Document-Derived Skill**:
  - [`skills/squat_standards.json`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/squat_standards.json): Inspectable, versioned JSON rules citing Reference pages 1–35 (combined PDF pages 4–38) with explicit `[ASSUMPTION]` tags.
  - [`skills/validator.py`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/validator.py): Runtime schema validator enforcing all required fields and assessability enums.
  - [`skills/squat_coach_skill.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/squat_coach_skill.md): Reusable agent prompt instructions.
- **Dependencies**: Listed in `requirements.txt`. Zero paid API requirements.

---

### Requirement 3: Build Note (Architecture, Choices, Time, Costs, Trade-offs)
- **Full Document**: [`BUILD_NOTE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/BUILD_NOTE.md)
- **Key Points**:
  - **Architecture**: Decoupled pipeline with Mermaid architecture diagram.
  - **Model & Tool Choices**: Evaluated YOLOv8n, YOLOv8s, and YOLOv8m. Selected **YOLOv8s-pose** for 98.8% keypoint confidence and low jitter ($\pm 1.1$px) with ~320ms CPU latency.
  - **Decoupled Verification**: Proved that changing a rule in `skills/squat_standards.json` dynamically alters the evaluation findings without code edits or video reprocessing (`demo_rule_change.py`).
  - **Actual Time Spent**: **~5 hours 15 minutes** (within assignment timebox).
  - **Costs**: Local execution cost: **$0.00 / video** (zero recurring LLM token fees or external vision API costs).
  - **Key Trade-Offs**: Enhanced Streamlit UI over complex React rewrite, preserving continuous runnable functionality while achieving consumer-grade simplicity.

---

### Requirement 4: Account of AI Collaboration & Failure Corrected
- **Full Document**: [`AI_USAGE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/AI_USAGE.md)
- **What Was Delegated**: Document OCR extraction, 2D vector geometry calculations, raw FFmpeg piping, and UI scaffolding.
- **What Was Inspected**: Biomechanical definitions against Starting Strength (Figure 2-1 depth plane), frame-by-frame visual overlay precision, and planar feasibility boundaries.
- **Real Bugs Caught and Corrected**:
  1. *Barbell Tracker Occlusion*: Initial tracker jumped to ceiling gymnast rings due to 450mm bumper plate shoulder occlusion; fixed with upper-torso bounding constraints and red collar HSV tracking with $80\text{ px/frame}$ velocity gating.
  2. *Depth Landmark Approximation*: Hip joint center approximates the crease of shorts (Point B); added low-margin boundary rule ($\pm 0.8$ cm) marking borderline squats as `CANNOT_ASSESS` with `[ASSUMPTION]` notes rather than false confidence.
  3. *Citation Drift*: Fixed multiple textbook page/figure misalignments in the schema against `docs/reference.pdf`.
  4. *Camera-Facing Side Switching*: Implemented automated cumulative confidence scoring to automatically detect left vs right facing lifters on fresh uploads.
  5. *Temporal Jitter*: Implemented 1-Euro adaptive temporal filter to kill derivative spike noise in velocity calculations.

---

### Requirement 5: Empirical Evidence (Common Sample, Unsuitable & Fresh Uploads)
- **Full Document**: [`EVALUATION_REPORT.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/EVALUATION_REPORT.md)
- **Evidence Summary**:
  1. **Common Sample (`samples/common_sample.mp4`)**:
     - Rep 1: High squat (`DOES_NOT_MEET_STANDARD`, $-1.5$ cm above patella).
     - Rep 2: Borderline depth (`CANNOT_ASSESS`, $-0.3$ cm margin within $\pm 0.8$ cm boundary uncertainty).
     - Back Angle: $\sim 60^\circ$ (`MEETS_STANDARD`).
     - Hip Drive: Strong vertical drive out of turnaround (`MEETS_STANDARD`).
     - Eye Gaze: Upward head tilt $64^\circ-84^\circ$ (`DOES_NOT_MEET_STANDARD`).
  2. **Unsuitable Recording 1: Frontal Perspective (`samples/unsuitable_front_view.mp4`)**:
     - System automatically detects non-sagittal angle (`is_side_view = False`).
     - Reports `UNSUITABLE_RECORDING` with `CANNOT_ASSESS` across all sagittal criteria.
  3. **Unsuitable Recording 2: Framing Cutoff (`samples/unsuitable_poor_framing_occlusion.mp4`)**:
     - Selectively gates only affected criteria (bar path, eye gaze as `CANNOT_ASSESS`) while evaluating visible anatomy.
  4. **Fresh External User Upload (`uploaded_4921641-hd_1066_1920_25fps.mp4`)**:
     - Successfully processed non-bundled real lifter video, automatically detecting right-facing orientation and 3 high squat repetitions.
  5. **Automated Unit Testing Suite**:
     - 14/14 unit tests passing in 0.018s (`python -m unittest discover tests -v`).
  6. **Decoupled Rule-Change Demonstration**:
     - Verified with `python demo_rule_change.py` dynamically flipping findings from `MEETS_STANDARD` to `DOES_NOT_MEET_STANDARD`.

---

## 🎯 Demonstration Walkthrough Guides
- **Live Script & 5-Min Pitch**: [`DEMO_SCRIPT.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/DEMO_SCRIPT.md)
- **Interactive Guide**: [`WALKTHROUGH_GUIDE.md`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/WALKTHROUGH_GUIDE.md)
