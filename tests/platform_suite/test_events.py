"""Tests for event system."""


from ncp.events.bus import EventBus
from ncp.events.event import Event, EventType
from ncp.events.queue import EventQueue
from ncp.events.registry import EventRegistry


class TestEvent:
    def test_event_creation(self):
        e = Event.create(EventType.PLANNER_STARTED, {"goal": "test"}, source="planner")
        assert e.type == EventType.PLANNER_STARTED.value
        assert e.payload["goal"] == "test"

    def test_event_serialization(self):
        e = Event.create(EventType.SYSTEM_STARTED, {})
        d = e.to_dict()
        assert "id" in d
        assert "timestamp" in d


class TestEventQueue:
    def test_queue_put_get(self):
        q = EventQueue(max_size=10)
        event = Event.create(EventType.SYSTEM_STARTED, {})
        assert q.put(event) is True
        retrieved = q.get()
        assert retrieved is not None
        assert retrieved.type == EventType.SYSTEM_STARTED.value

    def test_queue_size_limit(self):
        q = EventQueue(max_size=2)
        q.put(Event.create(EventType.SYSTEM_STARTED, {}))
        q.put(Event.create(EventType.SYSTEM_STARTED, {}))
        assert q.is_full() is True
        assert q.put(Event.create(EventType.SYSTEM_STARTED, {})) is False


class TestEventBus:
    def test_bus_publish_subscribe(self):
        bus = EventBus(queue_size=10)
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventType.SYSTEM_STARTED.value, handler)
        bus.start()

        event = Event.create(EventType.SYSTEM_STARTED, {"test": True})
        bus.publish(event)

        bus.stop()
        assert len(received) == 0  # Events processed via process_one, not auto

    def test_bus_start_stop(self):
        bus = EventBus()
        bus.start()
        assert bus.is_running is True
        bus.stop()
        assert bus.is_running is False


class TestEventRegistry:
    def test_subscribe_unsubscribe(self):
        reg = EventRegistry()
        def handler(e):
            return None
        reg.subscribe("test", handler)
        assert len(reg.get_handlers("test")) == 1
        reg.unsubscribe("test", handler)
        assert len(reg.get_handlers("test")) == 0

    def test_global_subscription(self):
        reg = EventRegistry()
        def handler(e):
            return None
        reg.subscribe_all(handler)
        assert len(reg.get_handlers("any")) == 1
