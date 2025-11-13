from pathlib import Path
import re


def other_instance_file_path(path: str | Path, suffix: str):
    path = str(path)

    a_suffix_regex = r"a\.(RCP|rcp)$"
    substitution = rf"{suffix}.\1"
    file_b_path = re.sub(a_suffix_regex, substitution, path, count=1, flags=re.MULTILINE)

    if file_b_path == path:
        raise ValueError(f"Cannot automatically find path to file {suffix} of file {path}, please provide it manually")

    return file_b_path


def file_a_to_name(file_a: str) -> str:
    name_match = re.match(r"(.*)a\.rcp", Path(file_a).name, flags=re.IGNORECASE)
    assert name_match, f"Couldn't parse instance name from file a path {file_a}"
    return name_match.group(1)
