import unittest
import subprocess
import json
import time

ENCODINGS = [
    "pairwise",
    "binary",
    "sequential",
    "commander",
    "product"
]

EXPECTED_COUNTS = {
    "pairwise": {"primary": 10000, "auxiliary": 0, "total": 10000, "clauses": 1646900},
    "binary": {"primary": 10000, "auxiliary": 3678, "total": 13678, "clauses": 269024},
    "sequential": {"primary": 10000, "auxiliary": 39402, "total": 49402, "clauses": 117812},
    "commander": {"primary": 10000, "auxiliary": 20536, "total": 30536, "clauses": 118092},
    "product": {"primary": 10000, "auxiliary": 9492, "total": 19492, "clauses": 116672}
}

class TestN100AllEncodings(unittest.TestCase):
    def test_n100(self):
        N = 100
        TIMEOUT = 300
        
        for enc_name in ENCODINGS:
            with self.subTest(encoding=enc_name):
                # We need to run each in a subprocess to respect memory limits and timeout
                cmd = [
                    ".venv/bin/python", "-m", "src.sat.solver",
                    "--n", str(N),
                    "--encoding", enc_name,
                    "--json"
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, check=True)
                    data = json.loads(result.stdout)
                    
                    self.assertEqual(data["status"], "SAT", f"Expected SAT for {enc_name}")
                    self.assertTrue(data["valid"], f"Expected valid=True for {enc_name}")
                    self.assertEqual(len(data["positions"]), N, f"Expected {N} queens for {enc_name}")
                    
                    expected = EXPECTED_COUNTS[enc_name]
                    self.assertEqual(data["primary_variables"], expected["primary"], f"Wrong primary_variables for {enc_name}")
                    self.assertEqual(data["auxiliary_variables"], expected["auxiliary"], f"Wrong auxiliary_variables for {enc_name}")
                    self.assertEqual(data["total_variables"], expected["total"], f"Wrong total_variables for {enc_name}")
                    self.assertEqual(data["clauses"], expected["clauses"], f"Wrong clauses for {enc_name}")
                    
                    # We also expect phase_policy in result
                    self.assertIn("phase_policy", data)
                    
                except subprocess.TimeoutExpired:
                    self.fail(f"Encoding {enc_name} TIMEOUT after {TIMEOUT} seconds for N={N}")
                except subprocess.CalledProcessError as e:
                    self.fail(f"Encoding {enc_name} ERROR: process exited with code {e.returncode}\nstderr: {e.stderr}")
                except json.JSONDecodeError:
                    self.fail(f"Encoding {enc_name} ERROR: could not parse JSON output")

if __name__ == '__main__':
    unittest.main()
