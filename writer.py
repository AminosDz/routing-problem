
def write_flows(flows):
    print(len(flows))
    lines = []
    for flow in flows:
        line = " ".join([str(flow.flow_id)] + list(map(str, flow.edge_ids))) 
        lines.append(line)
    
    print("\n".join(lines))
