"""
Biomechanical Analysis Module
Calculates Starting Strength diagnostic angles, depth margins, midfoot balance,
repetition phases, and hip drive initiation.
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

        primary_side = tracking_result.get("dominant_facing", "right")

        for f in frames:
            timestamps.append(f["timestamp"])
            obs = f["observed_kpts"]
            side = f.get("primary_side", "left")

            sh = obs.get(f"{side}_shoulder", {"pt": (0,0), "is_observed": False})
            hip = obs.get(f"{side}_hip", {"pt": (0,0), "is_observed": False})
            knee = obs.get(f"{side}_knee", {"pt": (0,0), "is_observed": False})
            ankle = obs.get(f"{side}_ankle", {"pt": (0,0), "is_observed": False})
            ear = obs.get(f"{side}_ear", {"pt": (0,0), "is_observed": False})
            eye = obs.get(f"{side}_eye", {"pt": (0,0), "is_observed": False})

            # Hip & knee Y coordinates (in pixel space, higher Y = lower elevation / closer to ground)
            hip_y_series.append(hip["pt"][1] if hip["is_observed"] else np.nan)
            knee_y_series.append(knee["pt"][1] if knee["is_observed"] else np.nan)

            # Midfoot calculation:
            # Starting Strength Ref p. 8: "the midfoot is exactly halfway between either end of the sole of the shoe"
            # Ankle is slightly behind midfoot. We estimate midfoot along the facing direction.
            if ankle["is_observed"]:
                facing = f.get("facing_dir", "right")
                offset = (f["shank_length"] * 0.18) if f.get("shank_length") else 25.0
                mf_x = ankle["pt"][0] + (offset if facing == "right" else -offset)
                midfoot_x_series.append(mf_x)
            else:
                midfoot_x_series.append(np.nan)

            # Barbell position
            if f["bar_pos"] is not None:
                bar_x_series.append(f["bar_pos"][0])
                bar_y_series.append(f["bar_pos"][1])
            else:
                bar_x_series.append(np.nan)
                bar_y_series.append(np.nan)

            # Diagnostic Angles (Figure 2-5)
            if hip["is_observed"] and sh["is_observed"]:
                b_ang = calculate_back_angle_to_horizontal(hip["pt"], sh["pt"], facing_dir=f.get("facing_dir", "right"))
                back_angles.append(b_ang)
            else:
                back_angles.append(np.nan)

            if hip["is_observed"] and knee["is_observed"] and ankle["is_observed"]:
                k_ang = calculate_angle_2d(hip["pt"], knee["pt"], ankle["pt"])
                knee_angles.append(k_ang)
            else:
                knee_angles.append(np.nan)

            if sh["is_observed"] and hip["is_observed"] and knee["is_observed"]:
                h_ang = calculate_angle_2d(sh["pt"], hip["pt"], knee["pt"])
                hip_angles.append(h_ang)
            else:
                hip_angles.append(np.nan)

            if ear["is_observed"] and eye["is_observed"] and sh["is_observed"] and hip["is_observed"]:
                h_tilt = calculate_head_angle_to_torso(ear["pt"], eye["pt"], sh["pt"], hip["pt"])
                head_tilt_series.append(h_tilt)
            else:
                head_tilt_series.append(np.nan)

        # Convert to numpy and interpolate sporadic missing points
        hip_y_arr = self._clean_series(hip_y_series)
        knee_y_arr = self._clean_series(knee_y_series)
        bar_x_arr = self._clean_series(bar_x_series)
        midfoot_x_arr = self._clean_series(midfoot_x_series)
        back_angles_arr = self._clean_series(back_angles)
        knee_angles_arr = self._clean_series(knee_angles)
        hip_angles_arr = self._clean_series(hip_angles)

        # Identify repetitions based on hip Y trajectory
        repetitions = self._detect_repetitions(hip_y_arr, knee_y_arr, fps, frames)

        # Enrich each repetition with detailed Starting Strength metrics
        enriched_reps = []
        for rep in repetitions:
            rep_data = self._compute_rep_metrics(
                rep=rep,
                hip_y=hip_y_arr,
                knee_y=knee_y_arr,
                bar_x=bar_x_arr,
                midfoot_x=midfoot_x_arr,
                back_angles=back_angles_arr,
                knee_angles=knee_angles_arr,
                hip_angles=hip_angles_arr,
                head_tilts=head_tilt_series,
                frames=frames,
                fps=fps
            )
            enriched_reps.append(rep_data)

        return {
            "repetitions": enriched_reps,
            "rep_count": len(enriched_reps),
            "time_series": {
                "timestamps": timestamps,
                "hip_y": hip_y_arr.tolist(),
                "knee_y": knee_y_arr.tolist(),
                "bar_x": bar_x_arr.tolist(),
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
        Descent starts when hip moves downward; ascent finishes when hip returns to lockout.
        """
        # Minimum rep duration ~ 1.2s -> int(1.2 * fps) frames
        min_distance = max(10, int(1.2 * fps))
        
        # Calculate vertical displacement range
        y_range = np.ptp(hip_y)
        if y_range < 40: # minimal movement
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

            reps.append({
                "rep_id": i + 1,
                "start_frame": int(rep_start),
                "bottom_frame": int(bottom_frame),
                "end_frame": int(rep_end),
                "duration_seconds": float((rep_end - rep_start) / fps)
            })

        return reps

    def _compute_rep_metrics(self, rep, hip_y, knee_y, bar_x, midfoot_x, back_angles, knee_angles, hip_angles, head_tilts, frames, fps):
        s_idx = rep["start_frame"]
        b_idx = rep["bottom_frame"]
        e_idx = rep["end_frame"]

        b_frame = frames[b_idx]
        b_obs = b_frame["observed_kpts"]
        side = b_frame.get("primary_side", "left")

        # 1. Depth assessment (Figure 2-1)
        # Point A: top of patella (knee joint)
        # Point B: apex of crease of shorts (hip joint)
        # Hip crease must drop BELOW top of patella:
        # In image pixels (Y increases downward), hip_y > knee_y means hip is lower than knee!
        bottom_hip_y = float(hip_y[b_idx])
        bottom_knee_y = float(knee_y[b_idx])
        
        # Depth margin: positive means hip is lower than patella (below parallel)
        depth_margin_px = bottom_hip_y - bottom_knee_y
        shank_len = b_frame.get("shank_length") or 100.0
        depth_margin_ratio = depth_margin_px / shank_len

        # Meets standard if hip crease drops below top of patella
        meets_depth = bool(depth_margin_px > 0)

        # 2. Bar path and midfoot balance
        # Segment bar path during this repetition
        rep_bar_x = bar_x[s_idx:e_idx+1]
        rep_midfoot_x = midfoot_x[s_idx:e_idx+1]
        
        horizontal_offsets = rep_bar_x - rep_midfoot_x
        mean_offset_px = float(np.mean(horizontal_offsets))
        max_drift_px = float(np.ptp(rep_bar_x))
        max_drift_ratio = float(max_drift_px / shank_len)
        
        # Meets bar path standard if drift is within ~15% of shank length
        meets_bar_path = bool(max_drift_ratio <= 0.16)

        # 3. Back angle at bottom (Figure 2-5, Ref p. 9, Ref p. 22 Fig 2-13)
        # Low-bar squat: ~45 degrees (acceptable range 32° to 62°)
        bottom_back_angle = float(back_angles[b_idx])
        meets_back_angle = bool(32.0 <= bottom_back_angle <= 62.0)
        is_too_vertical = bool(bottom_back_angle > 62.0)
        is_too_horizontal = bool(bottom_back_angle < 32.0)

        # 4. Knee angle at bottom
        bottom_knee_angle = float(knee_angles[b_idx])
        bottom_hip_angle = float(hip_angles[b_idx])

        # 5. Hip drive initiation (Ref p. 1, 22-23)
        # During the first 35% of ascent out of the bottom:
        ascent_len = max(1, e_idx - b_idx)
        early_ascent_end = b_idx + int(ascent_len * 0.35)
        
        # Hip vertical displacement in early ascent
        hip_ascent_delta_y = bottom_hip_y - hip_y[early_ascent_end] # positive = moved up
        # Torso angle change in early ascent
        torso_angle_change = back_angles[early_ascent_end] - bottom_back_angle
        
        # If torso angle drastically opened (> 12 deg) before hips rose, lifter lifted chest early
        # If torso angle drastically closed (< -10 deg), hips shot up while chest dropped ("good morning")
        leads_with_chest = bool(torso_angle_change > 12.0)
        hips_shoot_up = bool(torso_angle_change < -10.0)
        meets_hip_drive = bool(not leads_with_chest and not hips_shoot_up and hip_ascent_delta_y > 5.0)

        # 6. Eye gaze / cervical alignment (Ref pp. 23-25)
        # Head angle at bottom
        rep_head_tilts = [h for h in head_tilts[s_idx:e_idx+1] if not np.isnan(h)]
        mean_head_tilt = float(np.mean(rep_head_tilts)) if rep_head_tilts else 0.0
        # Normal neutral head angle is close to torso axis (within ~25 degrees)
        looks_up = bool(mean_head_tilt > 28.0)
        meets_eye_gaze = not looks_up

        # 7. Knee position at bottom (Figure 2-13: knees slightly in front of toes)
        knee_kpt = b_obs.get(f"{side}_knee", {"pt": (0,0), "is_observed": False})
        ankle_kpt = b_obs.get(f"{side}_ankle", {"pt": (0,0), "is_observed": False})
        facing = b_frame.get("facing_dir", "right")
        
        knee_travel_px = (knee_kpt["pt"][0] - ankle_kpt["pt"][0]) if facing == "right" else (ankle_kpt["pt"][0] - knee_kpt["pt"][0])
        knee_travel_ratio = float(knee_travel_px / shank_len)
        meets_knee_position = bool(0.0 <= knee_travel_ratio <= 0.45)

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
                "depth_margin_ratio": float(depth_margin_ratio),
                "meets_standard": meets_depth
            },
            "bar_path": {
                "mean_offset_px": mean_offset_px,
                "max_drift_px": max_drift_px,
                "max_drift_ratio": max_drift_ratio,
                "meets_standard": meets_bar_path
            },
            "back_angle": {
                "bottom_angle_deg": bottom_back_angle,
                "meets_standard": meets_back_angle,
                "is_too_vertical": is_too_vertical,
                "is_too_horizontal": is_too_horizontal
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
                "meets_standard": meets_hip_drive
            },
            "eye_gaze": {
                "head_tilt_deg": mean_head_tilt,
                "looks_up": looks_up,
                "meets_standard": meets_eye_gaze
            },
            "knee_position": {
                "knee_travel_ratio": knee_travel_ratio,
                "meets_standard": meets_knee_position
            }
        }
