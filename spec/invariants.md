# Invariants

- No state update is committed without constraint validation.
- Every entity has an id, type, and version.
- History is append-only.
- Skills are promoted only from repeated successful traces.
- Persistent storage must preserve provenance and version metadata.
