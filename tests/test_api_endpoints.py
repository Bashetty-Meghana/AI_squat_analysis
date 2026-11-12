"""
Unit & Integration Test Suite for FastAPI Endpoints
Tests health, sample listings, standards endpoint, and job submission with mocked worker.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from server import app

class TestFastAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "IronPath AI Squat Form Coach")

    def test_samples_endpoint(self):
        response = self.client.get("/api/samples")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)
        sample_ids = [s["id"] for s in data]
        self.assertIn("common_sample", sample_ids)
        self.assertIn("unsuitable_front_view", sample_ids)
        self.assertIn("unsuitable_poor_framing_occlusion", sample_ids)

    def test_standards_endpoint(self):
        response = self.client.get("/api/standards")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("criteria", data)
        self.assertEqual(len(data["criteria"]), 10)

    @patch("server.process_job_worker")
    def test_analyze_submission_sample(self, mock_worker):
        response = self.client.post("/api/analyze", data={"sample_id": "common_sample"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "QUEUED")

        # Check job status
        job_id = data["job_id"]
        status_res = self.client.get(f"/api/jobs/{job_id}")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertEqual(status_data["status"], "QUEUED")

    def test_analyze_invalid_sample_returns_400(self):
        response = self.client.post("/api/analyze", data={"sample_id": "non_existent_sample"})
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
