from Edge import Edge
from Group import Group
from Node import Node
from Demand import Demand
from Instance import Instance
from Group import Group
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
    groups = []
    for i in range(1,edge_count + 1):
        edge_id, group_id, start_id, end_id, distance, capacity = tuple(map(int,lines[i].strip().split(" ")))
        edge_i = Edge(edge_id, group_id, start_id, end_id, distance, capacity)
        # Add to nodes
        nodes_list[start_id].add_edge(edge_i)
        nodes_list[end_id].add_edge(edge_i)
        #Add to group 
        if group_id >= len(groups):
            groups.append(Group(group_id,[]))
        
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