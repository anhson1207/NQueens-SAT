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

    def test_lost_monitor_while_process_alive_returns_monitoring_error(self):
        """Simulate the case where psutil raises NoSuchProcess while the child process is still running."""
        call_count = 0

        def failing_snapshot(root):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise psutil.NoSuchProcess(pid=root.pid)
            from experiments.large_scale.resources import process_snapshot
            return process_snapshot(root)

        with patch("experiments.large_scale.resources.process_snapshot", side_effect=failing_snapshot):
            r = guarded_process(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=ROOT,
                env=os.environ.copy(),
                timeout=3.0,
                memory_mb=2048.0,
                reserve_mb=0.0,
                sample_seconds=0.02,
            )
            self.assertEqual(r["status"], "MONITORING_ERROR")
            self.assertIn("Target process lost during monitoring while still alive", r["error_message"])

    def test_root_access_denied_in_snapshot_returns_monitoring_error(self):
        """Ensure AccessDenied on root process memory_info is not swallowed as 0 RAM."""
        def access_denied_snapshot(root):
            raise psutil.AccessDenied(pid=root.pid)

        with patch("experiments.large_scale.resources.process_snapshot", side_effect=access_denied_snapshot):
            r = guarded_process(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=ROOT,
                env=os.environ.copy(),
                timeout=2.0,
                memory_mb=2048.0,
                reserve_mb=0.0,
                sample_seconds=0.02,
            )
            self.assertEqual(r["status"], "MONITORING_ERROR")
            self.assertIn("access denied", r["error_message"].lower())

    def test_child_access_denied_distinguishes_alive_vs_dead(self):
        """process_snapshot re-raises AccessDenied if child is still running, but ignores if already dead."""
        from unittest.mock import MagicMock
        from experiments.large_scale.resources import process_snapshot

        mock_root = MagicMock()
        mock_root.memory_info.return_value.rss = 1000000

        # Case 1: Living child with AccessDenied
        mock_alive_child = MagicMock()
        mock_alive_child.memory_info.side_effect = psutil.AccessDenied(pid=999)
        mock_alive_child.is_running.return_value = True
        mock_root.children.return_value = [mock_alive_child]

        with self.assertRaises(psutil.AccessDenied):
            process_snapshot(mock_root)

        # Case 2: Dead child with AccessDenied
        mock_dead_child = MagicMock()
        mock_dead_child.memory_info.side_effect = psutil.AccessDenied(pid=998)
        mock_dead_child.is_running.return_value = False
        mock_root.children.return_value = [mock_dead_child]

        rss, living = process_snapshot(mock_root)
        self.assertEqual(rss, 1000000)
        self.assertEqual(living, [mock_root])

    def test_exit_code_and_normal_completion(self):
        r = guarded_process(
            [sys.executable, "-c", "import sys; sys.exit(42)"],
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=5.0,
            memory_mb=2048.0,
            reserve_mb=0.0,
            sample_seconds=0.05,
        )
        self.assertIsNone(r["status"])
        self.assertEqual(r["returncode"], 42)


if __name__ == "__main__":
    unittest.main()

