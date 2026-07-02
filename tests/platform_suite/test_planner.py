"""Tests for planner module."""


from ncp.core.entities import Goal, Task
from ncp.planner.decomposition import Decomposer
from ncp.planner.objective import ObjectiveFunction


class TestDecomposer:
    def test_simple_decomposition(self):
        d = Decomposer()
        goal = Goal(name="simple_task")
        tasks = d.decompose(goal)
        assert len(tasks) >= 1

    def test_and_decomposition(self):
        d = Decomposer()
        goal = Goal(name="task A and task B")
        tasks = d.decompose(goal)
        assert len(tasks) >= 2

    def test_max_depth(self):
        d = Decomposer()
        goal = Goal(name="test")
        tasks = d.decompose(goal, max_depth=1)
        assert len(tasks) == 1


class TestObjectiveFunction:
    def test_score(self):
        obj = ObjectiveFunction()
        tasks = [Task(name="t1"), Task(name="t2")]
        score = obj.score(tasks)
        assert score > 0

    def test_score_empty(self):
        obj = ObjectiveFunction()
        score = obj.score([])
        assert score == 0.0

    def test_compare(self):
        obj = ObjectiveFunction()
        plan_a = [Task(name="a")]
        plan_b = [Task(name="b"), Task(name="c")]
        result = obj.compare(plan_a, plan_b)
        assert isinstance(result, int)
