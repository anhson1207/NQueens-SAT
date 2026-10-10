import unittest
from src.cplex_mip.solver import solve_nqueens_cplex_mip
from src.gurobi.solver import solve_nqueens_gurobi

class TestCplexMipVsGurobi(unittest.TestCase):
    def test_cross_check_n_4_to_12(self):
        for n in range(4, 13):
            cplex_result = solve_nqueens_cplex_mip(n, log_output=False)
            gurobi_result = solve_nqueens_gurobi(n, log_output=False)
            
            if cplex_result["status"] == "LICENSE_ERROR" or gurobi_result["status"] == "LICENSE_ERROR":
                continue
                
            self.assertEqual(cplex_result["status"], gurobi_result["status"], f"Status mismatch at N={n}")
            
            if cplex_result["status"] == "SAT":
                self.assertTrue(cplex_result["valid"], f"CPLEX invalid at N={n}")
                self.assertTrue(gurobi_result["valid"], f"Gurobi invalid at N={n}")

if __name__ == "__main__":
    unittest.main()

