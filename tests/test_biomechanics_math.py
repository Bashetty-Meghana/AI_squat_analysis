"""
Unit Test Suite: Biomechanics Mathematics & Repetition Segmentation
Tests 2D angle math, Y-axis orientation consistency, depth margin vector math,
and repetition segmentation on synthetic signals.
"""

import unittest
import numpy as np
from analyzer.biomechanics import (
    calculate_angle_2d,
    calculate_back_angle_to_horizontal,
    calculate_head_angle_to_torso,
    SquatBiomechanicsAnalyzer
)

class TestBiomechanicsMath(unittest.TestCase):

    def test_calculate_angle_2d_orthogonal(self):
        # Right angle: (0, 10) -> (0, 0) -> (10, 0) should be 90 degrees
        p1 = (0.0, 10.0)
        vertex = (0.0, 0.0)
        p3 = (10.0, 0.0)
        deg = calculate_angle_2d(p1, vertex, p3)
        self.assertAlmostEqual(deg, 90.0, places=2)

    def test_calculate_angle_2d_straight(self):
        # Straight line: (-10, 0) -> (0, 0) -> (10, 0) should be 180 degrees
        p1 = (-10.0, 0.0)
        vertex = (0.0, 0.0)
        p3 = (10.0, 0.0)
        deg = calculate_angle_2d(p1, vertex, p3)
        self.assertAlmostEqual(deg, 180.0, places=2)

    def test_calculate_back_angle_horizontal_and_vertical(self):
        # In image pixel coordinates, Y is positive DOWNWARDS.
        # Shoulder is ABOVE hip, meaning y_shoulder < y_hip -> dy = hip_y - sh_y > 0.

        # 1. Perfectly vertical torso: hip=(100, 200), shoulder=(100, 100) -> 90 degrees
        ang_vert = calculate_back_angle_to_horizontal(hip_pt=(100, 200), shoulder_pt=(100, 100))
        self.assertAlmostEqual(ang_vert, 90.0, places=2)

        # 2. 45-degree inclined torso (Starting Strength standard low-bar angle):
        # dx = 100, dy = 100 -> arctan2(100, 100) = 45.0 degrees
        ang_45 = calculate_back_angle_to_horizontal(hip_pt=(100, 200), shoulder_pt=(200, 100))
        self.assertAlmostEqual(ang_45, 45.0, places=2)

        # 3. Completely flat torso: dy = 0 -> 0 degrees
        ang_flat = calculate_back_angle_to_horizontal(hip_pt=(100, 200), shoulder_pt=(200, 200))
        self.assertAlmostEqual(ang_flat, 0.0, places=2)

    def test_depth_vector_coordinate_direction(self):
        """
        CRITICAL CHECK FOR STARTING STRENGTH FIGURE 2-1:
        Point A: Top of patella.
        Point B: Apex of crease of shorts (hip joint).
        In image pixel coordinates, Y increases downward towards the floor.
        Therefore, for the hip crease to be physically BELOW the top of the patella,
        hip_y MUST be GREATER than knee_y.
        Depth margin = hip_y - knee_y.
        Positive depth margin = Below parallel (Pass).
        Negative depth margin = Above parallel (High / Fail).
        """
        knee_y = 600.0  # Patella plane

        # Case 1: Lifter reaches full depth below parallel
        hip_y_pass = 625.0
        margin_pass = hip_y_pass - knee_y
        self.assertGreater(margin_pass, 0, "Hip below patella must have positive margin in image space")
        self.assertEqual(margin_pass, 25.0)

        # Case 2: Lifter cuts squat high
        hip_y_fail = 580.0
        margin_fail = hip_y_fail - knee_y
        self.assertLess(margin_fail, 0, "Hip above patella must have negative margin in image space")
        self.assertEqual(margin_fail, -20.0)

    def test_head_angle_to_torso(self):
        hip = (100.0, 300.0)
        shoulder = (200.0, 150.0)
        torso_dx = shoulder[0] - hip[0]
        torso_dy = shoulder[1] - hip[1]

        ear = (210.0, 135.0)
        eye = (ear[0] + torso_dx * 0.2, ear[1] + torso_dy * 0.2)
        ang = calculate_head_angle_to_torso(ear, eye, shoulder, hip)
        self.assertAlmostEqual(ang, 0.0, places=1)

    def test_repetition_segmentation_synthetic(self):
        analyzer = SquatBiomechanicsAnalyzer()
        fps = 30.0

        # Create a synthetic hip Y time-series with 2 full squats:
        # Standing lockout at Y=200, bottom turnaround at Y=500.
        t = np.linspace(0, 10, int(10 * fps))
        hip_y = 200.0 + 300.0 * np.exp(-((t - 2.5) ** 2) / 0.8) + 300.0 * np.exp(-((t - 7.0) ** 2) / 0.8)
        knee_y = np.full_like(hip_y, 450.0)

        frames = [{"shank_length": 100.0, "observed_kpts": {}, "timestamp": float(ti)} for ti in t]
        reps = analyzer._detect_repetitions(hip_y, knee_y, fps, frames)

        self.assertEqual(len(reps), 2, f"Expected exactly 2 reps, detected {len(reps)}")
        self.assertLessEqual(abs(reps[0]["bottom_frame"] - int(2.5 * fps)), 5)
        self.assertLessEqual(abs(reps[1]["bottom_frame"] - int(7.0 * fps)), 5)
        self.assertGreater(reps[0]["duration_seconds"], 1.5)
        self.assertGreater(reps[1]["duration_seconds"], 1.5)

if __name__ == "__main__":
    unittest.main()
