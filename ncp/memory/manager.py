"""Memory manager - Coordinates all memory tiers.

Manages working, session, episodic, semantic, procedural, skill, and archive memory.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from ncp.core.entities import Entity, Memory, Result, Skill, Task
from ncp.events.bus import EventBus
from ncp.events.event import EventType
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.storage import StorageInterface
from ncp.memory.archive import ArchiveMemory
from ncp.memory.consolidation import ConsolidationManager
from ncp.memory.embedding import embed, similarity
from ncp.memory.episodic import EpisodicMemory
from ncp.memory.forgetting import ForgettingPolicy
from ncp.memory.policies import MemoryPolicies
from ncp.memory.procedural import ProceduralMemory
from ncp.memory.ranking import MemoryRanker
from ncp.memory.replay import ReplayBuffer
from ncp.memory.retrieval import RetrievalEngine
from ncp.memory.semantic import SemanticMemory
from ncp.memory.session import SessionMemory
from ncp.memory.skill import SkillMemory
from ncp.memory.working import WorkingMemory
from ncp.storage.vector_store import VectorStore
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryManager(MemoryInterface):
    """Coordinates all memory tiers.

    Responsibilities:
    - Write new events into working/session memory
    - Trigger consolidation
    - Apply forgetting policy
    - Expose retrieval API
    """
    storage: StorageInterface
    event_bus: EventBus
    config: Config

    # Memory tiers
    working: WorkingMemory = field(default_factory=WorkingMemory)
    sessions: Dict[str, SessionMemory] = field(default_factory=dict)
    episodic: EpisodicMemory = field(default_factory=EpisodicMemory)
    semantic: SemanticMemory = field(default_factory=SemanticMemory)
    procedural: ProceduralMemory = field(default_factory=ProceduralMemory)
    skill_memory: SkillMemory = field(default_factory=SkillMemory)
    archive: ArchiveMemory = field(default_factory=ArchiveMemory)

    # Supporting components
    vectors: VectorStore = field(default_factory=VectorStore)
    vector_texts: Dict[str, str] = field(default_factory=dict)
    retrieval: RetrievalEngine = field(default_factory=RetrievalEngine)
    ranker: MemoryRanker = field(default_factory=MemoryRanker)
    forgetting: ForgettingPolicy = field(default_factory=ForgettingPolicy)
    replay: ReplayBuffer = field(default_factory=ReplayBuffer)
    policies: MemoryPolicies = field(default_factory=MemoryPolicies)

    def __post_init__(self):
        # Initialize consolidation manager
        self.consolidation = ConsolidationManager(
            replay_buffer=self.replay,
            episodic=self.episodic,
            semantic=self.semantic,
            skill_memory=self.skill_memory,
            event_bus=self.event_bus,
            config=self.config,
        )

        # Configure from config
        self.working.max_items = self.config.get("memory.working.max_items", 1024)
        self.episodic.max_episodes = self.config.get("memory.episodic.max_episodes", 10000)
        self.semantic.max_concepts = self.config.get("memory.semantic.max_concepts", 5000)

        logger.info("MemoryManager initialized with %d tiers", 7)

    def store(self, item: Union[Entity, Task, Result, Memory]) -> None:
        """Store an item in memory.

        Routes to appropriate tier based on item type.
        """
        # Always add to working memory
        self.working.add(item)

        # Embed the item's text so it becomes vector-retrievable
        text = self._item_text(item)
        if text:
            vector = embed(text)
            if isinstance(item, Memory):
                item.embeddings = vector
            self.vectors.store_embedding(str(item.id), vector)
            self.vector_texts[str(item.id)] = text

        if isinstance(item, Memory):
            # Route to specific tier
            if item.memory_type == "episodic":
                self._store_episodic(item)
            elif item.memory_type == "semantic":
                self.semantic.add_concept(
                    name=item.name or item.content[:50],
                    description=item.content,
                    confidence=item.confidence,
                )
            elif item.memory_type == "skill":
                if isinstance(item, Skill):
                    self.skill_memory.add_skill(item)
            elif item.memory_type == "archive":
                self.archive.archive(item)

        elif isinstance(item, Result):
            # Store result in episodic memory
            if item.status == "success":
                self.episodic.add_episode(
                    task=Task(name=str(item.task_id)),
                    result=item,
                )

        elif isinstance(item, Task):
            # Store task execution trace
            pass  # Handled by session tracking

        # Emit event
        self.event_bus.publish(
            type=EventType.MEMORY_STORED.value,
            payload={
                "item_type": type(item).__name__,
                "item_id": str(item.id),
            },
        )

        logger.debug("Stored item: %s (%s)", item.id, type(item).__name__)

    def _item_text(self, item: Union[Entity, Task, Result, Memory]) -> str:
        """Derive the embeddable text for an item."""
        if isinstance(item, Memory):
            return item.content or item.name
        if isinstance(item, Result):
            return str(item.output) if item.output else str(item.task_id)
        if isinstance(item, (Task, Entity)):
            return getattr(item, "description", "") or item.name
        return ""

    def _store_episodic(self, memory: Memory) -> None:
        """Store in episodic memory."""
        # Create a synthetic episode
        self.episodic.episodes.append(
            self.episodic.add_episode(
                task=Task(name=memory.name or "unknown"),
                result=Result(status="stored"),
            )
        )

    def retrieve(self, query: str, top_k: int = 10) -> List[Memory]:
        """Retrieve relevant memories across all tiers."""
        results = []

        # 1. Search episodic memory
        episodes = self.episodic.search(query, top_k)
        for ep in episodes:
            results.append(Memory(
                content=f"Episode: {ep.task_name}",
                memory_type="episodic",
                confidence=0.8 if ep.success else 0.4,
            ))

        # 2. Search semantic memory
        concepts = self.semantic.search(query, top_k)
        for concept in concepts:
            results.append(Memory(
                content=f"{concept.name}: {concept.description}",
                memory_type="semantic",
                confidence=concept.confidence,
            ))

        # 3. Vector search over everything ever stored (catches paraphrases
        # the keyword searches above miss)
        query_vector = embed(query)
        for key in self.vectors.search(query_vector, top_k):
            stored = self.vectors.vectors.get(key, [])
            if similarity(query_vector, stored) < 0.25:
                continue  # nearest neighbour, but not actually near
            text = self.vector_texts.get(key)
            if text and not any(r.content == text for r in results):
                results.append(Memory(
                    content=text,
                    memory_type="semantic",
                    confidence=0.6,
                    embeddings=self.vectors.vectors.get(key),
                ))

        # 4. Rank and return
        if results:
            return self.ranker.rank(results, query, top_k)

        return results

    def update(self, item: Memory) -> None:
        """Update an existing memory."""
        if item.memory_type == "semantic":
            self.semantic.add_concept(
                name=item.name or item.content[:50],
                description=item.content,
                confidence=item.confidence,
            )

        self.event_bus.publish(
            type=EventType.MEMORY_STORED.value,
            payload={"item_id": str(item.id), "action": "updated"},
        )

    def consolidate(self) -> None:
        """Trigger memory consolidation."""
        if self.consolidation.should_consolidate():
            result = self.consolidation.consolidate()
            self.event_bus.publish(
                type=EventType.MEMORY_CONSOLIDATED.value,
                payload=result,
            )

    def working_memory(self) -> List[Entity]:
        """Get current working memory contents."""
        return self.working.get_all()

    def create_session(self, name: str = "") -> SessionMemory:
        """Create a new session."""
        session = SessionMemory(name=name or f"session_{len(self.sessions)}")
        self.sessions[str(session.session_id)] = session
        return session

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "working_size": self.working.size,
            "session_count": len(self.sessions),
            "episodic_count": self.episodic.episode_count,
            "semantic_count": self.semantic.concept_count,
            "procedural_count": self.procedural.workflow_count,
            "skill_count": self.skill_memory.active_skill_count,
            "archive_entries": len(self.archive.entries),
            "replay_buffer_size": self.replay.size,
        }
