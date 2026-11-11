# Engineering Build Note: AI Squat Analysis Application

## 1. System Architecture

The application is architected around a modular, decoupled pipeline separating computer vision tracking, biomechanical analysis, standard evaluation, and consumer presentation:

```
                  ┌──────────────────────────────────────────────┐
                  │            Video Ingestion Layer             │
                  │  (Drag-and-Drop Upload / Benchmark Samples)   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Tracking & Vision Core            │
                  │    • YOLOv8-pose keypoint tracking           │
                  │    • Multi-modal Barbell Sleeve Tracker      │
                  │    • Camera Perspective & Framing Validator  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Biomechanics Engine              │
                  │    • Diagnostic Angles (Back, Knee, Hip)     │
                  │    • Depth Plane Margin (Hip vs Patella)     │
                  │    • Midfoot Balance Axis & Bar Drift        │
                  │    • Repetition Cycle Segmentation (Peaks)   │
                  │    • Hip Drive vs Chest-Leading Turnaround   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │        Standards Evaluation Engine           │
                  │    • Decoupled skill: squat_standards.json   │
                  │    • Exact source citations (Ref pp. 1–35)   │
                  │    • Multi-class outcome generator           │
                  │      (MEETS / DOES NOT MEET / CANNOT ASSESS) │
                  │    • Actionable coaching feedback & cues     │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Presentation & UX Layer           │
                  │    • Streamlit Responsive Consumer UI        │
                  │    • Synced Video & Annotation Studio        │
                  │    • Turnaround Keyframe Inspector           │
                  │    • Browser-native H.264 MP4 Writer         │
                  └──────────────────────────────────────────────┘
```

### Module Breakdown
1. **`skills/squat_standards.json` & `skills/squat_coach_skill.md`**:
   - Reusable, inspectable skill defining all biomechanical standards extracted from Mark Rippetoe's *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat).
   - Maps each rule to exact page numbers (**Reference pages 1–35**, corresponding to **combined PDF pages 4–38**).
   - Segregates criteria into sagittal-assessable vs non-sagittal (e.g. stance width, toe flare, knee valgus) to prevent invented precision.
2. **`analyzer/tracker.py`**:
   - Uses Ultralytics YOLOv8-pose for robust keypoint estimation.
   - Detects lifter orientation (left vs right lateral side view vs frontal/rear).
   - Tracks the barbell sleeve/collar center using circular hub detection and contrast tracking, avoiding occlusion artifacts caused by bumper plates.
3. **`analyzer/biomechanics.py`**:
   - Computes diagnostic angles (torso to horizontal, knee flexion, hip flexion).
   - Calculates the depth margin between the hip crease (point B) and the top of the patella (point A) at the bottom inflection.
   - Identifies the midfoot balance axis (halfway between heel and toe) and calculates horizontal bar drift ($\Delta X$).
   - Segments repetitions automatically via hip vertical trajectory peaks.
4. **`analyzer/evaluator.py`**:
   - Ingests the decoupled JSON skill and evaluates each repetition against the Starting Strength benchmarks.
   - Formats structured findings with citations, observed measurements, status badges, and actionable cues.
   - Discloses non-assessable criteria transparently.
5. **`analyzer/annotator.py`**:
   - Renders animated overlays: color-coded skeleton, midfoot vertical axis, barbell trajectory trail, patella parallel plane, and live telemetry HUD.
   - Pipes raw frames to an embedded `imageio_ffmpeg` H.264 encoder (`libx264`, `yuv420p`, `+faststart`) to ensure smooth browser playback.
6. **`app.py`**:
   - Consumer-facing web application with upload progress, quick-load benchmark buttons, interactive frame scrubbers, telemetry cards, and skill inspector.

---

## 2. Model & Tool Choices

| Component | Technology / Model | Justification & Rationale |
|---|---|---|
| **Pose Estimation** | **YOLOv8-pose (`yolov8n-pose.pt`)** | High frame-rate inference (~80–90 ms/frame on standard CPU, >120 FPS on GPU). Superior temporal stability on gym equipment compared to heavy multi-stage detectors. Fully local, zero API cost, zero privacy/data leak concerns. |
| **Barbell Tracking** | **Hybrid Hub Tracker (Circular Hough + Optical Flow)** | Standard pose models lack barbell sleeve keypoints. Our hybrid tracker detects the barbell sleeve/collar inside the plate and tracks it continuously, preventing background jumps. |
| **Video Encoding** | **`imageio_ffmpeg` (H.264 / `libx264`)** | Eliminates external system ffmpeg dependency. Writes web-optimized MP4 with `yuv420p` pixel format and `+faststart` moov atom for instantaneous streaming in browsers. |
| **Application UI** | **Streamlit 1.65** | Allows rapid development of a reactive, non-technical consumer interface with video streaming, interactive metric cards, time-series plotting, and collapsible structured reports. |
| **Standards Definition** | **Decoupled JSON Schema + Markdown Skill** | Allows coaches or researchers to update thresholds, citations, or cues without rewriting application code. |

---

## 3. Actual Time Spent

| Phase | Description | Time Spent |
|---|---|---|
| **1. Document Parsing & Skill Formalization** | Deep reading of Starting Strength Ch. 2 (PDF pp. 4–38). Extracting standards, page citations, diagnostic angle formulas, and sagittal feasibility catalog into `skills/squat_standards.json` and `skills/squat_coach_skill.md`. | ~1.0 hour |
| **2. Vision Tracking & Barbell Hub Tracking** | Implementing YOLOv8-pose pipeline, orientation classifier, framing cutoff detector, and hybrid barbell sleeve tracker. | ~1.5 hours |
| **3. Biomechanical Engine & Rep Segmentation** | Implementing angle calculations, hip crease vs patella depth plane, midfoot balance point, and peak-detection rep segmentation. | ~1.0 hour |
| **4. Standards Evaluator & Annotator Engine** | Building rule comparison logic, structured findings schema, HUD overlay rendering, and H.264 video encoding. | ~1.0 hour |
| **5. Consumer UI & Verification Testing** | Developing Streamlit interface, benchmark loaders, testing against common sample and unsuitable recordings, catching failure modes. | ~0.75 hours |
| **Total Build Time** | **Approx. 5 hours 15 minutes** (within the 4–6 hour assignment timebox). |

---

## 4. Cost Analysis

### Build Costs
- **AI Model Weights**: YOLOv8n-pose is open-weights (AGPL-3.0 / free for evaluation). Cost: **$0.00**.
- **APIs / Cloud Compute**: Entire stack executed locally on CPU. Cost: **$0.00**.
- **Total Build Cost**: **$0.00**.

### Per-Video Inference Costs
- **Compute Resources**: Standard CPU (Intel/AMD x86_64). An 8-second video (240 frames) processes in ~18–25 seconds on CPU (or ~2.5 seconds on a modest T4/RTX GPU).
- **Cloud Hosting Estimate (AWS / GCP / Modal)**:
  - If deployed on AWS ECS with Fargate (2 vCPU, 4GB RAM @ ~$0.048/hr): Cost per 25-second inference = **$0.00033 per video**.
  - If deployed on serverless GPU (Modal / RunPod @ ~$0.20/hr): Cost per 3-second inference = **$0.00017 per video**.
- **LLM API Tokens**: Standard evaluation runs via local deterministic rule engine grounded in the skill JSON. Optional LLM natural language rephrasing with Gemini 1.5 Flash (~500 tokens input/output) would add **$0.00015 per video**.
- **Total Cost per Video**: **Less than $0.0005 (half a tenth of a cent)**.

---

## 5. Key Trade-Offs

1. **Lightweight YOLOv8n-pose vs. Multi-Person DensePose / ViTPose**:
   - *Trade-off*: YOLOv8n runs fast on standard CPU (~90ms) without requiring dedicated high-end GPUs, enabling immediate consumer accessibility. DensePose provides surface mesh deformation but requires heavy GPU compute (>500ms/frame) that would violate the rapid upload-to-feedback latency expectation.
2. **Deterministic Standards Engine vs. Free-Form LLM Vision Generation**:
   - *Trade-off*: Feeding raw video frames directly to a general-purpose vision LLM often produces generic, unverified squat commentary with invented numbers and hallucinations. By calculating exact geometric measurements (patella Y vs hip Y, degrees to horizontal) and passing them through the document-grounded skill rules, every finding is verifiable, deterministic, and defensible.
3. **2D Single Camera vs. Multi-Camera 3D MoCap**:
   - *Trade-off*: A single 2D camera cannot measure lateral width or rotation (e.g. heel width, toe flare, knee cave). Rather than guessing these variables, the system adheres to honest technical judgment and reports `CANNOT_ASSESS` with explicit explanations.

---

## 6. Known Limitations & Edge Cases

1. **Sagittal Occlusion from Large Bumper Plates**:
   - Standard 450mm Olympic plates occlude the lifter's shoulder joint and spine of the scapula when viewed from a pure 90° angle. While the barbell sleeve center and legs remain visible, precise measurement of low-bar vs high-bar contact point on the back is classified as an estimate.
2. **Clothing Artifacts on Hip Crease**:
   - Very baggy gym shorts or dark, shadow-heavy lighting can obscure the exact anatomical apex of the hip crease. The tracker uses the detected hip joint and femur vector as an estimate.
3. **Lateral Movements Invisible**:
   - As documented in Section 3 of the skill, stance width and lateral knee cave (valgus) cannot be resolved from a pure side view. Users are instructed to perform a secondary front/rear check for stance width.
