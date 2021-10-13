from Instance import Instance
from collections import deque
from Flow import Flow
import time
from itertools import combinations, chain, product

class Solver():
    def __init__(self, instance):
        self.instance = instance
        self.cache = {}

    def get_from_cache(self, demand):
        i, j = [demand.start_id, demand.end_id].sort()
        path = self.cache[(i, j)]
        first_edge = self.instance.edges_list[path[0]]
        
        if first_edge.start_id == demand.start_id:
            return path
        else:
            return path[::-1]
    
    def in_cache(self, node_ids):
        i, j = min(node_ids), max(node_ids)
        return (i, j) in self.cache

    def put_in_cache(self, demand, path):
        n_id = demand.start_id
        n = self.instance.nodes_list[n_id]
        nodes = [n]
        for edge_id in path:
            edge = self.instance.edges_list[edge_id]
            n_id = n.next_node(edge)
            n = self.instance.nodes_list[n_id]
            nodes.append(n)

        ## add all pairs of nodes if one node is final
        final_nodes = []
        other_nodes = []
        for i in range(len(nodes)):
            node = nodes[i]
            if nodes[i].is_final:
                final_nodes.append((i, node))
            else:
                other_nodes.append((i, node))

        #add all pairs of (final_node1, final_node2) to cache
        #add all pairs of one non_final and one final to cache
        for s, d in chain(combinations(final_nodes, 2), product(final_nodes, other_nodes)):
            s_index, s_node = s 
            d_index, d_node = d
            path_to_cache = path[s_index:d_index] + path[d_index:s_index]

            self.add_to_cache((s_node.node_id, d_node.node_id), path_to_cache)

    def add_to_cache(self, node_ids, path):
        i, j = min(node_ids), max(node_ids)
        
        if i == node_ids[0]:
            self.cache[(i, j)] = path
        else:
            self.cache[(i, j)] = path[::-1]
    
    def solve(self, tic, criteria = "max_cap", order = None, time_limit=1.9):
        
        flows_list = []
    
        
        if order:
            sorted_demands = sorted(self.instance.demands_list,
                key= lambda d: d.flow_rate, reverse=False)
        else:
            sorted_demands = self.instance.demands_list
    
        for demand in sorted_demands:
            if time.time() - tic < time_limit:
                flow = self.get_path_bfs(demand, tic, time_limit, criteria=criteria)
                if flow and self.check_path(flow):
                    flows_list.append(flow)
                    self.update_graph(flow)
            else:
                break
        
        x = 0
        if len(flows_list) == 0:
            while True:
                x += 1
    
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

    def check_path(self, flow):
        prev_edge = None
        for edge_id in flow.edge_ids:
            edge = self.instance.edges_list[edge_id]

            # Check capacity
            if flow.flow_rate > edge.capacity:
                return False

            # Check GFL
            if self.instance.groups[edge.group_id].GFL <= 0:
                return False

            # Check SFL
            if self.instance.nodes_list[edge.start_id].SFL <= 0:
                return False
            if self.instance.nodes_list[edge.end_id].SFL <= 0:
                return False

            # Check constrained
            if prev_edge and edge.is_constrained(prev_edge):
                return False

            prev_edge = edge
        
        return True

    def get_path_bfs(self, demand, tic, time_limit, criteria = "max_cap"):

        if self.instance.nodes_list[demand.start_id].SFL <= 0:
            return None
        visited = set() 
        queue= deque()
  
        # Mark the source node as visited and enqueue it
        queue.append((demand.start_id, []))
        visited.add(demand.start_id)
        while queue and (time.time() - tic < time_limit):
 
            #Dequeue a vertex from queue
            n, cur_path = queue.popleft()
            
            #check cache
            if self.in_cache((n, demand.end_id)):
                concat_path = cur_path + self.get_from_cache((n, demand.end_id))
                flow = Flow(demand, concat_path)
                if self.check_path(flow):
                    return flow  
            
            # If this adjacent node is the destination node,
            # then return true
            if n == demand.end_id:
                flow = Flow(demand, cur_path)
                self.put_in_cache(demand, cur_path)
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
                        new_path = cur_path.copy()
                        new_path.append(chosen_edge.edge_id)
                        queue.append((i, new_path))
                        visited.add(i)
        # If BFS is complete without visited d
        return None
    
    def choose_edge_bfs(self, edges, demand, prev_edge, criteria = "min_dist"):

        possible_edges = []
        min_dist_edge = None 
        max_capacity_edge = None
        last_edge = None
        for edge in edges:
            
            # Verify constraint
            if prev_edge and edge.is_constrained(prev_edge):
                continue

            #Verify group gfl
            if self.instance.groups[edge.group_id].GFL <= 0:
                continue 

            # Verify edge capacity
            if edge.can_add_demand(demand):
                possible_edges.append(edge)
                last_edge = edge

                if not min_dist_edge or edge.distance < min_dist_edge.distance:
                    min_dist_edge = edge 

                if not max_capacity_edge or edge.capacity > max_capacity_edge.capacity:
                    max_capacity_edge = edge

                if criteria == "first_found":
                    return last_edge

        if criteria == "min_dist":
            return min_dist_edge
        elif criteria == "max_cap":
            return max_capacity_edge
        else:
            return None if len(possible_edges) == 0 else possible_edges[0]
        
