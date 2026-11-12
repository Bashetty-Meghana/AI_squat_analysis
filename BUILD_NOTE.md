# Engineering Build Note: AI Squat Form Coach

## 1. System Architecture

The application is architected around a decoupled, modular pipeline separating computer vision tracking, biomechanical analysis, standard evaluation, and consumer presentation:

```mermaid
flowchart TD
    A["Raw Squat Video (MP4 / MOV / AVI)"] --> B["Video Ingestion & Properties Inspection"]
    B --> C["Pose Estimation Engine (YOLOv8s-pose with YOLOv8n fallback)"]
    B --> D["Barbell Sleeve & Collar Tracker (HSV Color + Hough Circle + Velocity Gating)"]
    
    C --> E["Adaptive One-Euro Temporal Filter (Casiez et al. 2012)"]
    D --> E
    
    E --> F["Landmark Status Tagging (OBSERVED / ESTIMATED / LOST)"]
    F --> G["Perspective & Framing Validator (Sagittal vs Frontal / Bounds Check)"]
    
    G --> H["Biomechanics & VBT Engine"]
    H --> H1["Rep Segmentation with Hysteresis"]
    H --> H2["Depth Plane Analysis (Hip Crease vs Patella)"]
    H --> H3["Starting Strength Diagnostic Angles (Back, Knee, Hip)"]
    H --> H4["Midfoot Balance Axis & Horizontal Bar Drift"]
    H --> H5["Velocity-Based Training (MCV, Peak, Tempo, Fatigue Loss %)"]
    
    H1 & H2 & H3 & H4 & H5 --> I["Standards Evaluation Engine (analyzer/evaluator.py)"]
    
    S["Decoupled Skill Standards (skills/squat_standards.json)"] --> J["Runtime Schema Validator (skills/validator.py)"]
    J --> I
    
    I --> K1["Grounded Assessment Findings (Citations, Feedback, Uncertainty Notes)"]
    I --> K2["Overall Form Score (0-100) & Next-Set Plain English Fixes"]
    I --> K3["Non-Assessable Criteria & Filming Advice"]
    
    I --> L["Video & Overlay Generation (analyzer/annotator.py)"]
    L --> M1["Playable H.264 MP4 (imageio-ffmpeg libx264 yuv420p)"]
    L --> M2["Synchronized JSON Overlay Track (output/*_overlay_track.json)"]
    
    K1 & K2 & K3 & M1 & M2 --> N["Dual-Mode Consumer & Pro Dashboard (Streamlit / app.py)"]
```

---

## 2. Model & Tool Choices and Trade-Offs

| Component | Choice | Alternatives Evaluated | Rationale & Trade-Offs |
|---|---|---|---|
| **Pose Estimation** | **YOLOv8s-pose (`yolov8s-pose.pt`, 22.4MB)** | YOLOv8n-pose (6.8MB), YOLOv8m-pose (50.8MB), MediaPipe Pose Heavy, RTMPose | **YOLOv8s-pose** strikes the sweet spot: 98.8% keypoint confidence, low jitter ($\pm 1.1$px with 1-Euro filter), and ~320ms CPU latency. YOLOv8n was lighter (110ms) but jittery near turnaround; YOLOv8m was too heavy for real-time CPU without GPU (~850–5,950ms). |
| **Temporal Smoothing** | **1-Euro Filter (`OneEuroFilter`)** | Moving Average, Savitzky-Golay, Butterworth, Kalman Filter | 1-Euro Filter adapts cutoff frequency based on movement speed: low cutoff at low velocity eliminates static jitter at bottom turnaround, while high cutoff during explosive ascent eliminates phase lag without temporal distortion. |
| **Barbell Tracking** | **Multi-modal Hub Tracker + Velocity Gating** | Pure YOLO bounding box, CSRT Tracker, Optical Flow | Standard pose models lack barbell keypoints. Our multi-modal tracker uses dual-range HSV color masks for red collars, circular Hough circles, and $80\text{ px/frame}$ velocity gating, preventing ceiling/gym ring false positives. |
| **Standards Definition** | **Decoupled JSON Schema + Validator (`validator.py`)** | Hardcoded python constants, raw markdown prompt | Decouples coaching rules from code. Changing a single threshold in `skills/squat_standards.json` dynamically alters the evaluation findings without code edits or video reprocessing (proven in `demo_rule_change.py`). |
| **Video Encoding** | **`imageio_ffmpeg` (H.264 / `libx264`)** | OpenCV `cv2.VideoWriter`, system FFmpeg CLI | Built-in binary dependency. Encodes browser-native MP4 with `yuv420p` pixel format and `+faststart` moov atom flags, ensuring instantaneous browser playback on desktop and mobile. |
| **User Interface** | **Streamlit Dual-Mode Dashboard (`app.py`)** | FastAPI + React (Vite/Next.js) | **Decision**: Enhanced Streamlit with high-end glassmorphic styling and dual-mode architecture. Preserves zero-breaking-change continuous runnable state while delivering both consumer simplicity (0-100 score, traffic-light checklist, next-set cards) and coach depth (VBT, citations, overlay JSON). |

---

## 3. Cost & Latency Analysis

### Deployment Economics:
- **Compute Infrastructure**: Runs completely local on standard CPU hardware (4 cores, 8GB RAM). Zero cloud GPU dependency required, though CUDA is automatically utilized if available.
- **Inference Cost**: **$0.00 / video**. Zero recurring LLM token fees or external vision API costs.
- **Processing Latency**:
  - 8-second 1080p squat video (236 frames): ~70 seconds end-to-end on CPU (tracking + biomechanics + evaluation + H.264 encoding + overlay JSON).
  - With standard T4/A10 GPU: < 4 seconds end-to-end (>60 FPS).
- **Scalability**: Can be packaged into Docker containers (see `Dockerfile` and `docker-compose.yml`) and scaled horizontally across serverless container platforms (e.g. AWS ECS / GCP Cloud Run / Railway).

---

## 4. Key Engineering Discoveries & Safeguards

1. **Boundary Margin Uncertainty Rule**:
   2D pose keypoints localize the skeletal hip joint center (greater trochanter proxy), which approximates the anatomical *crease of the shorts* (Point B, Figure 2-1). To prevent false confidence on borderline squats, depth margins within $\pm 0.8\text{ cm}$ are marked as `CANNOT_ASSESS` with `[ASSUMPTION]` notes rather than an ungrounded pass/fail.
2. **Selective Perspective Invalidation**:
   Frontal videos (`samples/unsuitable_front_view.mp4`) automatically trigger `CAMERA_ANGLE_ERROR` and mark all sagittal criteria as `CANNOT_ASSESS`, refusing invented precision. Poorly framed videos (`samples/unsuitable_poor_framing_occlusion.mp4`) selectively gate only the affected criteria (bar path, eye gaze) while preserving valid inferences.
3. **Automated Camera-Facing Side Switching**:
   Cumulative confidence scoring across all keypoints automatically identifies the camera-facing side (`left` vs `right`), ensuring seamless operation on fresh uploads regardless of lifter direction.
