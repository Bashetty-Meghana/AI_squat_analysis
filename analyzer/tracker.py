"""
Movement and Barbell Tracker Module
Uses YOLOv8-pose for keypoint detection, orientation estimation, One-Euro temporal filtering,
and barbell plate/sleeve trajectory tracking with velocity gating and explicit confidence tagging.
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

COCO_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]


class OneEuroFilter:
    """
    1-Euro Filter for real-time temporal jitter reduction without phase lag.
    Paper: Casiez, Roussel, Vogel (CHI 2012).
    Adaptive cutoff frequency: low cutoff at low velocity (suppresses jitter),
    high cutoff at high velocity (eliminates lag).
    """
    def __init__(self, t0=0.0, x0=0.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = 0.0
        self.t_prev = float(t0) if t0 is not None else None

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2.0 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, t, x):
        if self.t_prev is None:
            self.t_prev = float(t)
            self.x_prev = float(x)
            self.dx_prev = 0.0
            return float(x)

        dt = float(t - self.t_prev)
        if dt <= 1e-5:
            return self.x_prev

        # Estimate rate of change (derivative)
        dx = (float(x) - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        edx = a_d * dx + (1.0 - a_d) * self.dx_prev

        # Dynamic cutoff frequency based on movement speed
        cutoff = self.min_cutoff + self.beta * abs(edx)
        a = self._alpha(cutoff, dt)
        x_hat = a * float(x) + (1.0 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = edx
        self.t_prev = float(t)
        return float(x_hat)

    def reset(self, t0=0.0, x0=0.0):
        self.t_prev = float(t0)
        self.x_prev = float(x0)
        self.dx_prev = 0.0


class PointFilter2D:
    """Combines two OneEuroFilters for 2D (x, y) coordinates."""
    def __init__(self, min_cutoff=1.2, beta=0.008, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.fx = None
        self.fy = None
        self.missing_streak = 0

    def update(self, t, pt):
        if pt is None:
            self.missing_streak += 1
            if self.missing_streak <= 5 and self.fx is not None:
                # Brief occlusion: hold last smoothed position as ESTIMATED
                return (self.fx.x_prev, self.fy.x_prev), "ESTIMATED"
            return None, "LOST"

        self.missing_streak = 0
        x, y = pt
        if self.fx is None:
            self.fx = OneEuroFilter(t0=t, x0=x, min_cutoff=self.min_cutoff, beta=self.beta, d_cutoff=self.d_cutoff)
            self.fy = OneEuroFilter(t0=t, x0=y, min_cutoff=self.min_cutoff, beta=self.beta, d_cutoff=self.d_cutoff)
            return (float(x), float(y)), "OBSERVED"

        sx = self.fx.filter(t, x)
        sy = self.fy.filter(t, y)
        return (sx, sy), "OBSERVED"


class SquatVideoTracker:
    def __init__(self, model_name=None, conf_thresh=0.35):
        # Automatically choose higher-accuracy model if available
        if model_name is None:
            if os.path.exists("yolov8s-pose.pt"):
                model_name = "yolov8s-pose.pt"
            elif os.path.exists("yolov8n-pose.pt"):
                model_name = "yolov8n-pose.pt"
            else:
                model_name = "yolov8s-pose.pt"

        self.model_name = model_name
        try:
            self.model = YOLO(model_name)
        except Exception as e:
            # Fallback to yolov8n-pose
            print(f"[Tracker] Warning: Failed to load {model_name} ({e}), falling back to yolov8n-pose.pt")
            self.model_name = "yolov8n-pose.pt"
            self.model = YOLO("yolov8n-pose.pt")

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

        # Check video validation flags
        validations = []
        if fps < 15.0:
            validations.append({"code": "LOW_FPS", "message": f"Frame rate is low ({fps:.1f} fps). Recommended is 30-60 fps."})
        if duration < 2.0:
            validations.append({"code": "TOO_SHORT", "message": f"Video duration ({duration:.1f}s) is too short to capture complete squat cycles."})
        elif duration > 180.0:
            validations.append({"code": "TOO_LONG", "message": f"Video duration ({duration:.1f}s) exceeds 3 minutes. Please trim to the relevant set."})

        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "validations": validations
        }

    def process_video(self, video_path, progress_callback=None, max_frames=None):
        props = self.inspect_video_properties(video_path)
        if not props:
            raise ValueError(f"Could not open video file: {video_path}")

        cap = cv2.VideoCapture(video_path)
        fps = props["fps"]
        total_frames = props["frame_count"]
        if max_frames and total_frames > max_frames:
            total_frames = max_frames

        width = props["width"]
        height = props["height"]

        # Setup filters for all keypoints to eliminate jitter
        filters = {name: PointFilter2D(min_cutoff=1.2, beta=0.008, d_cutoff=1.0) for name in COCO_KEYPOINTS}
        bar_filter = PointFilter2D(min_cutoff=0.8, beta=0.005, d_cutoff=1.0)

        frames_data = []
        barbell_path = []
        frame_idx = 0

        # Stats accumulators
        facing_directions = []
        shoulder_widths = []
        framing_issues = []
        people_counts = []
        lifter_height_ratios = []
        side_confidence_scores = {"left": 0.0, "right": 0.0}

        prev_bar_pos = None

        while True:
            ret, frame = cap.read()
            if not ret or (max_frames and frame_idx >= max_frames):
                break

            timestamp = frame_idx / fps

            # Run YOLO pose inference on frame (track up to 2 people to detect crowded background)
            results = self.model(frame, verbose=False, max_det=3)[0]
            kpts = None
            confs = None
            box = None

            detected_people_count = 0
            if results.boxes is not None:
                detected_people_count = len(results.boxes)
            people_counts.append(detected_people_count)

            if results.keypoints is not None and len(results.keypoints.xy) > 0 and len(results.keypoints.xy[0]) > 0:
                # Primary person is index 0
                kpts_xy = results.keypoints.xy[0].cpu().numpy()
                kpts_conf = results.keypoints.conf[0].cpu().numpy() if results.keypoints.conf is not None else np.ones(17)
                kpts = kpts_xy
                confs = kpts_conf

            if results.boxes is not None and len(results.boxes.xyxy) > 0:
                box = results.boxes.xyxy[0].cpu().numpy()
                box_h = box[3] - box[1]
                lifter_height_ratios.append(box_h / height)

            # Analyze frame
            frame_info = self._analyze_frame(
                frame=frame,
                frame_idx=frame_idx,
                fps=fps,
                timestamp=timestamp,
                width=width,
                height=height,
                kpts=kpts,
                confs=confs,
                box=box,
                filters=filters,
                bar_filter=bar_filter,
                prev_bar_pos=prev_bar_pos
            )

            # Update barbell path
            if frame_info["bar_pos"] is not None:
                prev_bar_pos = frame_info["bar_pos"]
                barbell_path.append({
                    "frame_idx": frame_idx,
                    "timestamp": timestamp,
                    "x": float(frame_info["bar_pos"][0]),
                    "y": float(frame_info["bar_pos"][1]),
                    "status": frame_info["bar_status"]
                })
            else:
                barbell_path.append({
                    "frame_idx": frame_idx,
                    "timestamp": timestamp,
                    "x": None,
                    "y": None,
                    "status": "LOST"
                })

            if frame_info.get("facing_dir"):
                facing_directions.append(frame_info["facing_dir"])
            if frame_info.get("shoulder_width_ratio"):
                shoulder_widths.append(frame_info["shoulder_width_ratio"])
            if frame_info.get("framing_cutoffs"):
                framing_issues.extend(frame_info["framing_cutoffs"])

            # Accumulate side confidences
            if "primary_side" in frame_info:
                side_confidence_scores[frame_info["primary_side"]] += frame_info.get("side_confidence", 1.0)

            frames_data.append(frame_info)
            frame_idx += 1

            if progress_callback and total_frames > 0 and frame_idx % 5 == 0:
                progress_callback(min(1.0, frame_idx / total_frames))

        cap.release()

        # Determine dominant orientation & view suitability
        dominant_facing = max(set(facing_directions), key=facing_directions.count) if facing_directions else "unknown"
        mean_shoulder_width = float(np.mean(shoulder_widths)) if shoulder_widths else 0.0

        # Primary camera-facing side (left vs right)
        primary_camera_side = "left" if side_confidence_scores["left"] >= side_confidence_scores["right"] else "right"

        # Check for multiple people
        has_multiple_people = False
        if people_counts:
            # If multiple persons detected in > 30% of frames
            multi_pct = sum(1 for c in people_counts if c > 1) / len(people_counts)
            if multi_pct > 0.30:
                has_multiple_people = True
                framing_issues.append("multiple_people_detected")

        # Check for tiny lifter (lifter < 30% of frame height)
        median_lifter_h = float(np.median(lifter_height_ratios)) if lifter_height_ratios else 0.0
        if median_lifter_h < 0.28:
            framing_issues.append("tiny_lifter_in_frame")

        # In pure side view:
        # 1. Shoulder X separation is small (< 0.32 of torso height).
        # 2. Dominant facing is lateral (left or right).
        is_side_view = (dominant_facing in ["left", "right"]) and (mean_shoulder_width < 0.32)
        view_classification = "sagittal_side_view" if is_side_view else "non_sagittal_or_frontal"

        unique_framing_cutoffs = list(dict.fromkeys(framing_issues))

        return {
            "model_used": self.model_name,
            "fps": fps,
            "width": width,
            "height": height,
            "total_frames": len(frames_data),
            "dominant_facing": dominant_facing,
            "primary_side": primary_camera_side,
            "camera_facing_side": primary_camera_side,
            "view_classification": view_classification,
            "is_side_view": is_side_view,
            "mean_shoulder_width_ratio": mean_shoulder_width,
            "median_lifter_height_ratio": median_lifter_h,
            "framing_issues": unique_framing_cutoffs,
            "frames_data": frames_data,
            "barbell_path": barbell_path
        }

    def _analyze_frame(self, frame, frame_idx, fps, timestamp, width, height, kpts, confs, box, filters, bar_filter, prev_bar_pos):
        data = {
            "frame_idx": frame_idx,
            "timestamp": timestamp,
            "observed_kpts": {},
            "bar_pos": None,
            "bar_status": "LOST",
            "facing_dir": None,
            "shoulder_width_ratio": None,
            "framing_cutoffs": [],
            "torso_length": None,
            "shank_length": None
        }

        if kpts is None or confs is None:
            data["framing_cutoffs"].append("lifter_not_detected")
            # Update filters with None
            for name in COCO_KEYPOINTS:
                smoothed_pt, status = filters[name].update(timestamp, None)
                data["observed_kpts"][name] = {"pt": smoothed_pt or (0.0, 0.0), "conf": 0.0, "status": status}
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

        # Map COCO keypoints through OneEuroFilters with status tagging
        observed = {}
        for i, name in enumerate(COCO_KEYPOINTS):
            c = float(confs[i])
            raw_pt = (float(kpts[i][0]), float(kpts[i][1]))
            if c >= self.conf_thresh:
                smoothed_pt, _ = filters[name].update(timestamp, raw_pt)
                observed[name] = {"pt": smoothed_pt, "conf": c, "status": "OBSERVED"}
            else:
                smoothed_pt, status = filters[name].update(timestamp, None)
                observed[name] = {"pt": smoothed_pt or raw_pt, "conf": c, "status": status}

        data["observed_kpts"] = observed

        ls = observed["left_shoulder"]
        rs = observed["right_shoulder"]
        lh = observed["left_hip"]
        rh = observed["right_hip"]
        lk = observed["left_knee"]
        rk = observed["right_knee"]
        la = observed["left_ankle"]
        ra = observed["right_ankle"]

        # Calculate side confidence
        left_score = ls["conf"] + lh["conf"] + lk["conf"] + la["conf"]
        right_score = rs["conf"] + rh["conf"] + rk["conf"] + ra["conf"]
        primary_side = "left" if left_score >= right_score else "right"
        data["primary_side"] = primary_side
        data["side_confidence"] = float(max(left_score, right_score))

        prim_shoulder = ls if primary_side == "left" else rs
        prim_hip = lh if primary_side == "left" else rh
        prim_knee = lk if primary_side == "left" else rk
        prim_ankle = la if primary_side == "left" else ra

        # Calculate torso and shank reference lengths
        if prim_shoulder["status"] in ["OBSERVED", "ESTIMATED"] and prim_hip["status"] in ["OBSERVED", "ESTIMATED"]:
            torso_len = float(np.linalg.norm(np.array(prim_shoulder["pt"]) - np.array(prim_hip["pt"])))
            data["torso_length"] = torso_len
        else:
            torso_len = None

        if prim_knee["status"] in ["OBSERVED", "ESTIMATED"] and prim_ankle["status"] in ["OBSERVED", "ESTIMATED"]:
            shank_len = float(np.linalg.norm(np.array(prim_knee["pt"]) - np.array(prim_ankle["pt"])))
            data["shank_length"] = shank_len
        else:
            shank_len = None

        # Check shoulder separation ratio vs torso length
        if ls["status"] == "OBSERVED" and rs["status"] == "OBSERVED" and torso_len and torso_len > 10:
            shoulder_sep_x = abs(ls["pt"][0] - rs["pt"][0])
            data["shoulder_width_ratio"] = float(shoulder_sep_x / torso_len)

        # Facing direction estimation
        if prim_knee["status"] in ["OBSERVED", "ESTIMATED"] and prim_hip["status"] in ["OBSERVED", "ESTIMATED"]:
            knee_hip_dx = prim_knee["pt"][0] - prim_hip["pt"][0]
            if abs(knee_hip_dx) > 15:
                data["facing_dir"] = "right" if knee_hip_dx > 0 else "left"

        # Barbell detection & tracking with velocity gating and One-Euro smoothing
        bar_raw, bar_status = self._track_barbell_sleeve(frame, prim_shoulder, prim_hip, torso_len, prev_bar_pos)
        if bar_raw is not None and bar_status in ["OBSERVED", "ESTIMATED"]:
            smoothed_bar, _ = bar_filter.update(timestamp, bar_raw)
            data["bar_pos"] = smoothed_bar
            data["bar_status"] = bar_status
        else:
            smoothed_bar, st = bar_filter.update(timestamp, None)
            data["bar_pos"] = smoothed_bar
            data["bar_status"] = st

        return data

    def _track_barbell_sleeve(self, frame, prim_shoulder, prim_hip, torso_len, prev_bar_pos):
        """
        Locates the barbell sleeve/plate center.
        Features:
        1. Plate red/orange collar and sleeve hub detection in HSV space.
        2. Circular Hough Transform on plate hub.
        3. Velocity gating: rejects jumps > 80 pixels/frame from previous bar position.
        4. Shoulder/wrist anatomical proxy only when sleeve detection fails (explicitly tagged ESTIMATED).
        5. Refuses tracking and returns LOST if out of anatomical boundaries.
        """
        h, w = frame.shape[:2]

        # Determine search anchor
        if prim_shoulder["status"] in ["OBSERVED", "ESTIMATED"]:
            sh_x, sh_y = prim_shoulder["pt"]
        elif prev_bar_pos is not None:
            sh_x, sh_y = prev_bar_pos
        else:
            return None, "LOST"

        search_rad = int(torso_len * 0.55) if torso_len else 90

        # Anchor ROI around shoulder/plate zone
        x_min = max(0, int(sh_x - search_rad * 1.3))
        x_max = min(w, int(sh_x + search_rad * 1.3))
        y_min = max(0, int(sh_y - search_rad * 0.8))
        y_max = min(h, int(sh_y + search_rad * 1.0))

        if x_max - x_min < 20 or y_max - y_min < 20:
            if prev_bar_pos is not None:
                return prev_bar_pos, "ESTIMATED"
            return None, "LOST"

        roi = frame[y_min:y_max, x_min:x_max]

        # Method 1: Red/orange sleeve collar detection (standard Olympic plates & lock collars)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([12, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([168, 70, 50]), np.array([180, 255, 255]))
        red_mask = mask1 | mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_red_center = None
        best_red_dist = float("inf")

        for c in contours:
            area = cv2.contourArea(c)
            if 60 < area < 12000:
                (cx, cy), radius = cv2.minEnclosingCircle(c)
                gx = x_min + cx
                gy = y_min + cy

                # Velocity gating: check distance from previous position
                if prev_bar_pos is not None:
                    d_prev = np.hypot(gx - prev_bar_pos[0], gy - prev_bar_pos[1])
                    if d_prev < 80.0 and d_prev < best_red_dist:
                        best_red_dist = d_prev
                        best_red_center = (float(gx), float(gy))
                else:
                    d_sh = np.hypot(gx - sh_x, gy - sh_y)
                    if d_sh < search_rad and d_sh < best_red_dist:
                        best_red_dist = d_sh
                        best_red_center = (float(gx), float(gy))

        if best_red_center is not None:
            return best_red_center, "OBSERVED"

        # Method 2: Circular Hough Transform on plate sleeve hub
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
                    if d < 75.0 and d < best_c_dist:
                        best_c_dist = d
                        best_circle = (float(gx), float(gy))
                else:
                    d = np.hypot(gx - sh_x, gy - sh_y)
                    if d < best_c_dist:
                        best_c_dist = d
                        best_circle = (float(gx), float(gy))

            if best_circle is not None:
                return best_circle, "OBSERVED"

        # Method 3: Velocity-gated hold of previous position (ESTIMATED)
        if prev_bar_pos is not None:
            # Check if previous bar pos is still within plausible distance to shoulder
            if np.hypot(prev_bar_pos[0] - sh_x, prev_bar_pos[1] - sh_y) < search_rad * 1.5:
                return prev_bar_pos, "ESTIMATED"

        # Method 4: Anatomical shoulder proxy (ESTIMATED)
        if prim_shoulder["status"] == "OBSERVED":
            return (float(sh_x), float(sh_y)), "ESTIMATED"

        return None, "LOST"
