# hired.content

Content generation logic and AI agent implementations.

Implement:

- DefaultAIAgent: Basic implementation using local LLM or API
- content source factories for common formats
- content extraction and filtering utilities

### Classes

| [`DefaultAIAgent`](#hired.content.DefaultAIAgent)(\*[, model, api_key])         | Default AI agent implementation (mock).                          |
|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`DictContentSource`](#hired.content.DictContentSource)(data)                      | Implements ContentSource for dictionary data.                    |
| [`FileContentSource`](#hired.content.FileContentSource)(path)                      | Implements ContentSource for file-based data.                    |
| [`LLMResumeAgent`](#hired.content.LLMResumeAgent)(\*[, model, client, api_key]) | AI agent that tailors a candidate's profile to a job via an LLM. |

### *class* hired.content.DefaultAIAgent(, model='default', api_key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Default AI agent implementation (mock).

### *class* hired.content.DictContentSource(data)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Implements ContentSource for dictionary data.

### *class* hired.content.FileContentSource(path)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Implements ContentSource for file-based data.

### *class* hired.content.LLMResumeAgent(, model='gpt-4o-mini', client=None, api_key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

AI agent that tailors a candidate’s profile to a job via an LLM.

Opt-in alternative to [`DefaultAIAgent`](#hired.content.DefaultAIAgent) (which is a pass-through). It
is **dependency-injected and lazy**: `openai` is imported only when an agent
is used *without* an injected `client`, so importing `hired` never
requires `openai`, and no API key is read at construction time. Inject a
`client` (anything exposing the OpenAI-style
`chat.completions.create`) to test without network or secrets.

```pycon
>>> class _FakeClient:
...     class chat:
...         class completions:
...             @staticmethod
...             def create(**_):
...                 ...
```
