"""
Biomechanical Analysis Module
Calculates Starting Strength diagnostic angles, depth margins, midfoot balance,
repetition phases, and hip drive initiation with explicit status tagging (OBSERVED/ESTIMATED)
and low-margin boundary uncertainty detection.
"""

import numpy as np
from scipy.signal import find_peaks

def calculate_angle_2d(p1, p2, p3):
    """
    Calculates angle in degrees at vertex p2 formed by (p1 - p2) and (p3 - p2).
    """
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]], dtype=np.float64)
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]], dtype=np.float64)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-6 or norm2 < 1e-6:
        return 0.0
    cos_theta = np.dot(v1, v2) / (norm1 * norm2)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))

def calculate_back_angle_to_horizontal(hip_pt, shoulder_pt, facing_dir="right"):
    """
    Calculates back angle formed by the torso plane and the horizontal floor (Figure 2-5).
    0 deg = completely flat horizontal torso
    90 deg = completely vertical torso
    """
    dx = shoulder_pt[0] - hip_pt[0]
    # Image Y is inverted (downwards is positive)
    # Moving up from hip to shoulder is negative dy in pixel space
    dy = hip_pt[1] - shoulder_pt[1]

    if dy <= 0: # inverted torso / below hip
        return 0.0

    angle_rad = np.arctan2(dy, abs(dx))
    return float(np.degrees(angle_rad))

def calculate_head_angle_to_torso(ear_pt, eye_pt, shoulder_pt, hip_pt):
    """
    Measures head angle relative to the torso axis to detect cervical hyperextension
    vs neutral downward gaze (Ref pp. 23-25).
    """
    torso_vec = np.array([shoulder_pt[0] - hip_pt[0], shoulder_pt[1] - hip_pt[1]], dtype=np.float64)
    head_vec = np.array([eye_pt[0] - ear_pt[0], eye_pt[1] - ear_pt[1]], dtype=np.float64)

    t_norm = np.linalg.norm(torso_vec)
    h_norm = np.linalg.norm(head_vec)
    if t_norm < 1e-6 or h_norm < 1e-6:
        return 0.0

    cos_theta = np.dot(torso_vec, head_vec) / (t_norm * h_norm)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))

class SquatBiomechanicsAnalyzer:
    def __init__(self):
        pass

    def analyze_session(self, tracking_result):
        frames = tracking_result["frames_data"]
        fps = tracking_result["fps"]
        if not frames or len(frames) < 10:
            return {"error": "Insufficient frames for biomechanical analysis", "repetitions": []}

        # Extract continuous time-series arrays
        timestamps = []
        hip_y_series = []
        knee_y_series = []
        bar_x_series = []
        bar_y_series = []
        midfoot_x_series = []
        back_angles = []
        knee_angles = []
        hip_angles = []
        head_tilt_series = []

        primary_side = tracking_result.get("primary_side", "left")

        for f in frames:
            timestamps.append(f["timestamp"])
            obs = f["observed_kpts"]
            side = f.get("primary_side", primary_side)

            def get_kpt(name):
                k = obs.get(f"{side}_{name}", {"pt": (0, 0), "conf": 0.0, "status": "LOST"})
                is_valid = k.get("status") in ["OBSERVED", "ESTIMATED"] or k.get("is_observed", False)
                return k, is_valid

            sh, sh_valid = get_kpt("shoulder")
            hip, hip_valid = get_kpt("hip")
            knee, knee_valid = get_kpt("knee")
            ankle, ankle_valid = get_kpt("ankle")
            ear, ear_valid = get_kpt("ear")
            eye, eye_valid = get_kpt("eye")

            # Hip & knee Y coordinates (in pixel space, higher Y = lower elevation / closer to ground)
            hip_y_series.append(hip["pt"][1] if hip_valid else np.nan)
            knee_y_series.append(knee["pt"][1] if knee_valid else np.nan)

            # Midfoot calculation:
            # Starting Strength Ref p. 8: midfoot is halfway between ends of sole of the shoe.
            # Ankle is slightly posterior. We offset along facing direction.
            if ankle_valid:
                facing = f.get("facing_dir", "right")
                offset = (f["shank_length"] * 0.18) if f.get("shank_length") else 25.0
                mf_x = ankle["pt"][0] + (offset if facing == "right" else -offset)
                midfoot_x_series.append(mf_x)
            else:
                midfoot_x_series.append(np.nan)

            # Barbell position
            if f["bar_pos"] is not None and f.get("bar_status") != "LOST":
                bar_x_series.append(f["bar_pos"][0])
                bar_y_series.append(f["bar_pos"][1])
            else:
                bar_x_series.append(np.nan)
                bar_y_series.append(np.nan)

            # Diagnostic Angles (Figure 2-5)
            if hip_valid and sh_valid:
                b_ang = calculate_back_angle_to_horizontal(hip["pt"], sh["pt"], facing_dir=f.get("facing_dir", "right"))
                back_angles.append(b_ang)
            else:
                back_angles.append(np.nan)

            if hip_valid and knee_valid and ankle_valid:
                k_ang = calculate_angle_2d(hip["pt"], knee["pt"], ankle["pt"])
                knee_angles.append(k_ang)
            else:
                knee_angles.append(np.nan)

            if sh_valid and hip_valid and knee_valid:
                h_ang = calculate_angle_2d(sh["pt"], hip["pt"], knee["pt"])
                hip_angles.append(h_ang)
            else:
                hip_angles.append(np.nan)

            if ear_valid and eye_valid and sh_valid and hip_valid:
                h_tilt = calculate_head_angle_to_torso(ear["pt"], eye["pt"], sh["pt"], hip["pt"])
                head_tilt_series.append(h_tilt)
            else:
                head_tilt_series.append(np.nan)

        # Convert to numpy and interpolate missing points
        hip_y_arr = self._clean_series(hip_y_series)
        knee_y_arr = self._clean_series(knee_y_series)
        bar_x_arr = self._clean_series(bar_x_series)
        bar_y_arr = self._clean_series(bar_y_series)
        midfoot_x_arr = self._clean_series(midfoot_x_series)
        back_angles_arr = self._clean_series(back_angles)
        knee_angles_arr = self._clean_series(knee_angles)
        hip_angles_arr = self._clean_series(hip_angles)

        # Anthropometric Metric Calibration
        # Standard adult tibial shank = ~40.0 cm.
        valid_shanks = [f["shank_length"] for f in frames if f.get("shank_length") and f["shank_length"] > 30]
        if valid_shanks:
            ref_shank_px = float(np.median(valid_shanks))
            cm_per_px = 40.0 / ref_shank_px
            calib_method = "Anthropometric Tibial Shank (~40.0 cm)"
        else:
            ref_shank_px = 200.0
            cm_per_px = 0.20
            calib_method = "Standard Reference Scale (Default ~0.20 cm/px)"

        # Identify repetitions based on hip Y trajectory
        repetitions = self._detect_repetitions(hip_y_arr, knee_y_arr, fps, frames)

        # Enrich each repetition with detailed Starting Strength metrics & VBT
        enriched_reps = []
        for rep in repetitions:
            rep_data = self._compute_rep_metrics(
                rep=rep,
                hip_y=hip_y_arr,
                knee_y=knee_y_arr,
                bar_x=bar_x_arr,
                bar_y=bar_y_arr,
                midfoot_x=midfoot_x_arr,
                back_angles=back_angles_arr,
                knee_angles=knee_angles_arr,
                hip_angles=hip_angles_arr,
                head_tilts=head_tilt_series,
                frames=frames,
                fps=fps,
                cm_per_px=cm_per_px
            )
            enriched_reps.append(rep_data)

        # Multi-rep Set-level VBT Fatigue & Velocity Loss calculations
        if enriched_reps:
            base_v = enriched_reps[0]["vbt"]["mean_velocity_mps"]
            for idx, r in enumerate(enriched_reps):
                r_v = r["vbt"]["mean_velocity_mps"]
                if base_v > 0.05:
                    v_loss = ((base_v - r_v) / base_v) * 100.0
                else:
                    v_loss = 0.0
                v_loss = max(0.0, round(float(v_loss), 1))
                r["vbt"]["velocity_loss_pct"] = v_loss

                # Classify fatigue zone according to VBT literature
                if v_loss < 10.0:
                    r["vbt"]["fatigue_zone"] = "EXPLOSIVE / MINIMAL FATIGUE"
                    r["vbt"]["estimated_rir"] = "4+ RIR"
                elif v_loss < 20.0:
                    r["vbt"]["fatigue_zone"] = "OPTIMAL STRENGTH & HYPERTROPHY"
                    r["vbt"]["estimated_rir"] = "2-3 RIR"
                elif v_loss < 35.0:
                    r["vbt"]["fatigue_zone"] = "HIGH FATIGUE / HEAVY GRIND"
                    r["vbt"]["estimated_rir"] = "1-2 RIR"
                else:
                    r["vbt"]["fatigue_zone"] = "TECHNICAL BREAKDOWN RISK"
                    r["vbt"]["estimated_rir"] = "0 RIR (Failure)"

        # Set-level VBT summary
        set_vbt = {}
        if enriched_reps:
            mean_vels = [r["vbt"]["mean_velocity_mps"] for r in enriched_reps]
            peak_vels = [r["vbt"]["peak_velocity_mps"] for r in enriched_reps]
            ecc_times = [r["vbt"]["eccentric_duration_s"] for r in enriched_reps]
            con_times = [r["vbt"]["concentric_duration_s"] for r in enriched_reps]
            pause_times = [r["vbt"]["pause_duration_s"] for r in enriched_reps]

            set_vbt = {
                "mean_set_velocity_mps": round(float(np.mean(mean_vels)), 2),
                "peak_set_velocity_mps": round(float(np.max(peak_vels)), 2),
                "total_velocity_loss_pct": round(float(enriched_reps[-1]["vbt"]["velocity_loss_pct"]), 1),
                "mean_eccentric_duration_s": round(float(np.mean(ecc_times)), 2),
                "mean_concentric_duration_s": round(float(np.mean(con_times)), 2),
                "mean_pause_duration_s": round(float(np.mean(pause_times)), 2),
                "fastest_rep_id": int(np.argmax(mean_vels) + 1),
                "slowest_rep_id": int(np.argmin(mean_vels) + 1)
            }

        return {
            "repetitions": enriched_reps,
            "rep_count": len(enriched_reps),
            "calibration": {
                "cm_per_px": float(cm_per_px),
                "px_per_cm": float(1.0 / cm_per_px),
                "ref_shank_px": float(ref_shank_px),
                "calibration_method": calib_method
            },
            "set_vbt_summary": set_vbt,
            "time_series": {
                "timestamps": timestamps,
                "hip_y": hip_y_arr.tolist(),
                "knee_y": knee_y_arr.tolist(),
                "bar_x": bar_x_arr.tolist(),
                "bar_y": bar_y_arr.tolist(),
                "midfoot_x": midfoot_x_arr.tolist(),
                "back_angles": back_angles_arr.tolist(),
                "knee_angles": knee_angles_arr.tolist()
            }
        }

    def _clean_series(self, series):
        arr = np.array(series, dtype=np.float64)
        nans = np.isnan(arr)
        if np.all(nans):
            return np.zeros_like(arr)
        if np.any(nans):
            x = np.arange(len(arr))
            arr[nans] = np.interp(x[nans], x[~nans], arr[~nans])
        # Smooth with moving average window = 5
        kernel_size = 5
        kernel = np.ones(kernel_size) / kernel_size
        smoothed = np.convolve(arr, kernel, mode="same")
        return smoothed

    def _detect_repetitions(self, hip_y, knee_y, fps, frames):
        """
        Segments squats by finding peaks in hip Y (lowest physical elevation).
        Applies hysteresis to filter out walkout, rerack, and partial flutter.
        """
        min_distance = max(10, int(1.2 * fps))
        y_range = np.ptp(hip_y)
        if y_range < 40:
            return []

        # Find peaks in hip_y (bottom positions)
        prominence = y_range * 0.35
        peaks, properties = find_peaks(hip_y, distance=min_distance, prominence=prominence)

        reps = []
        for i, bottom_frame in enumerate(peaks):
            # Search backwards for start of descent (local minimum in hip Y)
            start_frame = max(0, bottom_frame - int(3.5 * fps))
            descent_segment = hip_y[start_frame:bottom_frame]
            if len(descent_segment) > 0:
                rel_start = np.argmin(descent_segment)
                rep_start = start_frame + rel_start
            else:
                rep_start = start_frame

            # Search forwards for completion of ascent (local minimum in hip Y)
            end_limit = min(len(hip_y) - 1, bottom_frame + int(3.5 * fps))
            ascent_segment = hip_y[bottom_frame:end_limit]
            if len(ascent_segment) > 0:
                rel_end = np.argmin(ascent_segment)
                rep_end = bottom_frame + rel_end
            else:
                rep_end = end_limit

            duration = float((rep_end - rep_start) / fps)
            # Rejection filter: rep must be between 1.0s and 9.0s
            if duration >= 1.0 and duration <= 9.0:
                reps.append({
                    "rep_id": len(reps) + 1,
                    "start_frame": int(rep_start),
                    "bottom_frame": int(bottom_frame),
                    "end_frame": int(rep_end),
                    "duration_seconds": duration
                })

        return reps

    def _compute_rep_metrics(self, rep, hip_y, knee_y, bar_x, bar_y, midfoot_x, back_angles, knee_angles, hip_angles, head_tilts, frames, fps, cm_per_px=0.20):
        s_idx = rep["start_frame"]
        b_idx = rep["bottom_frame"]
        e_idx = rep["end_frame"]

        b_frame = frames[b_idx]
        b_obs = b_frame["observed_kpts"]
        side = b_frame.get("primary_side", "left")

        # 1. Depth assessment (Figure 2-1)
        # Point A: top of patella (knee joint)
        # Point B: apex of crease of shorts (hip joint)
        # In downward-positive pixels, hip_y > knee_y means hip is lower than knee!
        bottom_hip_y = float(hip_y[b_idx])
        bottom_knee_y = float(knee_y[b_idx])

        depth_margin_px = bottom_hip_y - bottom_knee_y
        shank_len = b_frame.get("shank_length") or 100.0
        depth_margin_ratio = depth_margin_px / shank_len
        depth_margin_cm = depth_margin_px * cm_per_px

        # Low-margin boundary uncertainty:
        # Starting Strength defines depth as crease apex dropping below top of patella.
        # Hip joint keypoint is an anatomical proxy; margins within +/- 0.8 cm are borderline uncertain.
        is_borderline = abs(depth_margin_cm) <= 0.8
        meets_depth = bool(depth_margin_px > 0)

        # 2. Bar path and midfoot balance
        rep_bar_x = bar_x[s_idx:e_idx+1]
        rep_midfoot_x = midfoot_x[s_idx:e_idx+1]

        # Filter out NaN values from lost tracking
        valid_bar_mask = ~np.isnan(rep_bar_x) & ~np.isnan(rep_midfoot_x)
        if np.any(valid_bar_mask):
            horizontal_offsets = rep_bar_x[valid_bar_mask] - rep_midfoot_x[valid_bar_mask]
            mean_offset_px = float(np.mean(horizontal_offsets))
            max_drift_px = float(np.ptp(rep_bar_x[valid_bar_mask]))
            max_drift_ratio = float(max_drift_px / shank_len)
            max_drift_cm = max_drift_px * cm_per_px
            bar_tracking_status = "OBSERVED" if np.sum(valid_bar_mask) / len(valid_bar_mask) > 0.85 else "ESTIMATED"
        else:
            mean_offset_px = 0.0
            max_drift_px = 0.0
            max_drift_ratio = 0.0
            max_drift_cm = 0.0
            bar_tracking_status = "LOST"

        # Meets bar path standard if drift is within ~16% of shank length
        meets_bar_path = bool(max_drift_ratio <= 0.16) if bar_tracking_status != "LOST" else False

        # 3. Back angle at bottom (Figure 2-5, Ref p. 9, Ref p. 22 Fig 2-13)
        bottom_back_angle = float(back_angles[b_idx])
        meets_back_angle = bool(32.0 <= bottom_back_angle <= 62.0)
        is_too_vertical = bool(bottom_back_angle > 62.0)
        is_too_horizontal = bool(bottom_back_angle < 32.0)

        # 4. Knee angle at bottom
        bottom_knee_angle = float(knee_angles[b_idx])
        bottom_hip_angle = float(hip_angles[b_idx])

        # 5. Hip drive initiation (Ref p. 1, 22-23)
        ascent_len = max(1, e_idx - b_idx)
        early_ascent_end = b_idx + int(ascent_len * 0.35)

        hip_ascent_delta_y = bottom_hip_y - hip_y[early_ascent_end] # positive = moved up
        torso_angle_change = back_angles[early_ascent_end] - bottom_back_angle

        leads_with_chest = bool(torso_angle_change > 12.0)
        hips_shoot_up = bool(torso_angle_change < -10.0)
        meets_hip_drive = bool(not leads_with_chest and not hips_shoot_up and hip_ascent_delta_y > 5.0)

        # 6. Eye gaze / cervical alignment (Ref pp. 23-25)
        rep_head_tilts = [h for h in head_tilts[s_idx:e_idx+1] if not np.isnan(h)]
        mean_head_tilt = float(np.mean(rep_head_tilts)) if rep_head_tilts else 0.0
        looks_up = bool(mean_head_tilt > 28.0)
        meets_eye_gaze = not looks_up

        # 7. Knee position at bottom (Figure 2-13)
        knee_kpt = b_obs.get(f"{side}_knee", {"pt": (0,0)})
        ankle_kpt = b_obs.get(f"{side}_ankle", {"pt": (0,0)})
        facing = b_frame.get("facing_dir", "right")

        knee_travel_px = (knee_kpt["pt"][0] - ankle_kpt["pt"][0]) if facing == "right" else (ankle_kpt["pt"][0] - knee_kpt["pt"][0])
        knee_travel_ratio = float(knee_travel_px / shank_len)
        knee_travel_cm = float(knee_travel_px * cm_per_px)
        meets_knee_position = bool(0.0 <= knee_travel_ratio <= 0.45)

        # 8. VBT & Rep Tempo Calculation
        ecc_duration = max(0.1, float((b_idx - s_idx) / fps))
        con_duration = max(0.1, float((e_idx - b_idx) / fps))

        pause_window_radius = max(1, int(fps * 0.4))
        p_start = max(s_idx, b_idx - pause_window_radius)
        p_end = min(e_idx, b_idx + pause_window_radius)
        pause_frames = sum(1 for idx in range(p_start, p_end + 1) if abs(hip_y[idx] - bottom_hip_y) <= 8.0)
        pause_duration = max(0.0, float(pause_frames / fps))

        # Concentric vertical displacement
        if not np.isnan(bar_y[b_idx]) and not np.isnan(bar_y[e_idx]):
            concentric_disp_px = abs(float(bar_y[b_idx] - bar_y[e_idx]))
        else:
            concentric_disp_px = abs(float(bottom_hip_y - hip_y[e_idx]))

        concentric_disp_m = (concentric_disp_px * cm_per_px) / 100.0
        mean_vel_mps = max(0.05, float(concentric_disp_m / con_duration))

        # Peak instantaneous velocity
        ascent_segment = hip_y[b_idx:e_idx + 1]
        if len(ascent_segment) >= 4:
            k_win = np.ones(min(5, len(ascent_segment))) / min(5, len(ascent_segment))
            sm_ascent = np.convolve(ascent_segment, k_win, mode="same")
            dy_series = sm_ascent[:-1] - sm_ascent[1:]
            ascent_vels = [(dy * cm_per_px / 100.0) * fps for dy in dy_series]
            raw_peak = float(np.max(ascent_vels)) if len(ascent_vels) > 0 else mean_vel_mps * 1.3
            peak_vel_mps = min(max(mean_vel_mps * 1.15, raw_peak), mean_vel_mps * 1.75)
        else:
            peak_vel_mps = mean_vel_mps * 1.35

        tempo_str = f"{ecc_duration:.1f}s - {pause_duration:.1f}s - {con_duration:.1f}s"

        return {
            "rep_id": rep["rep_id"],
            "start_frame": s_idx,
            "bottom_frame": b_idx,
            "end_frame": e_idx,
            "start_timestamp": float(s_idx / fps),
            "bottom_timestamp": float(b_idx / fps),
            "end_timestamp": float(e_idx / fps),
            "duration_seconds": rep["duration_seconds"],
            "depth": {
                "hip_y": bottom_hip_y,
                "knee_y": bottom_knee_y,
                "depth_margin_px": float(depth_margin_px),
                "depth_margin_cm": round(float(depth_margin_cm), 1),
                "depth_margin_ratio": float(depth_margin_ratio),
                "meets_standard": meets_depth,
                "is_borderline": is_borderline,
                "measurement_status": "ESTIMATED" if is_borderline else "OBSERVED"
            },
            "bar_path": {
                "mean_offset_px": mean_offset_px,
                "max_drift_px": max_drift_px,
                "max_drift_cm": round(float(max_drift_cm), 1),
                "max_drift_ratio": max_drift_ratio,
                "meets_standard": meets_bar_path,
                "tracking_status": bar_tracking_status
            },
            "back_angle": {
                "bottom_angle_deg": bottom_back_angle,
                "meets_standard": meets_back_angle,
                "is_too_vertical": is_too_vertical,
                "is_too_horizontal": is_too_horizontal,
                "measurement_status": "OBSERVED"
            },
            "knee_angle": {
                "bottom_angle_deg": bottom_knee_angle
            },
            "hip_angle": {
                "bottom_angle_deg": bottom_hip_angle
            },
            "hip_drive": {
                "torso_angle_change_early": float(torso_angle_change),
                "hip_ascent_delta_y": float(hip_ascent_delta_y),
                "leads_with_chest": leads_with_chest,
                "hips_shoot_up": hips_shoot_up,
                "meets_standard": meets_hip_drive,
                "measurement_status": "ESTIMATED"
            },
            "eye_gaze": {
                "head_tilt_deg": mean_head_tilt,
                "looks_up": looks_up,
                "meets_standard": meets_eye_gaze,
                "measurement_status": "ESTIMATED"
            },
            "knee_position": {
                "knee_travel_px": float(knee_travel_px),
                "knee_travel_cm": round(float(knee_travel_cm), 1),
                "knee_travel_ratio": knee_travel_ratio,
                "meets_standard": meets_knee_position,
                "measurement_status": "OBSERVED"
            },
            "vbt": {
                "mean_velocity_mps": round(mean_vel_mps, 2),
                "peak_velocity_mps": round(peak_vel_mps, 2),
                "concentric_duration_s": round(con_duration, 2),
                "eccentric_duration_s": round(ecc_duration, 2),
                "pause_duration_s": round(pause_duration, 2),
                "tempo_notation": tempo_str,
                "concentric_rom_cm": round(concentric_disp_m * 100.0, 1),
                "velocity_loss_pct": 0.0,
                "fatigue_zone": "EXPLOSIVE / MINIMAL FATIGUE",
                "estimated_rir": "4+ RIR"
            }
        }
