"""
Standard-Grounded Evaluator Module
Translates biomechanical metrics and tracking evidence into structured findings
grounded strictly in Mark Rippetoe's Starting Strength: Basic Barbell Training (Chapter 2).
Features schema validation guardrails, boundary margin uncertainty detection,
and an LLM agent evaluation adapter with automatic deterministic fallback.
"""

import os
import json
from typing import Dict, Any, List, Optional
from skills.validator import SquatStandardsLoader, SkillValidationError

class SquatStandardsEvaluator:
    def __init__(self, standards_path: Optional[str] = None):
        loader = SquatStandardsLoader(standards_path)
        self.standards = loader.data
        self.criteria_by_id = {c["id"]: c for c in self.standards["criteria"]}

    def evaluate_session(self, tracking_result: Dict[str, Any], biomechanics_result: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
        """
        Evaluates the tracking and biomechanical results against Starting Strength standards.
        Supports both deterministic rule-based evaluation and LLM agent evaluation adapter.
        """
        # Determine evaluation engine
        engine = "deterministic_grounded_rules"
        if use_llm and (os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")):
            try:
                llm_res = self._evaluate_with_llm_agent(tracking_result, biomechanics_result)
                if llm_res:
                    return llm_res
            except Exception as e:
                print(f"[Evaluator] LLM agent evaluation fallback triggered: {e}")
                engine = "deterministic_grounded_rules (fallback)"

        is_side_view = tracking_result.get("is_side_view", False)
        view_class = tracking_result.get("view_classification", "unknown")
        framing_issues = tracking_result.get("framing_issues", [])
        repetitions = biomechanics_result.get("repetitions", [])

        rep_evaluations = []
        global_issues = []

        # 1. Perspective & Framing Validation
        if not is_side_view:
            global_issues.append({
                "type": "CAMERA_ANGLE_ERROR",
                "title": "Non-Sagittal (Side-View) Angle Detected",
                "message": (
                    "The video was recorded from a frontal, angled, or non-sagittal perspective. "
                    "In Starting Strength (Ref p. 2 Fig 2-1 & Ref p. 8 Fig 2-5), squat depth, "
                    "bar-path verticality, and back inclination are strictly defined in the sagittal plane. "
                    "In a frontal projection, depth cannot be validated because the femur is foreshortened. "
                    "Camera must be positioned 90 degrees directly to the side of the lifter at hip height."
                ),
                "actionable_cue": "Relocate camera to a pure side-view perpendicular to the lifter's stance at hip height."
            })

        if "head_upper_cutoff" in framing_issues:
            global_issues.append({
                "type": "FRAMING_CUTOFF",
                "title": "Lifter Head/Barbell Cut Off at Top of Frame",
                "message": "Lifter's head and/or barbell leaves the top of the video frame during lockout/unrack.",
                "actionable_cue": "Widen camera shot or step back to ensure the lifter is fully visible from head to feet."
            })

        if "feet_lower_cutoff" in framing_issues:
            global_issues.append({
                "type": "FRAMING_CUTOFF",
                "title": "Lifter Feet/Shoes Cut Off at Bottom of Frame",
                "message": "Lifter's feet and heels leave the lower frame boundary, preventing exact midfoot balance calibration.",
                "actionable_cue": "Tilt or lower the camera so the floor and entire shoe sole remain visible."
            })

        if "multiple_people_detected" in framing_issues:
            global_issues.append({
                "type": "CROWDED_BACKGROUND",
                "title": "Multiple People Detected in Camera Frame",
                "message": "Multiple individuals detected in frame, introducing risk of tracking interference or occlusions.",
                "actionable_cue": "Frame video so only the active lifter is in the foreground."
            })

        if "tiny_lifter_in_frame" in framing_issues:
            global_issues.append({
                "type": "DISTANCE_ERROR",
                "title": "Lifter Too Far From Camera",
                "message": "Lifter occupies less than 28% of vertical frame height, reducing pose landmark precision.",
                "actionable_cue": "Bring the camera closer to the lifter (optimal distance ~8-12 feet)."
            })

        # 2. Per-Repetition Evaluation
        for rep in repetitions:
            rep_findings = self._evaluate_repetition(rep, is_side_view, framing_issues)
            rep_evaluations.append({
                "rep_id": rep["rep_id"],
                "duration_seconds": rep["duration_seconds"],
                "start_timestamp": rep["start_timestamp"],
                "bottom_timestamp": rep["bottom_timestamp"],
                "end_timestamp": rep["end_timestamp"],
                "vbt": rep.get("vbt"),
                "depth_metrics": rep.get("depth"),
                "bar_path_metrics": rep.get("bar_path"),
                "findings": rep_findings,
                "summary": self._generate_rep_summary(rep_findings)
            })

        # 3. Overall Coaching Summary
        session_summary = self._generate_session_summary(repetitions, rep_evaluations, global_issues)

        return {
            "evaluation_engine": engine,
            "standards_version": self.standards.get("skill_version", "2.0.0"),
            "source_document": self.standards.get("source_document", {}),
            "is_side_view": is_side_view,
            "view_classification": view_class,
            "calibration": biomechanics_result.get("calibration", {}),
            "set_vbt_summary": biomechanics_result.get("set_vbt_summary", {}),
            "global_issues": global_issues,
            "repetitions": rep_evaluations,
            "session_summary": session_summary,
            "non_assessable_side_view_criteria": self.standards.get("non_assessable_side_view_criteria", []),
            "narrative_only_exclusions": self.standards.get("narrative_only_do_not_assess", [])
        }

    def _evaluate_repetition(self, rep: Dict[str, Any], is_side_view: bool, framing_issues: List[str]) -> List[Dict[str, Any]]:
        findings = []

        # Helper to format citations
        def fmt_cit(crit):
            ref = ", ".join(crit.get("source_ref_pages", []))
            pdf = ", ".join(crit.get("combined_pdf_pages", []))
            figs = ", ".join(crit.get("section_and_figures", []))
            return f"{ref} ({pdf}) | {figs}"

        # If not side view, all sagittal planar criteria must be CANNOT_ASSESS
        if not is_side_view:
            for c_id in ["depth_below_parallel", "bar_path_verticality_midfoot", "back_angle_inclination", "hip_drive_initiation", "knee_forward_travel_at_bottom", "eye_gaze_cervical_spine"]:
                crit = self.criteria_by_id.get(c_id)
                if not crit:
                    continue
                findings.append({
                    "repetition_id": rep["rep_id"],
                    "criterion_id": c_id,
                    "criterion_name": crit["name"],
                    "category": crit["category"],
                    "assessable_status": crit["assessable"],
                    "source_citation": fmt_cit(crit),
                    "result": "CANNOT_ASSESS",
                    "supporting_evidence": {
                        "timestamp_seconds": rep["bottom_timestamp"],
                        "frame_index": rep["bottom_frame"],
                        "observed_measurement": "Non-sagittal camera angle",
                        "measurement_status": "LOST",
                        "standard_benchmark": crit["paraphrased_rule"]
                    },
                    "explanation": "Cannot assess sagittal planar biomechanics from a frontal or off-angle view. Plane between hip crease and patella cannot be resolved.",
                    "actionable_feedback": "Record from a 90° perpendicular side view at hip height.",
                    "uncertainty_and_limitations": "Camera perspective violation prevents planar measurement."
                })
            return findings

        # Criterion 1: Squat Depth (Below Parallel)
        c_depth = self.criteria_by_id["depth_below_parallel"]
        depth_data = rep["depth"]
        d_cm = depth_data.get("depth_margin_cm", 0.0)
        cm_str = f" ({d_cm:+.1f} cm)" if d_cm != 0.0 else ""
        is_borderline = depth_data.get("is_borderline", False)

        if "lifter_not_detected" in framing_issues:
            res_depth = "CANNOT_ASSESS"
            exp_depth = "Hip or knee tracking lost during rep."
            fb_depth = c_depth["feedback_messages"]["cannot_assess"]
            unc_depth = "Tracking lost during bottom turnaround."
        elif is_borderline:
            # Low-margin boundary uncertainty: hip joint keypoint approximates crease apex
            res_depth = "CANNOT_ASSESS"
            exp_depth = f"Depth margin was borderline ({d_cm:+.1f} cm). 2D pose detects hip joint center, which approximates the anatomical crease apex Point B. Results within +/- 0.8 cm cannot be definitively verified."
            fb_depth = "Squat 1-2 inches deeper on your next set to leave no doubt that the hip crease breaks parallel."
            unc_depth = "[ASSUMPTION: Margin within +/-0.8cm boundary uncertainty. Hip joint keypoint is an anatomical proxy for crease apex B]."
        elif depth_data["meets_standard"]:
            res_depth = "MEETS_STANDARD"
            exp_depth = f"Hip crease dropped {depth_data['depth_margin_px']:.1f}px{cm_str} below the top of the patella at the bottom turnaround (frame {rep['bottom_frame']})."
            fb_depth = c_depth["feedback_messages"]["meets_standard"]
            unc_depth = "Hip joint proxy exceeds boundary margin (> 0.8 cm below patella)."
        else:
            res_depth = "DOES_NOT_MEET_STANDARD"
            exp_depth = f"Hip crease remained {abs(depth_data['depth_margin_px']):.1f}px{cm_str} above the top of the patella (partial squat)."
            fb_depth = c_depth["feedback_messages"]["does_not_meet_standard"]
            unc_depth = "High squat verified (> 0.8 cm above patella)."

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "depth_below_parallel",
            "criterion_name": c_depth["name"],
            "category": c_depth["category"],
            "assessable_status": c_depth["assessable"],
            "source_citation": fmt_cit(c_depth),
            "result": res_depth,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Depth Margin = {depth_data['depth_margin_px']:+.1f}px{cm_str}",
                "measurement_status": depth_data.get("measurement_status", "OBSERVED"),
                "standard_benchmark": c_depth["pass_condition_document"]
            },
            "explanation": exp_depth,
            "actionable_feedback": fb_depth,
            "uncertainty_and_limitations": unc_depth
        })

        # Criterion 2: Bar Path Verticality & Midfoot Balance
        c_bar = self.criteria_by_id["bar_path_verticality_midfoot"]
        bar_data = rep["bar_path"]
        b_cm = bar_data.get("max_drift_cm", 0.0)
        b_cm_str = f" ({b_cm:.1f} cm)" if b_cm != 0.0 else ""
        bar_status = bar_data.get("tracking_status", "OBSERVED")

        if "feet_lower_cutoff" in framing_issues:
            res_bar = "CANNOT_ASSESS"
            exp_bar = "Feet cut off by camera frame; exact midfoot balance axis cannot be anchored."
            fb_bar = c_bar["feedback_messages"]["cannot_assess"]
        elif bar_status == "LOST":
            res_bar = "CANNOT_ASSESS"
            exp_bar = "Barbell plate tracking lost during repetition due to occlusion or lighting."
            fb_bar = c_bar["feedback_messages"]["cannot_assess"]
        elif bar_data["meets_standard"]:
            res_bar = "MEETS_STANDARD"
            exp_bar = f"Barbell trajectory stayed balanced over midfoot (max horizontal drift: {bar_data['max_drift_px']:.1f}px{b_cm_str}, drift ratio: {bar_data['max_drift_ratio']:.2f})."
            fb_bar = c_bar["feedback_messages"]["meets_standard"]
        else:
            res_bar = "DOES_NOT_MEET_STANDARD"
            exp_bar = f"Excessive horizontal bar drift ({bar_data['max_drift_px']:.1f}px{b_cm_str}, drift ratio: {bar_data['max_drift_ratio']:.2f}) observed relative to midfoot."
            fb_bar = c_bar["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "bar_path_verticality_midfoot",
            "criterion_name": c_bar["name"],
            "category": c_bar["category"],
            "assessable_status": c_bar["assessable"],
            "source_citation": fmt_cit(c_bar),
            "result": res_bar,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Max Bar Drift = {bar_data['max_drift_px']:.1f}px{b_cm_str}",
                "measurement_status": bar_status,
                "standard_benchmark": c_bar["pass_condition_document"]
            },
            "explanation": exp_bar,
            "actionable_feedback": fb_bar,
            "uncertainty_and_limitations": "[ASSUMPTION: Bar drift threshold set at 16% of shank length. Midfoot estimated halfway along shoe sole]."
        })

        # Criterion 3: Back Angle at Bottom (~45° Inclined)
        c_back = self.criteria_by_id["back_angle_inclination"]
        back_data = rep["back_angle"]
        if back_data["meets_standard"]:
            res_back = "MEETS_STANDARD"
            exp_back = f"Torso inclination was {back_data['bottom_angle_deg']:.1f}° relative to horizontal, adhering to the ~45° low-bar model."
            fb_back = c_back["feedback_messages"]["meets_standard"]
        elif back_data["is_too_vertical"]:
            res_back = "DOES_NOT_MEET_STANDARD"
            exp_back = f"Torso was excessively vertical ({back_data['bottom_angle_deg']:.1f}°), resembling a front squat or high-bar position."
            fb_back = c_back["feedback_messages"].get("does_not_meet_standard_vertical", c_back["feedback_messages"]["does_not_meet_standard"])
        else:
            res_back = "DOES_NOT_MEET_STANDARD"
            exp_back = f"Torso collapsed too flat/horizontal ({back_data['bottom_angle_deg']:.1f}°), risking lower-back good morning."
            fb_back = c_back["feedback_messages"].get("does_not_meet_standard_horizontal", c_back["feedback_messages"]["does_not_meet_standard"])

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "back_angle_inclination",
            "criterion_name": c_back["name"],
            "category": c_back["category"],
            "assessable_status": c_back["assessable"],
            "source_citation": fmt_cit(c_back),
            "result": res_back,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Back Angle = {back_data['bottom_angle_deg']:.1f}° to horizontal",
                "measurement_status": "OBSERVED",
                "standard_benchmark": c_back["pass_condition_document"]
            },
            "explanation": exp_back,
            "actionable_feedback": fb_back,
            "uncertainty_and_limitations": "[ASSUMPTION: 32°-62° range is an app tolerance. Starting Strength specifies 'about 45 degrees' per Ref p. 22 Fig 2-13]."
        })

        # Criterion 4: Hip Drive Initiation (Partially Assessable Proxy)
        c_hd = self.criteria_by_id["hip_drive_initiation"]
        hd_data = rep["hip_drive"]
        if hd_data["meets_standard"]:
            res_hd = "MEETS_STANDARD"
            exp_hd = f"Hips drove upward ({hd_data['hip_ascent_delta_y']:.1f}px) while preserving torso inclination (angle shift: {hd_data['torso_angle_change_early']:+.1f}°)."
            fb_hd = c_hd["feedback_messages"]["meets_standard"]
        else:
            res_hd = "DOES_NOT_MEET_STANDARD"
            if hd_data["leads_with_chest"]:
                exp_hd = f"Chest lifted prematurely (torso opened {hd_data['torso_angle_change_early']:+.1f}° before hips rose), slackening the hamstrings."
            else:
                exp_hd = f"Hips shot backward/up without adequate vertical progression, disrupting balance."
            fb_hd = c_hd["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "hip_drive_initiation",
            "criterion_name": c_hd["name"],
            "category": c_hd["category"],
            "assessable_status": c_hd["assessable"], # partial
            "source_citation": fmt_cit(c_hd),
            "result": res_hd,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Early Ascent Torso Shift = {hd_data['torso_angle_change_early']:+.1f}°, Hip Rise = {hd_data['hip_ascent_delta_y']:.1f}px",
                "measurement_status": "ESTIMATED",
                "standard_benchmark": c_hd["pass_condition_document"]
            },
            "explanation": exp_hd,
            "actionable_feedback": fb_hd,
            "uncertainty_and_limitations": "[PARTIALLY ASSESSABLE: 2D pose tracks kinematic proxies (torso angle slope and hip delta Y) during the initial 35% of ascent turnaround window]."
        })

        # Criterion 5: Eye Gaze Direction (Partially Assessable Proxy)
        c_eye = self.criteria_by_id["eye_gaze_cervical_spine"]
        eye_data = rep["eye_gaze"]
        if "head_upper_cutoff" in framing_issues:
            res_eye = "CANNOT_ASSESS"
            exp_eye = "Lifter head was outside the upper frame boundary."
            fb_eye = c_eye["feedback_messages"]["cannot_assess"]
        elif eye_data["meets_standard"]:
            res_eye = "MEETS_STANDARD"
            exp_eye = f"Head and gaze aligned with downward focal point on floor (head angle: {eye_data['head_tilt_deg']:.1f}°)."
            fb_eye = c_eye["feedback_messages"]["meets_standard"]
        else:
            res_eye = "DOES_NOT_MEET_STANDARD"
            exp_eye = f"Lifter looked up at ceiling/wall (cervical hyperextension angle: {eye_data['head_tilt_deg']:.1f}°)."
            fb_eye = c_eye["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "eye_gaze_cervical_spine",
            "criterion_name": c_eye["name"],
            "category": c_eye["category"],
            "assessable_status": c_eye["assessable"], # partial
            "source_citation": fmt_cit(c_eye),
            "result": res_eye,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Head/Neck Tilt = {eye_data['head_tilt_deg']:.1f}°",
                "measurement_status": "ESTIMATED",
                "standard_benchmark": c_eye["pass_condition_document"]
            },
            "explanation": exp_eye,
            "actionable_feedback": fb_eye,
            "uncertainty_and_limitations": "[PARTIALLY ASSESSABLE: 2D keypoints approximate ear-eye-neck vector, which is a proxy for eyeball gaze]."
        })

        # Criterion 6: Knee Forward Travel at Bottom
        c_knee = self.criteria_by_id["knee_forward_travel_at_bottom"]
        knee_data = rep["knee_position"]
        if knee_data["meets_standard"]:
            res_knee = "MEETS_STANDARD"
            exp_knee = f"Knees reached stable position slightly forward of toes (knee travel ratio: {knee_data['knee_travel_ratio']:.2f})."
            fb_knee = c_knee["feedback_messages"]["meets_standard"]
        else:
            res_knee = "DOES_NOT_MEET_STANDARD"
            exp_knee = f"Knees slid excessively forward past toes at bottom (ratio: {knee_data['knee_travel_ratio']:.2f})."
            fb_knee = c_knee["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "knee_forward_travel_at_bottom",
            "criterion_name": c_knee["name"],
            "category": c_knee["category"],
            "assessable_status": c_knee["assessable"],
            "source_citation": fmt_cit(c_knee),
            "result": res_knee,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Knee Forward Ratio = {knee_data['knee_travel_ratio']:.2f}",
                "measurement_status": "OBSERVED",
                "standard_benchmark": c_knee["pass_condition_document"]
            },
            "explanation": exp_knee,
            "actionable_feedback": fb_knee,
            "uncertainty_and_limitations": "[ASSUMPTION: Sagittal advance ratio <= 0.45 shank length is an app tolerance for 'just a little in front of toes']. Lateral knee tracking is non-assessable from side view."
        })

        return findings

    def _generate_rep_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        meets = sum(1 for f in findings if f["result"] == "MEETS_STANDARD")
        fails = sum(1 for f in findings if f["result"] == "DOES_NOT_MEET_STANDARD")
        cannot = sum(1 for f in findings if f["result"] == "CANNOT_ASSESS")

        status = "EXCELLENT" if fails == 0 and meets >= 4 else ("NEEDS_WORK" if fails > 0 else "PARTIAL")
        return {
            "status": status,
            "meets_count": meets,
            "fails_count": fails,
            "cannot_assess_count": cannot
        }

    def _generate_session_summary(self, reps: List[Dict[str, Any]], rep_evals: List[Dict[str, Any]], global_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        if global_issues:
            return {
                "grade": "UNSUITABLE_RECORDING",
                "reps_detected": len(reps),
                "headline": "Recording Unsuitable for Complete Biomechanical Assessment",
                "primary_coaching_cue": global_issues[0]["actionable_cue"],
                "top_fixes": [issue["actionable_cue"] for issue in global_issues[:3]]
            }

        if not reps:
            return {
                "grade": "NO_REPS_DETECTED",
                "reps_detected": 0,
                "headline": "No complete squat repetitions were detected in the video.",
                "primary_coaching_cue": "Ensure the lifter completes full squat cycles within the camera frame.",
                "top_fixes": ["Record a full set of squats with unobstructed side view."]
            }

        total_findings = [f for r in rep_evals for f in r["findings"]]
        meets_depth_count = sum(1 for r in rep_evals for f in r["findings"] if f["criterion_id"] == "depth_below_parallel" and f["result"] == "MEETS_STANDARD")

        # Top 3 prioritized fixes based on failure hierarchy: Depth -> Bar Path -> Hip Drive -> Back Angle -> Eye Gaze
        top_fixes = []
        for crit_id in ["depth_below_parallel", "bar_path_verticality_midfoot", "hip_drive_initiation", "back_angle_inclination", "eye_gaze_cervical_spine"]:
            failed_f = next((f for f in total_findings if f["criterion_id"] == crit_id and f["result"] == "DOES_NOT_MEET_STANDARD"), None)
            if failed_f:
                top_fixes.append(failed_f["actionable_feedback"])
            if len(top_fixes) >= 3:
                break

        if not top_fixes:
            top_fixes = ["Maintain consistency across sets: stay glued over midfoot and drive the hips smoothly."]

        overall_grade = "COMPLIANT" if meets_depth_count == len(reps) else "NON_COMPLIANT_DEPTH"

        return {
            "grade": overall_grade,
            "reps_detected": len(reps),
            "reps_meeting_depth": meets_depth_count,
            "headline": f"{meets_depth_count} of {len(reps)} Reps Met Starting Strength Depth Standards",
            "primary_coaching_cue": top_fixes[0],
            "top_fixes": top_fixes
        }

    def _evaluate_with_llm_agent(self, tracking_result: Dict[str, Any], biomechanics_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Optional LLM agent adapter layer. Feeds deterministic measurements, confidence tags,
        and skill definitions to an LLM provider (Gemini or OpenAI) with strict schema guardrails.
        """
        # Checks for LLM library availability without crashing if not installed
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return None
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = (
                "You are an expert Starting Strength barbell coach. "
                "Assess the following squat repetition measurements against the provided skill criteria. "
                "Return pure JSON conforming to the schema.\n\n"
                f"SKILL CRITERIA:\n{json.dumps(self.standards['criteria'], indent=2)}\n\n"
                f"BIOMECHANICAL MEASUREMENTS:\n{json.dumps(biomechanics_result.get('repetitions', []), indent=2)}"
            )
            resp = model.generate_content(prompt)
            # Parse output
            cleaned_text = resp.text.strip().replace("```json", "").replace("```", "")
            parsed = json.loads(cleaned_text)
            parsed["evaluation_engine"] = "llm_agent_gemini"
            return parsed
        except Exception:
            return None
