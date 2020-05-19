# -*- coding: utf-8 -*-
from code.src import Node
from code.src import Edge
import networkx as nx
import matplotlib.pyplot as plt


class Graph:
    """
    ui exploration graph
    """
    def __init__(self):
        """
        Initialize graph structure (a directed graph)
        """
        # Directed graph with multiple edges
        self.graph = nx.MultiDiGraph()
        self.root = None

    def add_single_node(self, node: Node):
        if node not in self.graph.nodes:
            self.graph.add_node(node, index=len(self.graph.nodes))

    def add_root_node(self, node: Node):
        self.root = node
        self.add_single_node(node)

    def get_node(self, node: Node) -> Node:
        """
        Determine whether a Node in the graph,
        if already in graph, return the old node in the graph, otherwise return the original new node
        """
        tmp_node = [old_node for old_node in self.graph.nodes if node.id == old_node.id]
        return tmp_node[0] if tmp_node else node

    def get_node_index(self, node: Node) -> int:
        return self.graph.nodes[node]['index']

    def add_nodes_with_edge(self, original_node: Node, next_node: Node, edge: Edge):
        if edge is None:
            return
        self.add_single_node(original_node)
        self.add_single_node(next_node)
        self.graph.add_edge(original_node, next_node, edge)

    def get_sub_nodes(self, node: Node, edge: Edge) -> [Node]:
        """
        Get all reachable nodes in the directed graph with Starting from a specified node and under specified path
        @param node: Source node
        @param edge: Nodes reachable by the specified path
        @return: List of nodes and paths
        """
        direct_sub_node = set()
        for sub_node, d_edges in self.graph[node].items():
            if edge.element_index in [d_edge.element_index for d_edge in d_edges.keys()]:
                direct_sub_node.add(sub_node)
        other_sub_nodes = set()
        for sub_node in direct_sub_node:
            other_sub_nodes.update(set(self.get_all_sub_nodes(sub_node)))
        all_sub_nodes = direct_sub_node.union(other_sub_nodes)
        # Keep only the nodes that enter the graph later than the source node to reduce the impact of the ring
        return [sub_node for sub_node in all_sub_nodes if self.graph.nodes[sub_node]['index'] > self.graph.nodes[node]['index']]

    def get_all_sub_nodes(self, node: Node) -> [Node]:
        """
        Starting from a node, get all the nodes reachable in the directed graph
        @param node: Source node
        @return: nodes in path
        """
        return nx.bfs_tree(self.graph, node)

    def get_path_between(self, target_node: Node, start_node: Node = None) -> [Node]:
        """
        Get the shortest path between two nodes
        :param start_node: Source node
        :param target_node: Target node
        :return: List of intermediate nodes, in order
        """
        if start_node is None:
            start_node = self.get_node(self.root)
        try:
            nodes = nx.shortest_path(self.graph, source=start_node, target=target_node)
        except:
            nodes = []
        return nodes

    def is_has_path(self, node: Node, next_node: Node) -> bool:
        return nx.has_path(self.graph, node, next_node)

    def get_edge(self, node: Node, next_node: Node) -> [Edge]:
        return self.graph[node][next_node]

    def draw(self):
        nx.draw(self.graph)
        plt.show()
