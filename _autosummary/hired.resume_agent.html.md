# hired.resume_agent

Resume Generation System - Core Architecture

A hybrid LangChain/DSPy system for AI-powered resume creation with manual
and autonomous operation modes.

Architecture follows supervisor-worker pattern with:

- ResumeSession: Stateful conversation manager for manual mode
- ResumeExpertAgent: Autonomous controller using ResumeSession as a tool
- Specialized worker agents: expansion, distillation, matching, search

### Classes

| [`ConversationMemory`](#hired.resume_agent.ConversationMemory)(\*[, max_recent_turns])         | Manages conversation history with tiered memory strategy.                   |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`DistillationAgent`](#hired.resume_agent.DistillationAgent)(\*[, llm_config])                | Distills verbose text into concise, impactful statements.                   |
| [`ExpansionAgent`](#hired.resume_agent.ExpansionAgent)(\*[, llm_config])                   | Expands brief bullet points into detailed achievement descriptions.         |
| [`LLMConfig`](#hired.resume_agent.LLMConfig)(model[, temperature, max_tokens, ...])   | Configuration for LLM model selection and parameters.                       |
| [`LLMProvider`](#hired.resume_agent.LLMProvider)(\*args, \*\*kwargs)                    | Protocol for LLM execution.                                                 |
| [`MatchingAgent`](#hired.resume_agent.MatchingAgent)(\*[, llm_config])                    | Performs semantic matching between candidate info and job requirements.     |
| [`ModelRegistry`](#hired.resume_agent.ModelRegistry)(supervisor, workers[, ...])          | Registry for different model configurations by role.                        |
| [`OperationMode`](#hired.resume_agent.OperationMode)(\*values)                            | Session operation mode.                                                     |
| [`Plan`](#hired.resume_agent.Plan)(steps, rationale[, created_at])               | Structured execution plan for resume creation.                              |
| [`PlanStep`](#hired.resume_agent.PlanStep)(id, action, description[, params, ...])   | A single step in an execution plan.                                         |
| [`ResumeExpertAgent`](#hired.resume_agent.ResumeExpertAgent)(\*[, llm_config, ...])           | Autonomous agent that uses ResumeSession as a tool.                         |
| [`ResumeSession`](#hired.resume_agent.ResumeSession)(job_info, candidate_info, \*[, ...]) | Stateful conversation session for resume creation.                          |
| [`SearchAgent`](#hired.resume_agent.SearchAgent)(\*[, llm_config])                      | Performs web searches to expand context about companies, technologies, etc. |
| [`SessionSnapshot`](#hired.resume_agent.SessionSnapshot)(turn_count, data, mode[, ...])     | Immutable snapshot of session state at a point in time.                     |
| [`SessionState`](#hired.resume_agent.SessionState)()                                     | Structured state for resume creation session.                               |
| [`SessionStore`](#hired.resume_agent.SessionStore)(\*[, data_dir])                       | Manages automatic persistence of resume sessions.                           |
| [`Turn`](#hired.resume_agent.Turn)(role, content[, timestamp, metadata])         | A single conversation turn.                                                 |

### *class* hired.resume_agent.ConversationMemory(, max_recent_turns=10)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Manages conversation history with tiered memory strategy.

Minimal docstring: Stores and retrieves conversation turns with summarization.

#### add_turn(role, content, \*\*metadata)

Add a conversation turn.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### get_all_turns()

Get all conversation turns.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Turn`](#hired.resume_agent.Turn)]

#### get_context_for_prompt()

Generate context for LLM prompt with recent history.

Yields dicts with ‘role’ and ‘content’ for LLM consumption.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### get_recent_turns(n=None)

Get the n most recent turns (defaults to max_recent_turns).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Turn`](#hired.resume_agent.Turn)]

#### summarize_old_turns()

Placeholder for summarization of old history.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.resume_agent.DistillationAgent(, llm_config=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Distills verbose text into concise, impactful statements.

Uses DSPy-optimized prompts with metrics for conciseness and clarity.

#### distill(verbose_text, , max_words=None, preserve_metrics=True)

Distill verbose text into concise statement.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> config = LLMConfig(model="gpt-4")
>>> agent = DistillationAgent(llm_config=config)
>>> agent.llm_config.model
'gpt-4'
```

### *class* hired.resume_agent.ExpansionAgent(, llm_config=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Expands brief bullet points into detailed achievement descriptions.

Uses DSPy-optimized prompts for consistent, high-quality expansions.

#### expand(brief_text, context, , target_length='detailed')

Expand brief text into detailed description.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> config = LLMConfig(model="gpt-4")
>>> agent = ExpansionAgent(llm_config=config)
>>> agent.llm_config.model
'gpt-4'
```

### *class* hired.resume_agent.LLMConfig(model, temperature=0.7, max_tokens=None, top_p=1.0, provider='openai', api_key=None, base_url=None, extra_params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for LLM model selection and parameters.

```pycon
>>> config = LLMConfig(model="gpt-4", temperature=0.7)
>>> config.model
'gpt-4'
```

#### to_dspy_lm()

Convert to DSPy LM instance.

#### to_langchain_kwargs()

Convert to LangChain model kwargs.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *class* hired.resume_agent.LLMProvider(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Protocol for LLM execution.

#### chat(messages, \*\*kwargs)

Generate response for chat messages.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### complete(prompt, \*\*kwargs)

Generate completion for prompt.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* hired.resume_agent.MatchingAgent(, llm_config=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Performs semantic matching between candidate info and job requirements.

Uses embedding-based similarity and cross-encoder reranking.

#### find_matches(candidate_text, job_requirements)

Find semantic matches between candidate experience and job needs.

Yields dicts with ‘candidate_snippet’, ‘job_requirement’, ‘score’.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### *class* hired.resume_agent.ModelRegistry(supervisor, workers, expansion=None, distillation=None, matching=None, search=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Registry for different model configurations by role.

Enables cost optimization by using different models for different tasks.

```pycon
>>> registry = ModelRegistry(
...     supervisor=LLMConfig("gpt-4"),
...     workers=LLMConfig("gpt-3.5-turbo")
... )
>>> registry.supervisor.model
'gpt-4'
```

#### *classmethod* default()

Create default registry with sensible model choices.

* **Return type:**
  [`ModelRegistry`](#hired.resume_agent.ModelRegistry)

#### *classmethod* fast()

Create registry optimized for speed/cost.

* **Return type:**
  [`ModelRegistry`](#hired.resume_agent.ModelRegistry)

#### get_config(role)

Get model config for specific role.

Falls back to workers config if role-specific config not set.

* **Return type:**
  [`LLMConfig`](#hired.resume_agent.LLMConfig)

#### *classmethod* quality()

Create registry optimized for quality.

* **Return type:**
  [`ModelRegistry`](#hired.resume_agent.ModelRegistry)

### *class* hired.resume_agent.OperationMode(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Session operation mode.

### *class* hired.resume_agent.Plan(steps, rationale, created_at=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Structured execution plan for resume creation.

#### get_executable_steps(completed_steps)

Get steps that can currently be executed.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`PlanStep`](#hired.resume_agent.PlanStep)]

#### to_markdown()

Convert plan to human-readable markdown.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### validate()

Validate plan structure and dependencies.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### *class* hired.resume_agent.PlanStep(id, action, description, params=<factory>, dependencies=<factory>, estimated_tokens=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single step in an execution plan.

#### can_execute(completed_steps)

Check if all dependencies are satisfied.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### *class* hired.resume_agent.ResumeExpertAgent(, llm_config=None, model_registry=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Autonomous agent that uses ResumeSession as a tool.

Operates in auto mode, making decisions about expansion, distillation,
search, and generation operations to produce complete resumes.

```pycon
>>> config = LLMConfig(model="gpt-4")
>>> agent = ResumeExpertAgent(llm_config=config)
>>> agent.llm_config.model
'gpt-4'
```

#### create_resume(session, , mode='standard', max_iterations=5)

Autonomously create resume using session as tool.

Operates in plan-and-execute pattern:

1. Analyze job and candidate info
2. Plan resume creation strategy
3. Execute operations (expand, distill, match)
4. Generate resume
5. Critique and refine

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### execute_plan(session, plan, , interactive=False, approval_callback=None)

Execute a plan step by step.

* **Parameters:**
  * **session** ([`ResumeSession`](#hired.resume_agent.ResumeSession)) – Resume session to operate on
  * **plan** ([`Plan`](#hired.resume_agent.Plan)) – Plan to execute
  * **interactive** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, pause after each step for approval
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  Dict with execution results and final outputs

#### propose_plan(session, , mode='standard')

Generate execution plan for resume creation.

Returns structured Plan object that can be edited before execution.

* **Return type:**
  [`Plan`](#hired.resume_agent.Plan)

#### revise_plan(plan, instruction)

Revise plan based on natural language instruction.

Uses LLM to interpret instruction and modify plan accordingly.

* **Return type:**
  [`Plan`](#hired.resume_agent.Plan)

### *class* hired.resume_agent.ResumeSession(job_info, candidate_info, , mode=OperationMode.MANUAL, system_prompt=None, max_recent_turns=10, llm_config=None, model_registry=None, auto_persist=True, data_dir=None, name=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Stateful conversation session for resume creation.

Provides manual chat interface where users give natural language
instructions to perform expansion, distillation, search, and generation
operations. Maintains conversation history and structured state.

```pycon
>>> config = LLMConfig("gpt-4")
>>> session = ResumeSession(
...     job_info="Senior ML Engineer at TechCo",
...     candidate_info="5 years Python, ML experience",
...     llm_config=config
... )
>>> session.llm_config.model
'gpt-4'
```

#### chat(user_message)

Process user instruction and return assistant response.

This is the main interface for manual mode operation.
Automatically persists session after each turn if auto_persist enabled.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *property* history *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[Turn](#hired.resume_agent.Turn)]*

Get all conversation turns.

#### *classmethod* list_persisted(data_dir=None)

List all persisted sessions.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

```pycon
>>> for session_info in ResumeSession.list_persisted():
...     print(session_info['session_id'])
```

#### *classmethod* load(session_id, , data_dir=None, llm_config=None)

Load session from persistent storage.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ResumeSession`](#hired.resume_agent.ResumeSession)]

```pycon
>>> session = ResumeSession.load("abc123def456")
>>> session.session_id if session else None
'abc123def456'
```

#### *property* metadata *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

Return a small metadata dict for quick inspection.

Includes: session_id, name, created_at (iso), n_turns, mode, model

#### save(data_dir=None)

Manually save session to persistent storage.

Returns path to saved session file.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

#### *property* snapshots *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[SessionSnapshot](#hired.resume_agent.SessionSnapshot)]*

Get all session snapshots.

#### *property* state *: [SessionState](#hired.resume_agent.SessionState)*

Get current session state.

#### switch_mode(mode)

Switch between manual and auto operation modes.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.resume_agent.SearchAgent(, llm_config=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Performs web searches to expand context about companies, technologies, etc.

Integrates with search APIs to gather relevant information.

#### search(query, , result_count=5)

Search web for relevant information.

Yields dicts with ‘title’, ‘snippet’, ‘url’.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### *class* hired.resume_agent.SessionSnapshot(turn_count, data, mode, timestamp=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Immutable snapshot of session state at a point in time.

```pycon
>>> snapshot = SessionSnapshot(turn_count=5, data={'skills': ['Python']})
>>> snapshot.turn_count
5
```

### *class* hired.resume_agent.SessionState

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Structured state for resume creation session.

Stores extracted entities, analysis results, and work-in-progress content.

#### get(key, default=None)

Get state value with default.

#### snapshot()

Create immutable snapshot of current state.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

#### update(updates)

Update state with new information.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.resume_agent.SessionStore(, data_dir=None)

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

Manages automatic persistence of resume sessions.

Sessions are saved after each chat turn to enable recovery and history.

```pycon
>>> store = SessionStore()
>>> store.data_dir.name
'resume_agent_sessions'
```

#### add(session)

Alias for save_session to behave like a set.add(session).

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

#### delete_session(session_id)

Delete session from persistent storage.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### list_sessions()

List all persisted sessions.

Yields session metadata dicts.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### load_session(session_id, , llm_config=None)

Load session from persistent storage.

Returns None if session not found.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ResumeSession`](#hired.resume_agent.ResumeSession)]

#### save_session(session)

Save session to persistent storage.

Returns path to saved session file.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### *class* hired.resume_agent.Turn(role, content, timestamp=<factory>, metadata=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single conversation turn.

```pycon
>>> turn = Turn(role="user", content="Make a resume")
>>> turn.role
'user'
```
