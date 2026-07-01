from __future__ import annotations
from .base import Reasoner
from ..core.universe import Universe
from ..core.transformation import TransformationCandidate
from ..core.transformations import make_create_entity, make_update_entity, make_add_relation, make_merge_entities

class RuleBasedReasoner(Reasoner):
    def propose(self, goal: str, universe: Universe, active_entity_ids: list[str]) -> list[TransformationCandidate]:
        goal_l = goal.lower()
        candidates: list[TransformationCandidate] = []

        if "create" in goal_l or "add" in goal_l or "new" in goal_l:
            candidates.append(
                TransformationCandidate(
                    name="create_entity",
                    task_type="create",
                    params={"name": "generated_item", "type": "concept"},
                    cost=1.0,
                    description="Create a new concept entity",
                    execute=make_create_entity("generated_item", "concept", {"source_goal": goal}, {"goal": goal}),
                )
            )

        if active_entity_ids:
            target = active_entity_ids[0]
            candidates.append(
                TransformationCandidate(
                    name="update_entity",
                    task_type="update",
                    params={"entity_id": target},
                    cost=0.5,
                    description="Update the most active entity",
                    execute=make_update_entity(target, {"last_goal": goal}, {"goal": goal}),
                )
            )

        if len(active_entity_ids) >= 2:
            a, b = active_entity_ids[:2]
            candidates.append(
                TransformationCandidate(
                    name="merge_entities",
                    task_type="merge",
                    params={"source": a, "target": b},
                    cost=1.4,
                    description="Merge the two most active entities",
                    execute=make_merge_entities(a, b, "merged_concept"),
                )
            )

        if universe.entities and active_entity_ids:
            src = active_entity_ids[0]
            tgt = list(universe.entities.keys())[0]
            candidates.append(
                TransformationCandidate(
                    name="add_relation",
                    task_type="relate",
                    params={"source": src, "target": tgt, "relation": "associated_with"},
                    cost=0.2,
                    description="Add a relation to anchor the active context",
                    execute=make_add_relation(src, tgt, "associated_with"),
                )
            )

        candidates.append(
            TransformationCandidate(
                name="query_memory",
                task_type="query",
                params={"query": goal},
                cost=0.3,
                description="Query memory for the current goal",
                execute=lambda u: u,
            )
        )
        return candidates
