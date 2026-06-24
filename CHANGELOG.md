# Changelog

All notable changes to this project are documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/);
each section corresponds to a git version tag (which is also the release
published to PyPI). Entries are commit subjects and PR titles, verbatim.

## [0.0.18] - 2026-06-24

- chore(pypi): polish project metadata (SPDX license, classifiers, keywords, urls) ([#29](https://github.com/thorwhalen/hired/pull/29))

## [0.0.17] - 2026-06-23

- chore(skills): migrate skills to top-level skills/ with .claude/skills symlinks ([#28](https://github.com/thorwhalen/hired/pull/28))

## [0.0.16] - 2026-06-23

- Refresh subsystem: soft/hard refresh of candidate info ([#22](https://github.com/thorwhalen/hired/pull/22), closes [#17](https://github.com/thorwhalen/hired/pull/17)) ([#26](https://github.com/thorwhalen/hired/pull/26))

## [0.0.15] - 2026-06-23

### Fixed

- fix(test): make add_source path test newline-stable on Windows; store text with \n ([#25](https://github.com/thorwhalen/hired/pull/25))

## [0.0.14] - 2026-06-23

### Added

- feat(candidate): cross-session knowledge — raw sources, Q&A→facts, topic dossiers ([#21](https://github.com/thorwhalen/hired/pull/21)) ([#24](https://github.com/thorwhalen/hired/pull/24))

## [0.0.13] - 2026-06-23

- Storage v2 foundation: filesystem codecs + two-level layout + facade split + migration ([#20](https://github.com/thorwhalen/hired/pull/20)) ([#23](https://github.com/thorwhalen/hired/pull/23))

## [0.0.12] - 2026-06-23

- Candidate Knowledge Base + JD Alignment subsystem (+ interview prep) ([#18](https://github.com/thorwhalen/hired/pull/18))

## [0.0.11] - 2026-06-12

- test: use patch.object in test_jobspy_not_available
- deps: pydantic[email] — EmailStr in the resume schema needs email-validator
- Build out hired + migrate to wads uv-based CI
- Incorporate changes from claude/add-search-hired-01HgCwVfvJyvQZDeoonz6HMz
- 0.0.10:
- Add search functionality to hired ([#3](https://github.com/thorwhalen/hired/pull/3))
- Modernizing python style
- 0.0.9:
- 0.0.4:
- test: Add unit tests for Plan and PlanStep validation and execution
- Implement multiple code changes for improved functionality and performance
- added a bunch of (doubtful) css and html templates
- Enhance resume rendering functionality and add new themes
- Add new entry templates for classic and markdown themes
- Refactor resume content handling to use ResumeSchemaExtended
- Add JSON Resume Schema and Pydantic models
- Refactor code structure for improved readability and maintainability
- Refactor code structure for improved readability and maintainability
- 0.0.3:
- 0.0.2:
- Initial commit

### Added

- feat: Finally, an AI Agent
- feat: Now fetching and caching the official resume json schema, and making pydantic models from it. Not completely finished transitioning though. Skipping two tests.
- feat: Update GitHub Actions permissions for GitHub Pages publishing
- feat: Add CI workflow for validation and publishing

### Changed

- refactor: Enhance session management and add MutableMapping support in SessionStore
- refactor: Improve readability of candidate names list in ThemeRegistry
- refactor: Delay renderer registration to avoid side effects and enhance lazy loading feat: Enhance HTML rendering to support custom templates and CSS feat: Add normalization and validation for resume content with optional strict checks test: Implement test for custom template rendering in HTMLRenderer
- refactor: Improve readability of conditionals in sanitize_rendercv_data and resumejson_to_rendercv functions

### Fixed

- fix: Update install_requires and testing dependencies in setup.cfg

### Docs

- docs: Update README and demo notebook to reflect new resume agent features and usage examples
- docs: Add comprehensive test notes and triage guidance for test files
