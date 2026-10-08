import unittest
import gurobipy as gp
from src.gurobi.solver import build_nqueens_model

class TestLargeGurobiModel(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env(empty=True)
        self.env.setParam("OutputFlag", 0)
        self.env.start()

    def tearDown(self):
        self.env.dispose()

    def test_build_model_n20(self):
        try:
            model, _ = build_nqueens_model(20, env=self.env)
            self.assertEqual(model.NumVars, 400)
            self.assertEqual(model.NumBinVars, 400)
            self.assertEqual(model.NumConstrs, 114)
        except gp.GurobiError as e:
            if "size-limited" in str(e).lower() or "size limited" in str(e).lower():
                self.skipTest("Gurobi restricted license blocked model building for N=20.")
            else:
                raise

    def test_build_model_n50(self):
        try:
            model, _ = build_nqueens_model(50, env=self.env)
            self.assertEqual(model.NumVars, 2500)
            self.assertEqual(model.NumBinVars, 2500)
            self.assertEqual(model.NumConstrs, 294)
        except gp.GurobiError as e:
            if "size-limited" in str(e).lower() or "size limited" in str(e).lower():
                self.skipTest("Gurobi restricted license blocked model building for N=50.")
            else:
                raise

    def test_build_model_n100(self):
        try:
            model, _ = build_nqueens_model(100, env=self.env)
            self.assertEqual(model.NumVars, 10000)
            self.assertEqual(model.NumBinVars, 10000)
            self.assertEqual(model.NumConstrs, 594)
        except gp.GurobiError as e:
            if "size-limited" in str(e).lower() or "size limited" in str(e).lower():
                self.skipTest("Gurobi restricted license blocked model building for N=100.")
            else:
                raise

if __name__ == "__main__":
    unittest.main()

