import typing as tp
from dataclasses import dataclass, field

from ortools.sat.python.cp_model import CpModel, IntervalVar, IntVar, LinearExprT

from . import instance


@dataclass
class ModelConfig:
    """
    Configuration for the ASCP model.

    Attributes:
        tmin (int): The minimum time value.
        tmax (int | None): The maximum time value. Leaving None calculates upper bound will be
            calculated as sum of all activity durations.
    """
    tmin: int = 0
    tmax: int | None = None


@dataclass
class Activity:
    activity: instance.Activity
    is_scheduled: IntVar
    start: IntVar
    interval: IntervalVar

    @property
    def end(self) -> LinearExprT:
        return self.interval.end_expr()


class Model:
    """
    A model for the ASCP problem. This is mostly a wrapper around OR-Tools CpModel which holds all
    the variables and constraints of the model.
    """

    @dataclass
    class __ResolvedConfig:
        tmin: int
        tmax: int

    def __init__(self,
        problem_instance: instance.Instance,
        objective: tp.Literal["cmax", "wt"] | None = None,
        config: ModelConfig = ModelConfig(),
    ):
        if objective is None:
            objective = "wt" if isinstance(problem_instance, instance.WtInstance) else "cmax"

        self.__instance = problem_instance
        self.__objective = objective
        self.__model = CpModel()
        self.__model.name = "ASCP"

        self.__config = Model.__ResolvedConfig(
            tmin=config.tmin,
            tmax=config.tmax or sum(a.duration for a in problem_instance.activities)
        )

        self.__create_activity_variables()
        self.__create_subgraph_variables()

        match objective:
            case "cmax": self.__make_cmax()
            case "wt": self.__make_wt()
            case _: raise ValueError(f"Invalid objective: {objective}")

        self.__create_activity_scheduled_constraints()
        self.__create_one_of_subgraph_constraints()
        self.__create_successor_constraints()
        self.__create_resource_constraints()

    @property
    def cp_model(self):
        return self.__model

    @property
    def objective_type(self):
        return self.__objective

    @property
    def instance(self) -> instance.Instance:
        return self.__instance

    @property
    def objective(self) -> IntVar:
        match self.__objective:
            case "cmax": return self.__cmax
            case "wt": return self.__wt
            case _: raise ValueError(f"Invalid objective: {self.__objective}")

    def __new_int_var(self, name: str, *, lb: int | None = None, ub: int | None = None) -> IntVar:
        lb = lb or self.__config.tmin
        ub = ub or self.__config.tmax
        return self.__model.new_int_var(lb, ub, name)

    def __create_activity_variables(self):
        def create_activity(activity: instance.Activity) -> Activity:
            is_scheduled = self.__model.new_bool_var(f"activity_{activity.id}_is_scheduled")
            start = self.__new_int_var(f"activity_{activity.id}_start")
            interval = self.__model.new_optional_fixed_size_interval_var(
                start,
                activity.duration,
                is_present=is_scheduled,
                name=f"activity_{activity.id}_interval"
            )

            return Activity(activity, is_scheduled, start, interval)

        self.activities = [create_activity(a) for a in self.__instance.activities]

    def __create_subgraph_variables(self):
        root_branch = self.__model.new_constant(True)
        other_branches = [
            self.__model.new_bool_var(f"subgraph_{subgraph.id}_branch_{branch}")
            for subgraph in self.__instance.subgraphs
            for branch in subgraph.branches
        ]

        self.branches = [root_branch, *other_branches]

    def __make_cmax(self):
        self.__cmax = self.__new_int_var("cmax")

        for activity in self.activities: (
            self.__model
                .add(activity.end <= self.__cmax)
                .only_enforce_if(activity.is_scheduled)
        )

        self.__model.minimize(self.__cmax)

    def __make_wt(self):
        err_message = lambda: "wt objective can only be used with WtInstance instances"
        assert isinstance(self.__instance, instance.WtInstance), err_message()

        tardinesses = []
        for act_id, due_date in self.__instance.due_dates.items():
            tardiness_var = self.__new_int_var(f"tardiness_{act_id}")
            delay = self.activities[act_id].end - due_date.due_date
            self.__model.add_max_equality(tardiness_var, [delay, 0])
            tardinesses.append(tardiness_var * due_date.weight)

        wt_domain = sum(dd.weight * self.__config.tmax for dd in self.__instance.due_dates.values())
        self.__wt = self.__new_int_var("wt", ub=wt_domain)
        self.__model.add(self.__wt == sum(tardinesses))
        self.__model.minimize(self.__wt)

    def __create_activity_scheduled_constraints(self):
        for activity in self.activities:
            self.__model.add_max_equality(
                activity.is_scheduled,
                [self.branches[branch] for branch in activity.activity.branches],
            )

    def __create_one_of_subgraph_constraints(self):
        for subgraph in self.__instance.subgraphs:
            self.__model.add(
                sum(self.branches[bi] for bi in subgraph.branches)
                == self.activities[subgraph.principal_activity].is_scheduled
            )

    def __create_successor_constraints(self):
        for activity in self.activities:
            for successor_idx in activity.activity.successors:
                successor = self.activities[successor_idx]
                (self.__model
                    .add(activity.interval.end_expr() <= successor.start)
                    .only_enforce_if(activity.is_scheduled, successor.is_scheduled)
                )

    def __create_resource_constraints(self):
        @dataclass
        class Resource:
            capacity: int
            intervals: tp.List[IntervalVar] = field(default_factory=list)
            demands: tp.List[int] = field(default_factory=list)

        resources = [Resource(cap) for cap in self.__instance.resources]

        for activity in self.activities:
            for resource_idx, demand in enumerate(activity.activity.requirements):
                resources[resource_idx].intervals.append(activity.interval)
                resources[resource_idx].demands.append(demand)

        for resource in resources:
            self.__model.add_cumulative(
                intervals=resource.intervals,
                demands=resource.demands,
                capacity=resource.capacity
            )
