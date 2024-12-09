#!/usr/bin/env python3

from __future__ import annotations
import argparse
import subprocess
from subprocess import CompletedProcess
from sys import stdin
from typing import TextIO


class Graph:
    class VertexDegree:
        def __init__(self, in_deg, out_deg):
            self.in_deg = in_deg
            self.out_deg = out_deg

        def __lt__(self, other: Graph.VertexDegree):
            return self.in_deg < other.in_deg or self.out_deg < other.out_deg

        def __ge__(self, other: Graph.VertexDegree):
            return self.in_deg >= other.in_deg and self.out_deg >= other.out_deg

    def __init__(self, input_file: TextIO):
        self.vertex_map: dict[str, int] = {}
        self.vertex_count: int = 0

        temp_edges = []
        for line in input_file:
            # data end is a blank line
            line = line.strip()
            if len(line) == 0: break

            v_start, v_end = line.split()

            # map the vertex names to numbers
            v_start_idx = self.get_vertex_idx(v_start)
            v_end_idx = self.get_vertex_idx(v_end)

            # we have to first keep the edges in a temporary array, as we don't know the final graph size yet
            temp_edges.append((v_start_idx, v_end_idx))

        # 2D array of 0 for every edge combination
        self.edges = [[False for _ in range(self.vertex_count)] for _ in range(self.vertex_count)]
        for edge in temp_edges:
            # the edges are directed and stored in a table
            # row = start idx
            # col = end idx
            # [row, col] = 1 <=> edge from start to end
            self.edges[edge[0]][edge[1]] = True

    def get_vertex_idx(self, vertex: str):
        if vertex not in self.vertex_map:
            self.vertex_map[vertex] = self.vertex_count
            idx = self.vertex_count
            self.vertex_count += 1
            return idx
        else:
            return self.vertex_map[vertex]

    def get_vertex_degree(self, vertex_idx):
        """
        :param vertex_idx:
        :return: (in, out)
        """
        deg_in = 0
        deg_out = 0

        # this index is start of the edge => row count of True = deg_out
        row = self.edges[vertex_idx]
        for out_vertex in row:
            if out_vertex:
                deg_out += 1

        # this index is end of the edge => column count of True = deg_in
        for row in self.edges:
            if row[vertex_idx]:
                deg_in += 1

        return Graph.VertexDegree(deg_in, deg_out)

    def iterate_edges(self, only_existing: bool):
        """

        :param only_existing:
        :return: (start, end, is_edge)
        """
        for start in range(self.vertex_count):
            for end in range(self.vertex_count):
                is_edge = self.is_edge(start, end)
                if only_existing:
                    if is_edge:
                        yield start, end, is_edge
                else:
                    yield start, end, is_edge

    def is_edge(self, start: int, end: int):
        return self.edges[start][end]


class ProblemDescription:
    def __init__(self, input_file: TextIO):
        # load the 2 graphs and create an internal description
        self.main_graph = Graph(input_file)
        self.subgraph = Graph(input_file)
        self.main_degrees: list[Graph.VertexDegree] = None
        self.sub_degrees: list[Graph.VertexDegree] = None

        # every vertex from the subgraph must be mapped to a vertex in the main graph
        #   (x_sub1_main1 || x_sub1_main2 ||...) && (x_sub2_main1 || x_sub2_main2 || ...) && ...
        #   \forall s = V(sub): CLAUSE ||= \forall m = V(main): emit(x_#s_#m)

        # if the main vertex has a degree smaller than the subgraph vertex, this mapping will never be true and
        # as such this variable can be removed

        # no 2 vertices from the subgraph are mapped to a single vertex in the main graph
        #   (!x_sub1_main1 || !x_sub1_main2) && (!x_sub1_main2 || !x_sub1_main3) && ... && (!x_sub2_main1 || !x_sub2_main2) && ...
        #   \forall s = V(sub): \forall m1, m2 = V(main) && m1 != m2: emit(!x_#s_#m1 || !x_#s_#m2)

        # if 2 vertices are mapped, an edge must exist between them in the searched subgraph
        #   x_sub1_main1 && x_sub2_main2 -> [edge main1 ~> main2]
        #   !x_sub1_main1 || !x_sub2_main2 || [edge main1 ~> main2]
        #   \forall m1, m2 = V(main) && m1 != m2: \forall e = E(sub): emit(!x_#eStart_#m1 || !x_#eEnd_#m2 || [edge m1 ~> m2])
        #       => clauses where the edges exist can be ignored, as the condition is always true

        # each tuple means mapping subgraph vertex idx -> main graph vertex idx
        self.clauses: list[list[tuple[int, int]]] = []

        # first vertex mapping (injective)
        #==vertex_map_clause = []
        for s in range(self.subgraph.vertex_count):
            vertex_map_clause = [] #==
            for m in range(self.main_graph.vertex_count):
                #main_degree = self.main_graph.get_vertex_degree(m)
                #sub_degree = self.subgraph.get_vertex_degree(s)
                # main in degree < sub in degree || main out degree < sub out degree => skip
                #if main_degree < sub_degree:
                #    continue

                vertex_map_clause.append((s, m))
            self.clauses.append(vertex_map_clause) #==
        #==self.clauses.append(vertex_map_clause)

        # then no mapping collides
        for s in range(self.subgraph.vertex_count):
            for m1 in range(self.main_graph.vertex_count):
                for m2 in range(self.main_graph.vertex_count):
                    if m1 == m2:
                        continue
                    self.clauses.append([(-s, -m1), (-s, -m2)]) #==
                    #==m1_degree = self.main_graph.get_vertex_degree(m1)
                    #==m2_degree = self.main_graph.get_vertex_degree(m2)
                    #==sub_degree = self.subgraph.get_vertex_degree(s)

                    # negative value means logical negation
                    #==this_clause = []

                    #==if m1_degree >= sub_degree:
                    #==    this_clause.append((-s, -m1))
                    #==if m2_degree >= sub_degree:
                    #==    this_clause.append((-s, -m2))
#==
                    #==if len(this_clause) > 0:
                    #==    self.clauses.append(this_clause)

        # finally edge preservation
        """ #==
        for m1 in range(self.main_graph.vertex_count):
            for m2 in range(self.main_graph.vertex_count):
                if m1 == m2:
                    continue

                m1_degree = self.main_graph.get_vertex_degree(m1)
                m2_degree = self.main_graph.get_vertex_degree(m2)

                for e in self.subgraph.iterate_edges(True):
                    # the clause would be always True
                    if self.main_graph.is_edge(m1, m2):
                        continue

                    s1 = e[0]
                    s2 = e[1]
                    s1_degree = self.main_graph.get_vertex_degree(s1)
                    s2_degree = self.main_graph.get_vertex_degree(s2)

                    this_clause = []
                    if m1_degree >= s1_degree:
                        this_clause.append((-s1, -m1))
                    if m2_degree >= s2_degree:
                        this_clause.append((-s2, -m2))

                    if len(this_clause) > 0:
                        self.clauses.append(this_clause)
        """
        for e in self.subgraph.iterate_edges(True):
            s1, s2, _ = e
            for m1 in range(self.main_graph.vertex_count):
                for m2 in range(self.main_graph.vertex_count):
                    if m1 == m2:
                        continue

                    if not self.main_graph.is_edge(m1, m2):
                        self.clauses.append([(-s1, -m1), (-s2, -m2)])

        self.filter_clauses()


    def filter_clauses(self):
        # now run the clause filtering
        # if the main graph vertex has a degree < than in the subgraph, this mapping will always be false
        self.main_degrees = [self.main_graph.get_vertex_degree(m) for m in range(self.main_graph.vertex_count)]
        self.sub_degrees = [self.subgraph.get_vertex_degree(s) for s in range(self.subgraph.vertex_count)]

        clauses_pre_filter = self.clauses
        self.clauses = []
        for clause in clauses_pre_filter:
            filtered = self.filter_single_clause(clause)
            if filtered is not None:
                if len(filtered) == 0:
                    # no literals in the clause are satisfiable based on the filtering,
                    # in CNF the entire formula is unsatisfiable
                    self.clauses = []
                    return
                self.clauses.append(filtered)


    def filter_single_clause(self, clause: list[tuple[int, int]]):
        clause_post_filter = []
        always_true = False
        for literal in clause:
            s, m = literal
            if s < 0:
                # this literal is negated
                s_deg = self.sub_degrees[-s]
                m_deg = self.main_degrees[-m]
                if m_deg < s_deg:
                    # this literal is always True, as such mapping can never exist
                    # therefore, the entire clause is always True and can be left out
                    always_true = True
                    break
                else:
                    clause_post_filter.append(literal)
            else:
                s_deg = self.sub_degrees[s]
                m_deg = self.main_degrees[m]
                if m_deg < s_deg:
                    # this mapping will never exist, and since it's a positive literal, we can just ignore it
                    pass
                else:
                    clause_post_filter.append(literal)
        if not always_true:
            return clause_post_filter
        else:
            return None


class CNFFormula:
    def __init__(self, problem: ProblemDescription):
        self.problem = problem
        self.clauses = problem.clauses
        self.variables = {}
        self.var_count = 0

        # count all variables (= distinct literals)
        for clause in self.clauses:
            for literal in clause:
                if literal not in self.variables:
                    self.variables[literal] = self.var_count
                    self.var_count += 1


    def write(self, output_file: TextIO):
        output_file.write(f'p cnf {self.var_count} {len(self.clauses)}\n')
        for clause in self.clauses:
            for literal in clause:
                # the format requires 1-indexed variables
                idx = self.variables[literal] + 1
                if literal[0] < 0:
                    idx = -idx
                output_file.write(f'{idx} ')
            output_file.write('0\n')


    def process_result(self, result: tuple[bool, str]):
        reverse_vars = {v: k for k,v in self.variables.items()}
        reverse_sub_vertices = {v: k for k,v in self.problem.subgraph.vertex_map.items()}
        reverse_main_vertices = {v: k for k, v in self.problem.main_graph.vertex_map.items()}

        if result[0]:
            print("The given graph DOES contain a subgraph isomorphic to the other graph")
            print("Vertex mapping:\n")
            for var in map(int, result[1].split()):
                if var == 0:
                    continue

                var -= 1

                variable = reverse_vars[abs(var)]
                s, m = variable

                sub_vertex = reverse_sub_vertices[abs(s)]
                main_vertex = reverse_main_vertices[abs(m)]

                if var < 0:
                    # this variable is not true in the final mapping
                    if s < 0:
                        # however this map should not have been included, -- -> +
                        # => this mapping IS in true
                        print(f'{sub_vertex} -> {main_vertex}')
                else:
                    if s >= 0:
                        # known positive mapping from the original problem
                        print(f'{sub_vertex} -> {main_vertex}')

        else:
            print("The given graph DOES NOT contain a subgraph isomorphic to the other graph")


def wrap_input(filename: str):
    if filename == '-':
        return stdin
    return open(filename, 'r')


def run_solver(solver: str, filename: str, verbosity: int):
    return subprocess.run([solver, '-model', '-verb=' + str(verbosity), filename], stdout=subprocess.PIPE)


def parse_result(result: CompletedProcess, should_print: bool):
    model: str | None = None
    satisfiable = False
    output: str = result.stdout.decode('utf-8')
    for line in output.split('\n'):
        if should_print: print(line)
        if len(line) == 0:
            continue
        if line[0] == 'c':
            # comment
            continue
        if line[0] == 's':
            # satisfiability
            if line[2:] == 'SATISFIABLE':
                satisfiable = True
        if line[0] == 'v':
            # model
            model = line[2:]
    return satisfiable, model


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default='-',
        type=str,
        help="Instance specification file"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help="DIMACS CNF output file"
    )
    parser.add_argument(
        "-s",
        "--solver",
        default="glucose-syrup"
    )
    parser.add_argument(
        "-r",
        "--run-solver",
        default=True,
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,2),
        help="SAT solver verbosity"
    )
    parser.add_argument(
        "-p",
        "--print",
        default=False,
        action=argparse.BooleanOptionalAction
    )

    args = parser.parse_args()

    problem = ProblemDescription(wrap_input(args.input))
    cnf = CNFFormula(problem)

    with open(args.output, 'w') as file:
        cnf.write(file)

    if args.run_solver:
        result = run_solver(args.solver, args.output, args.verb)
        parsed = parse_result(result, args.print)
        cnf.process_result(parsed)


if __name__ == "__main__": main()
