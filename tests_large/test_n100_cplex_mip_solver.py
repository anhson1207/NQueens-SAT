import unittest
from src.cplex_mip.solver import solve_nqueens_cplex_mip

class TestLargeCplexMipSolver(unittest.TestCase):
    def test_solve_n20(self):
        result = solve_nqueens_cplex_mip(20, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("CPLEX license blocked solving for N=20.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 20)

    def test_solve_n50(self):
        result = solve_nqueens_cplex_mip(50, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("CPLEX license blocked solving for N=50.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 50)

    def test_solve_n100(self):
        result = solve_nqueens_cplex_mip(100, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("CPLEX license blocked solving for N=100.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 100)

if __name__ == "__main__":
    unittest.main()

