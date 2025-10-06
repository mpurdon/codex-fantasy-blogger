"""Base class for agents."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Agent(ABC):
    """Simple base for agents in the workflow."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, *args, **kwargs):  # noqa: ANN002, ANN003 - interface defined per agent
        raise NotImplementedError
