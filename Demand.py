class Demand:

    def __init__(self, demand_id, start_id, end_id, flow_rate, inverted = False) -> None:
        self.demand_id = demand_id
        self.start_id = start_id
        self.end_id = end_id
        self.flow_rate = flow_rate
        self.inverted = inverted
