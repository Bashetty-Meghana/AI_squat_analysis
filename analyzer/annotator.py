"""
Video Annotator Module
Renders skeleton landmarks, barbell trajectory trail, midfoot vertical balance axis,
depth plane markers, and telemetry HUD into browser-compatible H.264 MP4.
Also exports structured JSON overlay track for browser-based interactive canvas rendering.
"""

import os
import cv2
import json
import numpy as np
import subprocess
import imageio_ffmpeg

class SquatVideoAnnotator:
    def __init__(self):
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def generate_annotated_video(self, input_video_path, output_video_path, tracking_result, biomechanics_result, overlay_json_path=None, progress_callback=None):
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video for annotation: {input_video_path}")

        fps = tracking_result["fps"]
        width = tracking_result["width"]
        height = tracking_result["height"]
        total_frames = tracking_result["total_frames"]
        frames_data = tracking_result["frames_data"]
        reps = biomechanics_result.get("repetitions", [])

        # Default overlay JSON path
        if overlay_json_path is None:
            base_dir = os.path.dirname(output_video_path) or "output"
            base_name = os.path.splitext(os.path.basename(output_video_path))[0]
            overlay_json_path = os.path.join(base_dir, f"{base_name}_overlay_track.json")

        # Map bottom frames for quick lookup
        bottom_frames = {r["bottom_frame"]: r for r in reps}

        # Setup FFmpeg pipe for H.264 MP4 writing
        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "bgr24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "22",
            "-movflags", "+faststart",
            output_video_path
        ]

        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        frame_idx = 0
        trail_points = []
        overlay_frames = []

        while True:
            ret, frame = cap.read()
            if not ret or frame_idx >= total_frames:
                break

            f_info = frames_data[frame_idx]
            obs = f_info["observed_kpts"]
            side = f_info.get("primary_side", "left")

            # Determine active rep and phase
            active_rep, phase_name = self._get_current_phase(frame_idx, reps)

            # Update barbell trajectory trail only if observed or estimated (never lost)
            bar_pos = f_info["bar_pos"]
            bar_st = f_info.get("bar_status", "LOST")
            if bar_pos is not None and bar_st != "LOST":
                trail_points.append((int(bar_pos[0]), int(bar_pos[1])))
                if len(trail_points) > 120:
                    trail_points.pop(0)

            # 1. Draw Midfoot Balance Line (Starting Strength Figure 2-5)
            self._draw_midfoot_balance_axis(frame, obs, side, f_info, height)

            # 2. Draw Barbell Trajectory Trail
            self._draw_barbell_trail(frame, trail_points, bar_pos, bar_st)

            # 3. Draw Skeleton Landmarks & Diagnostic Angles
            self._draw_skeleton(frame, obs, side, f_info)

            # 4. Draw Depth Plane at Bottom Position (Figure 2-1)
            is_bottom = frame_idx in bottom_frames
            if is_bottom or (active_rep and abs(frame_idx - active_rep["bottom_frame"]) <= 3):
                rep_for_bottom = bottom_frames.get(frame_idx) or active_rep
                self._draw_depth_plane(frame, rep_for_bottom, obs, side)

            # 5. Draw Telemetry HUD Banner
            self._draw_hud(frame, frame_idx, fps, active_rep, phase_name, f_info, reps)

            # Record frame in JSON overlay track
            frame_overlay = {
                "frame_idx": frame_idx,
                "timestamp": round(float(frame_idx / fps), 3),
                "phase": phase_name,
                "active_rep_id": active_rep["rep_id"] if active_rep else None,
                "is_bottom_frame": is_bottom,
                "landmarks": {
                    k: {
                        "x": round(float(v["pt"][0]), 1),
                        "y": round(float(v["pt"][1]), 1),
                        "status": v.get("status", "OBSERVED")
                    }
                    for k, v in obs.items() if v.get("pt") is not None
                },
                "barbell": {
                    "x": round(float(bar_pos[0]), 1) if bar_pos is not None else None,
                    "y": round(float(bar_pos[1]), 1) if bar_pos is not None else None,
                    "status": bar_st
                }
            }
            overlay_frames.append(frame_overlay)

            # Write frame to FFmpeg pipe
            pipe.stdin.write(frame.tobytes())

            frame_idx += 1
            if progress_callback and total_frames > 0 and frame_idx % 10 == 0:
                progress_callback(min(1.0, frame_idx / total_frames))

        cap.release()
        pipe.stdin.close()
        pipe.wait()

        # Write out overlay track JSON
        overlay_track_data = {
            "video_metadata": {
                "input_video": os.path.basename(input_video_path),
                "fps": fps,
                "width": width,
                "height": height,
                "total_frames": total_frames,
                "primary_side": tracking_result.get("primary_side", "left"),
                "dominant_facing": tracking_result.get("dominant_facing", "right"),
                "model_used": tracking_result.get("model_used", "yolov8s-pose.pt")
            },
            "repetitions": [
                {
                    "rep_id": r["rep_id"],
                    "start_frame": r["start_frame"],
                    "bottom_frame": r["bottom_frame"],
                    "end_frame": r["end_frame"],
                    "start_timestamp": r["start_timestamp"],
                    "bottom_timestamp": r["bottom_timestamp"],
                    "end_timestamp": r["end_timestamp"],
                    "depth_margin_cm": r["depth"].get("depth_margin_cm"),
                    "meets_depth": r["depth"].get("meets_standard"),
                    "is_borderline_depth": r["depth"].get("is_borderline", False),
                    "back_angle_deg": r["back_angle"].get("bottom_angle_deg"),
                    "mean_velocity_mps": r["vbt"].get("mean_velocity_mps")
                }
                for r in reps
            ],
            "frames": overlay_frames
        }

        os.makedirs(os.path.dirname(overlay_json_path) or ".", exist_ok=True)
        with open(overlay_json_path, "w", encoding="utf-8") as f:
            json.dump(overlay_track_data, f, indent=2)

        self.last_overlay_json_path = overlay_json_path
        return output_video_path

    def _get_current_phase(self, frame_idx, reps):
        for r in reps:
            if r["start_frame"] <= frame_idx <= r["end_frame"]:
                if frame_idx < r["bottom_frame"] - 5:
                    return r, "DESCENT"
                elif abs(frame_idx - r["bottom_frame"]) <= 5:
                    return r, "BOTTOM TURNAROUND"
                else:
                    return r, "ASCENT (HIP DRIVE)"
        return None, "SETUP / LOCKOUT"

    def _draw_midfoot_balance_axis(self, frame, obs, side, f_info, height):
        ankle = obs.get(f"{side}_ankle")
        if ankle and ankle.get("status") in ["OBSERVED", "ESTIMATED"]:
            facing = f_info.get("facing_dir", "right")
            offset = (f_info["shank_length"] * 0.18) if f_info.get("shank_length") else 25.0
            mf_x = int(ankle["pt"][0] + (offset if facing == "right" else -offset))
            # Draw dashed vertical line
            for y in range(int(height * 0.15), int(ankle["pt"][1] + 20), 16):
                cv2.line(frame, (mf_x, y), (mf_x, y + 8), (0, 220, 100), 2)
            cv2.putText(frame, "MIDFOOT BALANCE AXIS", (mf_x - 70, int(height * 0.14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 100), 1, cv2.LINE_AA)

    def _draw_barbell_trail(self, frame, trail_points, current_pos, status):
        # Refuse to draw barbell marker if lost
        if status == "LOST":
            return

        if len(trail_points) > 1:
            for i in range(1, len(trail_points)):
                alpha = i / len(trail_points)
                thickness = max(1, int(4 * alpha))
                color = (int(255 * alpha), int(100 * (1 - alpha)), int(230 * alpha))
                cv2.line(frame, trail_points[i-1], trail_points[i], color, thickness)

        if current_pos is not None:
            cx, cy = int(current_pos[0]), int(current_pos[1])
            col = (255, 0, 255) if status == "OBSERVED" else (0, 165, 255)
            cv2.circle(frame, (cx, cy), 12, col, 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)
            label = "BAR" if status == "OBSERVED" else "BAR [EST]"
            cv2.putText(frame, label, (cx + 14, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)

    def _draw_skeleton(self, frame, obs, side, f_info):
        sh = obs.get(f"{side}_shoulder")
        hip = obs.get(f"{side}_hip")
        knee = obs.get(f"{side}_knee")
        ankle = obs.get(f"{side}_ankle")
        ear = obs.get(f"{side}_ear")
        eye = obs.get(f"{side}_eye")

        # Bones
        bones = [
            (sh, hip, (0, 255, 200), 3),      # Torso plane
            (hip, knee, (0, 200, 255), 4),     # Femur
            (knee, ankle, (255, 200, 0), 4),   # Tibia / Shank
            (ear, eye, (200, 150, 255), 2),    # Head vector
            (sh, ear, (150, 150, 200), 2)      # Neck
        ]

        def is_valid_pt(p):
            return p and p.get("status") in ["OBSERVED", "ESTIMATED"] and p.get("pt") is not None

        for p1, p2, color, thick in bones:
            if is_valid_pt(p1) and is_valid_pt(p2):
                pt1 = (int(p1["pt"][0]), int(p1["pt"][1]))
                pt2 = (int(p2["pt"][0]), int(p2["pt"][1]))
                cv2.line(frame, pt1, pt2, color, thick)

        # Joints
        for name in [f"{side}_shoulder", f"{side}_hip", f"{side}_knee", f"{side}_ankle", f"{side}_ear", f"{side}_eye"]:
            kpt = obs.get(name)
            if kpt and is_valid_pt(kpt):
                pt = (int(kpt["pt"][0]), int(kpt["pt"][1]))
                if kpt.get("status") == "OBSERVED":
                    cv2.circle(frame, pt, 6, (0, 255, 0), -1)
                    cv2.circle(frame, pt, 8, (255, 255, 255), 1)
                else: # ESTIMATED
                    cv2.circle(frame, pt, 5, (0, 165, 255), -1)
                    cv2.circle(frame, pt, 7, (255, 255, 255), 1)

    def _draw_depth_plane(self, frame, rep, obs, side):
        hip = obs.get(f"{side}_hip")
        knee = obs.get(f"{side}_knee")
        if not (hip and knee and hip.get("status") in ["OBSERVED", "ESTIMATED"] and knee.get("status") in ["OBSERVED", "ESTIMATED"]):
            return

        k_x, k_y = int(knee["pt"][0]), int(knee["pt"][1])
        h_x, h_y = int(hip["pt"][0]), int(hip["pt"][1])

        # Patella horizontal plane line (Point A, Figure 2-1)
        w_span = 130
        cv2.line(frame, (k_x - w_span, k_y), (k_x + w_span, k_y), (0, 255, 255), 2)
        cv2.putText(frame, "PATELLA PLANE (PARALLEL)", (k_x - w_span, k_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        # Hip crease marker (Point B, Figure 2-1)
        meets = rep["depth"]["meets_standard"]
        is_borderline = rep["depth"].get("is_borderline", False)
        
        if is_borderline:
            color = (0, 215, 255) # Yellow/Orange for borderline uncertainty
            text_prefix = "DEPTH: BORDERLINE UNCERTAIN"
        elif meets:
            color = (0, 255, 0)
            text_prefix = "DEPTH: MEETS STANDARD"
        else:
            color = (0, 0, 255)
            text_prefix = "DEPTH: HIGH SQUAT"

        d_cm = rep["depth"].get("depth_margin_cm")
        cm_text = f" ({d_cm:+.1f} cm)" if d_cm is not None else ""
        text = f"{text_prefix}{cm_text}"

        cv2.circle(frame, (h_x, h_y), 10, color, -1)
        cv2.line(frame, (h_x, h_y), (h_x, k_y), color, 2)
        cv2.putText(frame, text, (h_x - 140, h_y + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, 2, cv2.LINE_AA)

    def _draw_hud(self, frame, frame_idx, fps, active_rep, phase_name, f_info, all_reps):
        h, w = frame.shape[:2]
        # Translucent HUD background bar
        box_h = 115
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, box_h), (12, 16, 24), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Subtle bottom border for HUD
        cv2.line(frame, (0, box_h), (w, box_h), (40, 50, 70), 1)

        # Title with VBT badge
        cv2.putText(frame, "IRONPATH AI | SQUAT COACH & VBT ENGINE", (20, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "STARTING STRENGTH GROUNDED", (w - 320, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

        # Rep Counter & Phase
        rep_text = f"REP: {active_rep['rep_id']} / {len(all_reps)}" if active_rep else f"TOTAL REPS: {len(all_reps)}"
        cv2.putText(frame, rep_text, (20, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 2, cv2.LINE_AA)

        phase_color = (0, 255, 128) if "HIP DRIVE" in phase_name else ((0, 220, 255) if "BOTTOM" in phase_name else (220, 220, 220))
        cv2.putText(frame, f"PHASE: {phase_name}", (170, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.55, phase_color, 2, cv2.LINE_AA)

        # VBT Speed & Tempo display
        if active_rep and "vbt" in active_rep:
            vbt = active_rep["vbt"]
            v_val = vbt["mean_velocity_mps"]
            v_color = (0, 255, 128) if v_val >= 0.50 else ((0, 220, 255) if v_val >= 0.35 else (0, 165, 255))
            vbt_text = f"CONCENTRIC VELOCITY: {v_val:.2f} m/s (Peak: {vbt['peak_velocity_mps']:.2f} m/s)"
            cv2.putText(frame, vbt_text, (20, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.5, v_color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"TEMPO: {vbt['tempo_notation']} | FATIGUE: {vbt['velocity_loss_pct']:.0f}%", (20, 106),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 220), 1, cv2.LINE_AA)
        else:
            t_sec = frame_idx / fps
            cv2.putText(frame, f"TIME: {t_sec:.2f}s (Frame {frame_idx})", (20, 84),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

        # Right-side biomechanical metrics HUD
        if active_rep and "back_angle" in active_rep:
            ang_val = active_rep["back_angle"]["bottom_angle_deg"]
            ang_color = (0, 255, 0) if active_rep["back_angle"]["meets_standard"] else (0, 165, 255)
            cv2.putText(frame, f"BACK ANGLE: {ang_val:.1f} deg (Ref ~45 deg)", (w - 380, 54),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, ang_color, 1, cv2.LINE_AA)

            d_val = active_rep["depth"]["depth_margin_px"]
            d_cm = active_rep["depth"].get("depth_margin_cm")
            cm_s = f" ({d_cm:+.1f}cm)" if d_cm is not None else ""
            if active_rep["depth"].get("is_borderline"):
                d_color = (0, 215, 255)
                res_s = "Borderline"
            else:
                d_color = (0, 255, 0) if active_rep["depth"]["meets_standard"] else (0, 0, 255)
                res_s = "Pass" if active_rep["depth"]["meets_standard"] else "High"
            d_text = f"DEPTH: {d_val:+.1f}px{cm_s} ({res_s})"
            cv2.putText(frame, d_text, (w - 380, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.48, d_color, 2, cv2.LINE_AA)

            drift_val = active_rep["bar_path"]["max_drift_px"]
            drift_cm = active_rep["bar_path"].get("max_drift_cm")
            drift_s = f" ({drift_cm:.1f}cm)" if drift_cm is not None else ""
            cv2.putText(frame, f"BAR DRIFT: {drift_val:.1f}px{drift_s}", (w - 380, 102),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
