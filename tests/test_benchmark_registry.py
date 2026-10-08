import unittest
from experiments.solver_registry import METHODS, REGISTRY, build_cli_command

class TestBenchmarkRegistry(unittest.TestCase):
    def test_nine_methods(self):
        self.assertEqual(len(METHODS), 9)
        self.assertEqual(len(REGISTRY), 9)
        
    def test_method_metadata(self):
        for method in METHODS:
            meta = REGISTRY[method]
            self.assertIn("method_family", meta)
            self.assertIn("module", meta)
            
    def test_build_cli_command_sat(self):
        config = {"sat_phase_policy": "solver_default", "timeout": 300}
        cmd = build_cli_command("sat_pairwise", 4, config)
        self.assertIn("--encoding", cmd)
        self.assertIn("pairwise", cmd)
        self.assertIn("--phase-policy", cmd)
        self.assertIn("solver_default", cmd)
        self.assertNotIn("--time-limit", cmd)
        
    def test_build_cli_command_cp_sat(self):
        config = {"workers": 2, "random_seed": 42, "timeout": 300}
        cmd = build_cli_command("cp_sat", 4, config)
        self.assertIn("--workers", cmd)
        self.assertIn("2", cmd)
        self.assertIn("--random-seed", cmd)
        self.assertIn("42", cmd)
        self.assertIn("--time-limit", cmd)
        self.assertNotIn("--encoding", cmd)
        
    def test_build_cli_command_gurobi(self):
        config = {"workers": 4, "random_seed": 10, "timeout": 150}
        cmd = build_cli_command("gurobi_mip", 8, config)
        self.assertIn("--threads", cmd)
        self.assertIn("4", cmd)
        self.assertIn("--random-seed", cmd)
        self.assertIn("10", cmd)
        self.assertNotIn("--encoding", cmd)

