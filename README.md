# AI Squat Analysis Application (Starting Strength Standards)

A consumer-facing AI application that accepts side-view videos of barbell squats, automatically tracks movement and barbell trajectory, segments repetitions, and provides structured biomechanical feedback strictly grounded in Mark Rippetoe's *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat).

---

## 🚀 Quickstart & Launch Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- No external FFmpeg installation required (`imageio-ffmpeg` bundles an embedded binary automatically).

### One-Click Launch (Windows)
Double-click `run.bat` or run in terminal:
```cmd
run.bat
```

### Linux / macOS Launch
```bash
chmod +x run.sh
./run.sh
```

### Manual Launch
```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```
The web application will open at `http://localhost:8501`.

---

## 🌟 Key Application Features

1. **Grounded Agent Skill (`skills/squat_standards.json` & `skills/squat_coach_skill.md`)**:
   - Every criterion cites exact source sections and reference pages (**Ref pp. 1–35** / **combined PDF pp. 4–38**).
   - Fully decoupled from application code, allowing coaches to inspect, refine, and update rules without rewriting the system.
2. **Side-View Feasibility & Honesty**:
   - Distinguishes sagittal-assessable criteria (Depth, Bar Path, Back Angle, Hip Drive, Eye Gaze) from non-assessable criteria (Stance Width, Toe Angle, Knee Valgus, Grip Width).
   - Explicitly returns `CANNOT_ASSESS` with explanations rather than inventing precision.
3. **Computer Vision Tracking Core**:
   - Pose estimation via YOLOv8-pose (`yolov8n-pose.pt`).
   - Multi-modal barbell sleeve tracker combining circular hub detection, dual-range color masking, and temporal optical flow, overcoming 450mm bumper plate occlusions.
4. **Interactive Consumer Experience**:
   - Drag-and-drop video upload with real-time progress indicators.
   - Quick-load benchmark buttons (Common Sample Video, Frontal View Unsuitable Sample, Framing Cutoff Sample).
   - Side-by-side video playback with live telemetry HUD, skeleton overlay, barbell path trail, and midfoot balance line.
   - Turnaround keyframe inspection gallery.
   - Per-rep telemetry cards and kinematic trajectory time-series charts.
   - Structured findings with status badges (`MEETS STANDARD`, `DOES NOT MEET STANDARD`, `CANNOT ASSESS`).

---

## 📁 Repository Structure

```
AI_squat_analysis/
├── app.py                      # Consumer-facing Streamlit application
├── requirements.txt            # Dependency specifications
├── run.bat                     # Windows one-click launch script
├── run.sh                      # Linux/macOS launch script
├── test_pipeline.py            # Automated end-to-end test script
├── BUILD_NOTE.md               # Architecture, time spent, costs, trade-offs, limitations
├── AI_USAGE.md                 # Account of AI usage, delegation, inspection, bug caught/fixed
├── EVALUATION_REPORT.md        # Verification evidence on common sample and unsuitable recordings
├── README.md                   # Setup guide and application documentation
├── analyzer/
│   ├── tracker.py              # Pose detection, orientation classifier, barbell sleeve tracker
│   ├── biomechanics.py         # Diagnostic angles, depth margin, midfoot balance, rep segmentation
│   ├── evaluator.py            # Standard-grounded evaluation engine with source citations
│   └── annotator.py            # Overlay rendering and H.264 MP4 browser-ready video generation
├── skills/
│   ├── squat_standards.json    # Machine-readable Starting Strength skill schema
│   └── squat_coach_skill.md    # Natural language agent prompt instructions
├── samples/
│   ├── common_sample.mp4       # Official hiring prompt YouTube video
│   ├── unsuitable_front_view.mp4 # Frontal angle perspective violation test
│   └── unsuitable_poor_framing_occlusion.mp4 # Framing cutoff and rack occlusion test
└── output/
    ├── annotated_common_sample.mp4
    ├── annotated_unsuitable_front.mp4
    ├── annotated_unsuitable_framing.mp4
    └── evaluation_common_sample.json
```

---

## 📋 Starting Strength Criteria Mapping

| Criterion | Source Section | Reference Citation | Combined PDF Citation | Sagittal Feasibility |
|---|---|---|---|---|
| **Squat Depth** | *Squat Depth – Safety and Importance* | Ref p. 2 (Fig 2-1), Ref p. 15 | PDF pp. 5, 18 | **Fully Assessable** |
| **Bar Path & Midfoot Balance** | *Loaded Human Movement* | Ref p. 6, Ref p. 8 (Fig 2-5) | PDF pp. 9, 11 | **Fully Assessable** |
| **Back Angle at Bottom** | *Diagnostic Angles* | Ref p. 9 (Fig 2-5), Ref p. 22 | PDF pp. 12, 25 | **Fully Assessable** |
| **Hip Drive Initiation** | *Generating Hip Drive* | Ref p. 1, Ref p. 23 (Fig 2-14) | PDF pp. 4, 26 | **Fully Assessable** |
| **Eye Gaze & Cervical Spine** | *Eye Gaze Direction* | Ref pp. 23–25 (Fig 2-15) | PDF pp. 26–28 | **Fully Assessable** |
| **Knee Position at Bottom** | *Figure 2-13 & 2-22* | Ref p. 22, Ref p. 32 | PDF pp. 25, 35 | **Partially Assessable** |
| **Stance Width** | *Generating Hip Drive* | Ref p. 14, Ref p. 20 (Fig 2-12) | PDF pp. 17, 23 | **Cannot Assess** (Requires Front View) |
| **Toe Angle (~30°)** | *Generating Hip Drive* | Ref p. 14, Ref p. 20 (Fig 2-12) | PDF pp. 17, 23 | **Cannot Assess** (Requires Top/Front View) |
| **Lateral Knee Tracking (Valgus)**| *Squat Depth* | Ref p. 14, Ref p. 33 | PDF pp. 17, 36 | **Cannot Assess** (Requires Front View) |
| **Grip Width & Wrist Alignment**| *Adding the Bar* | Ref pp. 27–28 (Fig 2-17, 2-18) | PDF pp. 30–31 | **Cannot Assess** (Occluded by Plates) |

---

## 📄 Key Project Reports

- [BUILD_NOTE.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/BUILD_NOTE.md): Architecture, model selection, actual time spent (~5h 15m), cost breakdown (<$0.0005/video), key trade-offs, and known limitations.
- [AI_USAGE.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/AI_USAGE.md): Transparent account of what was delegated to AI, what was verified, and the meaningful barbell sleeve occlusion failure caught and corrected.
- [EVALUATION_REPORT.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/EVALUATION_REPORT.md): Quantitative and visual empirical evidence on the common sample video and unsuitable recordings.
