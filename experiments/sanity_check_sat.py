import argparse
import json
import subprocess
import sys
import time

ENCODINGS = ["pairwise", "binary", "sequential", "commander", "product"]

def run_sanity_check(n_values):
    all_passed = True
    
    for n in n_values:
        print(f"\nN = {n}")
        print("-" * 75)
        print(f"{'Encoding':<12} {'Status':<10} {'Valid':<7} {'Variables':<10} {'Clauses':<10} {'Total Time':<12}")
        print("-" * 75)
        
        for enc in ENCODINGS:
            cmd = [
                ".venv/bin/python", "-m", "src.sat.solver",
                "--n", str(n),
                "--encoding", enc,
                "--json"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    if "ERROR" in result.stdout:
                        try:
                            data = json.loads(result.stdout)
                            status = "ERROR"
                            valid = "N/A"
                            vars_ = "N/A"
                            cls_ = "N/A"
                            ttime = "N/A"
                        except:
                            status = "ERROR"
                            valid = "N/A"
                            vars_ = "N/A"
                            cls_ = "N/A"
                            ttime = "N/A"
                    else:
                        status = "ERROR"
                        valid = "N/A"
                        vars_ = "N/A"
                        cls_ = "N/A"
                        ttime = "N/A"
                    all_passed = False
                else:
                    data = json.loads(result.stdout)
                    status = data.get("status", "UNKNOWN")
                    valid = str(data.get("valid", "N/A"))
                    vars_ = str(data.get("total_variables", "N/A"))
                    cls_ = str(data.get("clauses", "N/A"))
                    ttime = data.get("total_time")
                    ttime_str = f"{ttime:.3f}s" if ttime is not None else "N/A"
                    
                    if status != "SAT" and status != "UNSAT":
                        all_passed = False
                    if status == "SAT" and valid != "True":
                        all_passed = False
                        
                print(f"{enc:<12} {status:<10} {valid:<7} {vars_:<10} {cls_:<10} {ttime_str:<12}")
            except subprocess.TimeoutExpired:
                print(f"{enc:<12} {'TIMEOUT':<10} {'N/A':<7} {'N/A':<10} {'N/A':<10} {'>300s':<12}")
                all_passed = False
            except Exception as e:
                print(f"{enc:<12} {'ERROR':<10} {'N/A':<7} {'N/A':<10} {'N/A':<10} {'N/A':<12}")
                all_passed = False
                
    print("\nSanity Check Result:", "PASS" if all_passed else "FAIL")
    return 0 if all_passed else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAT Framework Sanity Check")
    parser.add_argument("--n", type=int, nargs='+', default=[4], help="Board sizes to test")
    args = parser.parse_args()
    
    sys.exit(run_sanity_check(args.n))
