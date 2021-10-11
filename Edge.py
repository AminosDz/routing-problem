class Edge:

    def __init__(self, edge_id, group_id, start_id, end_id, distance, capacity) -> None:
        self.edge_id = edge_id
        self.group_id = group_id
        self.start_id = start_id
        self.end_id = end_id
        self.distance = distance
        self.capacity = capacity
        self.constrained_edges = set()

    def add_constraint(self, edge_id):
        self.constrained_edges.add(edge_id)

    def is_constrained(self, other_edge):
        return other_edge.edge_id in self.constrained_edges

    def update_capacity(self, value):
        self.capacity -= value

    def can_add_demand(self, demand):
        return self.capacity >= demand.flow_rate
    