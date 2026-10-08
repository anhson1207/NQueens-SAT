import unittest
from src.cp_sat.solver import solve_nqueens_cp_sat
from src.sat.solver import solve_nqueens_pairwise

class TestCPSATvsSAT(unittest.TestCase):
    def test_cp_sat_vs_sat(self):
        N_VALUES = [1, 2, 3, 4, 5, 8]
        
        for n in N_VALUES:
            with self.subTest(n=n):
                sat_result = solve_nqueens_pairwise(n)
                cp_sat_result = solve_nqueens_cp_sat(n)
                
                self.assertEqual(sat_result["status"], cp_sat_result["status"], f"Status mismatch for N={n}")
                if sat_result["status"] == "SAT":
                    self.assertTrue(sat_result["valid"])
                    self.assertTrue(cp_sat_result["valid"])

if __name__ == '__main__':
    unittest.main()

