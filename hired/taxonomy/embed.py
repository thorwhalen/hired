"""The label-embedding seam (the ``embeddings`` extra).

An *embedder* is any ``Callable[[Sequence[str]], array-like (n, d)]``. The default,
:func:`sentence_transformer_embedder`, wraps ``all-MiniLM-L6-v2`` (384 dimensions,
CPU, no API key), imported only when called. Any other embedder can be injected
(an API model, or one from the fleet's embedding packages) as long as it returns
one vector per input text.

Vectors are compared by cosine. Everything here needs ``numpy``, which comes with
the ``embeddings`` extra.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

Embedder = Callable[[Sequence[str]], Any]

DFLT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_MISSING = (
    "Embedding-based skill adjacency needs the 'embeddings' extra:\n"
    "    pip install 'hired[embeddings]'"
)


def require_numpy():
    """Import numpy, or raise an ``ImportError`` that names the extra."""
    try:
        import numpy
    except ImportError as e:  # pragma: no cover - numpy ships with the extra
        raise ImportError(_MISSING) from e
    return numpy


def sentence_transformer_embedder(
    model_name: str = DFLT_EMBEDDING_MODEL, *, batch_size: int = 256
) -> Embedder:
    """An embedder backed by a local sentence-transformers model (loaded now)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(_MISSING) from e
    model = SentenceTransformer(model_name)

    def embed(texts: Sequence[str]):
        return model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    return embed


def unit_rows(matrix: Any):
    """``matrix`` as float32 rows of unit length (zero rows stay zero)."""
    np = require_numpy()
    m = np.asarray(matrix, dtype="float32")
    if m.ndim == 1:
        m = m[None, :]
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(norms == 0, 1.0, norms)
