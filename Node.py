class Node:

    def __init__(self, node_id, SFL = 200) -> None:
        self.node_id = node_id
        self.is_final = False
        self.SFL = SFL
        self.neighbors = {}

    def set_final(self):
        self.is_final = True 
    def add_edge(self, edge):
        other_node = edge.start_id if self.node_id != edge.start_id else edge.end_id

        if other_node in self.neighbors:
            self.neighbors[other_node].append(edge)
        else:
            self.neighbors[other_node] = [edge]

    def decrease_SFL(self, value=1):
        self.SFL -= value

    def next_node(self, edge):
        return edge.start_id if self.node_id != edge.start_id else edge.end_id
