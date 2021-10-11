from Instance import Instance
from collections import deque
from Flow import Flow

class Solver():
    def __init__(self, instance):
        self.instance = instance
    
    def solve(self, criteria = "max_cap", order = None):
        
        flows_list = []

        if order:
            sorted_demands = sorted(self.instance.demands_list,
                key= lambda d: d.flow_rate, reverse=order)

        for demand in self.instance.demands_list:
            flow = self.get_path_bfs(demand, criteria=criteria)
            if flow:
                flows_list.append(flow)
                self.update_graph(flow)
        return flows_list

    def update_graph(self, flow):
        node_id = flow.start_id
        edge_ids = flow.edge_ids
        #update first node SFL
        node = self.instance.nodes_list[node_id]
        node.decrease_SFL()
        for edge_id in edge_ids:
            #update edge capacity
            edge = self.instance.edges_list[edge_id]
            edge.update_capacity(flow.flow_rate)
            #update group GFL
            self.instance.groups[edge.group_id].update_GFL()
            #get next node
            next_node_id = node.next_node(edge)
            node = self.instance.nodes_list[next_node_id]
            #update node SFL
            node.decrease_SFL()
            
    def get_path_bfs(self, demand, criteria = "max_cap"):

        visited = set() 
        queue= deque()
  
        # Mark the source node as visited and enqueue it
        queue.append((demand.start_id, []))
        visited.add(demand.start_id)
        edges_list = []
        while queue:
 
            #Dequeue a vertex from queue
            n, cur_path = queue.popleft()
            
            # If this adjacent node is the destination node,
            # then return true
            if n == demand.end_id:
                flow = Flow(demand, cur_path)
                return flow

            #  Else, continue to do BFS
            for i in self.instance.nodes_list[n].neighbors:
                
                if i not in visited and self.instance.nodes_list[i].SFL > 0:
                    edges_n_i = self.instance.nodes_list[n].neighbors[i]
                    #print(cur_path)
                    prev_edge = self.instance.edges_list[cur_path[-1]] if len(cur_path) else None
                    chosen_edge = self.choose_edge_bfs(edges_n_i, demand,
                        prev_edge, criteria = criteria)

                    if chosen_edge:
                        cur_path = cur_path.copy()
                        cur_path.append(chosen_edge.edge_id)
                        queue.append((i, cur_path))
                        visited.add(i)
        # If BFS is complete without visited d
        return None
    
    def choose_edge_bfs(self, edges, demand, prev_edge, criteria = "min_dist"):

        possible_edges = []
        min_dist_edge = None 
        max_capacity_edge = None
        for edge in edges:
            
            # Verify constraint
            if prev_edge and edge.is_constrained(prev_edge):
                continue

            #Verify group gfl
            if self.instance.groups[edge.group_id].GFL == 0:
                continue 

            # Verify edge capacity
            if edge.can_add_demand(demand):
                possible_edges.append(edge.edge_id)

                if not min_dist_edge or edge.distance < min_dist_edge.distance:
                    min_dist_edge = edge 

                if not max_capacity_edge or edge.capacity > max_capacity_edge.capacity:
                    max_capacity_edge = edge
        
        if criteria == "min_dist":
            return min_dist_edge
        elif criteria == "max_cap":
            return max_capacity_edge
        else:
            return None if len(possible_edges) == 0 else possible_edges[0]

        
