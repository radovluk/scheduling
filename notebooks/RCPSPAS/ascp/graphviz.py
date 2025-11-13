import sys
import typing as Tp
from contextlib import contextmanager

from ascp.instance import Activity, Instance, RawInstance, Subgraph, WtInstance
from ascp.solver import Solution


class __DotPrinter:
    def __init__(self, file=sys.stdout):
        self.__indent = 0
        self.__indent_width = 2
        self.__file = file

    def __println(self, *args, sep: str = " "):
        indent = self.__indent * self.__indent_width * " "
        line = sep.join(args)

        print(indent + line, file=self.__file)

    def __call__(self, *args, sep: str = " "):
        self.__println(*args, sep=sep)

    @contextmanager
    def indent(self):
        self.__indent += 1
        try:
            yield
        finally:
            self.__indent -= 1

    @contextmanager
    def block(self, label: str):
        self.__println(f"{label} {{")
        with self.indent():
            yield
        self.__println("}")


def show_instance(
    instance: RawInstance | Instance,
    solution: Tp.Optional[Solution] = None,
    *,
    file=sys.stdout
):
    p = __DotPrinter(file=file)

    def show_successors():
        for activity in instance.activities:
            for successor in activity.successors:
                p(f"{activity.id} -> {successor}")

    def activity_label(activity: Activity) -> str:
        if solution:
            solved_activity = solution[activity]
            interval = [f"Interval: {solved_activity.start_time}-{solved_activity.end_time}"]
        else:
            interval = []

        if isinstance(instance, WtInstance) and activity.id in instance.due_dates:
            dd = instance.due_dates[activity.id]
            due_date = [f"Due: {dd.due_date}", f"Weight: {dd.weight}"]
        else:
            due_date = []

        return r"\n".join([
            f"{activity.id + 1}",
            f"Duration: {activity.duration}",
            f"Resources: {', '.join(str(r) for r in activity.requirements)}",
            *interval,
            *due_date,
        ])

    def show_activities():
        for activity in instance.activities:
            def is_branching():
                for sg in instance.subgraphs:
                    if isinstance(sg, Subgraph) and sg.principal_activity == activity.id:
                        return True
                return False

            style = []
            if solution and solution[activity].is_scheduled:
                style.append("filled")
            if is_branching():
                style.append("rounded")
            if isinstance(instance, WtInstance) and activity.id in instance.due_dates:
                style.append("bold")

            p(
                f"{activity.id} [",
                f'label="{activity_label(activity)}";',
                f'style="{",".join(style)}"',
                f'shape="{"diamond" if is_branching() else ""}"',
                "]",
                sep="",
            )
        p()

    def branch_cluster_label(branches: Tp.FrozenSet[int]):
        description = f"Branches: {{ {', '.join(str(br + 1) for br in sorted(branches))} }}"
        subgraphs = { gr.id
            for gr in instance.subgraphs
            if gr.branches & branches
        }

        if len(subgraphs) <= 1: return description
        subgraphs_desc = f"Belongs to subgraphs: {', '.join(str(sg) for sg in sorted(subgraphs))}"
        return description + "\n" + subgraphs_desc

    def show_branch_cluster(branches: Tp.FrozenSet[int]):
        with p.block(f"subgraph cluster_branches_{'_'.join(map(str, branches))}"):
            p("color = black;")
            p("fillcolor = white;")
            p(f'label="{branch_cluster_label(branches)}"')

            for activity in instance.activities:
                if activity.branches == branches:
                    p(f"{activity.id}")

    def show_subgraphs():
        branch_subsets = set(frozenset(activity.branches) for activity in instance.activities)
        for sg in instance.subgraphs:
            with p.block(f"subgraph cluster_subgraph_{sg.id}"):
                p("style = filled;")
                p("color = black;")
                p("fillcolor = lightgray;")
                p(f'label = "Subgraph {sg.id}"')

                def handle_branchset(branches: Tp.FrozenSet[int]):
                    if branches.issubset(sg.branches):
                        show_branch_cluster(branches)
                        return True

                    return False

                branch_subsets = set(filter(lambda bs : not handle_branchset(bs), branch_subsets))

        for branchset in filter(lambda bs: bs != { 0 }, branch_subsets):
            show_branch_cluster(branchset)

    with p.block("digraph G"):
        show_activities()
        show_successors()
        show_subgraphs()

    file.flush()
