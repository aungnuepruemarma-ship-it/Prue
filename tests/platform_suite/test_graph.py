"""Tests for graph module."""

from uuid import uuid4

from ncp.graph.edge import Edge, EdgeType
from ncp.graph.fractal import FractalAnalyzer
from ncp.graph.graph import Graph
from ncp.graph.hierarchy import GraphHierarchy
from ncp.graph.index import GraphIndex
from ncp.graph.metrics import GraphMetrics
from ncp.graph.node import Node
from ncp.graph.query import QueryEngine
from ncp.graph.traversal import TraversalEngine


class TestNode:
    def test_node_creation(self):
        n = Node(label="test", node_type="concept")
        assert n.label == "test"
        assert n.node_type == "concept"

    def test_node_confidence_update(self):
        n = Node(confidence=0.5)
        n.update_confidence(0.8)
        assert n.confidence == 0.8


class TestEdge:
    def test_edge_creation(self):
        e = Edge(source_id=uuid4(), target_id=uuid4(), edge_type=EdgeType.CAUSAL.value)
        assert e.weight == 1.0


class TestGraph:
    def test_empty_graph(self):
        g = Graph(name="test")
        assert g.get_stats()["node_count"] == 0

    def test_add_node(self):
        g = Graph()
        n = Node(label="test")
        g.add_node(n)
        assert g.get_stats()["node_count"] == 1

    def test_add_edge(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        g.add_node(n1)
        g.add_node(n2)
        e = Edge(source_id=n1.id, target_id=n2.id)
        g.add_edge(e)
        assert g.get_stats()["edge_count"] == 1

    def test_neighbors(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(Edge(source_id=n1.id, target_id=n2.id))
        neighbors = g.get_neighbors(n1.id)
        assert len(neighbors) == 1
        assert neighbors[0].label == "b"

    def test_find_path(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        n3 = Node(label="c")
        for n in [n1, n2, n3]:
            g.add_node(n)
        g.add_edge(Edge(source_id=n1.id, target_id=n2.id))
        g.add_edge(Edge(source_id=n2.id, target_id=n3.id))

        path = g.find_path(n1.id, n3.id)
        assert len(path) == 3

    def test_remove_node(self):
        g = Graph()
        n = Node(label="test")
        g.add_node(n)
        g.remove_node(n.id)
        assert g.get_stats()["node_count"] == 0

    def test_graph_stats(self):
        g = Graph()
        for i in range(5):
            g.add_node(Node(label=f"n{i}"))
        stats = g.get_stats()
        assert stats["node_count"] == 5


class TestGraphHierarchy:
    def test_hierarchy(self):
        h = GraphHierarchy()
        g = Graph(name="level0")
        h.add_graph(g, level=0)
        assert h.num_levels() == 1

    def test_parent_child(self):
        h = GraphHierarchy()
        parent = Graph(name="parent")
        child = Graph(name="child")
        h.add_graph(parent, level=0)
        h.add_graph(child, level=1, parent_id=parent.id)
        assert h.get_parent(child.id) == parent.id


class TestTraversalEngine:
    def test_bfs(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        n3 = Node(label="c")
        for n in [n1, n2, n3]:
            g.add_node(n)
        g.add_edge(Edge(source_id=n1.id, target_id=n2.id))
        g.add_edge(Edge(source_id=n1.id, target_id=n3.id))

        te = TraversalEngine(g)
        result = te.bfs(n1.id)
        assert len(result) == 3

    def test_dfs(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(Edge(source_id=n1.id, target_id=n2.id))

        te = TraversalEngine(g)
        result = te.dfs(n1.id)
        assert len(result) == 2


class TestQueryEngine:
    def test_find_by_label(self):
        g = Graph()
        n = Node(label="target")
        g.add_node(n)
        qe = QueryEngine(g)
        found = qe.get_node_by_label("target")
        assert found is not None

    def test_get_by_type(self):
        g = Graph()
        g.add_node(Node(label="a", node_type="concept"))
        g.add_node(Node(label="b", node_type="fact"))
        qe = QueryEngine(g)
        concepts = qe.get_nodes_by_type("concept")
        assert len(concepts) == 1


class TestGraphIndex:
    def test_build_and_search(self):
        g = Graph()
        n = Node(label="test", embedding=[1.0, 0.0, 0.0])
        g.add_node(n)

        idx = GraphIndex()
        idx.build(g)

        results = idx.search([1.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1


class TestGraphMetrics:
    def test_empty_metrics(self):
        g = Graph()
        m = GraphMetrics.compute(g)
        assert m.node_count == 0

    def test_simple_metrics(self):
        g = Graph()
        n1 = Node(label="a")
        n2 = Node(label="b")
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(Edge(source_id=n1.id, target_id=n2.id))

        m = GraphMetrics.compute(g)
        assert m.node_count == 2
        assert m.edge_count == 1
        assert m.avg_degree == 0.5


class TestFractalAnalyzer:
    def test_fractal_dimension_empty(self):
        h = GraphHierarchy()
        fa = FractalAnalyzer(h)
        g = Graph()
        df = fa.compute_fractal_dimension(g)
        assert df == 0.0
