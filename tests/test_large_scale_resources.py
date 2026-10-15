import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import psutil

from experiments.large_scale.resources import guarded_process

ROOT = Path(__file__).resolve().parent.parent


class TestLargeScaleResources(unittest.TestCase):
    def test_fast_clean_exit(self):
        r = guarded_process(
            [sys.executable, "-c", "print('fast exit success')"],
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=5.0,
            memory_mb=2048.0,
            reserve_mb=0.0,
            sample_seconds=0.05,
        )
        self.assertIsNone(r["status"])
        self.assertEqual(r["returncode"], 0)
        self.assertIn("fast exit success", r["stdout"])

    def test_timeout_and_termination(self):
        code = "import time; time.sleep(10)"
        r = guarded_process(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=0.3,
            memory_mb=2048.0,
            reserve_mb=0.0,
            sample_seconds=0.05,
        )
        self.assertEqual(r["status"], "TIMEOUT")
        self.assertIn("timeout", r["error_message"].lower())

    def test_resource_limit_triggered(self):
        # Allocate 30MB while cap is 1MB
        code = "import time; x = bytearray(30 * 1024 * 1024); time.sleep(5)"
        r = guarded_process(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=5.0,
            memory_mb=1.0,
            reserve_mb=0.0,
            sample_seconds=0.05,
        )
        self.assertEqual(r["status"], "RESOURCE_LIMIT")
        self.assertIn("Tree RSS", r["error_message"])

    def test_child_process_tree_cleanup(self):
        code = (
            "import subprocess, sys, time; "
            "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
            "print(p.pid, flush=True); "
            "time.sleep(30)"
        )
        r = guarded_process(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=0.5,
            memory_mb=2048.0,
            reserve_mb=0.0,
            sample_seconds=0.05,
        )
        self.assertEqual(r["status"], "TIMEOUT")
        child_pid = int(r["stdout"].strip().splitlines()[0])
        self.assertTrue(
            not psutil.pid_exists(child_pid)
            or psutil.Process(child_pid).status() == psutil.STATUS_ZOMBIE,
            f"Child process {child_pid} was not cleaned up"
        )

    def test_monitoring_access_denied_handled(self):
        with patch("experiments.large_scale.resources.psutil.Process") as mock_psutil_proc:
            mock_psutil_proc.side_effect = psutil.AccessDenied(pid=12345)
            r = guarded_process(
                [sys.executable, "-c", "import time; time.sleep(1)"],
                cwd=ROOT,
                env=os.environ.copy(),
                timeout=5.0,
                memory_mb=2048.0,
                reserve_mb=0.0,
                sample_seconds=0.05,
            )
            self.assertEqual(r["status"], "MONITORING_ERROR")
            self.assertIn("access denied", r["error_message"].lower())


if __name__ == "__main__":
    unittest.main()

