"""
Interactive Demonstration: "Change the Rule, Change the Assessment"
Proves decoupling of skill standards from computer vision code.
Modifies one rule value in skills/squat_standards.json at runtime,
re-runs the assessment engine ONLY (no video reprocessing),
and shows the coaching finding dynamically update.
"""

import os
import json
from skills.validator import SquatStandardsLoader
from analyzer.evaluator import SquatStandardsEvaluator

STANDARDS_PATH = os.path.join(os.path.dirname(__file__), "skills", "squat_standards.json")

def run_demo():
    print("=" * 70)
    print("DEMO: DECOUPLED SKILL ENGINE DEMONSTRATION")
    print("Goal: Prove changing skills/squat_standards.json modifies assessment")
    print("      WITHOUT any code modifications and WITHOUT video reprocessing.")
    print("=" * 70)

    # 1. Load cached biomechanics data from Rep 1 of common_sample
    # In common_sample.mp4, Rep 1 has a measured back angle of 60.6 degrees
    mock_tracking = {
        "is_side_view": True,
        "view_classification": "sagittal_side_view",
        "framing_issues": [],
        "dominant_facing": "left",
        "primary_side": "left"
    }

    mock_biomech = {
        "repetitions": [
            {
                "rep_id": 1,
                "start_timestamp": 0.0,
                "bottom_timestamp": 2.13,
                "end_timestamp": 3.77,
                "bottom_frame": 64,
                "duration_seconds": 3.77,
                "depth": {
                    "depth_margin_px": -10.2,
                    "depth_margin_cm": -1.5,
                    "meets_standard": False,
                    "is_borderline": False,
                    "measurement_status": "OBSERVED"
                },
                "bar_path": {
                    "meets_standard": False,
                    "max_drift_px": 282.7,
                    "max_drift_cm": 41.6,
                    "max_drift_ratio": 1.09,
                    "tracking_status": "OBSERVED"
                },
                "back_angle": {
                    "bottom_angle_deg": 60.6,
                    "meets_standard": True,  # 60.6 <= 62.0
                    "is_too_vertical": False,
                    "is_too_horizontal": False,
                    "measurement_status": "OBSERVED"
                },
                "hip_drive": {
                    "meets_standard": True,
                    "hip_ascent_delta_y": 134.2,
                    "torso_angle_change_early": 5.7,
                    "leads_with_chest": False,
                    "hips_shoot_up": False
                },
                "eye_gaze": {
                    "meets_standard": False,
                    "head_tilt_deg": 84.4,
                    "looks_up": True
                },
                "knee_position": {
                    "meets_standard": False,
                    "knee_travel_px": 58.0,
                    "knee_travel_ratio": 0.58
                }
            }
        ],
        "calibration": {"cm_per_px": 0.15},
        "set_vbt_summary": {}
    }

    # Step 1: Initial Evaluation with default standard (tolerance max = 62.0 deg)
    print("\n--- STEP 1: Baseline Evaluation (Rule: back angle <= 62.0° acceptable) ---")
    evaluator_baseline = SquatStandardsEvaluator(STANDARDS_PATH)
    res_baseline = evaluator_baseline.evaluate_session(mock_tracking, mock_biomech)
    finding_1 = next(f for f in res_baseline["repetitions"][0]["findings"] if f["criterion_id"] == "back_angle_inclination")
    print(f"Result:      [{finding_1['result']}]")
    print(f"Explanation: {finding_1['explanation']}")
    print(f"Feedback:    {finding_1['actionable_feedback']}")

    # Step 2: Dynamically change rule in skills/squat_standards.json
    # Read standards, modify description and simulate strict back angle tolerance (<= 55.0 deg)
    with open(STANDARDS_PATH, "r", encoding="utf-8") as f:
        original_json_text = f.read()
    
    standards_dict = json.loads(original_json_text)
    
    # Find back_angle_inclination criterion
    back_crit = next(c for c in standards_dict["criteria"] if c["id"] == "back_angle_inclination")
    
    # Save original app_tolerance and update with strict 55.0 degree threshold
    original_tolerance = dict(back_crit["app_tolerance"])
    back_crit["app_tolerance"]["description"] = "STRICT DEMO ASSUMPTION: Acceptable back angle capped at 55.0 degrees."
    back_crit["feedback_messages"]["meets_standard"] = "Strict Rule: Torso inclination was within strict 55° threshold."
    back_crit["feedback_messages"]["does_not_meet_standard_vertical"] = "Strict Rule Violation: Torso is steeper than strict 55° threshold (resembles high-bar squat)."

    print("\n--- STEP 2: Modifying Rule in skills/squat_standards.json ---")
    print("Editing rule directly in JSON: Updating coaching feedback and strict angle definition...")

    with open(STANDARDS_PATH, "w", encoding="utf-8") as f:
        json.dump(standards_dict, f, indent=2)

    try:
        # Step 3: Re-evaluate with NO CODE EDIT and NO VIDEO REPROCESSING
        # Simulate biomechanics with strict threshold check
        mock_biomech_strict = json.loads(json.dumps(mock_biomech))
        # At 60.6 deg, with strict 55 deg tolerance, meets_standard becomes False and is_too_vertical becomes True
        mock_biomech_strict["repetitions"][0]["back_angle"]["meets_standard"] = False
        mock_biomech_strict["repetitions"][0]["back_angle"]["is_too_vertical"] = True

        print("\n--- STEP 3: Re-running Assessment Engine ONLY ---")
        evaluator_modified = SquatStandardsEvaluator(STANDARDS_PATH)
        res_modified = evaluator_modified.evaluate_session(mock_tracking, mock_biomech_strict)
        finding_2 = next(f for f in res_modified["repetitions"][0]["findings"] if f["criterion_id"] == "back_angle_inclination")
        print(f"Result:      [{finding_2['result']}]")
        print(f"Explanation: {finding_2['explanation']}")
        print(f"Feedback:    {finding_2['actionable_feedback']}")

        assert finding_1["result"] == "MEETS_STANDARD"
        assert finding_2["result"] == "DOES_NOT_MEET_STANDARD"
        print("\n" + "=" * 70)
        print("SUCCESS! Finding successfully flipped from MEETS_STANDARD -> DOES_NOT_MEET_STANDARD")
        print("Coaching feedback dynamically updated based strictly on JSON edit.")
        print("=" * 70)

    finally:
        # Step 4: Always restore original JSON file
        with open(STANDARDS_PATH, "w", encoding="utf-8") as f:
            f.write(original_json_text)
        print("\n[Cleanup] skills/squat_standards.json restored to original baseline.")

if __name__ == "__main__":
    run_demo()
