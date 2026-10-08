import unittest
from src.cplex_cp.solver import solve_nqueens_cplex_cp

class TestLargeCplexCpSolver(unittest.TestCase):
    def test_solve_n20(self):
        result = solve_nqueens_cplex_cp(20, log_output=False)
        if result["status"] in ("LICENSE_ERROR", "MISSING_CP_ENGINE"):
            self.skipTest(f"CPLEX CP blocked solving for N=20: {result['status']}")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 20)

    def test_solve_n50(self):
        result = solve_nqueens_cplex_cp(50, log_output=False)
        if result["status"] in ("LICENSE_ERROR", "MISSING_CP_ENGINE"):
            self.skipTest(f"CPLEX CP blocked solving for N=50: {result['status']}")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 50)

    def test_solve_n100(self):
        result = solve_nqueens_cplex_cp(100, log_output=False)
        if result["status"] in ("LICENSE_ERROR", "MISSING_CP_ENGINE"):
            self.skipTest(f"CPLEX CP blocked solving for N=100: {result['status']}")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 100)

if __name__ == "__main__":
    unittest.main()

