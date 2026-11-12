"""
Skills Schema Validator & Runtime Loader
Validates skills/squat_standards.json ensuring every criterion satisfies
the strict assignment schema requirements.
"""

import json
import os
from typing import Dict, Any, List

REQUIRED_CRITERION_FIELDS = [
    "id",
    "name",
    "category",
    "paraphrased_rule",
    "source_ref_pages",
    "combined_pdf_pages",
    "section_and_figures",
    "view_required",
    "assessable",
    "metric_definition",
    "pass_condition_document",
    "document_gives_numeric_threshold",
    "app_tolerance",
    "feedback_messages"
]

VALID_ASSESSABLE_VALUES = ["yes", "partial", "no"]
VALID_VIEWS = ["sagittal_side_view", "coronal_front_view", "transverse_top_view", "any"]

class SkillValidationError(ValueError):
    pass

class SquatStandardsLoader:
    def __init__(self, standards_path: str = None):
        if standards_path is None:
            standards_path = os.path.join(os.path.dirname(__file__), "squat_standards.json")
        self.standards_path = standards_path
        self.data = self.load_and_validate()

    def load_and_validate(self) -> Dict[str, Any]:
        if not os.path.exists(self.standards_path):
            raise FileNotFoundError(f"Standards file not found: {self.standards_path}")
        
        with open(self.standards_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate root structure
        for root_key in ["skill_name", "skill_version", "source_document", "criteria", "non_assessable_side_view_criteria", "narrative_only_do_not_assess"]:
            if root_key not in data:
                raise SkillValidationError(f"Missing required top-level key: '{root_key}'")

        # Validate each criterion
        criteria = data.get("criteria", [])
        criterion_ids = set()

        for idx, crit in enumerate(criteria):
            for field in REQUIRED_CRITERION_FIELDS:
                if field not in crit:
                    raise SkillValidationError(f"Criterion #{idx} ('{crit.get('id', 'unknown')}') missing required field: '{field}'")

            c_id = crit["id"]
            if c_id in criterion_ids:
                raise SkillValidationError(f"Duplicate criterion id: '{c_id}'")
            criterion_ids.add(c_id)

            if crit["assessable"] not in VALID_ASSESSABLE_VALUES:
                raise SkillValidationError(f"Invalid assessable value '{crit['assessable']}' in '{c_id}'. Must be one of {VALID_ASSESSABLE_VALUES}")

            if crit["view_required"] not in VALID_VIEWS:
                raise SkillValidationError(f"Invalid view_required '{crit['view_required']}' in '{c_id}'. Must be one of {VALID_VIEWS}")

            # Verify app_tolerance explicitly flags assumption
            app_tol = crit.get("app_tolerance", {})
            if crit["document_gives_numeric_threshold"] is False and app_tol.get("is_assumption") is not True and app_tol.get("tolerance_type") != "none":
                raise SkillValidationError(f"Criterion '{c_id}' does not have a document numeric threshold, but app_tolerance is not flagged as an assumption!")

            # Verify feedback messages
            fb = crit["feedback_messages"]
            for m_key in ["meets_standard", "does_not_meet_standard", "cannot_assess"]:
                if m_key not in fb:
                    raise SkillValidationError(f"Criterion '{c_id}' feedback_messages missing '{m_key}'")

        return data

    def get_criterion(self, criterion_id: str) -> Dict[str, Any]:
        for c in self.data["criteria"]:
            if c["id"] == criterion_id:
                return c
        raise KeyError(f"Criterion '{criterion_id}' not found in standards.")

    def get_sagittal_assessable_criteria(self) -> List[Dict[str, Any]]:
        return [c for c in self.data["criteria"] if c["assessable"] in ["yes", "partial"] and c["view_required"] == "sagittal_side_view"]

    def get_non_assessable_criteria(self) -> List[Dict[str, Any]]:
        return self.data.get("non_assessable_side_view_criteria", [])

    def get_narrative_only_list(self) -> List[Dict[str, Any]]:
        return self.data.get("narrative_only_do_not_assess", [])

if __name__ == "__main__":
    loader = SquatStandardsLoader()
    print(f"Validation SUCCESS: {len(loader.data['criteria'])} criteria validated.")
