from docplex.mp.model import Model
model = Model()
x = model.binary_var_matrix(range(50), range(50), name="x")
for i in range(50):
    model.add_constraint(model.sum(x[i, j] for j in range(50)) == 1)
try:
    sol = model.solve()
    print("Solve details:", model.solve_details)
except Exception as e:
    import sys
    print("Exception type:", type(e))
    print("Exception message:", str(e))
