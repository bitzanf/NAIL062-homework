#!/usr/bin/env python3

import argparse
import subprocess
from sys import stdin
from typing import TextIO


class ProblemDescription:
    @classmethod
    def load(cls, input_file: TextIO):
        # load the 2 graphs and create an internal description
        problem = ProblemDescription()
        return problem


class CNFFormula:
    @classmethod
    def from_description(cls, problem: ProblemDescription):
        # transform a vertex-edge representation into clauses representing the isomorphism
        # note: probably some vertex renaming magic or many-to-many mapping ??
        formula = CNFFormula()
        return formula

    def write(self, output_file: TextIO):
        pass


def wrap_input(filename: str):
    if filename == '-':
        return stdin
    return open(filename, 'r')


def run_solver(solver: str, filename: str, verbosity: int):
    return subprocess.run([solver, '-model', 'verb=' + str(verbosity), filename], stdout=subprocess.PIPE)


def parse_result(result):
    pass


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

    args = parser.parse_args()

    problem = ProblemDescription.load(wrap_input(args.input))
    cnf = CNFFormula.from_description(problem)

    with open(args.output, 'w') as file:
        cnf.write(file)

    if args.run_solver:
        result = run_solver(args.solver, args.output, args.verb)
        parse_result(result)


if __name__ == "__main__": main()
