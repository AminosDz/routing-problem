
def write_flows(flows):
    print(len(flows))
    for flow in flows:
        line = " ".join([str(flow.flow_id)] + list(map(str, flow.edge_ids))) 
        print(line)