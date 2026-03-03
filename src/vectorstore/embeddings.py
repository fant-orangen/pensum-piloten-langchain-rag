"""Embedding model accessor.

Delegates to the central model factory in src.models so the provider
is controlled by a single LLM_PROVIDER setting.
"""

from src.models import get_embeddings

__all__ = ["get_embeddings"]
