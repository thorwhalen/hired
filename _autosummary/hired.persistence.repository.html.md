# hired.persistence.repository

A small repository base that maps validated domain models to a key-value store.

A [`Repository`](#hired.persistence.repository.Repository) wraps any `MutableMapping` (typically a `dol` file
store from [`hired.persistence.base`](hired.persistence.base.html.md#module-hired.persistence.base)) and a pydantic model class, handling
(de)serialization and validation so domain code deals in models, not dicts.

### Classes

| [`Repository`](#hired.persistence.repository.Repository)(store, \*[, model])   | Validated CRUD over a `MutableMapping` for a single pydantic model type.   |
|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------|

### *class* hired.persistence.repository.Repository(store, , model=None)

Bases: [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[`M`]

Validated CRUD over a `MutableMapping` for a single pydantic model type.

Subclasses set `model` and [`key_of()`](#hired.persistence.repository.Repository.key_of). The store holds plain
JSON-able dicts; models are validated on the way in and out.

#### key_of(item)

Derive the storage key for an item (defaults to its `id` field).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
