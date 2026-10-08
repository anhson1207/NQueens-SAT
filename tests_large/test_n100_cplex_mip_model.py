import unittest
from src.cplex_mip.solver import build_nqueens_model

class TestLargeCplexMipModel(unittest.TestCase):
    def test_build_model_n20(self):
        model, _ = build_nqueens_model(20)
        self.assertEqual(model.number_of_variables, 400)
        self.assertEqual(model.number_of_binary_variables, 400)
        self.assertEqual(model.number_of_linear_constraints, 114)
        model.end()

    def test_build_model_n50(self):
        model, _ = build_nqueens_model(50)
        self.assertEqual(model.number_of_variables, 2500)
        self.assertEqual(model.number_of_binary_variables, 2500)
        self.assertEqual(model.number_of_linear_constraints, 294)
        model.end()

    def test_build_model_n100(self):
        model, _ = build_nqueens_model(100)
        self.assertEqual(model.number_of_variables, 10000)
        self.assertEqual(model.number_of_binary_variables, 10000)
        self.assertEqual(model.number_of_linear_constraints, 594)
        model.end()

if __name__ == "__main__":
    unittest.main()

