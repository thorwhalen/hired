"""
Tools to convert/cast resources.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Optional

# --- Optional parsers ---------------------------------------------------------

# YAML is optional: register YAML only if import succeeds.
try:
    import yaml  # type: ignore

    _HAS_YAML = True
except Exception:
    _HAS_YAML = False

# TOML registration policy (for 3.10 support):
# 1) Prefer stdlib tomllib (Py 3.11+)
# 2) Else try third-party 'toml'
# 3) Else: no TOML parsing registered
_HAS_TOMLLIB = False
_HAS_TOML = False
_TOML_LOADER = None  # callable: (text:str)->Mapping[str, Any]

try:  # Python 3.11+
    import tomllib  # type: ignore

    _HAS_TOMLLIB = True

    def _toml_loads(text: str) -> Mapping[str, Any]:
        return tomllib.loads(text)

    _TOML_LOADER = _toml_loads
except Exception:
    try:  # Fallback to third-party 'toml'
        import toml  # type: ignore

        _HAS_TOML = True

        def _toml_loads(text: str) -> Mapping[str, Any]:
            # toml.loads returns a dict-like mapping
            return toml.loads(text)

        _TOML_LOADER = _toml_loads
    except Exception:
        _TOML_LOADER = None  # No TOML support available.

# --- castgraph imports --------------------------------------------------------

from i2.castgraph import ConversionRegistry, ConversionError  # type: ignore


# --- Helpers ------------------------------------------------------------------


def _read_bytes_from_pathlike(p: Path, ctx: Optional[dict]) -> bytes:
    """Read bytes from real filesystem, unless a virtual fs mapping is provided."""
    if ctx and "fs" in ctx:
        fs = ctx["fs"]
        data = fs[str(p)]
        return (
            data if isinstance(data, (bytes, bytearray)) else str(data).encode("utf-8")
        )
    return p.read_bytes()


def _str_maybe_path_to_bytes(s: str, ctx: Optional[dict]) -> bytes:
    """Heuristic for str inputs: prefer ctx['fs'], else real path if exists, else text."""
    if ctx:
        fs = ctx.get("fs", {})
        if s in fs:
            data = fs[s]
            return (
                data
                if isinstance(data, (bytes, bytearray))
                else str(data).encode("utf-8")
            )
        treat_as_path = ctx.get("treat_str_as_path")
        if treat_as_path is True:
            return _read_bytes_from_pathlike(Path(s), ctx)
        if treat_as_path is False:
            return s.encode("utf-8")
    return (
        _read_bytes_from_pathlike(Path(s), ctx)
        if os.path.exists(s)
        else s.encode("utf-8")
    )


def _parse_json_bytes(b: bytes) -> Mapping[str, Any]:
    return json.loads(b.decode("utf-8"))


def _parse_toml_bytes(b: bytes) -> Mapping[str, Any]:
    if _TOML_LOADER is None:
        raise ConversionError("TOML support not available (tomllib/toml missing).")
    return _TOML_LOADER(b.decode("utf-8"))


def _parse_yaml_bytes(b: bytes) -> Mapping[str, Any]:
    if not _HAS_YAML:
        raise ConversionError("YAML support not available (pyyaml not installed).")
    return yaml.safe_load(b.decode("utf-8")) or {}


def _sniff_and_parse(b: bytes) -> Mapping[str, Any]:
    """
    Best-effort content sniffing with only the parsers that are actually available.
      1) JSON
      2) TOML (only if tomllib/toml available)
      3) YAML (only if pyyaml available)
    """
    # JSON
    try:
        return _parse_json_bytes(b)
    except Exception:
        pass
    # TOML (conditionally)
    if _TOML_LOADER is not None:
        try:
            return _parse_toml_bytes(b)
        except Exception:
            pass
    # YAML (conditionally)
    if _HAS_YAML:
        try:
            return _parse_yaml_bytes(b)
        except Exception:
            pass
    raise ConversionError("Could not parse content as JSON, TOML, or YAML.")


def _parse_by_extension(path: Path, b: bytes) -> Mapping[str, Any]:
    ext = path.suffix.lower()
    if ext == ".json":
        return _parse_json_bytes(b)
    if ext == ".toml":
        if _TOML_LOADER is None:
            # Honor the requirement: do not "register" TOML if unavailable.
            raise ConversionError("TOML file given but no TOML parser is available.")
        return _parse_toml_bytes(b)
    if ext in (".yaml", ".yml"):
        if not _HAS_YAML:
            raise ConversionError("YAML file given but pyyaml is not installed.")
        return _parse_yaml_bytes(b)
    # Unknown extension: fall back to sniffing (with available parsers only).
    return _sniff_and_parse(b)


# --- Public registration ------------------------------------------------------


def register_std_config_converters(reg: ConversionRegistry) -> ConversionRegistry:
    """
    Register conversions to load JSON (+optional TOML/YAML) from:
      - pathlib.Path  → Mapping / dict
      - str (path or inline text) → Mapping / dict
      - bytes → Mapping / dict
      - pathlib.Path → bytes
      - str (path or inline text) → bytes

    Optional features:
      - TOML: only if either 'tomllib' (3.11+) or 'toml' is importable.
      - YAML: only if 'pyyaml' is importable.

    Context knobs:
      - fs: optional virtual filesystem mapping {path_str: bytes|str}
      - treat_str_as_path: True|False to force how str is interpreted

    Minimal doctest using an in-memory fs. Each format test is conditional
    on parser availability, so doctests pass regardless of environment:

        >>> from i2.castgraph import ConversionRegistry
        >>> reg = register_std_config_converters(ConversionRegistry())
        >>> fs = {"/a.json": b'{"x": 1}'}
        >>> ctx = {"fs": fs}
        >>> from pathlib import Path
        >>> reg.convert(Path("/a.json"), dict, context=ctx)["x"]
        1
        >>> # TOML path (only if parser available)
        >>> if _TOML_LOADER is not None:
        ...     fs["/b.toml"] = b'x = 2'
        ...     reg.convert(Path("/b.toml"), dict, context=ctx)["x"] == 2
        ... else:
        ...     True
        True
        >>> # YAML path (only if pyyaml available)
        >>> if _HAS_YAML:
        ...     fs["/c.yaml"] = "x: 3"
        ...     reg.convert(Path("/c.yaml"), dict, context=ctx)["x"] == 3
        ... else:
        ...     True
        True
    """

    # pathlib.Path -> bytes
    @reg.register(Path, bytes, cost=0.2)
    def path_to_bytes(p: Path, ctx: Optional[dict]) -> bytes:
        return _read_bytes_from_pathlike(p, ctx)

    # str -> bytes (heuristic path-or-text)
    @reg.register(str, bytes, cost=0.5)
    def str_to_bytes(s: str, ctx: Optional[dict]) -> bytes:
        # If the string looks like an HTTP(S) URL, fetch it directly.
        if isinstance(s, str) and (s.startswith("http://") or s.startswith("https://")):
            try:
                with urllib.request.urlopen(s) as resp:
                    return resp.read()
            except Exception as e:
                # Surface as a ConversionError so callers can react uniformly.
                raise ConversionError(f"Error fetching URL {s}: {e}")
        # Otherwise, preserve the existing heuristic (path vs inline text).
        return _str_maybe_path_to_bytes(s, ctx)

    # bytes -> Mapping (sniff with available parsers only)
    @reg.register(bytes, Mapping, cost=0.6)
    def bytes_to_mapping(b: bytes, ctx: Optional[dict]) -> Mapping[str, Any]:
        return _sniff_and_parse(b)

    # str -> Mapping (via bytes; extension-aware when forced/exists)
    @reg.register(str, Mapping, cost=0.8)
    def str_to_mapping(s: str, ctx: Optional[dict]) -> Mapping[str, Any]:
        b = reg.convert(s, bytes, context=ctx)
        if (ctx and ctx.get("treat_str_as_path") is True) or os.path.exists(s):
            try:
                return _parse_by_extension(Path(s), b)
            except Exception:
                pass
        return reg.convert(b, Mapping, context=ctx)

    # pathlib.Path -> Mapping (extension-aware; lowest cost)
    @reg.register(Path, Mapping, cost=0.3)
    def path_to_mapping(p: Path, ctx: Optional[dict]) -> Mapping[str, Any]:
        b = reg.convert(p, bytes, context=ctx)
        return _parse_by_extension(p, b)

    # Concrete dict targets, for convenience
    @reg.register(bytes, dict, cost=0.61)
    def bytes_to_dict(b: bytes, ctx: Optional[dict]) -> dict:
        return dict(reg.convert(b, Mapping, context=ctx))

    @reg.register(str, dict, cost=0.81)
    def str_to_dict(s: str, ctx: Optional[dict]) -> dict:
        return dict(reg.convert(s, Mapping, context=ctx))

    @reg.register(Path, dict, cost=0.31)
    def path_to_dict(p: Path, ctx: Optional[dict]) -> dict:
        return dict(reg.convert(p, Mapping, context=ctx))

    return reg


from typing import Mapping, Union, Optional, Any, Dict
from pathlib import Path

from i2.castgraph import ConversionRegistry  # your existing registry

# Create a module-level singleton registry and register the adapters once.
_REGISTRY = register_std_config_converters(ConversionRegistry())


def ensure_dict(
    src: Union[str, Mapping[str, Any]],
    *,
    treat_str_as_path: Optional[bool] = None,
    fs: Optional[Mapping[str, Union[bytes, str]]] = None,
) -> Mapping[str, Any]:
    """
    Ensure the src is in `Mapping` form, from filepaths, or bytes/string contents.

    - If `src` is already a mapping, return `src`.
    - If `src` is a `str`, it is interpreted either as a filesystem path or as
      inline content. Disambiguation policy:
        * If `treat_str_as_path` is True, treat it as a path.
        * If False, treat it as inline text.
        * If None (default), prefer `fs` if provided and keyed by `src`; else,
          treat as a real path if it exists; otherwise as inline text.
    - TOML is parsed only if `tomllib` (3.11+) or third-party `toml` is importable.
    - YAML is parsed only if `pyyaml` is importable.
    - JSON is always available via stdlib.

    Parameters
    ----------
    src : str | Mapping
        Path or inline text (`str`), or a `Mapping` (e.g., `dict`).
    treat_str_as_path : bool | None
        Force interpretation of strings. See policy above.
    fs : Mapping[str, bytes|str] | None
        Optional virtual filesystem for tests or in-memory content.

    Returns
    -------
    dict
        A `Mapping` (usually `dict`) representation of the parsed content.

    Raises
    ------
    ConversionError
        If no suitable parser is available for the given content/extension, or
        the content is invalid for all available parsers.

    Examples
    --------
    >>> # Mapping passthrough
    >>> ensure_dict({"a": 1})
    {'a': 1}

    >>> # Inline JSON
    >>> ensure_dict('{"a": 2}')
    {'a': 2}

    >>> # Virtual FS path resolution
    >>> memfs = {"/cfg.json": b'{"a": 3}'}
    >>> ensure_dict("/cfg.json", fs=memfs)
    {'a': 3}

    >>> # Force treating a string as inline text even if a real file exists:
    >>> ensure_dict('{"a": 4}', treat_str_as_path=False)
    {'a': 4}
    """
    if isinstance(src, Mapping):
        return src

    # Only `str` is allowed by the signature, but the registry can also handle
    # `pathlib.Path` and `bytes` if you decide to broaden the API later.
    context = {"fs": fs} if fs is not None else {}
    if treat_str_as_path is not None:
        context["treat_str_as_path"] = bool(treat_str_as_path)

    return _REGISTRY.convert(src, dict, context=context)
