import unittest
from src.cplex_mip.solver import build_nqueens_model

class TestCplexMipModel(unittest.TestCase):
    def test_build_model_n1(self):
        model, _ = build_nqueens_model(1)
        self.assertEqual(model.number_of_variables, 1)
        self.assertEqual(model.number_of_binary_variables, 1)
        self.assertEqual(model.number_of_linear_constraints, 2)
        model.end()

    def test_build_model_n2(self):
        model, _ = build_nqueens_model(2)
        self.assertEqual(model.number_of_variables, 4)
        self.assertEqual(model.number_of_binary_variables, 4)
        self.assertEqual(model.number_of_linear_constraints, 6)
        model.end()

    def test_build_model_n4(self):
        model, _ = build_nqueens_model(4)
        self.assertEqual(model.number_of_variables, 16)
        self.assertEqual(model.number_of_binary_variables, 16)
        self.assertEqual(model.number_of_linear_constraints, 18)
        model.end()

    def test_build_model_n8(self):
        model, _ = build_nqueens_model(8)
        self.assertEqual(model.number_of_variables, 64)
        self.assertEqual(model.number_of_binary_variables, 64)
        self.assertEqual(model.number_of_linear_constraints, 42)
        model.end()

    def test_build_model_n20(self):
        model, _ = build_nqueens_model(20)
        self.assertEqual(model.number_of_variables, 400)
        self.assertEqual(model.number_of_binary_variables, 400)
        self.assertEqual(model.number_of_linear_constraints, 114)
        model.end()

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            build_nqueens_model(0)
        with self.assertRaises(ValueError):
            build_nqueens_model(-1)

if __name__ == "__main__":
    unittest.main()

