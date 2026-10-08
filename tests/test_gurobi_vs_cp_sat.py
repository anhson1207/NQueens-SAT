import unittest
from src.gurobi.solver import solve_nqueens_gurobi
from src.cp_sat.solver import solve_nqueens_cp_sat

class TestGurobiVsCPSat(unittest.TestCase):
    def test_cross_check_n_4_to_12(self):
        for n in range(4, 13):
            cp_result = solve_nqueens_cp_sat(n)
            gurobi_result = solve_nqueens_gurobi(n, log_output=False)
            
            self.assertEqual(cp_result["status"], gurobi_result["status"], f"Status mismatch at N={n}")
            
            if cp_result["status"] == "SAT":
                self.assertTrue(cp_result["valid"], f"CP-SAT invalid at N={n}")
                self.assertTrue(gurobi_result["valid"], f"Gurobi invalid at N={n}")

if __name__ == "__main__":
    unittest.main()
