import os
from pathlib import Path
from typing import TextIO
from ascp.__shared import other_instance_file_path
from ascp.instance import AslibInstance, Instance, WtInstance


def __write_instance(instance: Instance, pa, pb):
    pa(len(instance.activities), len(instance.resources))
    pa(*instance.resources)

    pb(len(instance.subgraphs))
    for subgraph in sorted(instance.subgraphs, key=lambda s: s.id):
        pb(len(subgraph.branches), *sorted(b + 1 for b in subgraph.branches))

    for activity in sorted(instance.activities, key=lambda a: a.id):
        pa(
            activity.duration,
            *activity.requirements,
            len(activity.successors),
            *sorted(s + 1 for s in activity.successors),
        )

        pb(len(activity.branches), *sorted(b + 1 for b in activity.branches))


def __write_aslib_instance(instance: AslibInstance, pa, pb):
    pb(instance.params.flex, instance.params.nested, instance.params.linked)
    __write_instance(instance, pa, pb)

def __write_wt_instance(instance: WtInstance, pa, pb, pwt):
    __write_instance(instance, pa, pb)
    pwt(*instance.params.astuple())

    pwt(len(instance.due_dates))
    for a, dd in sorted(instance.due_dates.items()):
        pwt(a + 1, dd.weight, dd.due_date)


def write_instance(instance: Instance, file_a: str | Path):
    file_b = other_instance_file_path(file_a, "b")

    if os.path.exists(file_a) or os.path.exists(file_b):
        raise FileExistsError(f"File {file_a} or {file_b} already exists")

    os.makedirs(os.path.dirname(file_a), exist_ok=True)
    with open(file_a, "w") as fa, open(file_b, "w") as fb:
        def makeprint(f: TextIO):
            def p(*args, **kwargs):
                print(*args, **kwargs, file=f)
            return p

        pa = makeprint(fa)
        pb = makeprint(fb)

        if isinstance(instance, AslibInstance):
            __write_aslib_instance(instance, pa, pb)
        elif isinstance(instance, WtInstance):
            file_wt = other_instance_file_path(file_a, "wt")
            if os.path.exists(file_wt):
                raise FileExistsError(f"File {file_wt} already exists")
            with open(file_wt, "w") as fwt:
                pwt = makeprint(fwt)
                __write_wt_instance(instance, pa, pb, pwt)
        else:
            raise ValueError("Can only write WtInstance or AslibInstance")
