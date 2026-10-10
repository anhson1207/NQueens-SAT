import unittest
from src.cplex_cp.solver import solve_nqueens_cplex_cp

class TestCplexCpSolver(unittest.TestCase):
    def test_solve_n1(self):
        result = solve_nqueens_cplex_cp(1, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 1)

    def test_solve_n2(self):
        result = solve_nqueens_cplex_cp(2, log_output=False)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["valid"])

    def test_solve_n3(self):
        result = solve_nqueens_cplex_cp(3, log_output=False)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(result["has_solution"])
        self.assertIsNone(result["valid"])

    def test_solve_n4(self):
        result = solve_nqueens_cplex_cp(4, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 4)

    def test_solve_n5(self):
        result = solve_nqueens_cplex_cp(5, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 5)

    def test_solve_n8(self):
        result = solve_nqueens_cplex_cp(8, log_output=False)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["positions"]), 8)

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            solve_nqueens_cplex_cp(0)
        with self.assertRaises(ValueError):
            solve_nqueens_cplex_cp(4, time_limit=-1)
        with self.assertRaises(ValueError):
            solve_nqueens_cplex_cp(4, workers=0)
        with self.assertRaises(ValueError):
            solve_nqueens_cplex_cp(4, random_seed=-1)

if __name__ == "__main__":
    unittest.main()

