"""
Verification on a Fresh User-Uploaded Video (Not in /samples)
Tests end-to-end pipeline robustness on an external lifter video.
"""

import os
import json
import shutil
from analyzer.tracker import SquatVideoTracker
from analyzer.biomechanics import SquatBiomechanicsAnalyzer
from analyzer.evaluator import SquatStandardsEvaluator
from analyzer.annotator import SquatVideoAnnotator

def run_fresh_upload_test():
    temp_dir = os.environ.get("TEMP", "C:/Users/cnuba/AppData/Local/Temp")
    source_video = os.path.join(temp_dir, "uploaded_4921641-hd_1066_1920_25fps.mp4")
    
    if not os.path.exists(source_video):
        print(f"Error: {source_video} not found")
        return

    print("==================================================")
    print("TESTING FRESH USER UPLOAD (NON-BUNDLED VIDEO)")
    print(f"Source file: {source_video}")
    print("==================================================")

    # 1. Properties inspection
    tracker = SquatVideoTracker()
    props = tracker.inspect_video_properties(source_video)
    print("Video Properties:", props)

    # 2. Tracking with YOLOv8s-pose + One-Euro filtering + velocity gating
    print("\nRunning Pose & Barbell Tracking...")
    t_res = tracker.process_video(source_video)
    print(f"Tracking completed: {t_res['total_frames']} frames")
    print(f"  Model used: {t_res['model_used']}")
    print(f"  Dominant facing: {t_res['dominant_facing']}")
    print(f"  Primary side: {t_res['primary_side']}")
    print(f"  Is side view: {t_res['is_side_view']} ({t_res['view_classification']})")
    print(f"  Framing issues: {t_res['framing_issues']}")

    # 3. Biomechanical analysis
    print("\nRunning Biomechanical Analysis & Rep Segmentation...")
    biomech = SquatBiomechanicsAnalyzer()
    b_res = biomech.analyze_session(t_res)
    print(f"Repetitions detected: {b_res['rep_count']}")

    # 4. Standards-grounded evaluation
    print("\nEvaluating against Starting Strength Standards...")
    evaluator = SquatStandardsEvaluator()
    e_res = evaluator.evaluate_session(t_res, b_res)
    print(f"Overall Grade: {e_res['session_summary']['grade']}")
    print(f"Headline: {e_res['session_summary']['headline']}")
    print(f"Primary coaching cue: {e_res['session_summary']['primary_coaching_cue']}")

    for r in e_res.get("repetitions", []):
        print(f"\n--- Rep {r['rep_id']} (Duration: {r['duration_seconds']:.2f}s, Bottom @ {r['bottom_timestamp']:.2f}s) ---")
        for f in r["findings"]:
            print(f"  [{f['result']}] {f['criterion_name']} -> {f['explanation']}")
            print(f"     Limitation/Uncertainty: {f.get('uncertainty_and_limitations', 'None')}")

    # 5. Annotation & Overlay Track generation
    os.makedirs("output", exist_ok=True)
    out_mp4 = "output/annotated_fresh_upload_4921641.mp4"
    out_json = "output/annotated_fresh_upload_4921641_overlay_track.json"
    print(f"\nRendering Annotated Video -> {out_mp4}...")
    annotator = SquatVideoAnnotator()
    annotator.generate_annotated_video(source_video, out_mp4, t_res, b_res, overlay_json_path=out_json)
    print("Annotated video saved successfully!")

    with open("output/evaluation_fresh_upload_4921641.json", "w", encoding="utf-8") as f:
        json.dump(e_res, f, indent=2)
    print("Saved evaluation JSON to: output/evaluation_fresh_upload_4921641.json")

if __name__ == "__main__":
    run_fresh_upload_test()
