# IronPath AI — Consumer & Pro Squat Form Coach

> **AI Barbell Form Coach Grounded in Mark Rippetoe's *Starting Strength: Basic Barbell Training* (Chapter 2: The Squat).**  
> Features a beginner-friendly Consumer Mode (Form Score 0–100, plain-English mistake breakdown, and next-set action cues) and a Pro / Coach Mode (Velocity-Based Training, diagnostic angles, textbook citations, and synchronized JSON overlay tracks).

---

## ⚡ Quickstart & Launch Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.11, 3.12, and 3.13)
- Node.js 18+ (Tested on v24.13.0) for the React frontend.
- No external FFmpeg installation needed (`imageio-ffmpeg` bundles an embedded binary automatically).

### Option 1: Modern React + Tailwind Frontend (FastAPI Backend)
Double-click `run_react.bat` or run in terminal:
```cmd
run_react.bat
```
*(On macOS/Linux: `./run_react.sh`)*  
The application will launch on **`http://localhost:8000`**.

### Option 2: Streamlit All-in-One Frontend
Double-click `run.bat` or run in terminal:
```cmd
run.bat
```
*(On macOS/Linux: `./run.sh`)*  
The application will launch on **`http://localhost:8501`**.

### Docker Launch
```bash
docker compose up --build
```
The application will open at `http://localhost:8501`.

---

## 🌟 Key Product Capabilities

### 1. Consumer-Grade Simplicity (Default View)
- **Overall Form Score (0–100)**: Instant, intuitive score graded from A to C.
- **Traffic-Light Checklist**: Clear PASS / FIX NEEDED indicators for depth, head/neck alignment, back posture, and foot balance.
- **Next-Set Plain English Fixes**: Action cards telling lifters exactly what to focus on before stepping back up to the barbell (e.g. *"🔴 Squat 2 inches deeper: Sink your hips until your crease drops below the top of your knee"*).
- **Turnaround Comparison Gallery**: Keyframe photos captured at lowest turnaround labeled with pass, fail, or borderline depth lines.

### 2. Pro / Coach Mode (Toggle with 1 Click)
- **Velocity-Based Training (VBT)**: Live Mean Concentric Velocity ($V_{\text{mean}}$) and Peak Velocity ($V_{\text{peak}}$) in $m/s$, rep tempo notation (Descent - Pause - Ascent), and neuromuscular fatigue loss % with estimated Reps In Reserve (RIR).
- **Starting Strength Citations**: Every finding maps to exact reference pages (**Ref pp. 1–35** / **PDF pp. 4–38**), textbook figures (**Figs 2-1 to 2-22**), and section headings.
- **Diagnostic Angle Inspection**: Torso inclination relative to floor (~45° standard), calibrated depth margins in physical centimeters ($cm$), and horizontal bar drift relative to midfoot.
- **Synchronized JSON Overlay Track**: Per-frame skeleton landmarks, barbell sleeve coordinates with status flags (`OBSERVED`, `ESTIMATED`, `LOST`), and rep turnaround markers exported to `output/*_overlay_track.json`.

### 3. Rigorous & Honest AI
- **Decoupled Skill Standards (`skills/squat_standards.json`)**: Runtime schema validated by `skills/validator.py`. Rule changes in JSON dynamically alter assessment results with **zero code edits and zero video reprocessing** (proven via `demo_rule_change.py`).
- **Low-Margin Boundary Uncertainty**: 2D pose detects the skeletal hip joint center as an anatomical approximation for the crease of the shorts (Point B, Figure 2-1). Margins within $\pm 0.8\text{ cm}$ are honestly flagged as `CANNOT_ASSESS` (borderline uncertain) rather than a false-confident pass/fail.
- **Perspective & Framing Detection**: Frontal recordings (`samples/unsuitable_front_view.mp4`) automatically trigger `CAMERA_ANGLE_ERROR` and mark all sagittal criteria as `CANNOT_ASSESS`. Framing cutoffs (`samples/unsuitable_poor_framing_occlusion.mp4`) selectively gate only the affected criteria.
- **Adaptive Temporal Smoothing**: `OneEuroFilter` (Casiez et al., CHI 2012) eliminates static turnaround jitter while maintaining zero phase lag during explosive ascent.

---

## 📋 Starting Strength Criteria Mapping

| Criterion | Category | Assessable? | Source Citation | Standard Pass Condition | App Tolerance Flag |
|---|---|---|---|---|---|
| **Squat Depth (Below Parallel)** | Biomechanics | **Yes** | Ref p. 2, 15, 17 (PDF pp. 5, 18, 20) \| Fig 2-1, 2-10 | Hip crease drops below top of patella | `[ASSUMPTION]` $\pm 0.8$ cm boundary uncertainty margin |
| **Back Angle at Bottom** | Kinematics | **Yes** | Ref p. 9, 12, 22 (PDF pp. 12, 15, 25) \| Fig 2-5, 2-13 | Approximately 45° inclined to horizontal | `[ASSUMPTION]` $32^\circ - 62^\circ$ acceptable range |
| **Bar Path Over Midfoot** | Mechanics | **Yes** | Ref p. 6, 8, 12 (PDF pp. 9, 11, 15) \| Fig 2-3, 2-5, 2-7 | Straight vertical line directly over midfoot | `[ASSUMPTION]` Horizontal drift $\le 16\%$ of shank length |
| **Hip Drive Initiation** | Kinematics | **Partial** | Ref p. 1, 22, 23 (PDF pp. 4, 25, 26) \| Fig 2-14 | Hips shove straight up while preserving back angle | `[PARTIALLY ASSESSABLE]` 2D kinematic proxy |
| **Eye Gaze & Cervical Spine** | Posture | **Partial** | Ref pp. 23–26 (PDF pp. 26–29) \| Fig 2-15, 2-16 | Eyes fixed on floor 4–5 ft ahead, neutral neck | `[PARTIALLY ASSESSABLE]` 2D ear-eye vector proxy |
| **Knee Position at Bottom** | Kinematics | **Yes** | Ref p. 21, 22 (PDF pp. 24, 25) \| Fig 2-13 | Knees just a little in front of toes | `[ASSUMPTION]` Forward travel ratio $\le 0.45$ shank length |
| **Feet Flat / Heels Down** | Balance | **Partial** | Ref p. 8, 12 (PDF pp. 11, 15) \| Fig 2-5, 2-7 | Entire sole remains flat against floor | `[PARTIALLY ASSESSABLE]` Heel lift $> 8$ px |
| **Back Flatness (Lumbar)** | Safety | **Partial** | Ref p. 19, 21 (PDF pp. 22, 24) \| Fig 2-11 | Normal anatomical lumbar lordosis | `[PARTIALLY ASSESSABLE]` Weak from 2D side view |
| **Unrack / Rack Safety** | Protocol | **Partial** | Ref p. 26, 31 (PDF pp. 29, 34) \| Fig 2-21 | Step back into stance; walk forward into hooks | Setup frames required |
| **Bar Placement on Scapula**| Equipment | **No** | Ref p. 18, 27 (PDF pp. 21, 30) \| Fig 2-17, 2-18 | Bar rests right below spine of scapula | `[CANNOT ASSESS]` Occluded by 450mm bumper plates |

### Non-Assessable from Side View (Coronal / Transverse Requirements):
1. **Stance Width (Heels Shoulder-Width)**: Ref p. 14, 20 (Fig 2-12) — Requires frontal or rear view.
2. **Toe Angle (~30° Flare)**: Ref p. 14, 20 (Fig 2-12) — Requires top or frontal view.
3. **Knees Shoved Out Laterally (Valgus Check)**: Ref p. 14, 33 — Requires frontal view.
4. **Grip Width & Thumbless Grip**: Ref pp. 27–28 (Fig 2-17) — Occluded by bumper plates.
5. **Rack Height & Hook Clearance**: Ref p. 30 (Fig 2-19) — Requires unrack clip framing.

---

## 🧪 Verification & Test Commands

### 1. Run Automated Unit Test Suite (14 Tests)
```bash
python -m unittest discover tests -v
```
*Validates standards schema, angle math, Y-axis coordinate consistency ($y_{\text{hip}} > y_{\text{patella}}$ below parallel), rep segmentation on synthetic signals, and guardrails.*

### 2. Run Decoupled Rule-Change Demonstration
```bash
python demo_rule_change.py
```
*Edits a rule in `skills/squat_standards.json`, re-runs evaluation on cached measurements with NO code edits and NO video reprocessing, and dynamically flips finding from `MEETS_STANDARD` to `DOES_NOT_MEET_STANDARD`.*

### 3. Run Pipeline on All 3 Sample Clips
```bash
python test_all_samples.py
```
*Tests `common_sample.mp4`, `unsuitable_front_view.mp4`, and `unsuitable_poor_framing_occlusion.mp4`, verifying `CANNOT_ASSESS` and warning alerts.*

### 4. Run Pipeline on Fresh External Upload (Not in /samples)
```bash
python test_fresh_upload.py
```
*Tests a non-bundled user-uploaded video (`uploaded_4921641-hd_1066_1920_25fps.mp4`), automatically detecting 3 reps with right-facing lifter orientation.*

---

## 📁 Repository Structure

```
AI_squat_analysis/
├── app.py                      # Consumer-friendly & Pro dual-mode Streamlit dashboard
├── requirements.txt            # Python dependencies (YOLOv8, OpenCV, imageio-ffmpeg, Streamlit)
├── run.bat                     # Windows 1-click launch script
├── run.sh                      # Linux/macOS launch script
├── Dockerfile                  # Container definition with pre-cached model weights
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Configuration template
├── BUILD_NOTE.md               # Mermaid architecture diagram, model trade-offs, cost analysis
├── AI_USAGE.md                 # Account of AI collaboration, verification, and bug fixes
├── EVALUATION_REPORT.md        # Quantitative benchmarks across samples and fresh uploads
├── DEMO_SCRIPT.md              # 5-min executive pitch + 10-min live demo walkthrough
├── README.md                   # Project documentation & criteria mapping
├── analyzer/
│   ├── tracker.py              # YOLOv8s pose tracking, 1-Euro filter, velocity-gated bar tracking
│   ├── biomechanics.py         # Diagnostic angles, VBT velocity, rep segmentation, borderline depth
│   ├── evaluator.py            # Starting Strength grounded evaluator with guardrails & LLM adapter
│   └── annotator.py            # Telemetry HUD, depth plane overlay, and JSON overlay track generator
├── skills/
│   ├── squat_standards.json    # Machine-readable Starting Strength skill schema (10 criteria)
│   ├── squat_coach_skill.md    # Natural language agent prompt instructions
│   └── validator.py            # Runtime schema validator and loader
├── tests/
│   ├── test_standards_validation.py # Schema and guardrail unit tests
│   └── test_biomechanics_math.py    # Angle math and rep segmentation unit tests
├── docs/
│   ├── assignment.md           # Full hiring assignment text and evaluation rubric
│   ├── reference.pdf           # Starting Strength Ch. 2 (Ref pp. 1-35 / PDF pp. 4-38)
│   ├── AUDIT.md                # Phase 0 audit against assignment requirements
│   └── CHANGELOG.md            # Replacement and modification ledger
├── samples/
│   ├── common_sample.mp4       # Official benchmark YouTube video
│   ├── unsuitable_front_view.mp4 # Frontal angle perspective test
│   └── unsuitable_poor_framing_occlusion.mp4 # Framing cutoff and rack occlusion test
└── output/
    ├── annotated_common_sample.mp4
    ├── annotated_common_sample_overlay_track.json
    ├── evaluation_common_sample.json
    ├── eval_unsuitable_front.mp4
    ├── eval_unsuitable_framing.mp4
    └── annotated_fresh_upload_4921641.mp4
```

---

## 📄 Key Documentation Links

- [docs/AUDIT.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/docs/AUDIT.md): Comprehensive Phase 0 audit against all hiring requirements.
- [BUILD_NOTE.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/BUILD_NOTE.md): Architecture diagrams, pose model trade-offs, and latency/cost analysis.
- [AI_USAGE.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/AI_USAGE.md): Transparent account of AI collaboration and 5 real bugs caught and resolved.
- [EVALUATION_REPORT.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/EVALUATION_REPORT.md): Empirical benchmark results across all 3 sample clips and fresh uploads.
- [DEMO_SCRIPT.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/DEMO_SCRIPT.md): 5-minute executive pitch and 10-minute live demonstration walkthrough.
- [docs/CHANGELOG.md](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/docs/CHANGELOG.md): Complete ledger of file modifications, additions, and enhancements.
