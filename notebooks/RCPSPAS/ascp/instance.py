from dataclasses import dataclass
from typing import Self


@dataclass
class AlternativeStructureParams:
    flex: float
    nested: float
    linked: float


@dataclass
class Activity:
    id: int
    duration: int
    successors: set[int]
    branches: set[int]
    requirements: list[int]


@dataclass
class RawSubgraph:
    id: int
    branches: set[int]


@dataclass
class Subgraph(RawSubgraph):
    principal_activity: int


@dataclass(kw_only=True)
class __Instance[S: RawSubgraph]:
    resources: list[int]
    activities: list[Activity]
    subgraphs: list[S]
    name: str

RawInstance = __Instance[RawSubgraph]
Instance = __Instance[Subgraph]


@dataclass
class AslibInstanceFiles:
    file_a: str
    file_b: str

@dataclass(kw_only=True)
class AslibInstance(Instance):
    params: AlternativeStructureParams
    files: AslibInstanceFiles | None = None

    @classmethod
    def from_instance(
        cls,
        instance: Instance,
        params: AlternativeStructureParams,
        files: AslibInstanceFiles | None = None,
    ) -> Self:
        return cls(
            resources=instance.resources,
            activities=instance.activities,
            subgraphs=instance.subgraphs,
            name=instance.name,
            params=params,
            files=files
        )


@dataclass
class WtInstanceFiles:
    file_a: str
    file_b: str
    file_wt: str


@dataclass(kw_only=True)
class WtParams:
    activities_in_job: int
    jobs_in_instance: int
    instance_start_lag: float
    resource_overlap: float
    weight_range: tuple[int, int]

    __Tuple = tuple[int, int, float, float, int, int]

    def astuple(self) -> __Tuple:
        return (
            self.activities_in_job,
            self.jobs_in_instance,
            self.instance_start_lag,
            self.resource_overlap,
            *self.weight_range,
        )

    def tuple_labels(self) -> tuple[str, str, str, str, str, str]:
        return (
            "activities_in_job",
            "jobs_in_instance",
            "instance_start_lag",
            "resource_overlap",
            "weight_range_min",
            "weight_range_max",
        )

    @classmethod
    def fromtuple(cls, t: __Tuple) -> Self:
        return cls(
            activities_in_job=t[0],
            jobs_in_instance=t[1],
            instance_start_lag=t[2],
            resource_overlap=t[3],
            weight_range=(t[4], t[5]),
        )

    @classmethod
    def fromstr(cls, s: str) -> Self:
        [a, b, c, d, e, f] = s.split()
        return cls.fromtuple((int(a), int(b), float(c), float(d), int(e), int(f)))


@dataclass(frozen=True)
class WtDueDate:
    due_date: int
    weight: int

@dataclass(kw_only=True)
class WtInstance(Instance):
    due_dates: dict[int, WtDueDate]
    params: WtParams
    files: WtInstanceFiles | None

    @classmethod
    def from_instance(
        cls,
        instance: Instance,
        due_dates: dict[int, WtDueDate],
        params: WtParams,
        files: WtInstanceFiles | None = None,
    ) -> Self:
        return cls(
            resources=instance.resources,
            activities=instance.activities,
            subgraphs=instance.subgraphs,
            name=instance.name,
            due_dates=due_dates,
            params=params,
            files=files
        )
