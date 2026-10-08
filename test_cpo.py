import docplex.cp.model as cp
from docplex.cp.utils import CpoException
try:
    model = cp.CpoModel()
    a = model.integer_var(0, 1, "a")
    b = model.integer_var(0, 1, "b")
    model.add(model.all_diff([a, b]))
    print("Model built")
    res = model.solve(LogVerbosity="Quiet")
    if res.is_solution():
        print(f"CP Engine: AVAILABLE - a={res.get_value(a)}, b={res.get_value(b)}")
    else:
        print("CP Engine: UNKNOWN_STATUS")
        print("Solve status:", res.get_solve_status())
        print("Stop cause:", res.get_stop_cause())
except CpoException as e:
    print("CpoException:", e)
except Exception as e:
    print("Exception:", e)
