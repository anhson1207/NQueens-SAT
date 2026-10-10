import unittest
from src.cplex_cp.solver import solve_nqueens_cplex_cp
from src.cp_sat.solver import solve_nqueens_cp_sat

class TestCplexCpVsCpSat(unittest.TestCase):
    def test_cross_check_n_4_to_12(self):
        for n in range(4, 13):
            cplex_cp_result = solve_nqueens_cplex_cp(n, log_output=False)
            ortools_cp_result = solve_nqueens_cp_sat(n)
            
            if cplex_cp_result["status"] in ("LICENSE_ERROR", "MISSING_CP_ENGINE"):
                self.skipTest(f"CPLEX CP not available: {cplex_cp_result['status']}")
                
            self.assertEqual(cplex_cp_result["status"], ortools_cp_result["status"], f"Status mismatch at N={n}")
            
            if cplex_cp_result["status"] == "SAT":
                self.assertTrue(cplex_cp_result["valid"], f"CPLEX CP invalid at N={n}")
                self.assertTrue(ortools_cp_result["valid"], f"OR-Tools CP-SAT invalid at N={n}")

if __name__ == "__main__":
    unittest.main()

