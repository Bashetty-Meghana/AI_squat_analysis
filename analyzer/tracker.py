"""
Movement and Barbell Tracker Module
Uses YOLOv8-pose for keypoint detection, orientation estimation,
and barbell plate/sleeve trajectory tracking.
"""

import os
import cv2
import numpy as np
from ultralytics import YOLO

# COCO Keypoint Index Mapping:
# 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
# 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
# 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
# 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle

class SquatVideoTracker:
    def __init__(self, model_name="yolov8n-pose.pt", conf_thresh=0.35):
        self.model = YOLO(model_name)
        self.conf_thresh = conf_thresh

    def inspect_video_properties(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration
        }

    def process_video(self, video_path, progress_callback=None, max_frames=None):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if max_frames and total_frames > max_frames:
            total_frames = max_frames

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        frames_data = []
        barbell_path = []
        frame_idx = 0

        # Orientation stats
        facing_directions = []
        shoulder_widths = []
        framing_issues = []

        prev_bar_pos = None

        while True:
            ret, frame = cap.read()
            if not ret or (max_frames and frame_idx >= max_frames):
                break

            # Run YOLO pose inference on frame
            results = self.model(frame, verbose=False, max_det=1)[0]
            kpts = None
            confs = None
            box = None

            if results.keypoints is not None and len(results.keypoints.xy) > 0 and len(results.keypoints.xy[0]) > 0:
                kpts_xy = results.keypoints.xy[0].cpu().numpy()
                kpts_conf = results.keypoints.conf[0].cpu().numpy() if results.keypoints.conf is not None else np.ones(17)
                kpts = kpts_xy
                confs = kpts_conf

            if results.boxes is not None and len(results.boxes.xyxy) > 0:
                box = results.boxes.xyxy[0].cpu().numpy()

            # Analyze frame
            frame_info = self._analyze_frame(
                frame=frame,
                frame_idx=frame_idx,
                fps=fps,
                width=width,
                height=height,
                kpts=kpts,
                confs=confs,
                box=box,
                prev_bar_pos=prev_bar_pos
            )

            if frame_info["bar_pos"] is not None:
                prev_bar_pos = frame_info["bar_pos"]
                barbell_path.append((frame_idx, frame_info["bar_pos"][0], frame_info["bar_pos"][1]))

            if frame_info.get("facing_dir"):
                facing_directions.append(frame_info["facing_dir"])
            if frame_info.get("shoulder_width_ratio"):
                shoulder_widths.append(frame_info["shoulder_width_ratio"])
            if frame_info.get("framing_cutoffs"):
                framing_issues.extend(frame_info["framing_cutoffs"])

            frames_data.append(frame_info)
            frame_idx += 1

            if progress_callback and total_frames > 0 and frame_idx % 5 == 0:
                progress_callback(min(1.0, frame_idx / total_frames))

        cap.release()

        # Determine dominant orientation & view suitability
        dominant_facing = max(set(facing_directions), key=facing_directions.count) if facing_directions else "unknown"
        mean_shoulder_width = float(np.mean(shoulder_widths)) if shoulder_widths else 0.0

        # In pure side view, shoulder X separation is small (< 0.12 of torso height).
        # In frontal view, shoulder X separation is large (> 0.25 of torso height).
        is_side_view = (dominant_facing in ["left", "right"]) and (mean_shoulder_width < 0.32)
        view_classification = "sagittal_side_view" if is_side_view else "non_sagittal_or_frontal"

        # Check camera framing & occlusions
        unique_framing_cutoffs = list(set(framing_issues))

        return {
            "fps": fps,
            "width": width,
            "height": height,
            "total_frames": len(frames_data),
            "dominant_facing": dominant_facing,
            "view_classification": view_classification,
            "is_side_view": is_side_view,
            "mean_shoulder_width_ratio": mean_shoulder_width,
            "framing_issues": unique_framing_cutoffs,
            "frames_data": frames_data,
            "barbell_path": barbell_path
        }

    def _analyze_frame(self, frame, frame_idx, fps, width, height, kpts, confs, box, prev_bar_pos):
        timestamp = frame_idx / fps
        data = {
            "frame_idx": frame_idx,
            "timestamp": timestamp,
            "observed_kpts": {},
            "estimated_kpts": {},
            "bar_pos": None,
            "bar_is_observed": False,
            "facing_dir": None,
            "shoulder_width_ratio": None,
            "framing_cutoffs": [],
            "torso_length": None,
            "shank_length": None
        }

        if kpts is None or confs is None:
            data["framing_cutoffs"].append("lifter_not_detected")
            return data

        # Check framing cutoffs (head, feet, bounds)
        if box is not None:
            x1, y1, x2, y2 = box
            if y1 < height * 0.02:
                data["framing_cutoffs"].append("head_upper_cutoff")
            if y2 > height * 0.98:
                data["framing_cutoffs"].append("feet_lower_cutoff")
            if x1 < width * 0.02 or x2 > width * 0.98:
                data["framing_cutoffs"].append("horizontal_boundary_cutoff")

        # Map COCO keypoints
        # 5: L shoulder, 6: R shoulder, 11: L hip, 12: R hip, 13: L knee, 14: R knee, 15: L ankle, 16: R ankle
        names = [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ]

        observed = {}
        for i, name in enumerate(names):
            c = float(confs[i])
            pt = (float(kpts[i][0]), float(kpts[i][1]))
            if c >= self.conf_thresh:
                observed[name] = {"pt": pt, "conf": c, "is_observed": True}
            else:
                observed[name] = {"pt": pt, "conf": c, "is_observed": False}

        data["observed_kpts"] = observed

        # Determine facing direction (lateral left vs right)
        # In a side view facing right: nose/toes have higher X than ears/heels.
        # In facing left: nose/toes have lower X than ears/heels.
        ls = observed["left_shoulder"]
        rs = observed["right_shoulder"]
        lh = observed["left_hip"]
        rh = observed["right_hip"]
        lk = observed["left_knee"]
        rk = observed["right_knee"]
        la = observed["left_ankle"]
        ra = observed["right_ankle"]

        # Use primary side landmarks with highest confidence
        primary_side = "left" if (ls["conf"] + lh["conf"] + lk["conf"]) >= (rs["conf"] + rh["conf"] + rk["conf"]) else "right"
        data["primary_side"] = primary_side

        prim_shoulder = ls if primary_side == "left" else rs
        prim_hip = lh if primary_side == "left" else rh
        prim_knee = lk if primary_side == "left" else rk
        prim_ankle = la if primary_side == "left" else ra

        # Calculate torso and shank reference lengths for scale invariance
        torso_len = np.linalg.norm(np.array(prim_shoulder["pt"]) - np.array(prim_hip["pt"])) if (prim_shoulder["is_observed"] and prim_hip["is_observed"]) else None
        shank_len = np.linalg.norm(np.array(prim_knee["pt"]) - np.array(prim_ankle["pt"])) if (prim_knee["is_observed"] and prim_ankle["is_observed"]) else None
        data["torso_length"] = float(torso_len) if torso_len else None
        data["shank_length"] = float(shank_len) if shank_len else None

        # Check shoulder separation ratio vs torso length
        if ls["is_observed"] and rs["is_observed"] and torso_len and torso_len > 10:
            shoulder_sep_x = abs(ls["pt"][0] - rs["pt"][0])
            data["shoulder_width_ratio"] = float(shoulder_sep_x / torso_len)

        # Facing direction estimation
        if prim_knee["is_observed"] and prim_hip["is_observed"]:
            knee_hip_dx = prim_knee["pt"][0] - prim_hip["pt"][0]
            if abs(knee_hip_dx) > 15:
                data["facing_dir"] = "right" if knee_hip_dx > 0 else "left"

        # Barbell detection & tracking
        # The barbell rests on the lifter's back/posterior delts.
        # In a side view, the center of the bumper plate (sleeve) is clearly visible.
        bar_pt, bar_observed = self._track_barbell_sleeve(frame, prim_shoulder, prim_hip, torso_len, prev_bar_pos)
        data["bar_pos"] = bar_pt
        data["bar_is_observed"] = bar_observed

        return data

    def _track_barbell_sleeve(self, frame, prim_shoulder, prim_hip, torso_len, prev_bar_pos):
        """
        Locates the barbell sleeve/plate center.
        Combines red collar / circular hub detection with optical flow and spatial constraints.
        Restricts candidate positions strictly within the lifter's upper body / plate zone.
        """
        h, w = frame.shape[:2]
        
        # Determine valid spatial bounds for the barbell
        # Barbell must be at shoulder/upper torso level, never above head or below knees
        if prim_shoulder["is_observed"]:
            sh_x, sh_y = prim_shoulder["pt"]
        elif prev_bar_pos is not None:
            sh_x, sh_y = prev_bar_pos
        else:
            return None, False

        search_rad = int(torso_len * 0.55) if torso_len else 90
        
        x_min = max(0, int(sh_x - search_rad * 1.2))
        x_max = min(w, int(sh_x + search_rad * 1.2))
        y_min = max(0, int(sh_y - search_rad * 0.8))
        y_max = min(h, int(sh_y + search_rad * 0.9))

        if x_max - x_min < 20 or y_max - y_min < 20:
            return prev_bar_pos, False

        roi = frame[y_min:y_max, x_min:x_max]
        
        # 1. Color-based red sleeve/collar detection (common on barbell collars and Olympic plates)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([12, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([168, 70, 50]), np.array([180, 255, 255]))
        red_mask = mask1 | mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_red_center = None
        best_dist = float("inf")
        
        for c in contours:
            area = cv2.contourArea(c)
            if 80 < area < 10000:
                (cx, cy), radius = cv2.minEnclosingCircle(c)
                gx = x_min + cx
                gy = y_min + cy
                # Must be near shoulder / upper torso
                d = np.hypot(gx - sh_x, gy - sh_y)
                if prev_bar_pos is not None:
                    d_prev = np.hypot(gx - prev_bar_pos[0], gy - prev_bar_pos[1])
                    if d_prev < 80 and d_prev < best_dist:
                        best_dist = d_prev
                        best_red_center = (float(gx), float(gy))
                elif d < best_dist:
                    best_dist = d
                    best_red_center = (float(gx), float(gy))

        if best_red_center is not None:
            if prev_bar_pos is not None:
                # Smooth update
                sm_x = prev_bar_pos[0] * 0.15 + best_red_center[0] * 0.85
                sm_y = prev_bar_pos[1] * 0.15 + best_red_center[1] * 0.85
                return (sm_x, sm_y), True
            return best_red_center, True

        # 2. Circular Hough Transform on plate hub
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=25,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=int(search_rad * 0.5)
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            best_circle = None
            best_c_dist = float("inf")
            for (cx, cy, r) in circles:
                gx = x_min + cx
                gy = y_min + cy
                if prev_bar_pos is not None:
                    d = np.hypot(gx - prev_bar_pos[0], gy - prev_bar_pos[1])
                    if d < 60 and d < best_c_dist:
                        best_c_dist = d
                        best_circle = (float(gx), float(gy))
                else:
                    d = np.hypot(gx - sh_x, gy - sh_y)
                    if d < best_c_dist:
                        best_c_dist = d
                        best_circle = (float(gx), float(gy))

            if best_circle is not None:
                if prev_bar_pos is not None:
                    sm_x = prev_bar_pos[0] * 0.2 + best_circle[0] * 0.8
                    sm_y = prev_bar_pos[1] * 0.2 + best_circle[1] * 0.8
                    return (sm_x, sm_y), True
                return best_circle, True

        # 3. Fallback: If tracking continuous, keep vertical progression with shoulder delta
        if prev_bar_pos is not None:
            return prev_bar_pos, False

        return (float(sh_x), float(sh_y)), False
