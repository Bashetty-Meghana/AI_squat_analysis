"""
Video Annotator Module
Renders skeleton landmarks, barbell trajectory trail, midfoot vertical balance axis,
depth plane markers, and telemetry HUD into browser-compatible H.264 MP4.
"""

import os
import cv2
import numpy as np
import subprocess
import imageio_ffmpeg

class SquatVideoAnnotator:
    def __init__(self):
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def generate_annotated_video(self, input_video_path, output_video_path, tracking_result, biomechanics_result, progress_callback=None):
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video for annotation: {input_video_path}")

        fps = tracking_result["fps"]
        width = tracking_result["width"]
        height = tracking_result["height"]
        total_frames = tracking_result["total_frames"]
        frames_data = tracking_result["frames_data"]
        reps = biomechanics_result.get("repetitions", [])
        barbell_path = tracking_result["barbell_path"]

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

        while True:
            ret, frame = cap.read()
            if not ret or frame_idx >= total_frames:
                break

            f_info = frames_data[frame_idx]
            obs = f_info["observed_kpts"]
            side = f_info.get("primary_side", "left")

            # Determine active rep and phase
            active_rep, phase_name = self._get_current_phase(frame_idx, reps)

            # Update barbell trajectory trail
            if f_info["bar_pos"] is not None:
                trail_points.append((int(f_info["bar_pos"][0]), int(f_info["bar_pos"][1])))
                if len(trail_points) > 120: # keep last 120 frames for trail
                    trail_points.pop(0)

            # 1. Draw Midfoot Balance Line (Starting Strength Figure 2-5)
            self._draw_midfoot_balance_axis(frame, obs, side, f_info, height)

            # 2. Draw Barbell Trajectory Trail
            self._draw_barbell_trail(frame, trail_points, f_info["bar_pos"])

            # 3. Draw Skeleton Landmarks & Diagnostic Angles
            self._draw_skeleton(frame, obs, side, f_info)

            # 4. Draw Depth Plane at Bottom Position (Figure 2-1)
            is_bottom = frame_idx in bottom_frames
            if is_bottom or (active_rep and abs(frame_idx - active_rep["bottom_frame"]) <= 3):
                rep_for_bottom = bottom_frames.get(frame_idx) or active_rep
                self._draw_depth_plane(frame, rep_for_bottom, obs, side)

            # 5. Draw Telemetry HUD Banner
            self._draw_hud(frame, frame_idx, fps, active_rep, phase_name, f_info, reps)

            # Write frame to FFmpeg pipe
            pipe.stdin.write(frame.tobytes())

            frame_idx += 1
            if progress_callback and total_frames > 0 and frame_idx % 10 == 0:
                progress_callback(min(1.0, frame_idx / total_frames))

        cap.release()
        pipe.stdin.close()
        pipe.wait()

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
        if ankle and ankle["is_observed"]:
            facing = f_info.get("facing_dir", "right")
            offset = (f_info["shank_length"] * 0.18) if f_info.get("shank_length") else 25.0
            mf_x = int(ankle["pt"][0] + (offset if facing == "right" else -offset))
            # Draw dashed vertical line
            for y in range(int(height * 0.15), int(ankle["pt"][1] + 20), 16):
                cv2.line(frame, (mf_x, y), (mf_x, y + 8), (0, 220, 100), 2)
            cv2.putText(frame, "MIDFOOT BALANCE AXIS", (mf_x - 70, int(height * 0.14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 100), 1, cv2.LINE_AA)

    def _draw_barbell_trail(self, frame, trail_points, current_pos):
        if len(trail_points) > 1:
            for i in range(1, len(trail_points)):
                alpha = i / len(trail_points)
                thickness = max(1, int(4 * alpha))
                color = (int(255 * alpha), int(100 * (1 - alpha)), int(230 * alpha))
                cv2.line(frame, trail_points[i-1], trail_points[i], color, thickness)

        if current_pos is not None:
            cx, cy = int(current_pos[0]), int(current_pos[1])
            cv2.circle(frame, (cx, cy), 12, (255, 0, 255), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)
            cv2.putText(frame, "BAR", (cx + 14, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1, cv2.LINE_AA)

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

        for p1, p2, color, thick in bones:
            if p1 and p2 and p1["is_observed"] and p2["is_observed"]:
                pt1 = (int(p1["pt"][0]), int(p1["pt"][1]))
                pt2 = (int(p2["pt"][0]), int(p2["pt"][1]))
                cv2.line(frame, pt1, pt2, color, thick)

        # Joints
        for name in [f"{side}_shoulder", f"{side}_hip", f"{side}_knee", f"{side}_ankle", f"{side}_ear", f"{side}_eye"]:
            kpt = obs.get(name)
            if kpt:
                pt = (int(kpt["pt"][0]), int(kpt["pt"][1]))
                if kpt["is_observed"]:
                    cv2.circle(frame, pt, 6, (0, 255, 0), -1)
                    cv2.circle(frame, pt, 8, (255, 255, 255), 1)
                else:
                    cv2.circle(frame, pt, 5, (0, 165, 255), 1)

    def _draw_depth_plane(self, frame, rep, obs, side):
        hip = obs.get(f"{side}_hip")
        knee = obs.get(f"{side}_knee")
        if not (hip and knee and hip["is_observed"] and knee["is_observed"]):
            return

        k_x, k_y = int(knee["pt"][0]), int(knee["pt"][1])
        h_x, h_y = int(hip["pt"][0]), int(hip["pt"][1])

        # Patella horizontal plane line (Point A, Figure 2-1)
        w_span = 120
        cv2.line(frame, (k_x - w_span, k_y), (k_x + w_span, k_y), (0, 255, 255), 2)
        cv2.putText(frame, "PATELLA PLANE (PARALLEL)", (k_x - w_span, k_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        # Hip crease marker (Point B, Figure 2-1)
        meets = rep["depth"]["meets_standard"]
        color = (0, 255, 0) if meets else (0, 0, 255)
        text = "DEPTH: MEETS STANDARD (BELOW PARALLEL)" if meets else "DEPTH: HIGH (ABOVE PARALLEL)"

        cv2.circle(frame, (h_x, h_y), 10, color, -1)
        cv2.line(frame, (h_x, h_y), (h_x, k_y), color, 2)
        cv2.putText(frame, text, (h_x - 140, h_y + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

    def _draw_hud(self, frame, frame_idx, fps, active_rep, phase_name, f_info, all_reps):
        h, w = frame.shape[:2]
        # HUD background box
        box_h = 100
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, box_h), (20, 20, 24), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "STARTING STRENGTH AI SQUAT COACH", (20, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        # Rep Counter & Phase
        rep_text = f"REP: {active_rep['rep_id']} / {len(all_reps)}" if active_rep else f"TOTAL REPS: {len(all_reps)}"
        cv2.putText(frame, rep_text, (20, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2, cv2.LINE_AA)

        phase_color = (0, 255, 128) if "HIP DRIVE" in phase_name else ((0, 220, 255) if "BOTTOM" in phase_name else (220, 220, 220))
        cv2.putText(frame, f"PHASE: {phase_name}", (180, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.55, phase_color, 2, cv2.LINE_AA)

        # Frame and time
        t_sec = frame_idx / fps
        cv2.putText(frame, f"TIME: {t_sec:.2f}s (Frame {frame_idx})", (20, 84),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

        # Biomechanical metrics HUD
        if active_rep and "back_angle" in active_rep:
            ang_val = active_rep["back_angle"]["bottom_angle_deg"]
            ang_color = (0, 255, 0) if active_rep["back_angle"]["meets_standard"] else (0, 165, 255)
            cv2.putText(frame, f"BACK ANGLE: {ang_val:.1f} deg (Ref ~45 deg)", (w - 340, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, ang_color, 2, cv2.LINE_AA)

            d_val = active_rep["depth"]["depth_margin_px"]
            d_color = (0, 255, 0) if active_rep["depth"]["meets_standard"] else (0, 0, 255)
            d_text = f"DEPTH MARGIN: {d_val:+.1f}px ({'Pass' if active_rep['depth']['meets_standard'] else 'High'})"
            cv2.putText(frame, d_text, (w - 340, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.5, d_color, 2, cv2.LINE_AA)

            drift_val = active_rep["bar_path"]["max_drift_px"]
            cv2.putText(frame, f"BAR DRIFT: {drift_val:.1f}px", (w - 340, 86),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
