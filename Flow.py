class Flow:

    def __init__(self, demand, edge_ids) -> None:
        self.flow_id = demand.demand_id
        self.flow_rate = demand.flow_rate
        if demand.inverted:
            self.edge_ids = list(reversed(edge_ids)) 
            self.start_id = demand.end_id
            self.end_id = demand.start_id
        else: 
            self.edge_ids = edge_ids
            self.start_id = demand.start_id
            self.end_id = demand.end_id
