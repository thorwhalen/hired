"""The generated resume models stay readable by a type checker (hired#35).

``refresh_resume_schema`` regenerates ``resumejson_pydantic_models.py``; its
post-processing rewrites ``constr(...)`` as ``Annotated[str, StringConstraints(...)]``
and declares ``model_config`` as ``ClassVar[ConfigDict]``, so a refresh keeps both.
"""

from pathlib import Path

import pytest

from hired.util import _fix_resume_model_typing, _rewrite_constr

GENERATED = '''from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, constr


class Iso8601(RootModel[constr(pattern=r"^(a|b)$")]):
    root: constr(pattern=r"^(a|b)$") = Field(..., description="e.g. a")


class Item(BaseModel):
    model_config = ConfigDict(extra="allow")
    when: Iso8601 | None = None
'''


def test_constr_becomes_annotated_string_constraints():
    out = _fix_resume_model_typing(GENERATED)
    assert "constr" not in out
    assert out.count('Annotated[str, StringConstraints(pattern=r"^(a|b)$")]') == 2
    assert "from typing import Annotated, ClassVar, List, Optional" in out
    assert "StringConstraints" in out.split("from pydantic import ", 1)[1].splitlines()[0]
    assert "    model_config: ClassVar[ConfigDict] = ConfigDict(" in out


def test_the_fix_is_idempotent():
    once = _fix_resume_model_typing(GENERATED)
    assert _fix_resume_model_typing(once) == once


def test_validation_is_unchanged(tmp_path):
    import importlib.util
    import sys

    def load(code, name):
        path = tmp_path / f"{name}.py"
        path.write_text(code)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    before = load(GENERATED, "gen_before")
    after = load(_fix_resume_model_typing(GENERATED), "gen_after")
    assert before.Item.model_json_schema() == after.Item.model_json_schema()
    for value, ok in (("a", True), ("b", True), ("c", False)):
        for mod in (before, after):
            if ok:
                mod.Iso8601(value)
            else:
                with pytest.raises(Exception):
                    mod.Iso8601(value)


def test_a_paren_inside_the_pattern_is_not_the_calls_end():
    code = 'x: constr(pattern=r"^(\\\\)(a)$", min_length=1)'
    assert _rewrite_constr(code) == (
        'x: Annotated[str, StringConstraints(pattern=r"^(\\\\)(a)$", min_length=1)]'
    )


def test_the_shipped_models_carry_no_constr():
    import hired

    text = (Path(hired.__file__).parent / "resumejson_pydantic_models.py").read_text()
    assert "constr(" not in text and "StringConstraints(" in text


def test_non_ascii_before_the_call_on_the_same_line():
    """ast columns are UTF-8 byte offsets; the splice must count characters."""
    code = 'café: constr(pattern="x") = "Straße"'
    assert _rewrite_constr(code) == (
        'café: Annotated[str, StringConstraints(pattern="x")] = "Straße"'
    )


def test_a_parenthesised_typing_import_stays_valid_python():
    import ast

    code = GENERATED.replace(
        "from typing import List, Optional", "from typing import (\n    List,\n    Optional,\n)"
    )
    out = _fix_resume_model_typing(code)
    ast.parse(out)
    assert "from typing import Annotated, ClassVar\nfrom typing import (" in out
    assert _fix_resume_model_typing(out) == out
