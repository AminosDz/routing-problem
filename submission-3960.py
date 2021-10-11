from collections import deque
import time

class Demand:

    def __init__(self, demand_id, start_id, end_id, flow_rate) -> None:
        self.demand_id = demand_id
        self.start_id = start_id
        self.end_id = end_id
        self.flow_rate = flow_rate

class Flow:

    def __init__(self, demand, edge_ids) -> None:
        self.flow_id = demand.demand_id
        self.edge_ids = edge_ids
        self.start_id = demand.start_id
        self.end_id = demand.end_id
        self.flow_rate = demand.flow_rate

class Group:

    def __init__(self, group_id, edges_list = [], GFL = 100) -> None:
        self.group_id = group_id
        self.edge_ids_list = edges_list
        self.GFL = GFL

    def update_GFL(self, value=1):
        self.GFL -= value

    def add_edge(self, edge_id):
        self.edge_ids_list.append(edge_id)

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
    

class Instance:

    def __init__(self, node_count, edge_count, constraints_count, flow_count,
                nodes_list, edges_list, groups, demands_list) -> None:
        
        self.node_count = node_count
        self.edge_count = edge_count
        self.constraints_count = constraints_count
        self.flow_count = flow_count
        
        self.nodes_list = nodes_list
        self.edges_list = edges_list
        self.groups = groups
        self.demands_list = demands_list

class Node:

    def __init__(self, node_id, SFL = 200, is_sattelite = False) -> None:
        self.node_id = node_id
        self.is_sattelite = is_sattelite
        self.SFL = SFL
        self.neighbors = {}
        
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

class Solver():
    def __init__(self, instance):
        self.instance = instance
    
    def solve(self, criteria = "max_cap", order = None, time_limit=1.9):
        
        flows_list = []

        tic = time.time()
        if order:
            sorted_demands = sorted(self.instance.demands_list,
                key= lambda d: d.flow_rate, reverse=False)
        else:
            sorted_demands = self.instance.demands_list

        
        for demand in sorted_demands:
            if time.time() - tic < time_limit:
                flow = self.get_path_bfs(demand, criteria=criteria)
                if flow:
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
            if self.instance.groups[edge.group_id].GFL == 0:
                continue 

            # Verify edge capacity
            if edge.can_add_demand(demand):
                possible_edges.append(edge.edge_id)
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


def write_flows(flows):
    print(len(flows))
    for flow in flows:
        line = " ".join([str(flow.flow_id)] + list(map(str, flow.edge_ids))) 
        print(line)

import sys

def read_instance(path = None):
    
    if path:
        f = open(path)
        lines = f.readlines()
    else:
        lines = []
        f = sys.stdin
        line = input()
        lines.append(line)
        node_count, edge_count, constraints_count, flow_count = tuple(map(int,lines[0].strip().split(" ")))
        for _ in range(edge_count + constraints_count + flow_count):
            line = input()
            lines.append(line)

    node_count, edge_count, constraints_count, flow_count = tuple(map(int,lines[0].strip().split(" ")))

    nodes_list = []
    for i in range(node_count):
        node_i = Node(i)
        nodes_list.append(node_i)

    edges_list = []
    groups = {}
    for i in range(1,edge_count + 1):
        edge_id, group_id, start_id, end_id, distance, capacity = tuple(map(int,lines[i].strip().split(" ")))
        edge_i = Edge(edge_id, group_id, start_id, end_id, distance, capacity)
        # Add to nodes
        nodes_list[start_id].add_edge(edge_i)
        nodes_list[end_id].add_edge(edge_i)
        
        #Add to group
        groups.setdefault(group_id, Group(group_id,[]))
        groups[group_id].add_edge(edge_id)
      
        edges_list.append(edge_i)
        
    for i in range(edge_count +1, edge_count+ constraints_count +1):
        node_id, edge1_id, edge2_id = tuple(map(int,lines[i].strip().split(" ")))
        edges_list[edge1_id].add_constraint(edge2_id)
        edges_list[edge2_id].add_constraint(edge1_id)

    demands_list = []
    for i in range(edge_count+ constraints_count +1, edge_count+ constraints_count + flow_count +1):
        demand_id, start_id, end_id, flow_rate = tuple(map(int,lines[i].strip().split(" ")))
        demand_i = Demand(demand_id, start_id, end_id, flow_rate)
        demands_list.append(demand_i)

    instance = Instance(node_count, edge_count, constraints_count, flow_count,
        nodes_list, edges_list, groups, demands_list)

    return instance
    
instance = read_instance()

solver = Solver(instance)

flows = solver.solve(criteria="max_cap", order=False, time_limit= 1.5)
write_flows(flows)