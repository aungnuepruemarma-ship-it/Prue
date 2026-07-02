# Data Schemas

## Entity Hierarchy

Entity -> Goal -> Task -> Memory -> Skill -> Tool -> Result

## Event Schema

Event { id, type, payload, source, priority, timestamp }

## Graph Schema

Node { id, type, metadata, provenance, confidence, version }
Edge { id, source, target, type, weight, metadata }
