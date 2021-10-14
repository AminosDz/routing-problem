from collections import deque
import time
from itertools import combinations, chain, product

class Solver():
    def __init__(self, instance):
        self.instance = instance
        self.cache = {}
        self.cache_parents = {}
        self.invalid_demands = {}

    def get_from_cache(self, node_ids):
        i, j = min(node_ids), max(node_ids)
        path = self.cache[(i, j)]
        
        first_edge = self.instance.edges_list[path[0]]

        if node_ids[0] in (first_edge.start_id, first_edge.end_id):
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
        self.cache[(i, j)] = path
    
    def solve(self, tic, criteria = "max_cap", order = None, time_limit=1.9):
        
        flows_list = []
    
        if order:
            sorted_demands = sorted(self.instance.demands_list,
                key= lambda d: d.flow_rate, reverse=False)
        else:
            sorted_demands = self.instance.demands_list
    
        for demand in sorted_demands:
            if time.time() - tic < time_limit:
                if (demand.start_id, demand.end_id) not in self.invalid_demands or\
                    self.invalid_demands[(demand.start_id, demand.end_id)] <= demand.flow_rate:
                    flow = self.get_path_bfs(demand, tic, time_limit, criteria=criteria)

                if flow is None:
                    self.invalid_demands[(demand.start_id, demand.end_id)] = demand.flow_rate

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

    def check_path(self, flow):
        if len(flow.edge_ids) == 0:
            return False
        visited_edges = set()
        visited_nodes = set()
        prev_edge = None
        prev_node = flow.start_id
        for edge_id in flow.edge_ids:
            if edge_id in visited_edges:
                return False 

            visited_edges.add(edge_id)
            edge = self.instance.edges_list[edge_id]

            if prev_node in visited_nodes:
                return False
            visited_nodes.add(prev_node)

            if edge.start_id == prev_node:
                prev_node = edge.end_id
            elif edge.end_id == prev_node:
                prev_node = edge.start_id 
            else:
                return False

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
        
        if flow.end_id != prev_node:
            return False

        return True

    def get_level(self, node_id, level = 1):
        
        all_parents = []

        parents = { p: set([node_id]) for p in self.instance.nodes_list[node_id].neighbors.keys()}
        all_parents.append(parents)
        
        for l in range(level-1):
            
            parents={}
            for i in all_parents[-1]:
                self.instance.nodes_list[i].set_final()
                for j in self.instance.nodes_list[i].neighbors:
                    parents.setdefault(j,set()).add(i)
                    self.instance.nodes_list[j].set_final()
            
            all_parents.append(parents)
        
        return all_parents

    def get_path_bfs(self, demand, tic, time_limit, criteria = "max_cap"):

        if self.instance.nodes_list[demand.start_id].SFL <= 0 or \
            self.instance.nodes_list[demand.end_id].SFL <= 0:
            return None
        
        if demand.start_id in self.cache_parents:
            start_parents = self.cache_parents[demand.start_id]
        else:
            start_parents = self.get_level(demand.start_id, level=2)
            self.cache_parents[demand.start_id] = start_parents

        if demand.end_id in self.cache_parents:
            end_parents = self.cache_parents[demand.end_id]
        else:
            end_parents = self.get_level(demand.end_id, level=2)
            self.cache_parents[demand.end_id] = end_parents
        
        if sum([len(s) for s in start_parents]) > sum([len(s) for s in end_parents]):
            demand.start_id, demand.end_id = demand.end_id, demand.start_id
            demand.inverted=True
            
            parents = start_parents[0]
            # check that we have n-2 parents 
            if len(start_parents) > 1:
                parents2 = start_parents[1]
            else:
                parents2 = {}
            
        else :
            parents = end_parents[0]
            # check that we have n-2 parents 
            if len(end_parents) > 1:
                parents2 = end_parents[1]
            else:
                parents2 = {}
        
        parents[demand.end_id] = demand.end_id

        visited = set() 
        queue= deque()
  
        # Mark the source node as visited and enqueue it
        queue.append((demand.start_id, []))
        visited.add(demand.start_id)
        while queue and (time.time() - tic < time_limit):
 
            #Dequeue a vertex from queue
            n, cur_path = queue.popleft()

            # If this adjacent node is the destination node,
            # then return true
            if n == demand.end_id:
                flow = Flow(demand, cur_path)
                #self.put_in_cache(demand, cur_path.copy())
                return flow
            
            #check cache
            """if self.in_cache((n, demand.end_id)):
                concat_path = cur_path + self.get_from_cache((n, demand.end_id))
                flow = Flow(demand, concat_path)
                if self.check_path(flow):
                    return flow"""
            
            """for p in parents2:
                if self.in_cache((n,p)):
                    concat_path = cur_path + self.get_from_cache((n, p))
                    # If this adjacent adjacent node is the destination node,
                    # then return true
                    if n in parents2 and self.instance.nodes_list[n].SFL > 0:
                        for j in parents2[n]:
                            if j not in visited and self.instance.nodes_list[j].SFL > 0:
                                possible_edges = self.instance.nodes_list[n].neighbors[j]
                                prev_edge = self.instance.edges_list[concat_path[-1]] if len(concat_path) else None
                                chosen_edge = self.choose_edge_bfs(possible_edges,
                                    demand, prev_edge, criteria = criteria)

                                visited.add(n)
                                
                                if chosen_edge:
                                    new_path = concat_path.copy()
                                    new_path.append(chosen_edge.edge_id)
                                    
                                    possible_edges2 = self.instance.nodes_list[j].neighbors[demand.end_id]
                                    prev_edge2 = self.instance.edges_list[new_path[-1]] if len(new_path) else None
                                    chosen_edge2 = self.choose_edge_bfs(possible_edges2,
                                        demand, prev_edge2, criteria = criteria)
                                    
                                    visited.add(j)

                                    if chosen_edge2:
                                        new_path2 = new_path
                                        new_path2.append(chosen_edge2.edge_id)
                                        flow = Flow(demand, new_path2)
                                        if self.check_path(flow):
                                            self.put_in_cache(demand, new_path2.copy())
                                            return flow"""
                
            # If this adjacent adjacent node is the destination node,
            # then return true
            if n in parents2 and self.instance.nodes_list[n].SFL > 0:
                for j in parents2[n]:
                    if j not in visited and self.instance.nodes_list[j].SFL > 0:
                        possible_edges = self.instance.nodes_list[n].neighbors[j]
                        prev_edge = self.instance.edges_list[cur_path[-1]] if len(cur_path) else None
                        chosen_edge = self.choose_edge_bfs(possible_edges,
                            demand, prev_edge, criteria = criteria)

                        visited.add(n)
                        
                        if chosen_edge:
                            new_path = cur_path.copy()
                            new_path.append(chosen_edge.edge_id)
                            
                            possible_edges2 = self.instance.nodes_list[j].neighbors[demand.end_id]
                            prev_edge2 = self.instance.edges_list[new_path[-1]] if len(new_path) else None
                            chosen_edge2 = self.choose_edge_bfs(possible_edges2,
                                demand, prev_edge2, criteria = criteria)
                            
                            visited.add(j)

                            if chosen_edge2:
                                new_path2 = new_path
                                new_path2.append(chosen_edge2.edge_id)
                                flow = Flow(demand, new_path2)
                                #self.put_in_cache(demand, new_path2.copy())
                                return flow

            # If this adjacent node is the destination node,
            # then return true
            if n in parents and self.instance.nodes_list[demand.end_id].SFL > 0:
                if n == demand.end_id:
                    flow = Flow(demand, cur_path)
                    return flow
                else:
                    possible_edges = self.instance.nodes_list[n].neighbors[demand.end_id]
                    prev_edge = self.instance.edges_list[cur_path[-1]] if len(cur_path) else None
                    chosen_edge = self.choose_edge_bfs( possible_edges,
                        demand, prev_edge, criteria = criteria)

                    visited.add(n)

                    if chosen_edge:
                        new_path = cur_path
                        new_path.append(chosen_edge.edge_id)
                        flow = Flow(demand, new_path)
                        #self.put_in_cache(demand, new_path.copy())
                        return flow

            #  Else, continue to do BFS
            n_keys = list(self.instance.nodes_list[n].neighbors.keys())
            for i in n_keys[0:7]:
                
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
                return edge
        return None if len(possible_edges) == 0 else possible_edges[0]
        
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


class Demand:

    def __init__(self, demand_id, start_id, end_id, flow_rate, inverted = False) -> None:
        self.demand_id = demand_id
        self.start_id = start_id
        self.end_id = end_id
        self.flow_rate = flow_rate
        self.inverted = inverted


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


class Group:

    def __init__(self, group_id, edges_list = [], GFL = 100) -> None:
        self.group_id = group_id
        self.edge_ids_list = edges_list
        self.GFL = GFL

    def update_GFL(self, value=1):
        self.GFL -= value

    def add_edge(self, edge_id):
        self.edge_ids_list.append(edge_id)

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


import sys
def set_finals(nodes_list, demand):
    nodes_list[demand.start_id].set_final()
    nodes_list[demand.end_id].set_final()

def read_instance(path = None, criteria = "min_dist"):
    
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

    edges_list = [0] * edge_count
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
    
        edges_list[edge_id] = edge_i
    
    for i in range(node_count):
        
        sorted_neighbors = {v:nodes_list[i].neighbors[v] for v in sorted(nodes_list[i].neighbors, key= lambda x: len(nodes_list[x].neighbors), reverse=True)} # Sort the values
        nodes_list[i].neighbors = sorted_neighbors
        for n in nodes_list[i].neighbors:
            if criteria == "min_dist":
                nodes_list[i].neighbors[n] = \
                    sorted(nodes_list[i].neighbors[n],key= lambda x: x.distance)
            elif criteria == "max_cap":
                nodes_list[i].neighbors[n] = \
                    sorted(nodes_list[i].neighbors[n],key= lambda x: x.capacity, reverse = True)

    for i in range(edge_count +1, edge_count+ constraints_count +1):
        node_id, edge1_id, edge2_id = tuple(map(int,lines[i].strip().split(" ")))
        edges_list[edge1_id].add_constraint(edge2_id)
        edges_list[edge2_id].add_constraint(edge1_id)

    demands_list = []
    for i in range(edge_count+ constraints_count +1, edge_count+ constraints_count + flow_count +1):
        demand_id, start_id, end_id, flow_rate = tuple(map(int,lines[i].strip().split(" ")))
        demand_i = Demand(demand_id, start_id, end_id, flow_rate)
        
        set_finals(nodes_list, demand_i)
        demands_list.append(demand_i)

    instance = Instance(node_count, edge_count, constraints_count, flow_count,
        nodes_list, edges_list, groups, demands_list)

    return instance


def write_flows(flows):
    print(len(flows))
    lines = []
    for flow in flows:
        line = " ".join([str(flow.flow_id)] + list(map(str, flow.edge_ids))) 
        lines.append(line)
    
    print("\n".join(lines))

criteria="min_dist"
first_time = time.time()
instance = read_instance(criteria=criteria)
solver = Solver(instance)

flows = solver.solve(first_time, criteria=criteria, order=True, time_limit= 1.9)

write_flows(flows)