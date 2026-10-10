import unittest
from ortools.sat.python import cp_model

from src.cp_sat.solver import build_nqueens_model

class TestCPSATModel(unittest.TestCase):
    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            build_nqueens_model(0)
        with self.assertRaises(ValueError):
            build_nqueens_model(-1)
            
    def test_n1(self):
        model, queens = build_nqueens_model(1)
        self.assertEqual(len(queens), 1)
        # Validate model structure implicitly (OR-Tools model validation returns empty string if valid)
        self.assertEqual(model.Validate(), '')

    def test_n4(self):
        model, queens = build_nqueens_model(4)
        self.assertEqual(len(queens), 4)
        self.assertEqual(model.Validate(), '')

    def test_n8(self):
        model, queens = build_nqueens_model(8)
        self.assertEqual(len(queens), 8)
        self.assertEqual(model.Validate(), '')

    def test_deterministic_model_construction(self):
        model1, queens1 = build_nqueens_model(10)
        model2, queens2 = build_nqueens_model(10)
        
        # Check string representation or structure length
        self.assertEqual(str(model1.Proto()), str(model2.Proto()))

if __name__ == '__main__':
    unittest.main()
