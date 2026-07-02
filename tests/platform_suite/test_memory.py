"""Tests for memory module."""


from ncp.core.entities import Memory, Result, Skill, Task
from ncp.memory.archive import ArchiveMemory
from ncp.memory.episodic import EpisodicMemory
from ncp.memory.forgetting import ForgettingPolicy
from ncp.memory.procedural import ProceduralMemory
from ncp.memory.ranking import MemoryRanker
from ncp.memory.replay import ReplayBuffer
from ncp.memory.semantic import SemanticMemory
from ncp.memory.skill import SkillMemory
from ncp.memory.working import WorkingMemory


class TestWorkingMemory:
    def test_add_and_retrieve(self):
        wm = WorkingMemory(max_items=5)
        wm.add(Memory(content="test"))
        assert wm.size == 1

    def test_max_items(self):
        wm = WorkingMemory(max_items=3)
        for i in range(5):
            wm.add(Memory(content=f"item_{i}"))
        assert wm.size == 3

    def test_get_recent(self):
        wm = WorkingMemory(max_items=10)
        for i in range(5):
            wm.add(Memory(content=f"item_{i}"))
        recent = wm.get_recent(3)
        assert len(recent) == 3


class TestEpisodicMemory:
    def test_add_episode(self):
        em = EpisodicMemory()
        t = Task(name="test_task")
        r = Result(status="success")
        em.add_episode(t, r)
        assert em.episode_count == 1

    def test_success_rate(self):
        em = EpisodicMemory()
        em.add_episode(Task(name="t1"), Result(status="success"))
        em.add_episode(Task(name="t2"), Result(status="failure"))
        assert em.success_rate == 0.5

    def test_search(self):
        em = EpisodicMemory()
        em.add_episode(Task(name="test_search"), Result(status="success"))
        results = em.search("search")
        assert len(results) >= 1


class TestSemanticMemory:
    def test_add_concept(self):
        sm = SemanticMemory()
        c = sm.add_concept("AI", "Artificial Intelligence")
        assert c.name == "AI"
        assert sm.concept_count == 1

    def test_get_concept(self):
        sm = SemanticMemory()
        sm.add_concept("test", "description")
        found = sm.get_concept("test")
        assert found is not None

    def test_search(self):
        sm = SemanticMemory()
        sm.add_concept("machine_learning", "ML concepts")
        results = sm.search("learning")
        assert len(results) >= 1


class TestProceduralMemory:
    def test_add_workflow(self):
        pm = ProceduralMemory()
        pm.add_workflow("test_workflow", [{"step": 1}])
        assert pm.workflow_count == 1


class TestSkillMemory:
    def test_add_skill(self):
        sm = SkillMemory()
        skill = Skill(name="test_skill", trigger_patterns=["test"], is_active=True)
        sm.add_skill(skill)
        assert sm.active_skill_count == 1

    def test_find_by_trigger(self):
        sm = SkillMemory()
        skill = Skill(name="test", trigger_patterns=["trigger"], is_active=True)
        sm.add_skill(skill)
        found = sm.find_by_trigger("trigger")
        assert len(found) == 1


class TestArchiveMemory:
    def test_archive(self):
        am = ArchiveMemory()
        m = Memory(content="test content for archiving")
        entry = am.archive(m)
        assert entry.original_size > 0

    def test_compression_ratio(self):
        am = ArchiveMemory()
        assert am.compression_ratio == 1.0  # Empty


class TestMemoryRanker:
    def test_score(self):
        r = MemoryRanker()
        m = Memory(content="test", importance=0.8, confidence=0.9, recency=1.0)
        score = r.score(m, "test")
        assert score > 0

    def test_rank(self):
        r = MemoryRanker()
        memories = [
            Memory(content="a", importance=0.9),
            Memory(content="b", importance=0.1),
        ]
        ranked = r.rank(memories, "a")
        assert len(ranked) == 2


class TestForgettingPolicy:
    def test_should_forget_low_confidence(self):
        fp = ForgettingPolicy()
        m = Memory(content="test", confidence=0.05)
        assert fp.should_forget(m) is True

    def test_should_keep_high_importance(self):
        fp = ForgettingPolicy()
        m = Memory(content="test", importance=0.9, memory_type="semantic",
                    confidence=0.8, recency=0.5, access_count=5)
        assert fp.should_forget(m) is False

    def test_decay(self):
        fp = ForgettingPolicy(decay_rate=0.1)
        m = Memory(recency=1.0)
        fp.apply_decay(m, hours=1)
        assert m.recency < 1.0


class TestReplayBuffer:
    def test_add_sample(self):
        rb = ReplayBuffer(capacity=10)
        from ncp.memory.episodic import Episode
        rb.add(Episode(task_name="test"))
        samples = rb.sample(1)
        assert len(samples) == 1

    def test_capacity(self):
        rb = ReplayBuffer(capacity=2)
        from ncp.memory.episodic import Episode
        for i in range(5):
            rb.add(Episode(task_name=f"test_{i}"))
        assert rb.size == 2
