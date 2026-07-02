"""Tests for skills module."""


from ncp.core.entities import Result, Skill, Task
from ncp.memory.episodic import EpisodicMemory
from ncp.skills.benchmark import SkillBenchmark
from ncp.skills.extractor import SkillExtractor
from ncp.skills.library import SkillLibrary
from ncp.skills.registry import SkillRegistry


class TestSkillRegistry:
    def test_register_find(self):
        reg = SkillRegistry()
        skill = Skill(name="test")
        reg.register(skill)
        assert reg.get(skill.id) == skill

    def test_find_by_name(self):
        reg = SkillRegistry()
        reg.register(Skill(name="test_skill"))
        found = reg.find_by_name("test")
        assert len(found) == 1


class TestSkillExtractor:
    def test_extract_from_episodes(self):
        reg = SkillRegistry()
        extractor = SkillExtractor(registry=reg)
        episodic = EpisodicMemory()
        episodic.add_episode(Task(name="repeated_task"), Result(status="success"))
        episodic.add_episode(Task(name="repeated_task"), Result(status="success"))
        episodic.add_episode(Task(name="repeated_task"), Result(status="success"))

        skills = extractor.extract_from_episodes(episodic)
        assert len(skills) >= 1


class TestSkillBenchmark:
    def test_benchmark(self):
        sb = SkillBenchmark()
        skill = Skill(name="test", success_count=8, failure_count=2)
        result = sb.benchmark(skill)
        assert result["success_rate"] == 0.8

    def test_score(self):
        sb = SkillBenchmark()
        skill = Skill(name="test", success_count=10, confidence=0.9)
        score = sb.score(skill)
        assert score > 0


class TestSkillLibrary:
    def test_find_skill(self):
        reg = SkillRegistry()
        reg.register(Skill(name="my_skill"))
        lib = SkillLibrary(registry=reg)
        found = lib.find_skill("my_skill")
        assert found is not None
