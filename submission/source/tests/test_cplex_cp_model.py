import unittest
from src.cplex_cp.solver import build_nqueens_model

class TestCplexCpModel(unittest.TestCase):
    def test_build_model_n1(self):
        model, queens = build_nqueens_model(1)
        self.assertEqual(len(queens), 1)
        self.assertEqual(len(model.get_all_variables()), 1)

    def test_build_model_n4(self):
        model, queens = build_nqueens_model(4)
        self.assertEqual(len(queens), 4)
        self.assertEqual(len(model.get_all_variables()), 4)

    def test_build_model_n8(self):
        model, queens = build_nqueens_model(8)
        self.assertEqual(len(queens), 8)
        self.assertEqual(len(model.get_all_variables()), 8)

    def test_build_model_n20(self):
        model, queens = build_nqueens_model(20)
        self.assertEqual(len(queens), 20)
        self.assertEqual(len(model.get_all_variables()), 20)
        
    def test_build_model_n100(self):
        model, queens = build_nqueens_model(100)
        self.assertEqual(len(queens), 100)
        self.assertEqual(len(model.get_all_variables()), 100)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            build_nqueens_model(0)
        with self.assertRaises(ValueError):
            build_nqueens_model(-1)

if __name__ == "__main__":
    unittest.main()

