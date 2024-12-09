#!/usr/bin/env python3

from __future__ import annotations
import argparse
import subprocess
import time
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

        def __str__(self):
            return f'{self.in_deg} <-; {self.out_deg} ->'

    def __init__(self):
        self.vertex_map: dict[str, int] = {}
        self.vertex_count: int = 0
        self.edges: list[list[bool]] = []

    def prepare_edges(self):
        # 2D array of 0 for every edge combination
        self.edges = [[False for _ in range(self.vertex_count)] for _ in range(self.vertex_count)]

    @staticmethod
    def load_from_file(input_file: TextIO):
        graph = Graph()
        temp_edges = []
        first_line = True
        for line in input_file:
            # data end is a blank line
            line = line.strip()
            if len(line) == 0: break

            # first line contains all vertices
            if first_line:
                vertices = line.split()
                for v in vertices:
                    # add all vertices
                    graph.add_vertex(v)
                first_line = False
                graph.prepare_edges()
                continue

            v_start, v_end = line.split()

            # map the vertex names to numbers
            v_start_idx = graph.get_vertex_idx(v_start)
            v_end_idx = graph.get_vertex_idx(v_end)

            graph.edges[v_start_idx][v_end_idx] = True
            temp_edges.append((v_start_idx, v_end_idx))

        return graph

    def add_vertex(self, vertex: str):
        if vertex not in self.vertex_map:
            self.vertex_map[vertex] = self.vertex_count
            idx = self.vertex_count
            self.vertex_count += 1
            return idx
        else:
            raise RuntimeError(f'Vertex "{vertex}" is already present')

    def get_vertex_idx(self, vertex: str):
        if vertex in self.vertex_map:
            return self.vertex_map[vertex]
        else:
            raise RuntimeError(f'Vertex "{vertex}" is not in the graph')

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

    def set_edge(self, start: int, end: int):
        self.edges[start][end] = True


class Literal:
    def __init__(self, sub_vert: int, main_vert: int, positive: bool):
        self.sub_vert = sub_vert
        self.main_vert = main_vert
        self.positive = positive

    def __iter__(self):
        return iter((self.sub_vert, self.main_vert, self.positive))

    def __str__(self):
        mapping = f'({self.sub_vert}, {self.main_vert})'
        return mapping if self.positive else '-' + mapping

    def __hash__(self):
        # the hash ignores whether it is positive or negative,
        # as it is still the same variable
        return hash((self.sub_vert, self.main_vert))

    def __eq__(self, other: Literal):
        # again, we ignore the negation as it is the same variable
        return self.sub_vert == other.sub_vert and self.main_vert == other.main_vert


class ProblemDescription:
    def __init__(self, input_file: TextIO):
        # load the 2 graphs and create an internal description
        self.main_graph = Graph.load_from_file(input_file)
        self.subgraph = Graph.load_from_file(input_file)
        self.main_degrees: list[Graph.VertexDegree] = None
        self.sub_degrees: list[Graph.VertexDegree] = None

        # every vertex from the subgraph must be mapped to a vertex in the main graph
        #   (x_sub1_main1 || x_sub1_main2 ||...) && (x_sub2_main1 || x_sub2_main2 || ...) && ...
        #   \forall s = V(sub): CLAUSE ||= \forall m = V(main): emit(x_#s_#m)

        # if the main vertex has a degree smaller than the subgraph vertex, this mapping will never be true and
        # as such this variable can be removed
        # if such variable was negated, the entire clause can be omitted, as it is trivially true

        # no 2 vertices from the subgraph are mapped to a single vertex in the main graph
        #   (!x_sub1_main1 || !x_sub2_main1) && (!x_sub1_main_2 || !x_sub2_main2) && ...
        #   \forall m = V(main): \forall s1, s2 = V(sub) && s1 != s2: emit(!x_#s1_#m || !x_#s2_#m)

        # if 2 vertices are mapped, an edge must exist between them in the searched subgraph
        #   x_sub1_main1 && x_sub2_main2 -> [edge main1 ~> main2]
        #   !x_sub1_main1 || !x_sub2_main2 || [edge main1 ~> main2]
        #   \forall e = E(sub): \forall m1, m2 = V(main) && m1 != m2: emit(!x_#eStart_#m1 || !x_#eEnd_#m2 || [edge m1 ~> m2])
        #       => clauses where the edges exist can be ignored, as the condition is always true

        # each tuple means mapping subgraph vertex idx -> main graph vertex idx
        self.clauses: list[set[Literal]] = []

        self.generate_all_vertices_mapped()
        self.generate_no_2_sub_vertices_mapped_to_same_main()
        self.generate_all_sub_edges_mapped()
        self.filter_clauses()


    def generate_all_vertices_mapped(self):
        for s in range(self.subgraph.vertex_count):
            vertex_map_clause = set()
            for m in range(self.main_graph.vertex_count):
                vertex_map_clause.add(Literal(s, m, True))
            self.clauses.append(vertex_map_clause)


    def generate_no_2_sub_vertices_mapped_to_same_main(self):
        for m in range(self.main_graph.vertex_count):
            for s1 in range(self.subgraph.vertex_count):
                for s2 in range(self.subgraph.vertex_count):
                    if s1 == s2:
                        continue
                    self.clauses.append({Literal(s1, m, False), Literal(s2, m, False)})


    def generate_all_sub_edges_mapped(self):
        for e in self.subgraph.iterate_edges(True):
            s1, s2, _ = e
            for m1 in range(self.main_graph.vertex_count):
                for m2 in range(self.main_graph.vertex_count):
                    if m1 == m2:
                        continue

                    if not self.main_graph.is_edge(m1, m2):
                        self.clauses.append({Literal(s1, m1, False), Literal(s2, m2, False)})


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


    def filter_single_clause(self, clause: set[Literal]):
        clause_post_filter = set()
        always_true = False
        for literal in clause:
            s, m, pos = literal
            s_deg = self.sub_degrees[s]
            m_deg = self.main_degrees[m]
            if not pos:
                # this literal is negated
                if m_deg < s_deg:
                    # this literal is always True, as such mapping can never exist
                    # therefore, the entire clause is always True and can be left out
                    always_true = True
                    break
                else:
                    clause_post_filter.add(literal)
            else:
                if m_deg < s_deg:
                    # this mapping will never exist, and since it's a positive literal, we can just ignore it
                    pass
                else:
                    clause_post_filter.add(literal)
        if not always_true:
            return clause_post_filter
        else:
            return None


class CNFFormula:
    def __init__(self, problem: ProblemDescription):
        self.sub_vertices = problem.subgraph.vertex_map
        self.main_vertices = problem.main_graph.vertex_map
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
                if not literal.positive:
                    idx = -idx
                output_file.write(f'{idx} ')
            output_file.write('0\n')


    def process_result(self, result: tuple[bool, str]):
        reverse_vars = {v: k for k, v in self.variables.items()}
        reverse_sub_vertices = {v: k for k, v in self.sub_vertices.items()}
        reverse_main_vertices = {v: k for k, v in self.main_vertices.items()}

        if result[0]:
            print("The given graph DOES contain a subgraph isomorphic to the other graph")
            print("Vertex mapping:\n")
            for var in map(int, result[1].split()):
                # 0 means end of the model
                if var == 0:
                    break

                variable = reverse_vars[abs(var) - 1]
                s, m, pos = variable

                sub_vertex = reverse_sub_vertices[abs(s)]
                main_vertex = reverse_main_vertices[abs(m)]

                if var < 0:
                    # this variable is not true in the final mapping
                    if not pos:
                        # however this map should not have been included, - - = +
                        # => this mapping IS in the final output
                        print(f'{sub_vertex} -> {main_vertex}')
                else:
                    if pos:
                        # known positive mapping from the original problem
                        print(f'{sub_vertex} -> {main_vertex}')

        else:
            print("The given graph DOES NOT contain a subgraph isomorphic to the other graph")


def wrap_input(filename: str):
    if filename == '-':
        return stdin
    return open(filename, 'r')


def run_solver(solver: str, filename: str, verbosity: int):
    start = time.time()
    process = subprocess.run([solver, '-model', '-verb=' + str(verbosity), filename], stdout=subprocess.PIPE)
    end = time.time()
    return process, end - start


def parse_result(result: subprocess.CompletedProcess, should_print: bool):
    model: str | None = None
    satisfiable = False
    output: str = result.stdout.decode('utf-8')
    for line in output.split('\n'):
        if len(line) == 0:
            continue

        if should_print: print(line)
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
        default="glucose-syrup",
        help="Path to the solver"
    )
    parser.add_argument(
        "-r",
        "--run-solver",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Run the solver"
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,3),
        help="SAT solver verbosity"
    )
    parser.add_argument(
        "-p",
        "--print",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Print the SAT solver output"
    )

    args = parser.parse_args()

    start = time.time()
    problem = ProblemDescription(wrap_input(args.input))
    cnf = CNFFormula(problem)
    end = time.time()

    with open(args.output, 'w') as file:
        cnf.write(file)

    if args.run_solver:
        result, runtime = run_solver(args.solver, args.output, args.verb)
        parsed = parse_result(result, args.print)
        cnf.process_result(parsed)
        print(f'\nProcessing took approx. {runtime} seconds')
    print(f'Preprocessing took {end - start} seconds')

if __name__ == "__main__": main()
