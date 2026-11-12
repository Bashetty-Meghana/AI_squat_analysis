"""
FastAPI Server for IronPath AI Squat Form Coach
Wraps the decoupled /analyzer modules (tracker, biomechanics, evaluator, annotator)
into high-performance REST APIs with asynchronous job tracking, streaming media,
and full Starting Strength skill access.
"""

import os
import uuid
import json
import shutil
import threading
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from analyzer.tracker import SquatVideoTracker
from analyzer.biomechanics import SquatBiomechanicsAnalyzer
from analyzer.evaluator import SquatStandardsEvaluator
from analyzer.annotator import SquatVideoAnnotator
from skills.validator import SquatStandardsLoader

app = FastAPI(
    title="IronPath AI Squat Coach API",
    description="Biomechanical squat analysis grounded in Starting Strength (Mark Rippetoe)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory job store
JOBS: Dict[str, Dict[str, Any]] = {}
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "output", "uploads")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Shared analyzer instances
tracker = SquatVideoTracker()
biomech_analyzer = SquatBiomechanicsAnalyzer()
evaluator = SquatStandardsEvaluator()
annotator = SquatVideoAnnotator()

def process_job_worker(job_id: str, video_path: str):
    try:
        JOBS[job_id]["status"] = "PROCESSING"
        JOBS[job_id]["stage"] = "Inspecting video framing & properties"
        JOBS[job_id]["progress"] = 10

        props = tracker.inspect_video_properties(video_path)
        if not props:
            raise ValueError("Unable to read video file format.")

        JOBS[job_id]["stage"] = "Running YOLOv8 pose tracking & 1-Euro smoothing"
        JOBS[job_id]["progress"] = 25

        def track_cb(p):
            JOBS[job_id]["progress"] = 25 + int(p * 35)

        t_res = tracker.process_video(video_path, progress_callback=track_cb)

        JOBS[job_id]["stage"] = "Calculating Starting Strength diagnostic angles & VBT metrics"
        JOBS[job_id]["progress"] = 65
        b_res = biomech_analyzer.analyze_session(t_res)

        JOBS[job_id]["stage"] = "Evaluating criteria against Starting Strength standards"
        JOBS[job_id]["progress"] = 75
        e_res = evaluator.evaluate_session(t_res, b_res)

        JOBS[job_id]["stage"] = "Rendering browser-native H.264 video & JSON overlay track"
        JOBS[job_id]["progress"] = 85

        base_name = f"job_{job_id}"
        annot_mp4 = os.path.join(OUTPUT_DIR, f"{base_name}_annotated.mp4")
        overlay_json = os.path.join(OUTPUT_DIR, f"{base_name}_overlay_track.json")

        def annot_cb(p):
            JOBS[job_id]["progress"] = 85 + int(p * 14)

        annotator.generate_annotated_video(
            video_path,
            annot_mp4,
            t_res,
            b_res,
            overlay_json_path=overlay_json,
            progress_callback=annot_cb
        )

        # Load overlay track JSON
        overlay_data = {}
        if os.path.exists(overlay_json):
            with open(overlay_json, "r", encoding="utf-8") as f:
                overlay_data = json.load(f)

        # Compute consumer-friendly score & action tips
        consumer_summary = _build_consumer_summary(e_res, b_res)

        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["stage"] = "Complete"
        JOBS[job_id]["status"] = "DONE"
        JOBS[job_id]["results"] = {
            "evaluation": e_res,
            "overlay_track": overlay_data,
            "consumer_summary": consumer_summary,
            "video_filename": os.path.basename(video_path),
            "annotated_filename": os.path.basename(annot_mp4),
            "overlay_filename": os.path.basename(overlay_json)
        }

    except Exception as e:
        JOBS[job_id]["status"] = "FAILED"
        JOBS[job_id]["error"] = str(e)
        JOBS[job_id]["stage"] = "Failed"

def _build_consumer_summary(eval_res, bio_res):
    reps = eval_res.get("repetitions", [])
    if not reps or not eval_res.get("is_side_view", False):
        return {
            "score": 0,
            "grade": "CANNOT ASSESS",
            "grade_color": "#EF4444",
            "headline": "Video Angle Unsuitable",
            "fixes": [
                {
                    "type": "danger",
                    "title": "Move Camera to 90° Side View",
                    "desc": "We could not verify your squat from this perspective. Please place your phone at hip height, pointing directly at your side perpendicular to your stance."
                }
            ],
            "checklist": []
        }

    score = 100
    fixes = []
    checklist = []

    # Depth check
    depth_passes = [r["depth_metrics"]["meets_standard"] for r in reps if "depth_metrics" in r]
    pass_count = sum(depth_passes)
    total_reps = len(depth_passes)

    if pass_count == total_reps:
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "pass", "note": "Hit full depth on all reps!"})
        fixes.append({
            "type": "success",
            "title": "✅ Depth Was Spot On!",
            "desc": "You sank deep enough on every rep! Your hips dropped below your knees, engaging your full posterior chain and keeping your knees healthy."
        })
    elif pass_count > 0:
        score -= 15 * (total_reps - pass_count)
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "fail", "note": f"Passed {pass_count}/{total_reps} reps"})
        fixes.append({
            "type": "danger",
            "title": "🔴 Squat 2 Inches Deeper",
            "desc": f"You stopped slightly high on {total_reps - pass_count} of your {total_reps} reps. On your next set, sink your hips about 1 to 2 inches lower until your hip crease breaks below the top of your knee before standing up."
        })
    else:
        score -= 30
        checklist.append({"name": "Squat Depth (Low Enough)", "status": "fail", "note": "All reps were high"})
        fixes.append({
            "type": "danger",
            "title": "🔴 Squat Deeper (Below Knee Level)",
            "desc": "Your squats were high (above parallel). Next set, lower your hips until your hip crease drops below the top of your knee so your glutes and hamstrings can do the work."
        })

    # Head / Eye Gaze
    looking_up = any(any(f["criterion_id"] == "eye_gaze_cervical_spine" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if looking_up:
        score -= 10
        checklist.append({"name": "Head & Eye Direction", "status": "fail", "note": "Looking up at ceiling"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Look at the Floor, Not the Ceiling",
            "desc": "You're tilting your head up to look at the mirror or ceiling. That puts unwanted strain on your cervical spine. Keep your chin neutral and fix your eyes on a spot on the floor 4 to 5 feet ahead."
        })
    else:
        checklist.append({"name": "Head & Eye Direction", "status": "pass", "note": "Neutral neck, eyes down"})

    # Back Posture
    back_bad = any(any(f["criterion_id"] == "back_angle_inclination" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if back_bad:
        score -= 10
        checklist.append({"name": "Back Posture & Support", "status": "fail", "note": "Torso angle off target"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Maintain Torso Incline",
            "desc": "Your back angle shifted off target. Keep your chest tight and maintain a natural ~45° incline without collapsing forward or remaining vertical."
        })
    else:
        checklist.append({"name": "Back Posture & Support", "status": "pass", "note": "Flat, strong back"})

    # Foot Balance
    balance_bad = any(any(f["criterion_id"] == "bar_path_verticality_midfoot" and f["result"] == "DOES_NOT_MEET_STANDARD" for f in r["findings"]) for r in reps)
    if balance_bad:
        score -= 10
        checklist.append({"name": "Foot Balance (Midfoot)", "status": "fail", "note": "Bar drifted forward"})
        fixes.append({
            "type": "warning",
            "title": "🟡 Keep Weight Over Midfoot",
            "desc": "The barbell drifted slightly forward towards your toes. Keep the weight centered directly over your shoelaces to avoid wasting energy."
        })
    else:
        checklist.append({"name": "Foot Balance (Midfoot)", "status": "pass", "note": "Balanced over midfoot"})

    score = max(40, min(100, score))
    if score >= 90:
        grade = "EXCELLENT FORM (A)"
        grade_color = "#10B981"
        headline = "Outstanding Reps! Keep the Weight Moving."
    elif score >= 75:
        grade = "SOLID FORM (B+)"
        grade_color = "#38BDF8"
        headline = "Good Form with 1 or 2 Quick Fixes Needed."
    elif score >= 60:
        grade = "FAIR FORM (B)"
        grade_color = "#F59E0B"
        headline = "Solid Effort — Focus on Depth Before Adding More Weight."
    else:
        grade = "NEEDS WORK (C)"
        grade_color = "#EF4444"
        headline = "Form Needs Adjustment — Review the Action Tips Below."

    return {
        "score": score,
        "grade": grade,
        "grade_color": grade_color,
        "headline": headline,
        "fixes": fixes,
        "checklist": checklist
    }

# -----------------
# API Routes
# -----------------

@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "IronPath AI Squat Form Coach",
        "standards_version": evaluator.standards.get("skill_version", "2.0.0"),
        "active_jobs": len(JOBS)
    }

@app.get("/api/standards")
def get_standards():
    return evaluator.standards

@app.get("/api/samples")
def list_samples():
    return [
        {
            "id": "common_sample",
            "title": "Benchmark Squat Video (2 Reps)",
            "description": "Standard barbell squat performed in gym setting",
            "filename": "common_sample.mp4",
            "expected_outcome": "Passes back angle; high on rep 1, borderline depth on rep 2"
        },
        {
            "id": "unsuitable_front_view",
            "title": "Frontal Angle (Wrong Perspective)",
            "description": "Recorded from coronal perspective; depth cannot be validated",
            "filename": "unsuitable_front_view.mp4",
            "expected_outcome": "Triggers CAMERA_ANGLE_ERROR with CANNOT_ASSESS alert"
        },
        {
            "id": "unsuitable_poor_framing_occlusion",
            "title": "Framing Cutoff & Occlusion",
            "description": "Recorded inside rack with head and feet truncated",
            "filename": "unsuitable_poor_framing_occlusion.mp4",
            "expected_outcome": "Selectively gates bar path and eye gaze due to frame truncation"
        }
    ]

@app.post("/api/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    sample_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    job_id = str(uuid.uuid4())[:8]
    target_path = None

    if sample_id:
        sample_map = {
            "common_sample": "common_sample.mp4",
            "unsuitable_front_view": "unsuitable_front_view.mp4",
            "unsuitable_poor_framing_occlusion": "unsuitable_poor_framing_occlusion.mp4"
        }
        fname = sample_map.get(sample_id)
        if not fname:
            raise HTTPException(status_code=400, detail="Unknown sample_id")
        target_path = os.path.join(SAMPLES_DIR, fname)
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="Sample video file missing on disk")
    elif file:
        safe_name = f"{job_id}_{file.filename}"
        target_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        raise HTTPException(status_code=400, detail="Must provide either sample_id or video file")

    # Initialize job record
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "progress": 0,
        "stage": "Job queued for analysis",
        "results": None,
        "error": None
    }

    # Start processing in background thread
    t = threading.Thread(target=process_job_worker, args=(job_id, target_path), daemon=True)
    t.start()

    return {"job_id": job_id, "status": "QUEUED"}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "error": job["error"],
        "has_results": job["results"] is not None
    }

@app.get("/api/jobs/{job_id}/results")
def get_job_results(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    job = JOBS[job_id]
    if job["status"] != "DONE" or not job["results"]:
        raise HTTPException(status_code=400, detail=f"Job is not completed yet (status: {job['status']})")
    return job["results"]

@app.get("/api/media/{filename}")
def get_media_file(filename: str):
    # Search in output/, samples/, or output/uploads/
    for folder in [OUTPUT_DIR, SAMPLES_DIR, UPLOAD_DIR]:
        path = os.path.join(folder, filename)
        if os.path.exists(path) and os.path.isfile(path):
            return FileResponse(path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Media file not found")

# Mount built frontend if available
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
