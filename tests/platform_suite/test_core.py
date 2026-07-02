"""Tests for core entity hierarchy."""

from uuid import UUID

from ncp.core.entities import Entity, Goal, Memory, Skill, Task, Version


class TestEntity:
    def test_entity_creation(self):
        e = Entity(name="test")
        assert e.name == "test"
        assert isinstance(e.id, UUID)

    def test_entity_serialization(self):
        e = Entity(name="test", description="desc")
        d = e.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "desc"


class TestGoal:
    def test_goal_creation(self):
        g = Goal(name="test_goal", priority=5)
        assert g.name == "test_goal"
        assert g.priority == 5
        assert g.status == "pending"

    def test_goal_serialization(self):
        g = Goal(name="test")
        d = g.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "pending"


class TestTask:
    def test_task_creation(self):
        t = Task(name="test_task", capability_required="llm")
        assert t.name == "test_task"
        assert t.capability_required == "llm"
        assert t.max_retries == 3

    def test_task_with_dependencies(self):
        t1 = Task(name="t1")
        t2 = Task(name="t2")
        t2.dependencies.append(t1.id)
        assert t1.id in t2.dependencies


class TestMemory:
    def test_memory_relevance(self):
        m = Memory(content="test content about AI", importance=0.8, confidence=0.9)
        score = m.score_relevance("AI")
        assert score > 0

    def test_memory_creation(self):
        m = Memory(content="test", memory_type="episodic")
        assert m.memory_type == "episodic"


class TestSkill:
    def test_skill_success_rate(self):
        s = Skill(name="test_skill", success_count=8, failure_count=2)
        assert s.success_rate == 0.8

    def test_skill_inherits_memory(self):
        s = Skill(name="test")
        assert isinstance(s, Memory)


class TestVersion:
    def test_version_string(self):
        v = Version(major=1, minor=2, patch=3)
        assert str(v) == "1.2.3"
