# hired.taxonomy.embed

The label-embedding seam (the `embeddings` extra).

An *embedder* is any `Callable[[Sequence[str]], array-like (n, d)]`. The default,
[`sentence_transformer_embedder()`](#hired.taxonomy.embed.sentence_transformer_embedder), wraps `all-MiniLM-L6-v2` (384 dimensions,
CPU, no API key), imported only when called. Any other embedder can be injected
(an API model, or one from the fleet’s embedding packages) as long as it returns
one vector per input text.

Vectors are compared by cosine. Everything here needs `numpy`, which comes with
the `embeddings` extra.

### Functions

| [`require_numpy`](#hired.taxonomy.embed.require_numpy)()                                  | Import numpy, or raise an `ImportError` that names the extra.           |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [`sentence_transformer_embedder`](#hired.taxonomy.embed.sentence_transformer_embedder)([model_name, ...]) | An embedder backed by a local sentence-transformers model (loaded now). |
| [`unit_rows`](#hired.taxonomy.embed.unit_rows)(matrix)                                | `matrix` as float32 rows of unit length (zero rows stay zero).          |

### hired.taxonomy.embed.require_numpy()

Import numpy, or raise an `ImportError` that names the extra.

### hired.taxonomy.embed.sentence_transformer_embedder(model_name='sentence-transformers/all-MiniLM-L6-v2', , batch_size=256)

An embedder backed by a local sentence-transformers model (loaded now).

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]], [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.taxonomy.embed.unit_rows(matrix)

`matrix` as float32 rows of unit length (zero rows stay zero).
