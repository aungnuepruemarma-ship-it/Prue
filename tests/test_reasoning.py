import json

from ncp.adapters.external import ExternalAdapter
from ncp.core.runtime import build_default_universe
from ncp.reasoning.llm_adapter import LLMAdapter
from ncp.reasoning.mythos_adapter import MythosAdapter
from ncp.reasoning.rule_based import RuleBasedReasoner


def test_external_adapter_registry():
    adapter = ExternalAdapter(name="test")
    assert not adapter.available()
    adapter.register("echo", lambda **kw: kw)
    assert adapter.available("echo")
    assert adapter.call("echo", x=1) == {"x": 1}


def test_llm_adapter_falls_back_without_transport():
    adapter = LLMAdapter(adapter=ExternalAdapter(name="empty"))
    u = build_default_universe()
    got = [c.name for c in adapter.propose("update the root", u, ["e_root"])]
    want = [c.name for c in RuleBasedReasoner().propose("update the root", u, ["e_root"])]
    assert got == want


def test_llm_adapter_parses_transport_actions():
    def fake_complete(prompt: str, model: str) -> str:
        return json.dumps([
            {"action": "update_entity", "entity_id": "e_root", "state": {"note": "from llm"}},
            {"action": "add_relation", "source": "e_root", "target": "e_mem", "relation_type": "informs"},
            {"action": "update_entity", "entity_id": "nonexistent"},
        ])

    transport = ExternalAdapter(name="fake")
    transport.register("complete", fake_complete)
    adapter = LLMAdapter(adapter=transport)
    candidates = adapter.propose("anything", build_default_universe(), ["e_root"])
    assert [c.name for c in candidates] == ["update_entity", "add_relation"], "invalid actions must be dropped"


def test_llm_adapter_falls_back_on_transport_error():
    def broken(prompt: str, model: str) -> str:
        raise RuntimeError("network down")

    transport = ExternalAdapter(name="broken")
    transport.register("complete", broken)
    adapter = LLMAdapter(adapter=transport)
    assert adapter.propose("update the root", build_default_universe(), ["e_root"])


def test_mythos_adapter_falls_back_without_executable():
    adapter = MythosAdapter()
    assert not adapter.available()
    assert adapter.propose("build a thing", build_default_universe(), ["e_root"])
