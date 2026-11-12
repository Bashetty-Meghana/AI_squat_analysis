"""
Unit Test Suite: Standards Schema Validation & Guardrails
Tests that skills/squat_standards.json strictly satisfies the assignment criteria,
rejects malformed schemas, and enforces guardrails against unknown criterion IDs.
"""

import os
import json
import unittest
from skills.validator import SquatStandardsLoader, SkillValidationError, REQUIRED_CRITERION_FIELDS
from analyzer.evaluator import SquatStandardsEvaluator

STANDARDS_PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "squat_standards.json")

class TestStandardsValidation(unittest.TestCase):

    def test_standards_file_exists(self):
        self.assertTrue(os.path.exists(STANDARDS_PATH), f"Standards file missing at {STANDARDS_PATH}")

    def test_standards_loader_validates_successfully(self):
        loader = SquatStandardsLoader(STANDARDS_PATH)
        data = loader.data
        self.assertEqual(data["skill_name"], "starting_strength_squat_assessment")
        self.assertGreaterEqual(data["skill_version"], "2.0.0")
        self.assertEqual(len(data["criteria"]), 10)

    def test_every_criterion_has_required_schema_fields(self):
        loader = SquatStandardsLoader(STANDARDS_PATH)
        for crit in loader.data["criteria"]:
            for field in REQUIRED_CRITERION_FIELDS:
                self.assertIn(field, crit, f"Criterion {crit.get('id')} missing required field: {field}")
            self.assertIn(crit["assessable"], ["yes", "partial", "no"])
            self.assertIn(crit["view_required"], ["sagittal_side_view", "coronal_front_view", "transverse_top_view", "any"])
            self.assertIsInstance(crit["source_ref_pages"], list)
            self.assertGreater(len(crit["source_ref_pages"]), 0)
            self.assertIsInstance(crit["combined_pdf_pages"], list)
            self.assertGreater(len(crit["combined_pdf_pages"]), 0)
            self.assertIsInstance(crit["section_and_figures"], list)
            self.assertGreater(len(crit["section_and_figures"]), 0)
            self.assertIn("app_tolerance", crit)
            self.assertIn("is_assumption", crit["app_tolerance"])

    def test_non_assessable_side_view_criteria_present(self):
        loader = SquatStandardsLoader(STANDARDS_PATH)
        non_assessable = loader.data["non_assessable_side_view_criteria"]
        self.assertGreaterEqual(len(non_assessable), 5)
        for item in non_assessable:
            self.assertIn("criterion_name", item)
            self.assertIn("why_unassessable", item)
            self.assertIn("source_ref_pages", item)

    def test_narrative_only_exclusions_present(self):
        loader = SquatStandardsLoader(STANDARDS_PATH)
        exclusions = loader.data["narrative_only_do_not_assess"]
        self.assertGreaterEqual(len(exclusions), 4)
        topics = [x["topic"] for x in exclusions]
        self.assertTrue(any("Front Squat" in t for t in topics))
        self.assertTrue(any("ACL" in t or "Cruciate" in t for t in topics))
        self.assertTrue(any("Stretch-Reflex" in t for t in topics))

    def test_validator_rejects_missing_field(self):
        bad_data = {
            "skill_name": "broken_skill",
            "skill_version": "1.0.0",
            "source_document": {},
            "criteria": [
                {
                    "id": "depth_test",
                    "name": "Depth Test"
                }
            ],
            "non_assessable_side_view_criteria": [],
            "narrative_only_do_not_assess": []
        }
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(bad_data))
            tmp_path = f.name

        try:
            with self.assertRaises(SkillValidationError):
                SquatStandardsLoader(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_evaluator_guardrail_non_sagittal_view(self):
        evaluator = SquatStandardsEvaluator(STANDARDS_PATH)
        mock_tracking = {
            "is_side_view": False,
            "view_classification": "non_sagittal_or_frontal",
            "framing_issues": ["non_sagittal_perspective"],
            "dominant_facing": "frontal",
            "primary_side": "left"
        }
        mock_biomech = {
            "repetitions": [
                {
                    "rep_id": 1,
                    "start_timestamp": 0.0,
                    "bottom_timestamp": 2.0,
                    "end_timestamp": 4.0,
                    "bottom_frame": 60,
                    "duration_seconds": 4.0,
                    "depth": {"meets_standard": True, "depth_margin_px": 25.0, "depth_margin_cm": 5.0, "is_borderline": False},
                    "bar_path": {"meets_standard": True, "max_drift_px": 10.0, "max_drift_cm": 2.0, "max_drift_ratio": 0.05, "tracking_status": "OBSERVED"},
                    "back_angle": {"bottom_angle_deg": 48.0, "meets_standard": True, "is_too_vertical": False, "is_too_horizontal": False},
                    "hip_drive": {"meets_standard": True, "hip_ascent_delta_y": 50.0, "torso_angle_change_early": 2.0, "leads_with_chest": False, "hips_shoot_up": False},
                    "eye_gaze": {"meets_standard": True, "head_tilt_deg": 10.0, "looks_up": False},
                    "knee_position": {"meets_standard": True, "knee_travel_px": 20.0, "knee_travel_ratio": 0.20}
                }
            ],
            "calibration": {"cm_per_px": 0.2},
            "set_vbt_summary": {}
        }

        result = evaluator.evaluate_session(mock_tracking, mock_biomech)
        self.assertFalse(result["is_side_view"])
        self.assertGreater(len(result["global_issues"]), 0)
        self.assertEqual(result["session_summary"]["grade"], "UNSUITABLE_RECORDING")
        for r in result["repetitions"]:
            for f in r["findings"]:
                self.assertEqual(f["result"], "CANNOT_ASSESS", f"Criterion {f['criterion_id']} was not CANNOT_ASSESS in non-sagittal view!")

    def test_evaluator_guardrail_borderline_depth(self):
        evaluator = SquatStandardsEvaluator(STANDARDS_PATH)
        mock_tracking = {
            "is_side_view": True,
            "view_classification": "sagittal_side_view",
            "framing_issues": [],
            "dominant_facing": "right",
            "primary_side": "right"
        }
        mock_biomech = {
            "repetitions": [
                {
                    "rep_id": 1,
                    "start_timestamp": 0.0,
                    "bottom_timestamp": 2.0,
                    "end_timestamp": 4.0,
                    "bottom_frame": 60,
                    "duration_seconds": 4.0,
                    "depth": {"meets_standard": True, "depth_margin_px": 2.0, "depth_margin_cm": 0.4, "is_borderline": True, "measurement_status": "ESTIMATED"},
                    "bar_path": {"meets_standard": True, "max_drift_px": 10.0, "max_drift_cm": 2.0, "max_drift_ratio": 0.05, "tracking_status": "OBSERVED"},
                    "back_angle": {"bottom_angle_deg": 48.0, "meets_standard": True, "is_too_vertical": False, "is_too_horizontal": False},
                    "hip_drive": {"meets_standard": True, "hip_ascent_delta_y": 50.0, "torso_angle_change_early": 2.0, "leads_with_chest": False, "hips_shoot_up": False},
                    "eye_gaze": {"meets_standard": True, "head_tilt_deg": 10.0, "looks_up": False},
                    "knee_position": {"meets_standard": True, "knee_travel_px": 20.0, "knee_travel_ratio": 0.20}
                }
            ],
            "calibration": {"cm_per_px": 0.2},
            "set_vbt_summary": {}
        }

        result = evaluator.evaluate_session(mock_tracking, mock_biomech)
        depth_finding = next(f for f in result["repetitions"][0]["findings"] if f["criterion_id"] == "depth_below_parallel")
        self.assertEqual(depth_finding["result"], "CANNOT_ASSESS")
        self.assertIn("borderline", depth_finding["explanation"].lower())
        self.assertIn("ASSUMPTION", depth_finding["uncertainty_and_limitations"])

if __name__ == "__main__":
    unittest.main()
