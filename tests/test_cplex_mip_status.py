import unittest
from src.cplex_mip.solver import classify_cplex_status

class TestCplexMipStatus(unittest.TestCase):
    def test_classify_cplex_status(self):
        self.assertEqual(classify_cplex_status(101, "MIP optimal", True), "SAT")
        self.assertEqual(classify_cplex_status(101, "MIP optimal", False), "UNKNOWN")
        
        self.assertEqual(classify_cplex_status(102, "MIP optimal tolerance", True), "SAT")
        self.assertEqual(classify_cplex_status(102, "MIP optimal tolerance", False), "UNKNOWN")
        
        self.assertEqual(classify_cplex_status(103, "MIP infeasible", False), "UNSAT")
        
        self.assertEqual(classify_cplex_status(107, "Time limit exceeded, integer solution", True), "SAT")
        self.assertEqual(classify_cplex_status(107, "Time limit exceeded, integer solution", False), "TIMEOUT")
        
        self.assertEqual(classify_cplex_status(108, "Time limit exceeded, no integer solution", False), "TIMEOUT")
        
        self.assertEqual(classify_cplex_status(1016, "Promotional version limits exceeded", False), "LICENSE_ERROR")
        
        self.assertEqual(classify_cplex_status(999, "Unknown code", False), "UNKNOWN")

if __name__ == "__main__":
    unittest.main()

