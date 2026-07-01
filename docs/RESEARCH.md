# NCP in Context: Related Work and Borrowable Ideas

*Positions NCP's design against agent orchestration frameworks, cognitive architectures, formally-verified action gating, and skill-library research. Companion to `ANALYSIS.md`.*

## 1. What NCP is, in one sentence

NCP proposes a loop where every candidate action must pass an explicit **admissibility gate (Φ)** and is then ranked by a **global objective over the resulting world state** — a "verify-then-score" architecture — combined with automatic **skill promotion** from recurring action patterns and a typed **capability router**.

Each of these ideas has a mature counterpart in the literature. NCP's distinguishing (if currently under-implemented) trait is putting all four in one small loop with the constraint gate as a first-class, mandatory stage.

## 2. Related work, mapped module by module

### 2.1 Orchestration frameworks — LangGraph, AutoGen, CrewAI

The 2026 landscape of agent orchestration is dominated by [LangGraph](https://presenc.ai/research/multi-agent-orchestration-frameworks-2026) (graph-based control flow, the largest production footprint), [CrewAI](https://cordum.io/blog/ai-agent-frameworks-comparison) (role-based crews, easiest to prototype), and [AutoGen](https://pecollective.com/blog/ai-agent-frameworks-compared/) (conversational multi-agent teams, strongest in research settings).

What they map to in NCP:

| NCP piece | Framework counterpart | Gap |
|---|---|---|
| `Runtime.step` loop | LangGraph's directed graph with conditional edges | NCP's flow is hardcoded; LangGraph makes the topology data |
| `JsonStore.save()` every step | LangGraph **checkpointing with time travel** — durable per-step state snapshots you can rewind and fork | NCP rewrites whole files and can't restore (there is no load path) |
| `CapabilityRouter` + `CapabilityCard` | Tool/agent registries with schema-typed dispatch | NCP's cards are dead data; routing is keyword matching |
| `MemoryGraph` / `HistoryLog` | Framework memory stores (episodic threads, vector recall) | NCP has structure but no retrieval — nothing ever *reads* the graph |

**Verdict**: NCP's loop is a miniature of what LangGraph formalizes. The single most valuable import is *checkpointed, resumable state* — it would also force fixing the clone/aliasing bug, since checkpoints demand value semantics.

### 2.2 Cognitive architectures — Soar, ACT-R, CoALA

NCP's spec (`spec/requirements.md`) demands "working, episodic, semantic, and skill memory layers" — this is precisely the memory taxonomy that [Soar and ACT-R introduced](https://arxiv.org/html/2309.02427v3) and that the **CoALA** framework ("Cognitive Architectures for Language Agents", [arXiv:2309.02427](https://arxiv.org/html/2309.02427v3)) revived for LLM agents. NCP implements none of the tiering, but the vocabulary is clearly inherited from this lineage.

The strongest single parallel is **Soar chunking vs NCP skill promotion**. Soar's chunking mechanism [compiles successful problem-solving episodes into reusable productions](https://quiq.com/blog/what-is-cognitive-architecture/) — effectively writing new rules into procedural memory. NCP's `SkillExtractor.promote` is a degenerate version: it counts action bigrams. Three things Soar does that NCP should copy:

1. **Success-gating** — Soar chunks over *solved* subgoals; NCP promotes bigrams from all events including rejected ones (violating its own invariant).
2. **Context in the pattern** — a chunk records the conditions under which the sequence worked, not just the sequence. NCP's `Skill.pattern` is two bare op names with no preconditions.
3. **Skills feed back into behavior** — Soar's chunks fire on later matching states. NCP's skills are write-only: nothing ever consults `SkillLibrary` when proposing candidates.

NCP's `ActivationEngine` (token-overlap × confidence, threshold, decay-free) is likewise a toy version of ACT-R's **activation-based retrieval** (base-level activation + spreading activation + noise). Borrowing even base-level decay (recently-used entities stay warm) would make activation less knife-edge than the current 0.34-vs-0.35 behavior.

### 2.3 Constraint gates — actual SMT, guardrails, shielding

NCP's README promises an "SMT-style finite constraint gate"; the implementation is six if-statements. The real version of this idea now exists in the literature: [solver-aided verification of tool-use policy compliance](https://arxiv.org/html/2603.20449) translates policies into SMT-LIB and intercepts planned tool calls with **Z3 at runtime**; deterministic control layers ([Chimera](https://medium.com/data-science-collective/csl-core-the-practical-guide-to-writing-safety-policies-your-ai-cant-break-231781c5684e), [provably secure agent guardrails](https://arxiv.org/html/2605.29251)) enforce policies verified at compile time; [Agentproof](https://arxiv.org/pdf/2603.20356) statically verifies agent workflow graphs.

The shared architecture in that work matches NCP's Φ position exactly: *the probabilistic proposer (LLM/reasoner) is untrusted; a deterministic checker sits between proposal and execution*. What NCP needs to be a legitimate member of this family:

- **Declarative constraints** — Φ's checks should be data (predicates over the trial state), not hardcoded branches, so policies can be added without editing the checker. The hardcoded `"forbidden" in goal` check is the anti-pattern.
- **Side-effect-free evaluation** — trial application must be on a true deep copy (currently violated; see `ANALYSIS.md` §7.1). Every system above treats the checker's purity as non-negotiable.
- **Optionally, a real solver** — for the finite domain NCP works in (bounded entities/relations), encoding invariants in Z3 via `z3-solver` is a small dependency and would make "SMT-style" literal. This is genuinely fashionable and useful territory in 2026.

### 2.4 Skill libraries — Voyager and successors

[Voyager](https://arxiv.org/abs/2305.16291) established the modern skill-library pattern: an ever-growing library of **executable, self-verified code skills**, added only after the skill demonstrably works, retrieved by embedding similarity, and composed into more complex skills. Follow-up work extends this with RL-refined skills (SAGE) and the broader ["skill engineering" paradigm](https://arxiv.org/html/2602.12430v1) — skills as bundles of instructions + scripts + metadata, loaded on demand ([SoK: Agentic Skills](https://arxiv.org/html/2602.20867v1)).

Against this, NCP's bigram skills are missing the three properties that make Voyager's library work: skills are **executable** (Voyager stores programs; NCP stores two op names), **verified** (added on success; NCP counts rejected events), and **retrieved** (used in later tasks; NCP never reads them back).

## 3. Where NCP is genuinely distinctive

- **Objective over the resulting world state.** Most agent frameworks score *actions* (rewards, critiques, votes). NCP scores the *post-state* (entropy + size + cost of the trial universe). That's closer to model-based planning/utility theory than to mainstream LLM-agent practice, and it's a defensible niche — but the current objective is goal-agnostic, which inverts its incentives (`ANALYSIS.md` §7.3). Adding a goal-relevance term would keep the distinctive shape while fixing the behavior.
- **The mandatory gate-then-score pipeline.** Guardrail research bolts checking onto existing agents; NCP builds the loop around it. As a *reference architecture for admissibility-gated agents*, a small, dependency-free, readable implementation has pedagogical value — if the gate is actually pure.

## 4. Borrowable ideas, ranked by fit

1. **Value-semantics state + checkpointing** (from LangGraph): deep-copy clones, then persist per-step snapshots you can reload. Fixes the aliasing bug and adds resumability at once.
2. **Success-gated, retrievable skills** (from Soar chunking + Voyager): promote only from accepted traces, store preconditions, and consult the library during candidate proposal.
3. **Declarative Φ, optionally Z3-backed** (from solver-aided policy compliance): constraints as data; a real solver makes the "SMT-style" claim honest and enables unsat-core-based *explanations* — a natural upgrade to `explanation.py`.
4. **Goal-conditioned objective** (from utility-based planning): add a relevance term (e.g., token overlap between goal and candidate description/params) so the goal's own action isn't structurally penalized.
5. **Real capability routing** (from tool-schema dispatch): make `route` consult the `CapabilityCard` registry — match goal-derived task types to card strengths — and implement one real LLM adapter behind the existing `Reasoner` ABC so the router has something meaningfully different to route to.

Concrete implementation steps for these live in `IMPROVEMENT_ROADMAP.md`.

## Sources

- [Multi-Agent Orchestration Frameworks 2026 (Presenc AI)](https://presenc.ai/research/multi-agent-orchestration-frameworks-2026)
- [Best AI Agent Frameworks 2026 (Cordum)](https://cordum.io/blog/ai-agent-frameworks-comparison)
- [AI Agent Frameworks Compared: LangGraph vs CrewAI vs AutoGen (PE Collective)](https://pecollective.com/blog/ai-agent-frameworks-compared/)
- [Cognitive Architectures for Language Agents (CoALA)](https://arxiv.org/html/2309.02427v3)
- [Cognitive Architecture Explained (Quiq)](https://quiq.com/blog/what-is-cognitive-architecture/)
- [SoK: Agentic Skills — Beyond Tool Use in LLM Agents](https://arxiv.org/html/2602.20867v1)
- [Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents](https://arxiv.org/html/2603.20449)
- [Provably Secure Agent Guardrail](https://arxiv.org/html/2605.29251)
- [Agentproof: Static Verification of Agent Workflow Graphs](https://arxiv.org/pdf/2603.20356)
- [Chimera: Deterministic Control Layer (Medium)](https://medium.com/data-science-collective/csl-core-the-practical-guide-to-writing-safety-policies-your-ai-cant-break-231781c5684e)
- [Voyager: An Open-Ended Embodied Agent with Large Language Models](https://arxiv.org/abs/2305.16291)
- [Agent Skills for Large Language Models: Architecture, Acquisition, Security](https://arxiv.org/html/2602.12430v1)
