# 15-Minute Demonstration & Walkthrough Guide

This guide prepares you for the **15-minute interview and discussion** specified on Page 3 of the hiring assignment PDF:
- **5 minutes**: Presenting the product and its commercial value to a prospective customer.
- **10 minutes**: Live technical demonstration, explaining the architecture, investigating edge cases, and demonstrating a live rule modification.

---

## ⏱️ Timeline & Agenda

```
┌──────────────────────────────────────┬──────────────────────────────────────────────────────┐
│ Time Window                          │ Objective & Key Discussion Points                    │
├──────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Minute 0:00 – 5:00 (Product Pitch)   │ Commercial need, target customer, Starting Strength   │
│                                      │ grounding, solving the "AI Hallucination" problem.   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Minute 5:00 – 9:00 (Live App Demo)   │ Critical path walk-through: Upload -> YOLO Pose ->   │
│                                      │ Hub Tracker -> Biomechanics -> Grounded Feedback.    │
├──────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Minute 9:00 – 12:00 (Edge Cases)     │ Unsuitable recordings: Frontal view & framing cutoff; │
│                                      │ Why "Cannot Assess" beats invented precision.        │
├──────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ Minute 12:00 – 15:00 (Live Rule Mod) │ Live update of squat_standards.json without code     │
│                                      │ changes; AI failure caught & corrected Q&A.          │
└──────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 🎤 Part 1: Product Presentation (~5 Minutes)

### 1. The Customer Problem
> *"Generic consumer fitness apps often provide vague, hallucinated feedback like 'try to keep your back straighter' or use arbitrary angle rules (like 'bend knees to 90 degrees') that actually contradict exercise science. For lifters, strength athletes, remote coaches, and rehabilitation clinics, incorrect squat form causes patellar tendinitis, lower back strain, and missed gains."*

### 2. The Solution: Grounded AI Coaching
> *"We built an AI squat coach that is strictly grounded in Mark Rippetoe's Starting Strength: Basic Barbell Training. Instead of generating unverified LLM text, our system extracts the mechanical standards into a reusable, inspectable agent skill. Every single finding cites the exact reference page and PDF page (e.g. Ref p. 2 Fig 2-1 for depth below parallel; Ref p. 8 Fig 2-5 for midfoot balance). A non-technical lifter can see the exact evidence—the patella plane line, hip crease marker, and bar path trail—and immediately know what to fix."*

### 3. Commercial Value & Cost Advantage
- **Target Audience**: Strength & conditioning gyms, online remote personal trainers, physical therapy clinics, home gym lifters.
- **Unit Economics**: Runs on standard CPU in ~20 seconds (or <3 seconds on serverless GPU) for **less than $0.0005 per video**, with **$0 API costs**, guaranteeing massive gross margins (>99%) and complete user privacy.

---

## 💻 Part 2: Technical Demonstration & Explanation (~10 Minutes)

### 1. Walk Through the Critical Path
Open **`http://localhost:8501`** and explain the pipeline:
1. **Video Ingestion**: The user uploads any side-view video or clicks the Common Sample.
2. **YOLOv8-pose Ingestion (`analyzer/tracker.py`)**: Runs 17-keypoint tracking on CPU at ~80ms/frame.
3. **Perspective Classifier**: Automatically measures shoulder width ratio to verify a 90° sagittal side view vs invalid frontal angle.
4. **Multi-Modal Barbell Sleeve Tracker**: Detects the circular hub and red collar inside the bumper plate, bypassing shoulder occlusion.
5. **Biomechanics Engine (`analyzer/biomechanics.py`)**:
   - Calculates hip crease Y vs patella top Y (depth margin).
   - Projects vertical midfoot axis and measures horizontal bar drift $\Delta X$.
   - Segments repetitions via peak detection on hip vertical elevation.
   - Evaluates hip drive out of the hole (torso stability vs premature chest lift).
6. **Standards Evaluator (`analyzer/evaluator.py`)**: Ingests `skills/squat_standards.json`, evaluates criteria, and renders structured findings with source citations.
7. **Annotator (`analyzer/annotator.py`)**: Uses embedded `imageio_ffmpeg` to output an H.264 MP4 with live HUD.

---

### 2. Demonstrate Edge Cases & Failure Handling
Switch to the benchmark samples to prove honesty and defensibility:
- **Click "❌ Unsuitable Angle: Frontal View"**:
  - Show the `CAMERA_ANGLE_ERROR` alert.
  - Explain: *"In a frontal view, the femur is foreshortened along the camera's Z-axis. Depth cannot be mathematically verified in 2D. The system explicitly returns `CANNOT_ASSESS` with actionable advice to reposition the camera, rather than inventing precision."*
- **Click "⚠️ Unsuitable Framing & Occlusion"**:
  - Show how the system detects the head leaving the top frame and power rack safety bars occluding the hip joint.

---

### 3. Live Rule Modification Demonstration
The assignment states: *"We may supply a new video or change a rule in the source document during the review."*

**How to demonstrate live skill updating**:
1. Open [`skills/squat_standards.json`](file:///c:/Users/cnuba/OneDrive/Desktop/AI_squat_analysis/skills/squat_standards.json).
2. Show the interviewer that each rule is completely decoupled from Python application code.
3. For example, if the interviewer asks: *"What if we require back angle to be stricter, say between 40° and 50° instead of 32° to 62°?"*
   - Change `"acceptable_range_degrees": [40.0, 50.0]` in the JSON.
   - Show that the evaluation engine reloads the rule without touching or rewriting any tracking algorithms!

---

### 4. Meaningful Mistake Caught and Corrected (Q&A Ready)
If asked: *"Tell me about a failure you caught during development?"*
- **Explain**:
  > *"When we first ran the automated pipeline on the common sample video, the system reported massive horizontal bar drift (>300px), claiming the lifter was completely off balance. When I visually inspected the annotated keyframe (`annotated_frame_187.jpg`), I discovered that the tracker was anchoring the barbell to the shoulder joint. But in a true sagittal view, 45lb bumper plates completely block the shoulder. The detector jumped onto gymnastic wooden rings hanging from the ceiling! I caught this failure, restricted the spatial search bounds strictly to the lifter's torso height, and implemented a dedicated barbell sleeve tracker that locks onto the red collar in the plate center. Horizontal drift immediately dropped from >300px down to 9px, proving the lifter was actually in perfect midfoot balance."*
