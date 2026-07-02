"""Tests for constraints module."""


from ncp.constraints.policies import ConstraintPolicies
from ncp.constraints.solver import ConstraintSolver
from ncp.core.entities import Task


class TestConstraintPolicies:
    def test_capability_allowed(self):
        p = ConstraintPolicies(allowed_capabilities=["cap1"])
        assert p.is_capability_allowed("cap1") is True
        assert p.is_capability_allowed("cap2") is False

    def test_blocked_capability(self):
        p = ConstraintPolicies(blocked_capabilities=["bad"])
        assert p.is_capability_allowed("bad") is False
        assert p.is_capability_allowed("good") is True


class TestConstraintSolver:
    def test_valid_task(self):
        solver = ConstraintSolver()
        task = Task(name="test", estimated_cost=0.5)
        assert solver.validate(task) is True

    def test_cost_exceeded(self):
        solver = ConstraintSolver()
        task = Task(name="test", estimated_cost=999)
        assert solver.validate(task) is False

    def test_retries_exceeded(self):
        solver = ConstraintSolver()
        task = Task(name="test", retry_count=10)
        assert solver.validate(task) is False

    def test_explain(self):
        solver = ConstraintSolver()
        task = Task(name="test", estimated_cost=999)
        explanation = solver.explain(task)
        assert "Cost" in explanation
