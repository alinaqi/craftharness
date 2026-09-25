"""conduit source adapters.

Each adapter normalizes one external provider into the conduit ``Record``
shape. Adapters are registered here by ``capability`` so the gateway can route
a ``Query`` to the adapters that serve it. A capability may have more than one
provider (independence for high-risk claims), so the registry maps a
capability to a list of adapter classes.
"""
from __future__ import annotations

from .dataforseo import DataForSeoAdapter
from .apify import ApifyAdapter

# capability -> list of adapter classes serving it
REGISTRY: dict[str, list[type]] = {
    "keywords": [DataForSeoAdapter],
    "crawl": [ApifyAdapter],
}

# provider (str) -> adapter class, for direct lookup by name
ADAPTERS: dict[str, type] = {
    DataForSeoAdapter.provider: DataForSeoAdapter,
    ApifyAdapter.provider: ApifyAdapter,
}

__all__ = ["ADAPTERS", "REGISTRY", "DataForSeoAdapter", "ApifyAdapter"]
