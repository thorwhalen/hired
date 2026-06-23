"""A small repository base that maps validated domain models to a key-value store.

A :class:`Repository` wraps any ``MutableMapping`` (typically a :mod:`dol` file
store from :mod:`hired.persistence.base`) and a pydantic model class, handling
(de)serialization and validation so domain code deals in models, not dicts.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from typing import Generic, TypeVar

from pydantic import BaseModel

M = TypeVar('M', bound=BaseModel)


class Repository(Generic[M]):
    """Validated CRUD over a ``MutableMapping`` for a single pydantic model type.

    Subclasses set :attr:`model` and :meth:`key_of`. The store holds plain
    JSON-able dicts; models are validated on the way in and out.
    """

    model: type[M]

    def __init__(self, store: MutableMapping, *, model: type[M] | None = None):
        self._store = store
        if model is not None:
            self.model = model
        if not getattr(self, 'model', None):
            raise TypeError('Repository requires a `model` class.')

    # --- subclasses may override ------------------------------------------
    def key_of(self, item: M) -> str:
        """Derive the storage key for an item (defaults to its ``id`` field)."""
        return getattr(item, 'id')

    # --- core CRUD ---------------------------------------------------------
    def add(self, item: M) -> str:
        key = self.key_of(item)
        self._store[key] = item.model_dump(mode='json')
        return key

    def get(self, key: str) -> M:
        return self.model.model_validate(self._store[key])

    def __getitem__(self, key: str) -> M:
        return self.get(key)

    def __setitem__(self, key: str, item: M) -> None:
        self._store[key] = item.model_dump(mode='json')

    def __delitem__(self, key: str) -> None:
        del self._store[key]

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def values(self) -> Iterator[M]:
        for key in self._store:
            yield self.get(key)

    def items(self) -> Iterator[tuple[str, M]]:
        for key in self._store:
            yield key, self.get(key)
