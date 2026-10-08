import unittest
from src.gurobi.solver import solve_nqueens_gurobi

class TestGurobiSolver(unittest.TestCase):
    def test_solve_n1(self):
        result = solve_nqueens_gurobi(1, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 1)
        self.assertEqual(result["positions"][0], (0, 0))

    def test_solve_n2(self):
        result = solve_nqueens_gurobi(2, log_output=False)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["valid"])

    def test_solve_n3(self):
        result = solve_nqueens_gurobi(3, log_output=False)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["valid"])

    def test_solve_n4(self):
        result = solve_nqueens_gurobi(4, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 4)

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(0)
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(-1)
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(4, time_limit=-1.0)
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(4, time_limit=0)
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(4, threads=0)
        with self.assertRaises(ValueError):
            solve_nqueens_gurobi(4, threads=-1)

if __name__ == "__main__":
    unittest.main()

