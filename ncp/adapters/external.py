from __future__ import annotations

class ExternalAdapter:
    def __init__(self, name: str):
        self.name = name

    def available(self) -> bool:
        return False
