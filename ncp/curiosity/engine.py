from __future__ import annotations
from collections import Counter
from ..core.universe import Universe

class CuriosityEngine:
    def suggest_next_goal(self, universe: Universe, events: list[dict]) -> str:
        if not events:
            return "explore current memory"
        candidates = Counter()
        for e in events[-10:]:
            goal = str(e.get("goal", ""))
            for word in goal.lower().split():
                if len(word) > 3:
                    candidates[word] += 1
        if candidates:
            top = candidates.most_common(1)[0][0]
            return f"research {top}"
        return "inspect memory graph"
