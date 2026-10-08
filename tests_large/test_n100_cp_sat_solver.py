import unittest
import subprocess
import json

class TestLargeCPSATSolver(unittest.TestCase):
    def run_cp_sat(self, n, timeout=315):
        cmd = [
            ".venv/bin/python", "-m", "src.cp_sat.solver",
            "--n", str(n),
            "--time-limit", "300.0",
            "--json"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
            data = json.loads(result.stdout)
            return data
        except subprocess.TimeoutExpired:
            self.fail(f"CP-SAT TIMEOUT after {timeout} seconds for N={n}")
        except subprocess.CalledProcessError as e:
            self.fail(f"CP-SAT ERROR: process exited with code {e.returncode}\nstderr: {e.stderr}")
        except json.JSONDecodeError:
            self.fail(f"CP-SAT ERROR: could not parse JSON output")

    def test_n020(self):
        data = self.run_cp_sat(20)
        self.assertEqual(data["status"], "SAT")
        self.assertTrue(data["valid"])
        self.assertEqual(len(data["positions"]), 20)
        self.assertEqual(data["decision_variables"], 20)
        
    def test_n050(self):
        data = self.run_cp_sat(50)
        self.assertEqual(data["status"], "SAT")
        self.assertTrue(data["valid"])
        self.assertEqual(len(data["positions"]), 50)
        self.assertEqual(data["decision_variables"], 50)
        
    def test_n100(self):
        data = self.run_cp_sat(100)
        self.assertEqual(data["status"], "SAT")
        self.assertTrue(data["valid"])
        self.assertEqual(len(data["positions"]), 100)
        self.assertEqual(data["decision_variables"], 100)

if __name__ == '__main__':
    unittest.main()

