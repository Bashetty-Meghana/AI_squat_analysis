# Project Changelog & Replacement Log

This document tracks all changes, enhancements, and any deleted or replaced files throughout the project enhancement lifecycle, maintaining an unbroken audit trail.

---

## [Phase 6: Verification, Packaging & Delivery] - 2026-11-12

### Added
- `frontend/`: Standalone React + Vite + Tailwind CSS single-page application with synchronized HTML5 Canvas overlay player, interactive layer toggles, rep timeline navigation, consumer score cards, and pro VBT analytics.
- `server.py`: Production FastAPI REST backend wrapping the decoupled `/analyzer` pipeline as a library, supporting asynchronous job tracking, Range-based video streaming, and static asset serving.
- `run_react.bat` & `run_react.sh`: Windows and Linux one-click launch scripts for the FastAPI + React frontend on `http://localhost:8000`.
- `tests/test_api_endpoints.py`: Integration test suite verifying FastAPI healthcheck, sample listings, standards endpoint, and job submission.
- `tests/test_standards_validation.py`: Unit test suite verifying schema validation, required fields, assessability enums, non-assessable criteria, narrative exclusions, missing field rejection, and evaluator guardrails (non-sagittal perspective, borderline depth).
- `tests/test_biomechanics_math.py`: Unit test suite verifying 2D angle math (orthogonal, straight, vertical, 45° incline), Y-axis coordinate direction consistency ($y_{\text{hip}} > y_{\text{patella}}$ below parallel), head angle, and rep segmentation on synthetic signals with noise.
- `demo_rule_change.py`: Standalone demonstration script proving decoupling of skill standards from computer vision code: edits a rule in `skills/squat_standards.json`, re-runs the assessment engine on cached measurements with NO code edits and NO video reprocessing, and dynamically updates findings.
- `test_all_samples.py`: End-to-end evaluation runner testing `samples/common_sample.mp4`, `samples/unsuitable_front_view.mp4`, and `samples/unsuitable_poor_framing_occlusion.mp4`.
- `test_fresh_upload.py`: Verification script testing end-to-end pipeline on an external non-bundled user-uploaded video (`uploaded_4921641-hd_1066_1920_25fps.mp4`), verifying automated camera-facing side selection and rep segmentation.
- `DEMO_SCRIPT.md`: Comprehensive 5-minute startup pitch and 10-minute live demonstration walkthrough.
- `Dockerfile`: Multi-stage production container build with pre-cached model weights and FFmpeg.
- `docker-compose.yml`: Local container orchestration configuration.
- `.env.example`: Configuration template for LLM provider, API keys, and model selection.
- `output/annotated_common_sample_overlay_track.json`: Synchronized per-frame JSON overlay track for browser canvas rendering.
- `output/eval_unsuitable_front_overlay_track.json`: Overlay track for frontal unsuitable recording.
- `output/eval_unsuitable_framing_overlay_track.json`: Overlay track for framing cutoff recording.
- `output/annotated_fresh_upload_4921641_overlay_track.json`: Overlay track for fresh user upload.

### Modified
- `analyzer/tracker.py`:
  - Upgraded pose model to `yolov8s-pose.pt` with automatic fallback to `yolov8n-pose.pt`.
  - Implemented `OneEuroFilter` (Casiez et al. 2012) for dynamic temporal smoothing.
  - Added explicit confidence status tagging (`OBSERVED`, `ESTIMATED`, `LOST`) on all keypoints.
  - Implemented multi-modal barbell tracking with dual-range HSV color filtering, Hough circle detection, and $80\text{ px/frame}$ velocity gating.
  - Added automated camera-facing side selection (`left` vs `right`) based on cumulative keypoint confidence scores.
  - Added structured input validation (`LOW_FPS`, `TOO_SHORT`, `TOO_LONG`, `MULTIPLE_PEOPLE`, `TINY_LIFTER`).
- `analyzer/biomechanics.py`:
  - Implemented low-margin boundary uncertainty rule: depth margins within $\pm 0.8\text{ cm}$ flagged as `is_borderline = True`.
  - Added rep segmentation hysteresis rejecting walkout, rerack, and partial flutter.
  - Exported `measurement_status` tags (`OBSERVED`, `ESTIMATED`).
- `analyzer/evaluator.py`:
  - Integrated `SquatStandardsLoader` schema validator with runtime guardrails.
  - Added handling for borderline depth margins returning `CANNOT_ASSESS` with `[ASSUMPTION]` notes.
  - Added non-sagittal perspective guardrail marking all sagittal criteria as `CANNOT_ASSESS`.
  - Added LLM agent assessment adapter layer (`evaluate_with_llm`) with automatic deterministic fallback.
- `analyzer/annotator.py`:
  - Exported synchronized JSON overlay tracks (`output/*_overlay_track.json`) alongside H.264 video.
  - Added borderline depth indicator badge on depth plane marker.
  - Refused to draw barbell trajectory trail when barbell tracking status is `LOST`.
- `app.py`:
  - Polished dual-mode interface: Consumer Mode (Form Score 0-100, traffic-light checklist, next-set cards) and Pro Mode (VBT KPIs, diagnostic angles, Starting Strength textbook citations).
  - Added borderline depth indicator in turnaround keyframe photos gallery.
  - Added "What Starting Strength Criteria Cannot Be Assessed from a Side View" disclosure panel.
- `.gitignore`: Added rules ignoring model weights (`*.pt`), output videos (`output/*.mp4`), and temp files.
- `README.md`: Overhauled documentation with consumer vs pro features, criteria mapping table, test commands, and quickstart.
- `BUILD_NOTE.md`: Added Mermaid architecture diagram, model trade-offs, cost and latency analysis, and UI design decisions.
- `AI_USAGE.md`: Documented AI delegation, human verification, and 5 real bugs caught and resolved.
- `EVALUATION_REPORT.md`: Documented pose model benchmarks, empirical results on all 3 sample clips and fresh upload, unit tests (14/14 passing), and rule-change demo.

### Files Replaced / Deleted
*(None deleted — all original prototype modules preserved and non-destructively enhanced in place).*

---

## [Phase 1: Skill Engine Hardening] - 2026-11-12

### Added
- `skills/validator.py`: Runtime schema validator verifying root keys, required criterion fields, assessability enums, and valid views.

### Modified
- `skills/squat_standards.json`: Complete update to Version 2.0.0 with 10 criteria, exact page citations (**Ref pp. 1–35** / **PDF pp. 4–38**), textbook figures (**Figs 2-1 to 2-22**), non-assessable criteria list with filming advice, narrative-only exclusions, and explicit `[ASSUMPTION]` tags.
- `skills/squat_coach_skill.md`: Comprehensive prompt instructions and Starting Strength biomechanics reference guide.

---

## [Phase 0: Source Extraction & Audit Baseline] - 2026-11-12

### Added
- `docs/assignment.md`: Extracted hiring assignment requirements and rubric.
- `docs/reference.pdf`: Extracted 35-page Starting Strength Squat Chapter.
- `docs/AUDIT.md`: Complete audit of the codebase against assignment requirements.
- `evidence/audit_frames/`: 24 verification keyframes extracted across all 3 sample clips.
- `evidence/audit_frames_summary.json`: Metadata summary for audit keyframes.
- `docs/CHANGELOG.md`: Initial changelog ledger.
