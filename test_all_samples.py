"""
Comprehensive Test Script for All Sample Clips
Evaluates:
1. samples/common_sample.mp4
2. samples/unsuitable_front_view.mp4
3. samples/unsuitable_poor_framing_occlusion.mp4
Saves evaluations to output/ and prints detailed assessment status.
"""

import os
import json
from analyzer.tracker import SquatVideoTracker
from analyzer.biomechanics import SquatBiomechanicsAnalyzer
from analyzer.evaluator import SquatStandardsEvaluator
from analyzer.annotator import SquatVideoAnnotator

def test_clip(video_path, out_prefix):
    print(f"\n==========================================")
    print(f"Testing: {video_path}")
    print(f"==========================================")
    
    tracker = SquatVideoTracker()
    props = tracker.inspect_video_properties(video_path)
    print(f"Properties: {props['width']}x{props['height']} @ {props['fps']:.1f} fps ({props['duration']:.1f}s)")
    if props["validations"]:
        for v in props["validations"]:
            print(f"  [VALIDATION] {v['code']}: {v['message']}")

    print("Running tracking (YOLOv8s-pose + One-Euro filter + velocity gating)...")
    t_res = tracker.process_video(video_path)
    print(f"Tracking done: {t_res['total_frames']} frames")
    print(f"  Dominant facing: {t_res['dominant_facing']}")
    print(f"  Primary camera-facing side: {t_res['primary_side']}")
    print(f"  Is side view: {t_res['is_side_view']} ({t_res['view_classification']})")
    print(f"  Framing issues: {t_res['framing_issues']}")

    print("Running biomechanics...")
    biomech = SquatBiomechanicsAnalyzer()
    b_res = biomech.analyze_session(t_res)
    print(f"Biomechanics done: {b_res['rep_count']} reps detected.")

    print("Running evaluator...")
    evaluator = SquatStandardsEvaluator()
    e_res = evaluator.evaluate_session(t_res, b_res)
    print(f"Evaluation Grade: {e_res['session_summary']['grade']}")
    print(f"Headline: {e_res['session_summary']['headline']}")
    print(f"Primary cue: {e_res['session_summary']['primary_coaching_cue']}")

    for r in e_res.get("repetitions", []):
        print(f"\n  --- Rep {r['rep_id']} ---")
        for f in r["findings"]:
            print(f"    [{f['result']}] {f['criterion_name']} -> {f['explanation']}")

    # Annotate
    mp4_out = f"output/{out_prefix}.mp4"
    json_out = f"output/{out_prefix}_overlay_track.json"
    annotator = SquatVideoAnnotator()
    annotator.generate_annotated_video(video_path, mp4_out, t_res, b_res, overlay_json_path=json_out)
    print(f"Saved: {mp4_out} and {json_out}")

    eval_json = f"output/{out_prefix}_evaluation.json"
    with open(eval_json, "w", encoding="utf-8") as f:
        json.dump(e_res, f, indent=2)
    print(f"Saved evaluation: {eval_json}")

    return e_res

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    res_front = test_clip("samples/unsuitable_front_view.mp4", "eval_unsuitable_front")
    res_framing = test_clip("samples/unsuitable_poor_framing_occlusion.mp4", "eval_unsuitable_framing")
    print("\nAll unsuitable sample tests complete!")
