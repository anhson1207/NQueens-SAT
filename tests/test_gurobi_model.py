import unittest
import gurobipy as gp
from src.gurobi.solver import build_nqueens_model

class TestGurobiModel(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env(empty=True)
        self.env.setParam("OutputFlag", 0)
        self.env.start()

    def tearDown(self):
        self.env.dispose()

    def test_build_model_n1(self):
        model, _ = build_nqueens_model(1, env=self.env)
        self.assertEqual(model.NumVars, 1)
        self.assertEqual(model.NumBinVars, 1)
        self.assertEqual(model.NumConstrs, 2)

    def test_build_model_n2(self):
        model, _ = build_nqueens_model(2, env=self.env)
        self.assertEqual(model.NumVars, 4)
        self.assertEqual(model.NumBinVars, 4)
        self.assertEqual(model.NumConstrs, 6)

    def test_build_model_n4(self):
        model, _ = build_nqueens_model(4, env=self.env)
        self.assertEqual(model.NumVars, 16)
        self.assertEqual(model.NumBinVars, 16)
        self.assertEqual(model.NumConstrs, 18)

    def test_build_model_n8(self):
        model, _ = build_nqueens_model(8, env=self.env)
        self.assertEqual(model.NumVars, 64)
        self.assertEqual(model.NumBinVars, 64)
        self.assertEqual(model.NumConstrs, 42)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            build_nqueens_model(0, env=self.env)
        with self.assertRaises(ValueError):
            build_nqueens_model(-1, env=self.env)

if __name__ == "__main__":
    unittest.main()

