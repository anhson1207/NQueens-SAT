import docplex.cp.model as cp
from docplex.cp.utils import CpoException
try:
    model = cp.CpoModel()
    n = 100
    queens = model.integer_var_list(n, 0, n - 1, "q")
    model.add(model.all_diff(queens))
    model.add(model.all_diff([queens[i] - i for i in range(n)]))
    model.add(model.all_diff([queens[i] + i for i in range(n)]))
    print("Model built")
    res = model.solve(LogVerbosity="Quiet")
    if res.is_solution():
        print("CP Engine: AVAILABLE for N=100")
    else:
        print("CP Engine: UNKNOWN_STATUS")
        print("Solve status:", res.get_solve_status())
        print("Stop cause:", res.get_stop_cause())
        if res.get_solve_status() == "Unknown" and str(res.get_stop_cause()) == "Unknown":
            print("Possible License Limit")
except CpoException as e:
    print("CpoException:", e)
except Exception as e:
    print("Exception:", e)
