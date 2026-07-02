"""Tests for the feature-hashing embeddings and vector memory retrieval."""

from ncp.core.entities import Memory
from ncp.events.bus import EventBus
from ncp.memory.embedding import embed, similarity
from ncp.memory.manager import MemoryManager
from ncp.storage.storage import Storage
from ncp.utils.config import Config


def make_memory() -> MemoryManager:
    config = Config()
    return MemoryManager(storage=Storage(config=config), event_bus=EventBus(queue_size=100), config=config)


class TestEmbedding:
    def test_deterministic_and_normalized(self):
        a = embed("optimize the database query")
        assert a == embed("optimize the database query")
        assert abs(sum(v * v for v in a) - 1.0) < 1e-9

    def test_similarity_orders_related_above_unrelated(self):
        query = embed("optimize the database query")
        related = embed("tune slow database queries")
        unrelated = embed("paint the garden fence")
        assert similarity(query, related) > similarity(query, unrelated)
        assert similarity(query, related) > 0.2

    def test_empty_text_embeds_to_zero_vector(self):
        assert not any(embed(""))


class TestMemoryVectorRetrieval:
    def test_store_populates_vector_store_and_embeddings(self):
        memory = make_memory()
        item = Memory(content="the router selects providers by capability", memory_type="semantic")
        memory.store(item)
        assert str(item.id) in memory.vectors.vectors
        assert item.embeddings is not None and any(item.embeddings)

    def test_retrieve_finds_paraphrased_memory_via_vectors(self):
        memory = make_memory()
        memory.store(Memory(
            content="checkpoint every execution node for crash recovery",
            memory_type="episodic",
            name="zq-opaque-name",  # keyword search can't find it by content terms
        ))
        results = memory.retrieve("recover execution after a crash", top_k=5)
        assert any("checkpoint every execution node" in m.content for m in results)

    def test_store_mirrors_into_knowledge_graph(self):
        memory = make_memory()
        memory.store(Memory(content="the kernel unifies both pipelines", memory_type="semantic"))
        memory.store(Memory(content="providers are selected by constraints", memory_type="semantic"))
        graph = memory.knowledge_graph
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1, "consecutive items are linked temporally"
        assert memory.retrieval.graph is graph, "retrieval engine reads the live mirror"
        assert memory.graph_index.lookup_by_type("semantic")

    def test_retrieve_uses_graph_label_match(self):
        memory = make_memory()
        memory.store(Memory(content="the kernel unifies both pipelines", memory_type="episodic", name="x"))
        results = memory.retrieve("kernel", top_k=5)
        assert any("kernel unifies" in m.content for m in results)

    def test_retrieve_skips_unrelated_vectors(self):
        memory = make_memory()
        memory.store(Memory(content="paint the garden fence", memory_type="episodic", name="x"))
        results = memory.retrieve("compile the execution graph", top_k=5)
        assert not any("garden fence" in m.content for m in results)
