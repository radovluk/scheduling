import os


from collections import deque
from typing import Callable, Optional

from ascp.__shared import other_instance_file_path, file_a_to_name

from .instance import (
    Activity,
    AlternativeStructureParams,
    AslibInstance,
    AslibInstanceFiles,
    Instance,
    RawInstance,
    RawSubgraph,
    Subgraph,
    WtDueDate,
    WtInstance,
    WtInstanceFiles,
    WtParams,
)


def __read_file(file_path: str):
    def lines():
        with open(file_path, 'r') as f:
            for line in map(str.strip, f):
                if line: yield line.strip()

    ls = lines()
    def next_line(): return next(ls)
    return next_line


def __nums[T](line: str, to_num: Callable[[str], T] = int) -> list[T]:
    return list(map(to_num, line.split()))


def __parse_subgraph(id: int, line: str) -> RawSubgraph:
    [count, *branches] = __nums(line)
    assert count == len(branches), f"Expected {count} branches, got {len(branches)}"
    return RawSubgraph(id, set(b - 1 for b in branches))


def __parse_activity(id: int, resource_count: int, line_a: str, line_b: str) -> Activity:
    ints_a = __nums(line_a)
    ints_b = __nums(line_b)

    [duration, *ints_a] = ints_a
    resources = ints_a[:resource_count]

    [successors_count, *successors] = ints_a[resource_count:]
    assert_err = lambda: f"Expected {successors_count} successors, got {len(successors)}"
    assert successors_count == len(successors), assert_err()

    [branches_count, *branches] = ints_b
    assert_err = lambda: f"Expected {branches_count} branches, got {len(branches)}"
    assert branches_count == len(branches), assert_err()

    return Activity(
        id=id,
        duration=duration,
        successors=set(s - 1 for s in successors),
        branches=set(b - 1 for b in branches),
        requirements=resources
    )


def __verify_branch_ids(subgraphs: list[RawSubgraph]):
    total_branch_count = sum(len(sg.branches) for sg in subgraphs)
    all_branches_set = __union(*[sg.branches for sg in subgraphs])

    err_message = lambda: f"Subgraph branch IDs must be consecutive integers starting from 1, got {all_branches_set}"
    assert set(range(1, total_branch_count + 1)) == all_branches_set, err_message()


def __verify_topsort_and_sink_activity(activities: list[Activity], check_sink: bool = True):
    reverse_neighbours = [[] for _ in activities]
    for activity in activities:
        for successor in activity.successors:
            assert successor > activity.id, \
                f"Activities must be in topological order, got {activity.id} -> {successor}"
            reverse_neighbours[successor].append(activity.id)

    if not check_sink:
        return

    hopeful_sink = activities[-1].id
    queue = deque([hopeful_sink])
    seen = set([hopeful_sink])

    while queue:
        activity = queue.popleft()
        for neighbour in reverse_neighbours[activity]:
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)

    all_activities = set(a.id for a in activities)
    err_message = lambda: f"Activities {all_activities.difference(seen)} not reachable from sink {hopeful_sink + 1}"
    assert seen == all_activities, err_message()

    err_message = lambda: f"Sink activity {hopeful_sink + 1} must only belong to branch 0"
    assert activities[hopeful_sink].branches == { 0 }, err_message()


__ReadLine = Callable[[], str]
def __load_instance(read_line_a: __ReadLine, read_line_b: __ReadLine, name: str, check_sink: bool = True) -> RawInstance:
    [activity_count, resource_count] = __nums(read_line_a())
    resources = __nums(read_line_a())
    assert_err = lambda: f"Expected {resource_count} resources, got {len(resources)}"
    assert resource_count == len(resources), assert_err()

    [num_subgraphs] = __nums(read_line_b())
    subgraphs = [ __parse_subgraph(i, read_line_b()) for i in range(num_subgraphs) ]
    __verify_branch_ids(subgraphs)

    activities = [
        __parse_activity(i, resource_count, read_line_a(), read_line_b())
        for i in range(activity_count)
    ]
    __verify_topsort_and_sink_activity(activities, check_sink)

    return RawInstance(
        activities=activities,
        resources=resources,
        subgraphs=subgraphs,
        name=name,
    )


def __load_aslib_instance(
    read_line_a: __ReadLine, read_line_b: __ReadLine,
    name: str, file_a: str, file_b: str
) -> AslibInstance:
    [flex, nest, link] = __nums(read_line_b(), float)
    params = AlternativeStructureParams(flex, nest, link)

    instance = __load_instance(read_line_a, read_line_b, name)
    instance = reconstruct_instance(instance)

    return AslibInstance.from_instance(instance, params, AslibInstanceFiles(file_a, file_b))


def __load_wt_instance(
    read_line_a: __ReadLine, read_line_b: __ReadLine, read_line_wt: __ReadLine,
    name: str, file_a: str, file_b: str, file_wt: str
) -> WtInstance:
    params = WtParams.fromstr(read_line_wt())
    [num_wt] = __nums(read_line_wt())

    due_dates = dict[int, WtDueDate]()
    for i in range(num_wt):
        [activity_id, weight, due_date] = __nums(read_line_wt())
        due_dates[activity_id - 1] = WtDueDate(due_date, weight)

    instance = __load_instance(read_line_a, read_line_b, name, check_sink=False)
    instance = reconstruct_instance(instance)

    return WtInstance.from_instance(
        instance,
        due_dates,
        params,
        WtInstanceFiles(file_a, file_b, file_wt)
    )


def load_instance(file_a: str) -> WtInstance | AslibInstance:
    file_b = other_instance_file_path(file_a, "b")
    file_wt = other_instance_file_path(file_a, "wt")

    read_line_a = __read_file(file_a)
    read_line_b = __read_file(file_b)

    name = file_a_to_name(file_a)
    if not os.path.exists(file_wt):
        return __load_aslib_instance(read_line_a, read_line_b, name, file_a, file_b)
    else:
        read_line_wt = __read_file(file_wt)
        return __load_wt_instance(read_line_a, read_line_b, read_line_wt, name, file_a, file_b, file_wt)


def __all_disjoint[T](*sets: set[T]) -> bool:
    seen: set[T] = set()

    for s in sets:
        if s.intersection(seen):
            return False

        seen.update(s)

    return True


def __union[T](*sets: set[T]) -> set[T]:
    return set().union(*sets)


def __index_where[T](lst: list[T], predicate: Callable[[T], bool]) -> Optional[int]:
    for i, item in enumerate(lst):
        if predicate(item):
            return i

    return None


def __check_branching_activity_precedes_whole_subgraph(
    instance: RawInstance,
    branching_activity: int,
    subgraph: RawSubgraph
):
    required_activities = {
        a.id for a in instance.activities
        if a.branches.intersection(subgraph.branches)
    }

    err_message = lambda: f"Branching activity {branching_activity} must not be in subgraph {subgraph.id}"
    assert branching_activity not in required_activities, err_message()

    seen = set([branching_activity])
    q = deque([branching_activity])

    while q and required_activities:
        activity = q.popleft()
        for successor in instance.activities[activity].successors:
            if successor in seen: continue

            required_activities.discard(successor)
            seen.add(successor)
            q.append(successor)

    err_message = lambda: f"Branching activity {branching_activity} does not cause all activities in subgraph {subgraph.id}"
    assert not required_activities, err_message()


def reconstruct_instance(instance: RawInstance):
    branching_activities: list[int | None] = [None for _ in instance.subgraphs]

    for activity in instance.activities:
        successor_branchsets = [instance.activities[s].branches for s in activity.successors]
        if not all(len(s) == 1 for s in successor_branchsets): continue
        if not __all_disjoint(*successor_branchsets): continue

        successor_branchset = __union(*successor_branchsets)
        subgraph = __index_where(instance.subgraphs, lambda s: s.branches == successor_branchset)
        if subgraph is None: continue

        err_message = lambda old_ba: (
            f"Subgraph {subgraph} has multiple possible branching activities: "
            f"{old_ba + 1}, {activity.id + 1}"
        )
        assert branching_activities[subgraph] is None, err_message(branching_activities[subgraph])
        branching_activities[subgraph] = activity.id

    def unwrap_activity(subgraph: int, a: int | None) -> int:
        assert a is not None, f"Subgraph {subgraph} has no branching activity"
        return a

    unwrapped_branching_activities = [unwrap_activity(i, a) for i, a in enumerate(branching_activities)]
    for ba, sg in zip(unwrapped_branching_activities, instance.subgraphs):
        __check_branching_activity_precedes_whole_subgraph(instance, ba, sg)

    return Instance(
        resources=instance.resources,
        activities=instance.activities,
        name=instance.name,
        subgraphs=[
            Subgraph(
                id=s.id,
                branches=s.branches,
                principal_activity=unwrapped_branching_activities[s.id]
            )
            for s in instance.subgraphs
        ]
    )
