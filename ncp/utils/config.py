from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Config:
    max_entities: int = 1000
    max_relations: int = 5000
    skill_threshold: int = 2
    active_threshold: float = 0.35
    output_dir: str = "ncp_output"
