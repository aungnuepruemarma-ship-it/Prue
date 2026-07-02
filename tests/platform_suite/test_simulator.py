"""Tests for simulator module."""


from ncp.constraints.solver import ConstraintSolver
from ncp.core.entities import Result, Task
from ncp.simulator.simulator import Simulator


class TestSimulator:
    def test_simulate_valid_task(self):
        sim = Simulator(constraints=ConstraintSolver())
        task = Task(name="test", estimated_cost=0.1)
        result = sim.simulate(task)
        assert isinstance(result, Result)
        assert result.confidence > 0

    def test_simulate_invalid_task(self):
        sim = Simulator(constraints=ConstraintSolver())
        task = Task(name="test", estimated_cost=999)
        result = sim.simulate(task)
        assert result.status == "predicted_failure"

    def test_estimate_cost(self):
        sim = Simulator(constraints=ConstraintSolver())
        task = Task(name="test")
        cost = sim.estimate_cost(task)
        assert cost > 0
