from heuristics import Solver
from reader import read_instance
from writer import write_flows
from Flow import Flow

instance = read_instance(path="data/input.txt")

solver = Solver(instance)

flows = solver.solve( criteria="min_dist", order=False)
write_flows(flows)
