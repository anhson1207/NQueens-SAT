import unittest
from src.gurobi.solver import solve_nqueens_gurobi

class TestLargeGurobiSolver(unittest.TestCase):
    def test_solve_n20(self):
        result = solve_nqueens_gurobi(20, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("Gurobi restricted license blocked solving for N=20.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 20)

    def test_solve_n50(self):
        result = solve_nqueens_gurobi(50, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("Gurobi restricted license blocked solving for N=50.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 50)

    def test_solve_n100(self):
        result = solve_nqueens_gurobi(100, log_output=False)
        if result["status"] == "LICENSE_ERROR":
            self.skipTest("Gurobi restricted license blocked solving for N=100.")
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 100)

if __name__ == "__main__":
    unittest.main()

