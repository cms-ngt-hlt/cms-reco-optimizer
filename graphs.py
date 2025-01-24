
import networkx as nx
import re
import numpy as np

def convert_to_graph(original_graph):
    # original autorh: Marco Rovere
    consumes = nx.DiGraph()
    consumed_by = nx.DiGraph()
    with open(original_graph, 'r') as f:
        for line in f:
            # Find nodes and add them, together with their attributes
            m_nodes = re.match('(\d+).*label=([A-Za-z0-9_@""]+),.*tooltip=([A-Za-z0-9_@""]+)', line)
            m_edges = re.match('(\d+) -> (\d+)(\[.*\]){0,1};', line)
            if m_nodes:
                node_id = int(m_nodes.group(1))
                consumes.add_node(node_id)
                consumes.nodes[node_id]["python_label"] = m_nodes.group(2)
                consumes.nodes[node_id]["cpp_type"] = m_nodes.group(3)
                consumed_by.add_node(node_id)
                consumed_by.nodes[node_id]["python_label"] = m_nodes.group(2)
                consumed_by.nodes[node_id]["cpp_type"] = m_nodes.group(3)
            # Find edges and establish them
            elif m_edges:
                if m_edges.group(3) and (m_edges.group(3).find('dashed') != -1):
                    continue
                start_node = int(m_edges.group(1))
                end_node = int(m_edges.group(2))
                consumes.add_edge(start_node, end_node)
                consumed_by.add_edge(end_node, start_node)        
    
    return consumes

def from_modules_to_module(graph,starts,end):
    end_node = [x for x,y in graph.nodes(data=True) if y['python_label']==end]
    assert(len(end_node)<=1) ## python_label should be unique
    all_modules = []
    if len(end_node) == 0:
        print("Warning! Module not found in the process.")
        return all_modules
    end_node = end_node[0]
    for s in starts:
        start_node = [x for x,y in graph.nodes(data=True) if y['python_label']==s]
        assert(len(start_node)<=1) ## python_label should be unique
        if len(start_node) == 0:
            print("Warning! Module ",s," not found in the process.")
            continue
        start_node = start_node[0]
        # print(list(nx.all_simple_paths(graph, end_node, start_node)))
        all_modules = sum(list(nx.all_simple_paths(graph, end_node, start_node)), all_modules)
        # print(sum(list(nx.all_simple_paths(graph, end_node, start_node)), []))
    
    all_modules = np.unique([a for a in all_modules if a!=start_node])
    all_modules = [graph.nodes[a]["python_label"] for a in all_modules]
    
    # print(all_modules)
    return all_modules