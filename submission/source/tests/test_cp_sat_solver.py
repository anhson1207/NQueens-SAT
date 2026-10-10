import unittest
from src.cp_sat.solver import solve_nqueens_cp_sat

class TestCPSATSolver(unittest.TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            solve_nqueens_cp_sat(0)
        with self.assertRaises(ValueError):
            solve_nqueens_cp_sat(4, time_limit=-1.0)
        with self.assertRaises(ValueError):
            solve_nqueens_cp_sat(4, workers=0)
            
    def test_solver_status_and_validity(self):
        EXPECTED_STATUS = {
            1: "SAT",
            2: "UNSAT",
            3: "UNSAT",
            4: "SAT",
            5: "SAT",
            8: "SAT",
        }
        for n, expected_status in EXPECTED_STATUS.items():
            with self.subTest(n=n):
                result = solve_nqueens_cp_sat(n)
                self.assertEqual(result["status"], expected_status, f"Failed for N={n}")
                
                if expected_status == "SAT":
                    self.assertTrue(result["valid"], f"Solution not valid for N={n}")
                    self.assertIsNotNone(result["positions"])
                    self.assertEqual(len(result["positions"]), n)
                else:
                    self.assertFalse(result["has_solution"])
                    self.assertIsNone(result["positions"])

    def test_solver_result_schema(self):
        result = solve_nqueens_cp_sat(4, time_limit=10.0, workers=2, random_seed=42)
        self.assertEqual(result["method"], "CP-SAT")
        self.assertEqual(result["time_limit"], 10.0)
        self.assertEqual(result["workers"], 2)
        self.assertEqual(result["random_seed"], 42)
        self.assertIn("build_time", result)
        self.assertIn("solve_time", result)
        self.assertIn("total_time", result)
        self.assertIn("statistics", result)
        self.assertIn("conflicts", result["statistics"])

if __name__ == '__main__':
    unittest.main()

