import os
import re
import time

from alive_progress import alive_it
from typing import Callable, Iterable

from ascp.instance import AslibInstance, Instance, WtInstance
from .__shared import file_a_to_name
from .load_instance import load_instance

__BROKEN_INSTANCE_PREFIX = "!broken_"
__SKIPPED_INSTANCE_PREFIX = "!skipped_"


def __mark_as_broken(root: str, filepath: str):
    print(f"Broken instance {filepath}")

    instance_prefix_match = re.match(r"(.*)a\.rcp", filepath, re.IGNORECASE)
    assert instance_prefix_match
    instance_prefix = instance_prefix_match.group(1)

    all_instance_files = filter(lambda x: x.startswith(instance_prefix), os.listdir(root))
    for file in all_instance_files:
        os.rename(os.path.join(root, file), os.path.join(root, __BROKEN_INSTANCE_PREFIX + file))


#TODO: cite https://stackoverflow.com/a/4836734
def __natural_sort(vals):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(vals, key=alphanum_key)


def __iterate_instances[I: Instance](
    root_dir: str,
    load_instance: Callable[[str], I],
    recursive: bool = False,
    visit_hidden: bool = False,
    show_progress: bool = True,
) -> Iterable[I]:
    def should_explore(file: str) -> bool:
        if file.lower().startswith(__SKIPPED_INSTANCE_PREFIX): return False
        if visit_hidden: return True

        return not file.startswith(".")

    yielded = False
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = __natural_sort([d for d in dirs if should_explore(d)]) if recursive else []
        files[:] = __natural_sort([f for f in files if should_explore(f)])

        instance_files = [
            file
            for file in files
            if file.lower().endswith("a.rcp")
            and not file.lower().startswith(__BROKEN_INSTANCE_PREFIX)
        ]

        if instance_files:
            print(f"Iterating {root}")

            progress = alive_it if show_progress else lambda x: x
            for file in progress(instance_files):
                try:
                    instance = load_instance(os.path.join(root, file))
                except StopIteration:
                    __mark_as_broken(root, file)
                    continue

                yielded = True
                yield instance

    if not yielded:
        print(f"Warning: No instances found in {root_dir}")


def iterate_instances(
    root_dir: str,
    *,
    recursive: bool = False,
    visit_hidden: bool = False,
    show_progress: bool = True,
) -> Iterable[AslibInstance | WtInstance]:
    for el in __iterate_instances(
        root_dir,
        load_instance,
        recursive,
        visit_hidden,
        show_progress,
    ): yield el


class Timer:
    def __init__(self):
        self.__start_time = self.__lap_time = time.perf_counter()

    def lap(self) -> float:
        prev_time = self.__lap_time
        curr_time = self.__lap_time = time.perf_counter()
        return curr_time - prev_time

    def lap_time(self) -> float:
        return time.perf_counter() - self.__lap_time

    def elapsed_time(self) -> float:
        return time.perf_counter() - self.__start_time


file_a_to_name = file_a_to_name
