"""SourceAdapter — the contract every conduit data source implements.

An adapter maps one ``capability`` (e.g. ``"web.search"``, ``"seo.keywords"``)
onto a concrete provider, fetching evidence as ``Record`` objects that already
carry ``Provenance``. The registry lets the gateway resolve a ``Query`` to the
adapter that serves its capability without hard-coding provider imports.

Pure stdlib. No side effects on import.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from conduit.core.schema import Query, Record

__all__ = ["SourceAdapter", "AdapterRegistry", "registry", "register", "get_adapter"]


class SourceAdapter(ABC):
    """Abstract base for a single-capability evidence source.

    Subclasses set ``capability`` and ``provider`` (either as class attributes
    or in ``__init__``) and implement ``fetch``. ``health`` reports whether the
    adapter can currently serve requests (credentials present, endpoint up).
    """

    capability: str = ""
    provider: str = ""

    @abstractmethod
    async def fetch(self, req: Query) -> list[Record]:
        """Fetch evidence for ``req`` and return records with provenance.

        Implementations must attach a ``Provenance`` to every ``Record`` (use
        ``conduit.core.make_provenance``) and honour ``req.timeout_ms`` /
        ``req.cost_budget``. Return an empty list when nothing matches; raise on
        transport/credential failure so the gateway can fall back.
        """
        raise NotImplementedError

    def health(self) -> bool:
        """Return True when the adapter is ready to serve requests.

        Default implementation reports healthy once both ``capability`` and
        ``provider`` are set; override to probe credentials or the upstream.
        """
        return bool(self.capability and self.provider)


class AdapterRegistry:
    """Maps a capability string to the adapter that serves it.

    One capability resolves to exactly one adapter; registering a second
    adapter for the same capability replaces the first unless ``replace`` is
    False, in which case a ``ValueError`` is raised.
    """

    def __init__(self) -> None:
        self._by_capability: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter, *, replace: bool = True) -> SourceAdapter:
        """Register ``adapter`` under its ``capability`` and return it."""
        capability = adapter.capability
        if not capability:
            raise ValueError("adapter.capability must be a non-empty string")
        if not replace and capability in self._by_capability:
            raise ValueError(f"capability already registered: {capability!r}")
        self._by_capability[capability] = adapter
        return adapter

    def unregister(self, capability: str) -> None:
        """Remove the adapter registered under ``capability`` if present."""
        self._by_capability.pop(capability, None)

    def get(self, capability: str) -> SourceAdapter | None:
        """Return the adapter for ``capability``, or None if unregistered."""
        return self._by_capability.get(capability)

    def require(self, capability: str) -> SourceAdapter:
        """Return the adapter for ``capability`` or raise ``KeyError``."""
        adapter = self._by_capability.get(capability)
        if adapter is None:
            raise KeyError(f"no adapter registered for capability: {capability!r}")
        return adapter

    def capabilities(self) -> list[str]:
        """Return the sorted list of registered capability names."""
        return sorted(self._by_capability)

    def healthy(self) -> dict[str, bool]:
        """Return a capability -> health() map for every registered adapter."""
        return {cap: a.health() for cap, a in self._by_capability.items()}


# Module-level default registry plus thin convenience wrappers so callers can
# ``from conduit.adapters.base import register, get_adapter`` without threading
# a registry instance everywhere.
registry = AdapterRegistry()


def register(adapter: SourceAdapter, *, replace: bool = True) -> SourceAdapter:
    """Register ``adapter`` in the default registry."""
    return registry.register(adapter, replace=replace)


def get_adapter(capability: str) -> SourceAdapter | None:
    """Look up an adapter by capability in the default registry."""
    return registry.get(capability)
