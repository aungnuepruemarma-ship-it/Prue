"""Tests for the event dispatcher/publisher/subscriber/priority and workers."""

from ncp.events.bus import EventBus
from ncp.events.dispatcher import EventDispatcher
from ncp.events.event import EventType
from ncp.events.priority import EventPriority
from ncp.events.publisher import EventPublisher
from ncp.events.subscriber import EventSubscriber
from ncp.workers.scheduler import WorkerScheduler


def make_bus() -> EventBus:
    return EventBus(queue_size=100, auto_dispatch=True)


class TestEventPublisher:
    def test_publish_carries_type_source_and_priority(self):
        bus = make_bus()
        bus.start()
        seen = []
        bus.subscribe(EventType.TASK_FAILED.value, seen.append)
        publisher = EventPublisher(bus, source="kernel")

        event = publisher.publish(EventType.TASK_FAILED, {"run": "r1"}, priority=EventPriority.HIGH)
        assert event.source == "kernel"
        assert event.priority == EventPriority.HIGH
        assert seen and seen[0].payload == {"run": "r1"}

    def test_set_source(self):
        publisher = EventPublisher(make_bus(), source="a")
        publisher.set_source("b")
        event = publisher.publish(EventType.TASK_STARTED, {})
        assert event.source == "b"


class TestEventPriority:
    def test_ordering(self):
        assert EventPriority.CRITICAL < EventPriority.HIGH < EventPriority.NORMAL
        assert EventPriority.NORMAL < EventPriority.LOW < EventPriority.BACKGROUND


class TestEventDispatcher:
    def test_routes_events_to_registered_workers(self):
        bus = make_bus()
        bus.start()
        dispatcher = EventDispatcher(bus)
        calls = []
        dispatcher.register_worker("w1", lambda e: calls.append(e.type), [EventType.TASK_FINISHED.value])

        assert dispatcher.get_workers_for(EventType.TASK_FINISHED.value) == ["w1"]
        assert dispatcher.get_workers_for("nothing.subscribed") == []
        bus.publish(type=EventType.TASK_FINISHED.value, payload={})
        assert calls == [EventType.TASK_FINISHED.value]


class TestEventSubscriber:
    def test_subscribe_and_unsubscribe(self):
        bus = make_bus()
        bus.start()
        subscriber = EventSubscriber(bus, name="observer")
        seen = []
        handler = seen.append

        subscriber.subscribe(EventType.TASK_STARTED.value, handler)
        bus.publish(type=EventType.TASK_STARTED.value, payload={"n": 1})
        subscriber.unsubscribe(EventType.TASK_STARTED.value, handler)
        bus.publish(type=EventType.TASK_STARTED.value, payload={"n": 2})
        assert len(seen) == 1 and seen[0].payload == {"n": 1}


class TestWorkerScheduler:
    def test_register_worker_delegates_to_dispatcher(self):
        bus = make_bus()
        bus.start()
        scheduler = WorkerScheduler(event_bus=bus)
        ran = []
        scheduler.register_worker("cleanup", lambda e: ran.append("cleanup"), [EventType.TASK_FINISHED.value])

        assert scheduler.dispatcher.get_workers_for(EventType.TASK_FINISHED.value) == ["cleanup"]
        scheduler.start_all()
        bus.publish(type=EventType.TASK_FINISHED.value, payload={})
        assert ran == ["cleanup"]
