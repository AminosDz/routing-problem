class Group:

    def __init__(self, group_id, edges_list = [], GFL = 100) -> None:
        self.group_id = group_id
        self.edge_ids_list = edges_list
        self.GFL = GFL

    def update_GFL(self, value=1):
        self.GFL -= value

    def add_edge(self, edge_id):
        self.edge_ids_list.append(edge_id)
