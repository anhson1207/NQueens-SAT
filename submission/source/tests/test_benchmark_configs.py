import unittest
from experiments.benchmark_runner import generate_schedule

class TestBenchmarkConfigs(unittest.TestCase):
    def test_schedule_generation(self):
        methods = ["sat_pairwise", "cp_sat"]
        n_values = [4, 8]
        repeats = 2
        schedule = generate_schedule(n_values, methods, repeats, 42)
        
        # Warmup: 2 methods * 1 repeat (N=4) = 2 trials
        # Official: 2 methods * 2 N_values * 2 repeats = 8 trials
        # Total = 10
        self.assertEqual(len(schedule), 10)
        
        warmups = [t for t in schedule if t["is_warmup"]]
        self.assertEqual(len(warmups), 2)
        
        officials = [t for t in schedule if not t["is_warmup"]]
        self.assertEqual(len(officials), 8)
        
        # Check distribution
        for r in range(1, repeats + 1):
            for n in n_values:
                trials_rn = [t for t in officials if t["repetition"] == r and t["n"] == n]
                self.assertEqual(len(trials_rn), len(methods))
                
    def test_schedule_determinism(self):
        s1 = generate_schedule([4,8], ["m1", "m2", "m3"], 2, 42)
        s2 = generate_schedule([4,8], ["m1", "m2", "m3"], 2, 42)
        self.assertEqual(s1, s2)
        
        s3 = generate_schedule([4,8], ["m1", "m2", "m3"], 2, 99)
        self.assertNotEqual(s1, s3)

