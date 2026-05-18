"""Abstract base class shared by all cycling-coach agents."""

import logging
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Common interface and utilities for every agent in the pipeline.

    Each concrete agent receives the shared context dict, performs its work
    (API calls, LLM inference, calculations, etc.), and returns the enriched
    context so the next agent can build on it.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """Execute this agent's work and return the updated context.

        Args:
            context: Shared pipeline state created by ``create_context()``.

        Returns:
            The same dict with this agent's outputs written in-place.
        """

    def _add_error(self, context: dict, message: str) -> None:
        """Append *message* to ``context['errors']`` and log it as an error.

        Args:
            context: Shared pipeline state.
            message: Human-readable description of what went wrong.
        """
        context.setdefault("errors", []).append(message)
        self.logger.error(message)
