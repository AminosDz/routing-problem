class Instance:

    def __init__(self, node_count, edge_count, constraints_count, flow_count,
                nodes_list, edges_list, groups, demands_list ) -> None:
        
        self.node_count = node_count
        self.edge_count = edge_count
        self.constraints_count = constraints_count
        self.flow_count = flow_count
        
        self.nodes_list = nodes_list
        self.edges_list = edges_list
        self.groups = groups
        self.demands_list = demands_list
