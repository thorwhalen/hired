"""Tests for the Storage v2 layout: filesystem codecs, two-level split, migration.

All persistence is redirected to a temp dir via ``HIRED_DATA_DIR`` so nothing
touches the real data root, and no real candidate data is used.
"""

import json
import os

import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv('HIRED_DATA_DIR', str(tmp_path))
    yield tmp_path


def _all_files(root):
    return sorted(
        os.path.relpath(os.path.join(r, f), root).replace(os.sep, '/')
        for r, _d, fs in os.walk(root)
        for f in fs
    )


# --------------------------------------------------------------------------- #
# Codecs: extensions on the filesystem side, bare keys on the facade
# --------------------------------------------------------------------------- #
def test_json_store_writes_dot_json_with_bare_keys(tmp_path):
    from hired.persistence import json_store

    store = json_store(str(tmp_path / 'facts'))
    store['fact-1'] = {'a': 1}
    store['sub/fact-2'] = {'b': 2}  # nested keys create dirs
    assert sorted(store) == ['fact-1', 'sub/fact-2']  # keys are extension-less
    assert _all_files(tmp_path / 'facts') == ['fact-1.json', 'sub/fact-2.json']
    # files are real JSON on disk
    assert json.loads((tmp_path / 'facts' / 'fact-1.json').read_text()) == {'a': 1}


def test_markdown_store_writes_dot_md_with_bare_keys(tmp_path):
    from hired.persistence import markdown_store

    store = markdown_store(str(tmp_path / 'docs'))
    store['synopsis'] = '# hi'
    assert sorted(store) == ['synopsis']
    assert os.listdir(tmp_path / 'docs') == ['synopsis.md']
    assert (tmp_path / 'docs' / 'synopsis.md').read_text() == '# hi'


def test_bytes_store_keeps_real_filename(tmp_path):
    from hired.persistence import bytes_store

    store = bytes_store(str(tmp_path / 'raw'))
    store['cv.pdf'] = b'%PDF-1.4'
    assert sorted(store) == ['cv.pdf']  # extension IS the domain key here
    assert os.listdir(tmp_path / 'raw') == ['cv.pdf']


# --------------------------------------------------------------------------- #
# Two-level layout on disk
# --------------------------------------------------------------------------- #
def test_two_level_layout_paths(tmp_path):
    from hired.candidate import CandidateKnowledgeBase
    from hired.candidate.base import Fact, FactCategory

    kb = CandidateKnowledgeBase()
    kb.add_fact(Fact(statement='Knows Python', category=FactCategory.SKILL))
    kb.regenerate_synopsis()
    kb.save_upload('cv.pdf', b'%PDF')
    ws = kb.jd('acme', company='Acme')
    ws.save_report('role-1', {'verdict': {'recommendation': 'apply'}})

    files = _all_files(tmp_path / 'users' / 'me')
    # user-level info + raw
    assert any(f.startswith('user/info/facts/') and f.endswith('.json') for f in files)
    assert 'user/info/synopsis.md' in files
    assert 'user/raw/cv.pdf' in files
    # engagement-level
    assert 'jds/acme/reports/role-1.json' in files
    assert 'jds/acme/meta.json' in files


# --------------------------------------------------------------------------- #
# Migration from legacy flat layout
# --------------------------------------------------------------------------- #
def _make_legacy(base):
    """Build a v1 flat layout (extension-less files) under ``base``."""
    def w(rel, obj):
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w') as f:
            json.dump(obj, f) if isinstance(obj, (dict, list)) else f.write(obj)

    w('facts/fact-1', {'statement': 'x'})
    w('qa/qa-1', {'question': 'q', 'answer': 'a'})
    w('synopsis/synopsis.md', '# synopsis')
    os.makedirs(os.path.join(base, 'uploads'), exist_ok=True)
    with open(os.path.join(base, 'uploads', 'cv.pdf'), 'wb') as f:
        f.write(b'%PDF')
    w('reports/acme-role-1', {'verdict': {'recommendation': 'apply'}})
    w('company/acme', {'summary': 's'})
    w('interview_prep/acme--kyc', {'body': 'b'})
    w('report_history/acme-role-1/2026-01-01T00-00-00', {'verdict': {'recommendation': 'stretch'}})


def test_migration_moves_and_extensions_and_grouping(tmp_path):
    from hired.persistence import migrate_user_to_v2

    base = tmp_path / 'users' / 'me'
    _make_legacy(str(base))

    plan = migrate_user_to_v2('me')
    assert plan  # something was moved

    files = _all_files(base)
    # user-level
    assert 'user/info/facts/fact-1.json' in files
    assert 'user/info/qa/qa-1.json' in files
    assert 'user/info/synopsis.md' in files
    assert 'user/raw/cv.pdf' in files
    # engagement-level, all grouped under the single 'acme' company workspace
    assert 'jds/acme/reports/acme-role-1.json' in files
    assert 'jds/acme/company/acme.json' in files
    assert 'jds/acme/interview_prep/acme--kyc.json' in files
    assert 'jds/acme/report_history/acme-role-1/2026-01-01T00-00-00.json' in files
    assert 'jds/acme/meta.json' in files
    # legacy dirs are gone
    for legacy in ('facts', 'qa', 'synopsis', 'uploads', 'reports', 'company'):
        assert not (base / legacy).exists()


def test_migration_is_idempotent(tmp_path):
    from hired.persistence import migrate_user_to_v2

    base = tmp_path / 'users' / 'me'
    _make_legacy(str(base))
    migrate_user_to_v2('me')
    assert migrate_user_to_v2('me') == []  # second run is a no-op


def test_interrupted_migration_resumes_without_data_loss(tmp_path, monkeypatch):
    from hired.persistence import is_legacy_layout, migrate_user_to_v2
    from hired.persistence import migrate as migrate_mod

    base = tmp_path / 'users' / 'me'
    _make_legacy(str(base))

    # Make the 3rd move blow up mid-migration (simulates crash / disk-full).
    real_move = migrate_mod.shutil.move
    calls = {'n': 0}

    def flaky_move(src, dst):
        calls['n'] += 1
        if calls['n'] == 3:
            raise OSError('simulated interruption')
        return real_move(src, dst)

    monkeypatch.setattr(migrate_mod.shutil, 'move', flaky_move)
    with pytest.raises(OSError):
        migrate_user_to_v2('me')

    # Still detected as legacy (NOT silently flipped to "already v2") -> resumable.
    assert is_legacy_layout('me') is True

    # Resume with the real move: completes, and the engagement data is recovered.
    monkeypatch.setattr(migrate_mod.shutil, 'move', real_move)
    migrate_user_to_v2('me')
    assert is_legacy_layout('me') is False
    files = _all_files(base)
    assert 'jds/acme/reports/acme-role-1.json' in files
    assert 'jds/acme/company/acme.json' in files
    assert 'user/info/facts/fact-1.json' in files


def test_kb_auto_migrates_legacy_on_init(tmp_path):
    from hired.candidate import CandidateKnowledgeBase

    base = tmp_path / 'users' / 'me'
    _make_legacy(str(base))

    kb = CandidateKnowledgeBase()  # ensure_v2 fires in __init__
    # facts readable through the new layout
    assert 'fact-1' in list(kb._store.facts)
    # the engagement is discoverable, reports readable through the workspace
    assert 'acme' in kb.jds()
    assert kb.jd('acme').get_report('acme-role-1')['verdict']['recommendation'] == 'apply'
    assert kb.synopsis == '# synopsis'
