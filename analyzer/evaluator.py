"""
Standard-Grounded Evaluator Module
Translates biomechanical metrics and tracking evidence into structured findings
grounded strictly in Starting Strength (Mark Rippetoe).
"""

import json
import os

class SquatStandardsEvaluator:
    def __init__(self, standards_path=None):
        if standards_path is None:
            standards_path = os.path.join(os.path.dirname(__file__), "..", "skills", "squat_standards.json")
        with open(standards_path, "r", encoding="utf-8") as f:
            self.standards = json.load(f)
        self.criteria_by_id = {c["id"]: c for c in self.standards["criteria"]}

    def evaluate_session(self, tracking_result, biomechanics_result):
        """
        Performs holistic evaluation of session and per-rep analysis.
        """
        is_side_view = tracking_result.get("is_side_view", False)
        view_class = tracking_result.get("view_classification", "unknown")
        framing_issues = tracking_result.get("framing_issues", [])
        repetitions = biomechanics_result.get("repetitions", [])

        rep_evaluations = []
        global_issues = []

        # 1. Camera Angle & Framing Evaluation
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
                "actionable_cue": "Relocate camera to a pure side-view perpendicular to the lifter's stance."
            })

        if "head_upper_cutoff" in framing_issues:
            global_issues.append({
                "type": "FRAMING_CUTOFF",
                "title": "Lifter Head/Barbell Cut Off at Top of Frame",
                "message": "Lifter's head and/or barbell barbell path leaves the top of the video frame during lockout/unrack.",
                "actionable_cue": "Widen camera shot or step back to ensure the lifter is fully visible from head to feet."
            })

        if "feet_lower_cutoff" in framing_issues:
            global_issues.append({
                "type": "FRAMING_CUTOFF",
                "title": "Lifter Feet/Shoes Cut Off at Bottom of Frame",
                "message": "Lifter's feet and heels leave the lower frame boundary, preventing exact midfoot balance calibration.",
                "actionable_cue": "Tilt or lower the camera so the floor and entire shoe sole remain visible."
            })

        # 2. Per-Repetition Evaluation against Starting Strength Standards
        for rep in repetitions:
            rep_findings = self._evaluate_repetition(rep, is_side_view, framing_issues)
            rep_evaluations.append({
                "rep_id": rep["rep_id"],
                "duration_seconds": rep["duration_seconds"],
                "start_timestamp": rep["start_timestamp"],
                "bottom_timestamp": rep["bottom_timestamp"],
                "end_timestamp": rep["end_timestamp"],
                "findings": rep_findings,
                "summary": self._generate_rep_summary(rep_findings)
            })

        # 3. Overall Coaching Summary & Priority Focus
        session_summary = self._generate_session_summary(repetitions, rep_evaluations, global_issues)

        return {
            "standards_version": self.standards.get("skill_version", "1.0.0"),
            "source_document": self.standards.get("source_document", {}),
            "is_side_view": is_side_view,
            "view_classification": view_class,
            "global_issues": global_issues,
            "repetitions": rep_evaluations,
            "session_summary": session_summary,
            "non_assessable_side_view_criteria": self._get_non_assessable_report()
        }

    def _evaluate_repetition(self, rep, is_side_view, framing_issues):
        findings = []

        # If not side view, all sagittal planar criteria must be CANNOT_ASSESS
        if not is_side_view:
            for c_id in ["depth_below_parallel", "bar_path_verticality_midfoot", "back_angle_inclination", "hip_drive_initiation", "eye_gaze_cervical_spine", "knee_forward_travel_at_bottom"]:
                crit = self.criteria_by_id[c_id]
                findings.append({
                    "repetition_id": rep["rep_id"],
                    "criterion_id": c_id,
                    "criterion_name": crit["name"],
                    "source_section": crit["source_section"],
                    "source_citation": f"{crit['reference_citation']} ({crit['combined_pdf_citation']})",
                    "result": "CANNOT_ASSESS",
                    "supporting_evidence": {
                        "timestamp_seconds": rep["bottom_timestamp"],
                        "frame_index": rep["bottom_frame"],
                        "observed_measurement": "Non-sagittal camera angle",
                        "standard_benchmark": crit["standard_description"]
                    },
                    "explanation": "Cannot assess sagittal planar biomechanics from a frontal or off-angle view. Plane between hip crease and patella cannot be resolved.",
                    "actionable_feedback": "Record from a 90° perpendicular side view at hip height.",
                    "uncertainty_and_limitations": "Camera perspective violation prevents planar measurement."
                })
            return findings

        # Criterion 1: Squat Depth (Below Parallel)
        c_depth = self.criteria_by_id["depth_below_parallel"]
        depth_data = rep["depth"]
        if "lifter_not_detected" in framing_issues:
            res_depth = "CANNOT_ASSESS"
            exp_depth = "Hip or knee tracking lost during rep."
            fb_depth = c_depth["feedback_messages"]["cannot_assess"]
        elif depth_data["meets_standard"]:
            res_depth = "MEETS_STANDARD"
            exp_depth = f"Hip crease dropped {depth_data['depth_margin_px']:.1f}px below the top of the patella at the bottom turnaround (frame {rep['bottom_frame']})."
            fb_depth = c_depth["feedback_messages"]["meets_standard"]
        else:
            res_depth = "DOES_NOT_MEET_STANDARD"
            exp_depth = f"Hip crease remained {abs(depth_data['depth_margin_px']):.1f}px above the top of the patella (partial squat)."
            fb_depth = c_depth["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "depth_below_parallel",
            "criterion_name": c_depth["name"],
            "source_section": c_depth["source_section"],
            "source_citation": f"{c_depth['reference_citation']} ({c_depth['combined_pdf_citation']})",
            "result": res_depth,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Depth Margin = {depth_data['depth_margin_px']:+.1f}px ({'Below parallel' if depth_data['meets_standard'] else 'High / Above parallel'})",
                "standard_benchmark": "Hip crease must drop below the top of the patella (Figure 2-1)"
            },
            "explanation": exp_depth,
            "actionable_feedback": fb_depth,
            "uncertainty_and_limitations": "Calculated between detected hip joint and patella apex. Clothing folds or loose shorts may add minor variance."
        })

        # Criterion 2: Bar Path Verticality & Midfoot Balance
        c_bar = self.criteria_by_id["bar_path_verticality_midfoot"]
        bar_data = rep["bar_path"]
        if "feet_lower_cutoff" in framing_issues:
            res_bar = "CANNOT_ASSESS"
            exp_bar = "Feet cut off by camera frame; exact midfoot balance axis cannot be anchored."
            fb_bar = c_bar["feedback_messages"]["cannot_assess"]
        elif bar_data["meets_standard"]:
            res_bar = "MEETS_STANDARD"
            exp_bar = f"Barbell trajectory stayed balanced over midfoot (max horizontal drift: {bar_data['max_drift_px']:.1f}px, drift ratio: {bar_data['max_drift_ratio']:.2f})."
            fb_bar = c_bar["feedback_messages"]["meets_standard"]
        else:
            res_bar = "DOES_NOT_MEET_STANDARD"
            exp_bar = f"Excessive horizontal bar drift ({bar_data['max_drift_px']:.1f}px, drift ratio: {bar_data['max_drift_ratio']:.2f}) observed relative to midfoot."
            fb_bar = c_bar["feedback_messages"]["does_not_meet_standard"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "bar_path_verticality_midfoot",
            "criterion_name": c_bar["name"],
            "source_section": c_bar["source_section"],
            "source_citation": f"{c_bar['reference_citation']} ({c_bar['combined_pdf_citation']})",
            "result": res_bar,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Max Bar Drift = {bar_data['max_drift_px']:.1f}px, Normalized Drift Ratio = {bar_data['max_drift_ratio']:.2f}",
                "standard_benchmark": "Straight vertical line directly over midfoot balance point (Figure 2-5)"
            },
            "explanation": exp_bar,
            "actionable_feedback": fb_bar,
            "uncertainty_and_limitations": "Barbell sleeve center tracked visually with Kalman smoothing. Midfoot located halfway along shoe sole."
        })

        # Criterion 3: Back Angle at Bottom (~45° Inclination)
        c_back = self.criteria_by_id["back_angle_inclination"]
        back_data = rep["back_angle"]
        if back_data["meets_standard"]:
            res_back = "MEETS_STANDARD"
            exp_back = f"Torso inclination was {back_data['bottom_angle_deg']:.1f}° relative to horizontal, adhering to the ~45° low-bar model."
            fb_back = c_back["feedback_messages"]["meets_standard"]
        elif back_data["is_too_vertical"]:
            res_back = "DOES_NOT_MEET_STANDARD"
            exp_back = f"Torso was excessively vertical ({back_data['bottom_angle_deg']:.1f}°), resembling a front squat or high-bar position."
            fb_back = c_back["feedback_messages"]["does_not_meet_standard_vertical"]
        else:
            res_back = "DOES_NOT_MEET_STANDARD"
            exp_back = f"Torso collapsed too flat/horizontal ({back_data['bottom_angle_deg']:.1f}°), risking lower-back good morning."
            fb_back = c_back["feedback_messages"]["does_not_meet_standard_horizontal"]

        findings.append({
            "repetition_id": rep["rep_id"],
            "criterion_id": "back_angle_inclination",
            "criterion_name": c_back["name"],
            "source_section": c_back["source_section"],
            "source_citation": f"{c_back['reference_citation']} ({c_back['combined_pdf_citation']})",
            "result": res_back,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Back Angle = {back_data['bottom_angle_deg']:.1f}° to horizontal",
                "standard_benchmark": "Approximately 45° inclined relative to horizontal floor (Ref p. 22 Fig 2-13)"
            },
            "explanation": exp_back,
            "actionable_feedback": fb_back,
            "uncertainty_and_limitations": "Torso plane vector measured between hip joint and shoulder acromion. Shoulder position partially occluded by bumper plate."
        })

        # Criterion 4: Hip Drive Initiation
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
            "source_section": c_hd["source_section"],
            "source_citation": f"{c_hd['reference_citation']} ({c_hd['combined_pdf_citation']})",
            "result": res_hd,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Early Ascent Torso Shift = {hd_data['torso_angle_change_early']:+.1f}°, Hip Rise = {hd_data['hip_ascent_delta_y']:.1f}px",
                "standard_benchmark": "Hips shove straight up out of the bottom while preserving back angle (Ref p. 1, 23)"
            },
            "explanation": exp_hd,
            "actionable_feedback": fb_hd,
            "uncertainty_and_limitations": "Evaluated across initial 35% of ascent turnaround window."
        })

        # Criterion 5: Eye Gaze Direction
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
            "source_section": c_eye["source_section"],
            "source_citation": f"{c_eye['reference_citation']} ({c_eye['combined_pdf_citation']})",
            "result": res_eye,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Head/Neck Tilt = {eye_data['head_tilt_deg']:.1f}° ({'Neutral/Down' if eye_data['meets_standard'] else 'Looking up'})",
                "standard_benchmark": "Eyes fixed on floor 4-5 feet ahead with chin neutral (Ref pp. 23-25)"
            },
            "explanation": exp_eye,
            "actionable_feedback": fb_eye,
            "uncertainty_and_limitations": "Measured from ear, eye, and torso vectors. Hats or hair may add tracking noise."
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
            "source_section": c_knee["source_section"],
            "source_citation": f"{c_knee['reference_citation']} ({c_knee['combined_pdf_citation']})",
            "result": res_knee,
            "supporting_evidence": {
                "timestamp_seconds": rep["bottom_timestamp"],
                "frame_index": rep["bottom_frame"],
                "observed_measurement": f"Knee Forward Ratio = {knee_data['knee_travel_ratio']:.2f}",
                "standard_benchmark": "Knees just a little in front of the toes at bottom (Ref p. 22 Fig 2-13)"
            },
            "explanation": exp_knee,
            "actionable_feedback": fb_knee,
            "uncertainty_and_limitations": "Evaluates sagittal knee advance. Lateral knee tracking is non-assessable from side view."
        })

        return findings

    def _generate_rep_summary(self, findings):
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

    def _generate_session_summary(self, reps, rep_evals, global_issues):
        if global_issues:
            return {
                "grade": "UNSUITABLE_RECORDING",
                "reps_detected": len(reps),
                "headline": "Recording Unsuitable for Complete Biomechanical Assessment",
                "primary_coaching_cue": global_issues[0]["actionable_cue"]
            }

        if not reps:
            return {
                "grade": "NO_REPS_DETECTED",
                "reps_detected": 0,
                "headline": "No complete squat repetitions were detected in the video.",
                "primary_coaching_cue": "Ensure the lifter completes full squat cycles within the camera frame."
            }

        total_findings = [f for r in rep_evals for f in r["findings"]]
        meets_depth_count = sum(1 for r in rep_evals for f in r["findings"] if f["criterion_id"] == "depth_below_parallel" and f["result"] == "MEETS_STANDARD")
        
        # Priority feedback cue: Depth > Bar Path > Hip Drive > Back Angle > Eye Gaze
        priority_cue = "Keep up the great work! Maintain balance over midfoot and drive hips up."
        for crit_id in ["depth_below_parallel", "bar_path_verticality_midfoot", "hip_drive_initiation", "back_angle_inclination", "eye_gaze_cervical_spine"]:
            failed_f = next((f for f in total_findings if f["criterion_id"] == crit_id and f["result"] == "DOES_NOT_MEET_STANDARD"), None)
            if failed_f:
                priority_cue = failed_f["actionable_feedback"]
                break

        overall_grade = "COMPLIANT" if meets_depth_count == len(reps) else "NON_COMPLIANT_DEPTH"

        return {
            "grade": overall_grade,
            "reps_detected": len(reps),
            "reps_meeting_depth": meets_depth_count,
            "headline": f"{meets_depth_count} of {len(reps)} Reps Met Starting Strength Depth Standards",
            "primary_coaching_cue": priority_cue
        }

    def _get_non_assessable_report(self):
        """
        Returns the formal disclosure of criteria from Starting Strength that cannot be assessed
        from a side-view video, fulfilling the assignment requirement.
        """
        non_assessable_ids = [
            "stance_width_shoulder_heels",
            "toe_angle_30_degrees",
            "knees_shoved_out_lateral",
            "grip_and_wrist_straightness",
            "bar_placement_scapula_shelf",
            "rack_height_and_unrack"
        ]
        report = []
        for c_id in non_assessable_ids:
            crit = self.criteria_by_id[c_id]
            report.append({
                "criterion_id": c_id,
                "criterion_name": crit["name"],
                "source_section": crit["source_section"],
                "citation": f"{crit['reference_citation']} ({crit['combined_pdf_citation']})",
                "standard_description": crit["standard_description"],
                "status": "CANNOT_ASSESS_FROM_SIDE_VIEW",
                "explanation": crit["feedback_messages"]["cannot_assess"]
            })
        return report
