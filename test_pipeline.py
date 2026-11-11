"""
End-to-End Test Script
Runs tracker, biomechanics, evaluator, and annotator on sample videos.
"""

import os
import json
from analyzer.tracker import SquatVideoTracker
from analyzer.biomechanics import SquatBiomechanicsAnalyzer
from analyzer.evaluator import SquatStandardsEvaluator
from analyzer.annotator import SquatVideoAnnotator

def run_test(video_path, output_annotated_path):
    print(f"=== Testing video: {video_path} ===")
    tracker = SquatVideoTracker()
    props = tracker.inspect_video_properties(video_path)
    print("Video props:", props)

    print("Running tracking...")
    tracking_res = tracker.process_video(video_path)
    print(f"Tracking complete: {tracking_res['total_frames']} frames, side_view={tracking_res['is_side_view']}, facing={tracking_res['dominant_facing']}")

    print("Running biomechanics...")
    biomech = SquatBiomechanicsAnalyzer()
    biomech_res = biomech.analyze_session(tracking_res)
    print(f"Biomechanics complete: {biomech_res['rep_count']} reps detected.")

    print("Running standards evaluator...")
    evaluator = SquatStandardsEvaluator()
    eval_res = evaluator.evaluate_session(tracking_res, biomech_res)
    print("Session Grade:", eval_res["session_summary"]["grade"])
    print("Headline:", eval_res["session_summary"]["headline"])
    print("Primary cue:", eval_res["session_summary"]["primary_coaching_cue"])

    for r in eval_res["repetitions"]:
        print(f"\n--- Rep {r['rep_id']} (duration: {r['duration_seconds']:.2f}s, bottom frame: {r['bottom_timestamp']:.2f}s) ---")
        for f in r["findings"]:
            print(f"  [{f['result']}] {f['criterion_name']} -> {f['explanation']}")
            print(f"     Citation: {f['source_citation']}")

    print("\nRendering annotated video...")
    annotator = SquatVideoAnnotator()
    annotator.generate_annotated_video(
        video_path,
        output_annotated_path,
        tracking_res,
        biomech_res
    )
    print(f"Annotated video saved to: {output_annotated_path}")

    return eval_res

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    res_common = run_test("samples/common_sample.mp4", "output/annotated_common_sample.mp4")
    with open("output/evaluation_common_sample.json", "w", encoding="utf-8") as f:
        json.dump(res_common, f, indent=2)
    print("\nDone testing common sample!")
