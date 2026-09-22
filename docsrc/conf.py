"""Sphinx configuration for the hired documentation site.

Every setting comes from ``[tool.epythet]`` in ``pyproject.toml``, by way of the
settings epythet generates -- except the one override below. This file is
deliberately *not* epythet's two-line shim: epythet regenerates a ``conf.py``
that carries its marker line, so a committed override has to be spelled as an
ordinary import (``epythet.scaffold.write_generated_file`` leaves a ``conf.py``
without the marker alone).
"""

from epythet import sphinx_conf as _epythet_generated

globals().update(
    {_k: _v for _k, _v in vars(_epythet_generated).items() if not _k.startswith("_")}
)

# -- overrides ---------------------------------------------------------------

# Name the published Markdown twin of a page by *appending* ".md" to the HTML
# file name ("<page>.html.md"), never by replacing the ".html" suffix.
#
# sphinx_llm's default ("auto") publishes both spellings, and for a module whose
# last name component is `html` the two collide: under the append spelling the
# twin of `hired.renderers` is `hired.renderers.html.md`, and under the replace
# spelling the twin of `hired.renderers.html` is also `hired.renderers.html.md`.
# The build then aborts with an ExtensionError. "append" drops the replace
# spelling, which is the redundant one: epythet's own
# `<link rel="alternate" type="text/markdown">` tags point at "<page>.html.md".
#
# The alternative -- renaming the `hired.renderers.html` module -- would break
# every importer of a public name, so it is not on the table.
llms_txt_suffix_mode = "append"
