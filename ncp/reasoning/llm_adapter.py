from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from ..adapters.external import ExternalAdapter
from ..core.transformations import (
    TransformationCandidate,
    make_add_relation,
    make_create_entity,
    make_merge_entities,
    make_update_entity,
)
from ..core.universe import Universe
from .base import Reasoner
from .rule_based import RuleBasedReasoner

ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"

PROMPT_TEMPLATE = """You propose actions for a knowledge-graph runtime.
Goal: {goal}
Entities: {entities}
Active entity ids: {active}

Respond with ONLY a JSON array of action objects, no prose. Allowed actions:
- {{"action": "create_entity", "name": str, "type": str}}
- {{"action": "update_entity", "entity_id": str, "state": object, "knowledge": object}}
- {{"action": "add_relation", "source": str, "target": str, "relation_type": str}}
- {{"action": "merge_entities", "source": str, "target": str, "name": str}}
- {{"action": "query_memory"}}
Use only entity ids that exist. Propose 1-4 actions that advance the goal."""

def anthropic_messages_transport(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 1024) -> str:
    """Minimal stdlib Messages API call; returns the response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_ENDPOINT,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("stop_reason") == "refusal":
        raise RuntimeError("model refused the request")
    return "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")

def default_llm_adapter() -> ExternalAdapter:
    adapter = ExternalAdapter(name="anthropic")
    if os.environ.get("ANTHROPIC_API_KEY"):
        adapter.register("complete", anthropic_messages_transport)
    return adapter

class LLMAdapter(Reasoner):
    """Proposes candidates via an LLM; falls back to rules when offline.

    The transport is injected through an ExternalAdapter ("complete"
    capability), so the reasoner works without network access and tests can
    supply a fake completion function.
    """

    def __init__(self, adapter: ExternalAdapter | None = None, model: str = DEFAULT_MODEL):
        self.adapter = adapter if adapter is not None else default_llm_adapter()
        self.model = model
        self.fallback = RuleBasedReasoner()

    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        if not self.adapter.available("complete"):
            return self.fallback.propose(goal, universe, active_entity_ids)
        try:
            prompt = PROMPT_TEMPLATE.format(
                goal=goal,
                entities=json.dumps({eid: e.name for eid, e in universe.entities.items()}),
                active=json.dumps(active_entity_ids),
            )
            text = self.adapter.call("complete", prompt=prompt, model=self.model)
            candidates = self._parse_actions(text, universe)
            return candidates or self.fallback.propose(goal, universe, active_entity_ids)
        except Exception:
            return self.fallback.propose(goal, universe, active_entity_ids)

    def _parse_actions(self, text: str, universe: Universe) -> list[TransformationCandidate]:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return []
        actions = json.loads(text[start:end + 1])
        candidates: list[TransformationCandidate] = []
        for action in actions:
            candidate = self._to_candidate(action, universe)
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    def _to_candidate(self, action: dict[str, Any], universe: Universe) -> TransformationCandidate | None:
        kind = action.get("action")
        if kind == "create_entity" and action.get("name"):
            return TransformationCandidate(
                name="create_entity", task_type="create",
                params={"name": action["name"], "type": action.get("type", "concept")},
                cost=1.0, description=f"Create entity {action['name']}",
                execute=make_create_entity(action["name"], action.get("type", "concept")),
            )
        if kind == "update_entity" and action.get("entity_id") in universe.entities:
            return TransformationCandidate(
                name="update_entity", task_type="update",
                params={"entity_id": action["entity_id"]},
                cost=0.5, description=f"Update entity {action['entity_id']}",
                execute=make_update_entity(action["entity_id"], action.get("state") or {}, action.get("knowledge") or {}),
            )
        if kind == "add_relation" and action.get("source") in universe.entities and action.get("target") in universe.entities:
            relation_type = action.get("relation_type", "associated_with")
            return TransformationCandidate(
                name="add_relation", task_type="relate",
                params={"source": action["source"], "target": action["target"], "relation": relation_type},
                cost=0.2, description=f"Relate {action['source']} to {action['target']}",
                execute=make_add_relation(action["source"], action["target"], relation_type),
            )
        if kind == "merge_entities" and action.get("source") in universe.entities and action.get("target") in universe.entities:
            return TransformationCandidate(
                name="merge_entities", task_type="merge",
                params={"source": action["source"], "target": action["target"]},
                cost=1.4, description="Merge two entities",
                execute=make_merge_entities(action["source"], action["target"], action.get("name", "merged_concept")),
            )
        if kind == "query_memory":
            return TransformationCandidate(
                name="query_memory", task_type="query", params={},
                cost=0.3, description="Query memory", execute=lambda u: u,
            )
        return None
