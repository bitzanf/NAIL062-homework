#!/usr/bin/env python3
import random
import sys
from sys import argv
from solver import Graph

self_edges = False

def make_random_edges(edge_count: int, graph: Graph):
    vertices = list(range(graph.vertex_count))
    for e in range(edge_count):
        created = False
        while not created:
            v1 = random.choice(vertices)
            v2 = random.choice(vertices)
            if v1 == v2 and not self_edges:
                continue

            if graph.is_edge(v1, v2):
                continue

            graph.set_edge(v1, v2)
            created = True


def make_graph(vertex_count: int, edge_count: int, vertex_name: str):
    if edge_count > vertex_count**2:
        print('The graph canť have more than vertex_count^2 edges!', file=sys.stderr)
        exit(1)

    graph = Graph()
    # generate all vertices nicely numbered
    for v in range(vertex_count):
        graph.add_vertex(f'{vertex_name}{v}')
    graph.prepare_edges()

    # now generate random edges
    make_random_edges(edge_count, graph)
    return graph


def expand_graph(vertex_count: int, edge_count: int, graph: Graph, graph_edge_count: int, vertex_name: str):
    if vertex_count < graph.vertex_count or edge_count < graph_edge_count:
        print("The expanded graph can't have fewer edges or vertices!", file=sys.stderr)
        exit(1)

    # copy the graph and add vertices and edges
    large_graph = Graph()
    for i in range(vertex_count):
        # "copy" vertices
        large_graph.add_vertex(f'{vertex_name}{i}')

    for row in graph.edges:
        r = []
        for col in row:
            r.append(col)
        large_graph.edges.append(r)

    # append new edge rows
    for i in range(graph.vertex_count, large_graph.vertex_count, 1):
        large_graph.edges.append([False for _ in range(large_graph.vertex_count)])

    # append new edge columns
    for i in range(graph.vertex_count):
        row = large_graph.edges[i]
        for j in range(vertex_count - graph.vertex_count):
            row.append(False)

    # add the remaining edges
    make_random_edges(edge_count - graph_edge_count, large_graph)
    return large_graph


def print_graph(graph: Graph):
    for v in graph.vertex_map:
        print(v, end=' ')
    print()

    reverse_vertices = {v: k for k, v in graph.vertex_map.items()}
    for start in range(graph.vertex_count):
        for end in range(graph.vertex_count):
            if graph.is_edge(start, end):
                print(reverse_vertices[start], reverse_vertices[end])
    print()


def main():
    if len(argv) != 6:
        print('Usage: generator.py <True|False guarantee subgraph> <n vertices in G> <n edges in G> <n vertices in H> <n edges in H>', file=sys.stderr)
        exit(1)

    force_subgraph = bool(argv[1])
    nGV = int(argv[2])
    nGE = int(argv[3])
    nHV = int(argv[4])
    nHE = int(argv[5])

    if nGV < nHV or nGE < nHE:
        print("The subgraph can't be larger than the main graph!", file=sys.stderr)
        exit(1)

    H = make_graph(nHV, nHE, 'u')

    if force_subgraph:
        G = expand_graph(nGV, nGE, H, nHE, 'v')
    else:
        G = make_graph(nGV, nGE, 'v')

    print_graph(G)
    print_graph(H)

if __name__ == '__main__': main()
