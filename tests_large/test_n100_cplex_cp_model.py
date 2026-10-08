import unittest
from src.cplex_cp.solver import build_nqueens_model

class TestLargeCplexCpModel(unittest.TestCase):
    def test_build_model_n20(self):
        model, queens = build_nqueens_model(20)
        self.assertEqual(len(queens), 20)
        self.assertEqual(len(model.get_all_variables()), 20)

    def test_build_model_n50(self):
        model, queens = build_nqueens_model(50)
        self.assertEqual(len(queens), 50)
        self.assertEqual(len(model.get_all_variables()), 50)

    def test_build_model_n100(self):
        model, queens = build_nqueens_model(100)
        self.assertEqual(len(queens), 100)
        self.assertEqual(len(model.get_all_variables()), 100)

if __name__ == "__main__":
    unittest.main()

