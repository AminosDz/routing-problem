class Flow:

    def __init__(self, demand, edge_ids) -> None:
        self.flow_id = demand.demand_id
        self.edge_ids = edge_ids
        self.start_id = demand.start_id
        self.end_id = demand.end_id
        self.flow_rate = demand.flow_rate