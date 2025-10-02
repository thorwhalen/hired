"""
Resume Generation System - Core Architecture

A hybrid LangChain/DSPy system for AI-powered resume creation with manual
and autonomous operation modes.

Architecture follows supervisor-worker pattern with:
- ResumeSession: Stateful conversation manager for manual mode
- ResumeExpertAgent: Autonomous controller using ResumeSession as a tool
- Specialized worker agents: expansion, distillation, matching, search
"""

from dataclasses import dataclass, field, asdict
from typing import (
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Any,
    MutableMapping,
    Callable,
    List,
    Set,
)
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import hashlib
import pickle
import copy


APP_DATA_PATH = Path.home() / ".cache" / "hired"
SESSION_DATA_PATH = APP_DATA_PATH / "resume_agent_sessions"

# ============================================================================
# Base Types and Protocols
# ============================================================================


class OperationMode(Enum):
    """Session operation mode."""

    MANUAL = "manual"
    AUTO = "auto"


@dataclass
class LLMConfig:
    """
    Configuration for LLM model selection and parameters.

    >>> config = LLMConfig(model="gpt-4", temperature=0.7)
    >>> config.model
    'gpt-4'
    """

    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    provider: str = "openai"  # "openai", "anthropic", "together", etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: dict = field(default_factory=dict)

    def to_langchain_kwargs(self) -> dict:
        """Convert to LangChain model kwargs."""
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        kwargs.update(self.extra_params)
        return kwargs

    def to_dspy_lm(self):
        """Convert to DSPy LM instance."""
        # TODO: Import and instantiate appropriate DSPy LM
        # import dspy
        # return dspy.LM(model=self.model, **self.to_langchain_kwargs())
        pass


class LLMProvider(Protocol):
    """Protocol for LLM execution."""

    def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion for prompt."""
        ...

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Generate response for chat messages."""
        ...


@dataclass
class ModelRegistry:
    """
    Registry for different model configurations by role.

    Enables cost optimization by using different models for different tasks.

    >>> registry = ModelRegistry(
    ...     supervisor=LLMConfig("gpt-4"),
    ...     workers=LLMConfig("gpt-3.5-turbo")
    ... )
    >>> registry.supervisor.model
    'gpt-4'
    """

    supervisor: LLMConfig
    workers: LLMConfig
    expansion: Optional[LLMConfig] = None
    distillation: Optional[LLMConfig] = None
    matching: Optional[LLMConfig] = None
    search: Optional[LLMConfig] = None

    def get_config(self, role: str) -> LLMConfig:
        """
        Get model config for specific role.

        Falls back to workers config if role-specific config not set.
        """
        config = getattr(self, role, None)
        return config or self.workers

    @classmethod
    def default(cls) -> 'ModelRegistry':
        """Create default registry with sensible model choices."""
        return cls(
            supervisor=LLMConfig(model="gpt-4", temperature=0.3),
            workers=LLMConfig(model="gpt-3.5-turbo", temperature=0.7),
        )

    @classmethod
    def fast(cls) -> 'ModelRegistry':
        """Create registry optimized for speed/cost."""
        config = LLMConfig(model="gpt-3.5-turbo", temperature=0.7)
        return cls(supervisor=config, workers=config)

    @classmethod
    def quality(cls) -> 'ModelRegistry':
        """Create registry optimized for quality."""
        config = LLMConfig(model="gpt-4", temperature=0.3)
        return cls(supervisor=config, workers=config)


@dataclass
class Turn:
    """A single conversation turn.

    >>> turn = Turn(role="user", content="Make a resume")
    >>> turn.role
    'user'
    """

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class SessionSnapshot:
    """Immutable snapshot of session state at a point in time.

    >>> snapshot = SessionSnapshot(turn_count=5, data={'skills': ['Python']})
    >>> snapshot.turn_count
    5
    """

    turn_count: int
    data: dict
    mode: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PlanStep:
    """A single step in an execution plan."""

    id: str
    action: str  # e.g., "analyze_job", "expand_achievements"
    description: str  # Human-readable description
    params: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)  # IDs of prerequisite steps
    estimated_tokens: Optional[int] = None

    def can_execute(self, completed_steps: set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep_id in completed_steps for dep_id in self.dependencies)


@dataclass
class Plan:
    """Structured execution plan for resume creation."""

    steps: list[PlanStep]
    rationale: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """Convert plan to human-readable markdown."""
        lines = [f"# Resume Creation Plan\n", f"**Rationale:** {self.rationale}\n"]
        for i, step in enumerate(self.steps, 1):
            deps = (
                f" (depends on: {', '.join(step.dependencies)})"
                if step.dependencies
                else ""
            )
            lines.append(f"{i}. **[{step.action}]** {step.description}{deps}")
            if step.params:
                lines.append(f"   - Params: {step.params}")
        return "\n".join(lines)

    def validate(self) -> list[str]:
        """Validate plan structure and dependencies."""
        errors = []
        step_ids = {step.id for step in self.steps}

        # Check for missing dependencies and self-dependency
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    errors.append(
                        f"Step '{step.id}' depends on non-existent step '{dep_id}'"
                    )
            if step.id in step.dependencies:
                errors.append(f"Step '{step.id}' depends on itself")

        # Detect cycles in dependency graph using DFS
        graph = {step.id: list(step.dependencies) for step in self.steps}

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(node: str) -> bool:
            if node in visited:
                return False
            if node in visiting:
                return True  # cycle found

            visiting.add(node)
            for nbr in graph.get(node, []):
                if dfs(nbr):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for node in graph:
            if dfs(node):
                errors.append(f"Dependency cycle detected involving step '{node}'")
                break

        return errors

    def get_executable_steps(self, completed_steps: set[str]) -> list[PlanStep]:
        """Get steps that can currently be executed."""
        return [
            step
            for step in self.steps
            if step.id not in completed_steps and step.can_execute(completed_steps)
        ]


# ============================================================================
# Session Persistence
# ============================================================================


class SessionStore(MutableMapping):
    """
    Manages automatic persistence of resume sessions.

    Sessions are saved after each chat turn to enable recovery and history.

    >>> store = SessionStore()
    >>> store.data_dir
    PosixPath('~/.cache/hired/resume_agent_sessions')
    """

    def __init__(self, *, data_dir: Optional[Path] = None):
        self.data_dir = self._resolve_data_dir(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_data_dir(data_dir: Optional[Path]) -> Path:
        """Resolve data directory path."""
        if data_dir:
            return Path(data_dir).expanduser()

        # Default: ~/.cache/hired/resume_agent_sessions/
        default = SESSION_DATA_PATH
        return default

    def _generate_session_id(self, job_info: str, candidate_info: str) -> str:
        """Generate unique session ID from inputs."""
        content = f"{job_info}::{candidate_info}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def save_session(self, session: 'ResumeSession') -> Path:
        """
        Save session to persistent storage.

        Returns path to saved session file.
        """
        session_id = session.session_id
        session_file = self.data_dir / f"{session_id}.pkl"

        # Create serializable session data
        session_data = {
            'session_id': session.session_id,
            'job_info': session.job_info,
            'candidate_info': session.candidate_info,
            'mode': session.mode.value,
            'history': [asdict(turn) for turn in session.history],
            'state': session.state.snapshot(),
            'snapshots': [asdict(snap) for snap in session.snapshots],
            'created_at': session.created_at.isoformat(),
            'updated_at': datetime.now().isoformat(),
            'llm_config': asdict(session.llm_config),
            'name': getattr(session, 'name', None),
        }

        # Save with pickle for full object support
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)

        # Also save JSON version for human readability
        json_file = self.data_dir / f"{session_id}.json"
        with open(json_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)

        return session_file

    def load_session(
        self, session_id: str, *, llm_config: Optional[LLMConfig] = None
    ) -> Optional['ResumeSession']:
        """
        Load session from persistent storage.

        Returns None if session not found.
        """
        session_file = self.data_dir / f"{session_id}.pkl"

        if not session_file.exists():
            return None

        with open(session_file, 'rb') as f:
            session_data = pickle.load(f)

        # Reconstruct session
        config = llm_config or LLMConfig(**session_data['llm_config'])

        session = ResumeSession(
            job_info=session_data['job_info'],
            candidate_info=session_data['candidate_info'],
            llm_config=config,
            mode=OperationMode(session_data['mode']),
            auto_persist=False,  # Prevent re-persisting during load
            name=session_data.get('name'),
        )

        # Restore state
        session.session_id = session_data['session_id']
        session.created_at = datetime.fromisoformat(session_data['created_at'])
        session._state._data = session_data['state']

        # Restore history
        session._memory._turns = [
            Turn(**turn_data) for turn_data in session_data['history']
        ]

        # Restore optional name
        session.name = session_data.get('name')

        return session

    def list_sessions(self) -> Iterable[dict]:
        """
        List all persisted sessions.

        Yields session metadata dicts.
        """
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    yield {
                        'session_id': data['session_id'],
                        'created_at': data['created_at'],
                        'updated_at': data['updated_at'],
                        'turn_count': len(data['history']),
                        'mode': data['mode'],
                        'name': data.get('name'),
                    }
            except Exception:
                continue

    def delete_session(self, session_id: str) -> bool:
        """Delete session from persistent storage."""
        pkl_file = self.data_dir / f"{session_id}.pkl"
        json_file = self.data_dir / f"{session_id}.json"

        deleted = False
        if pkl_file.exists():
            pkl_file.unlink()
            deleted = True
        if json_file.exists():
            json_file.unlink()
            deleted = True

        return deleted

    # -----------------------------
    # MutableMapping interface
    # -----------------------------
    def __getitem__(self, key):
        """s[key] or s[(key, llm_config)] -> load_session(key, llm_config=...)

        Accepts either a single session_id string or a tuple of (session_id, llm_config).
        """
        if isinstance(key, tuple):
            session_id, maybe_cfg = key
            if isinstance(maybe_cfg, LLMConfig):
                return self.load_session(session_id, llm_config=maybe_cfg)
            elif isinstance(maybe_cfg, dict):
                return self.load_session(session_id, llm_config=LLMConfig(**maybe_cfg))
            else:
                # Try to pass through whatever it is; load_session will error if invalid
                return self.load_session(session_id, llm_config=maybe_cfg)
        else:
            return self.load_session(key)

    def __setitem__(self, key, value: 'ResumeSession') -> None:
        """s[session_id] = session -> save session, aligning session_id if needed."""
        session_id = key
        if not isinstance(value, ResumeSession):
            raise TypeError("Value must be a ResumeSession instance")

        # If the session_id differs, deepcopy and align the id to avoid mutating caller
        if getattr(value, 'session_id', None) != session_id:
            new_session = copy.deepcopy(value)
            new_session.session_id = session_id
            # Optionally update created_at to now for the new id
            new_session.created_at = getattr(new_session, 'created_at', datetime.now())
            self.save_session(new_session)
        else:
            self.save_session(value)

    def __delitem__(self, key) -> None:
        deleted = self.delete_session(key)
        if not deleted:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        """Iterate over session ids (so list(s) == s.list_sessions())."""
        for info in self.list_sessions():
            yield info['session_id']

    def __len__(self) -> int:
        return sum(1 for _ in self.list_sessions())

    def add(self, session: 'ResumeSession') -> Path:
        """Alias for save_session to behave like a set.add(session)."""
        return self.save_session(session)


# ============================================================================
# Memory and State Management
# ============================================================================


class ConversationMemory:
    """Manages conversation history with tiered memory strategy.

    Minimal docstring: Stores and retrieves conversation turns with summarization.
    """

    def __init__(self, *, max_recent_turns: int = 10):
        self._turns: list[Turn] = []
        self._max_recent_turns = max_recent_turns
        self._summary: Optional[str] = None

    def add_turn(self, role: str, content: str, **metadata) -> None:
        """Add a conversation turn."""
        turn = Turn(role=role, content=content, metadata=metadata)
        self._turns.append(turn)

    def get_recent_turns(self, n: Optional[int] = None) -> list[Turn]:
        """Get the n most recent turns (defaults to max_recent_turns)."""
        n = n or self._max_recent_turns
        return self._turns[-n:]

    def get_all_turns(self) -> list[Turn]:
        """Get all conversation turns."""
        return self._turns.copy()

    def get_context_for_prompt(self) -> Iterable[dict]:
        """
        Generate context for LLM prompt with recent history.

        Yields dicts with 'role' and 'content' for LLM consumption.
        """
        for turn in self.get_recent_turns():
            yield {"role": turn.role, "content": turn.content}

    def summarize_old_turns(self) -> None:
        """Placeholder for summarization of old history."""
        # TODO: Implement summarization using LLM for turns beyond max_recent
        pass


class SessionState:
    """Structured state for resume creation session.

    Stores extracted entities, analysis results, and work-in-progress content.
    """

    def __init__(self):
        self._data: dict = {
            'candidate': {},
            'job': {},
            'extracted_entities': {},
            'expansions': {},
            'distillations': {},
            'drafts': {},
            'searches': {},
        }

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value) -> None:
        self._data[key] = value

    def update(self, updates: dict) -> None:
        """Update state with new information."""
        for key, value in updates.items():
            if key in self._data and isinstance(self._data[key], dict):
                self._data[key].update(value)
            else:
                self._data[key] = value

    def snapshot(self) -> dict:
        """Create immutable snapshot of current state."""
        return json.loads(json.dumps(self._data))  # Deep copy via JSON

    def get(self, key: str, default=None):
        """Get state value with default."""
        return self._data.get(key, default)


# ============================================================================
# Core Session Manager
# ============================================================================


class ResumeSession:
    """
    Stateful conversation session for resume creation.

    Provides manual chat interface where users give natural language
    instructions to perform expansion, distillation, search, and generation
    operations. Maintains conversation history and structured state.

    >>> config = LLMConfig("gpt-4")
    >>> session = ResumeSession(
    ...     job_info="Senior ML Engineer at TechCo",
    ...     candidate_info="5 years Python, ML experience",
    ...     llm_config=config
    ... )
    >>> session.llm_config.model
    'gpt-4'
    """

    def __init__(
        self,
        job_info: str,
        candidate_info: str,
        *,
        mode: OperationMode = OperationMode.MANUAL,
        system_prompt: Optional[str] = None,
        max_recent_turns: int = 10,
        llm_config: Optional[LLMConfig] = None,
        model_registry: Optional[ModelRegistry] = None,
        auto_persist: bool = True,
        data_dir: Optional[Path] = None,
        name: Optional[str] = None,
    ):
        self.job_info = job_info
        self.candidate_info = candidate_info
        self.mode = mode

        # Model configuration - prioritize registry, then config, then default
        if model_registry:
            self.model_registry = model_registry
            self.llm_config = model_registry.supervisor
        elif llm_config:
            self.llm_config = llm_config
            self.model_registry = None
        else:
            # Default: use GPT-4 for supervisor
            self.llm_config = LLMConfig(model="gpt-4", temperature=0.3)
            self.model_registry = None

        self._memory = ConversationMemory(max_recent_turns=max_recent_turns)
        self._state = SessionState()
        self._snapshots: list[SessionSnapshot] = []

        # Session metadata
        self.created_at = datetime.now()
        self.session_id = self._generate_session_id()

        # Persistence
        self.auto_persist = auto_persist
        self._store = SessionStore(data_dir=data_dir) if auto_persist else None

        # Optional human-friendly name for the session
        self.name = name

        # Initialize state with job and candidate info
        self._state['candidate']['raw_info'] = candidate_info
        self._state['job']['raw_info'] = job_info

        # System prompt for resume expert
        self._system_prompt = system_prompt or self._default_system_prompt()

        # Worker agents (initialized with configs from registry if available)
        self._expansion_agent = self._init_expansion_agent()
        self._distillation_agent = self._init_distillation_agent()
        self._matching_agent = self._init_matching_agent()
        self._search_agent = self._init_search_agent()

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        content = (
            f"{self.job_info}::{self.candidate_info}::{datetime.now().isoformat()}"
        )
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def _init_expansion_agent(self) -> 'ExpansionAgent':
        """Initialize expansion agent with appropriate model config."""
        config = (
            self.model_registry.get_config('expansion')
            if self.model_registry
            else self.llm_config
        )
        return ExpansionAgent(llm_config=config)

    def _init_distillation_agent(self) -> 'DistillationAgent':
        """Initialize distillation agent with appropriate model config."""
        config = (
            self.model_registry.get_config('distillation')
            if self.model_registry
            else self.llm_config
        )
        return DistillationAgent(llm_config=config)

    def _init_matching_agent(self) -> 'MatchingAgent':
        """Initialize matching agent with appropriate model config."""
        config = (
            self.model_registry.get_config('matching')
            if self.model_registry
            else self.llm_config
        )
        return MatchingAgent(llm_config=config)

    def _init_search_agent(self) -> 'SearchAgent':
        """Initialize search agent with appropriate model config."""
        config = (
            self.model_registry.get_config('search')
            if self.model_registry
            else self.llm_config
        )
        return SearchAgent(llm_config=config)

    @staticmethod
    def _default_system_prompt() -> str:
        """Default system prompt for resume expert."""
        return """You are an expert resume consultant and career advisor.
        
Your role is to help candidates create compelling, tailored resumes by:
- Analyzing job descriptions to extract key requirements
- Expanding brief bullets into detailed achievement descriptions
- Distilling verbose text into concise, impactful statements
- Matching candidate experience to job requirements
- Researching companies and providing relevant context
- Generating well-structured, ATS-friendly resume content

You have access to specialized tools for expansion, distillation, 
semantic matching, and web search. Use these tools strategically to
produce high-quality results."""

    def chat(self, user_message: str) -> str:
        """
        Process user instruction and return assistant response.

        This is the main interface for manual mode operation.
        Automatically persists session after each turn if auto_persist enabled.
        """
        # Add user message to history
        self._memory.add_turn("user", user_message)

        # Create snapshot before processing
        self._create_snapshot()

        # Route to supervisor agent for processing
        assistant_response = self._process_with_supervisor(user_message)

        # Add assistant response to history
        self._memory.add_turn("assistant", assistant_response)

        # Auto-save session
        if self.auto_persist:
            self.save()

        return assistant_response

    def _process_with_supervisor(self, instruction: str) -> str:
        """
        Process instruction through supervisor agent.

        Supervisor analyzes instruction and routes to appropriate worker agents.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.tools import tool
        except ImportError:
            return self._fallback_processing(instruction)

        # Initialize LLM with session config
        llm = ChatOpenAI(**self.llm_config.to_langchain_kwargs())

        # Define tools for the supervisor
        tools = self._create_supervisor_tools()

        # Create prompt with system instructions and context
        prompt = self._create_supervisor_prompt()

        # Create agent with tools
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )

        # Execute with full context
        context = {
            "input": instruction,
            "job_info": self.job_info,
            "candidate_info": self.candidate_info,
            "conversation_history": self._format_history_for_prompt(),
            "current_state": self._format_state_for_prompt(),
        }

        result = agent_executor.invoke(context)
        return result.get("output", "No response generated")

    def _fallback_processing(self, instruction: str) -> str:
        """
        Fallback processing when LangChain not available.

        Uses direct LLM call without agent framework.
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.llm_config.api_key)

            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "system", "content": f"Job Info:\n{self.job_info}"},
                {
                    "role": "system",
                    "content": f"Candidate Info:\n{self.candidate_info}",
                },
            ]

            # Add conversation history
            for turn in self._memory.get_recent_turns():
                messages.append({"role": turn.role, "content": turn.content})

            # Add current instruction
            messages.append({"role": "user", "content": instruction})

            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=messages,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {e}\n\nTo use AI agents, install: pip install langchain langchain-openai openai"

    def _create_supervisor_tools(self) -> list:
        """Create tools for supervisor agent."""
        from langchain_core.tools import tool

        @tool
        def expand_bullet_point(brief_text: str, context: str = "") -> str:
            """
            Expand a brief bullet point into a detailed achievement description.
            Use this when the user wants to elaborate on experience or add more detail.

            Args:
                brief_text: The brief text to expand
                context: Additional context about the role or situation
            """
            context_dict = {"additional_context": context}
            result = self._expansion_agent.expand(brief_text, context_dict)
            self._state['expansions'][brief_text] = result
            return result

        @tool
        def distill_text(verbose_text: str, max_words: int = 50) -> str:
            """
            Distill verbose text into a concise, impactful statement.
            Use this when the user wants to make text more concise.

            Args:
                verbose_text: The verbose text to distill
                max_words: Maximum word count for the result
            """
            result = self._distillation_agent.distill(verbose_text, max_words=max_words)
            self._state['distillations'][verbose_text[:50]] = result
            return result

        @tool
        def search_company_info(company_name: str) -> str:
            """
            Search for information about a company.
            Use this when the user wants to know more about a company.

            Args:
                company_name: Name of the company to research
            """
            results = list(self._search_agent.search(company_name, result_count=5))
            summary = "\n\n".join(
                [
                    f"**{r['title']}**\n{r['snippet']}\nSource: {r['url']}"
                    for r in results
                ]
            )
            self._state['searches'][company_name] = summary
            return summary

        @tool
        def find_skill_matches(candidate_section: str, job_requirements: str) -> str:
            """
            Find matches between candidate skills and job requirements.
            Use this to identify aligned experience.

            Args:
                candidate_section: Section of candidate info to analyze
                job_requirements: Job requirements to match against
            """
            matches = list(
                self._matching_agent.find_matches(candidate_section, job_requirements)
            )
            result = "\n".join(
                [
                    f"- Match (score {m['score']:.2f}): '{m['candidate_snippet']}' "
                    f"aligns with '{m['job_requirement']}'"
                    for m in matches
                ]
            )
            self._state['extracted_entities']['matches'] = matches
            return result

        @tool
        def generate_resume_section(
            section_name: str, content_guidance: str = ""
        ) -> str:
            """
            Generate a specific resume section (experience, skills, summary, etc.).
            Use this to create formatted resume content.

            Args:
                section_name: Name of the section (e.g., "experience", "skills", "summary")
                content_guidance: Guidance on what to include
            """
            # Use the LLM to generate the section
            prompt = f"""Generate a {section_name} section for a resume.

Job Description:
{self.job_info}

Candidate Information:
{self.candidate_info}

{f'Additional Guidance: {content_guidance}' if content_guidance else ''}

Accumulated Context:
{self._format_state_for_prompt()}

Generate a professional, ATS-friendly {section_name} section in markdown format."""

            # Direct LLM call for generation
            result = self._generate_with_llm(prompt)
            self._state['drafts'][section_name] = result
            return result

        return [
            expand_bullet_point,
            distill_text,
            search_company_info,
            find_skill_matches,
            generate_resume_section,
        ]

    def _create_supervisor_prompt(self):
        """Create prompt template for supervisor agent."""
        from langchain_core.prompts import ChatPromptTemplate

        return ChatPromptTemplate.from_messages(
            [
                ("system", self._system_prompt),
                ("system", "Job Description:\n{job_info}"),
                ("system", "Candidate Information:\n{candidate_info}"),
                ("system", "Conversation History:\n{conversation_history}"),
                ("system", "Current State:\n{current_state}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

    def _format_history_for_prompt(self) -> str:
        """Format conversation history for prompt."""
        turns = self._memory.get_recent_turns(5)  # Last 5 turns
        if not turns:
            return "No previous conversation."

        formatted = []
        for turn in turns:
            role = "User" if turn.role == "user" else "Assistant"
            formatted.append(f"{role}: {turn.content[:200]}...")
        return "\n".join(formatted)

    def _format_state_for_prompt(self) -> str:
        """Format current state for prompt."""
        state_summary = []

        if self._state['expansions']:
            state_summary.append(
                f"Expansions created: {len(self._state['expansions'])}"
            )
        if self._state['distillations']:
            state_summary.append(
                f"Distillations created: {len(self._state['distillations'])}"
            )
        if self._state['searches']:
            state_summary.append(
                f"Searches performed: {list(self._state['searches'].keys())}"
            )
        if self._state['drafts']:
            state_summary.append(
                f"Draft sections: {list(self._state['drafts'].keys())}"
            )

        return "\n".join(state_summary) if state_summary else "No accumulated work yet."

    def _generate_with_llm(self, prompt: str) -> str:
        """Generate response using configured LLM."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.llm_config.api_key)

            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens or 2000,
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating content: {e}"

    def _create_snapshot(self) -> None:
        """Create and store session snapshot."""
        snapshot = SessionSnapshot(
            turn_count=len(self._memory.get_all_turns()),
            data=self._state.snapshot(),
            mode=self.mode.value,
        )
        self._snapshots.append(snapshot)

    @property
    def history(self) -> list[Turn]:
        """Get all conversation turns."""
        return self._memory.get_all_turns()

    def __iter__(self) -> Iterator[Turn]:
        """Iterate over conversation turns."""
        return iter(self._memory.get_all_turns())

    @property
    def state(self) -> SessionState:
        """Get current session state."""
        return self._state

    @property
    def snapshots(self) -> list[SessionSnapshot]:
        """Get all session snapshots."""
        return self._snapshots.copy()

    @property
    def metadata(self) -> dict:
        """Return a small metadata dict for quick inspection.

        Includes: session_id, name, created_at (iso), n_turns, mode, model
        """
        return {
            'session_id': getattr(self, 'session_id', None),
            'name': getattr(self, 'name', None),
            'created_at': (
                getattr(self, 'created_at', None).isoformat()
                if getattr(self, 'created_at', None)
                else None
            ),
            'n_turns': len(self.history) if self.history is not None else 0,
            'mode': self.mode.value if getattr(self, 'mode', None) else None,
            'model': getattr(self.llm_config, 'model', None),
        }

    def __repr__(self) -> str:
        meta = self.metadata
        name = f"'{meta['name']}' " if meta.get('name') else ""
        return (
            f"<ResumeSession {name}id={meta.get('session_id')} "
            f"model={meta.get('model')} turns={meta.get('n_turns')} "
            f"created={meta.get('created_at')}>"
        )

    def switch_mode(self, mode: OperationMode) -> None:
        """Switch between manual and auto operation modes."""
        self.mode = mode
        self._memory.add_turn(
            "system", f"Mode switched to {mode.value}", mode_change=True
        )

        # Save after mode switch
        if self.auto_persist:
            self.save()

    def save(self, data_dir: Optional[Path] = None) -> Path:
        """
        Manually save session to persistent storage.

        Returns path to saved session file.
        """
        store = self._store or SessionStore(data_dir=data_dir)
        return store.save_session(self)

    @classmethod
    def load(
        cls,
        session_id: str,
        *,
        data_dir: Optional[Path] = None,
        llm_config: Optional[LLMConfig] = None,
    ) -> Optional['ResumeSession']:
        """
        Load session from persistent storage.

        >>> session = ResumeSession.load("abc123def456")
        >>> session.session_id if session else None
        'abc123def456'
        """
        store = SessionStore(data_dir=data_dir)
        return store.load_session(session_id, llm_config=llm_config)

    @classmethod
    def list_persisted(cls, data_dir: Optional[Path] = None) -> Iterable[dict]:
        """
        List all persisted sessions.

        >>> for session_info in ResumeSession.list_persisted():
        ...     print(session_info['session_id'])
        """
        store = SessionStore(data_dir=data_dir)
        return store.list_sessions()


# ============================================================================
# Worker Agents (Specialized Operations)
# ============================================================================


class ExpansionAgent:
    """
    Expands brief bullet points into detailed achievement descriptions.

    Uses DSPy-optimized prompts for consistent, high-quality expansions.
    """

    def __init__(self, *, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config or LLMConfig(model="gpt-3.5-turbo")
        self._llm = self._init_llm()

    def _init_llm(self):
        """Initialize LLM provider."""
        try:
            from openai import OpenAI

            return OpenAI(api_key=self.llm_config.api_key)
        except ImportError:
            return None

    def expand(
        self, brief_text: str, context: dict, *, target_length: str = "detailed"
    ) -> str:
        """
        Expand brief text into detailed description.

        >>> config = LLMConfig(model="gpt-4")
        >>> agent = ExpansionAgent(llm_config=config)
        >>> agent.llm_config.model
        'gpt-4'
        """
        if not self._llm:
            return f"[EXPANDED - No LLM] {brief_text}"

        prompt = f"""Expand this brief bullet point into a detailed achievement description.

Brief text: {brief_text}

Context: {context.get('additional_context', 'N/A')}

Guidelines:
- Start with a strong action verb
- Include specific metrics and quantifiable results where possible
- Highlight the impact and outcome
- Keep it concise but detailed (2-3 sentences max)
- Use professional tone suitable for a resume

Expanded description:"""

        try:
            response = self._llm.chat.completions.create(
                model=self.llm_config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens or 200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[EXPANSION ERROR: {e}] {brief_text}"


class DistillationAgent:
    """
    Distills verbose text into concise, impactful statements.

    Uses DSPy-optimized prompts with metrics for conciseness and clarity.
    """

    def __init__(self, *, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config or LLMConfig(model="gpt-3.5-turbo")
        self._llm = self._init_llm()

    def _init_llm(self):
        """Initialize LLM provider."""
        try:
            from openai import OpenAI

            return OpenAI(api_key=self.llm_config.api_key)
        except ImportError:
            return None

    def distill(
        self,
        verbose_text: str,
        *,
        max_words: Optional[int] = None,
        preserve_metrics: bool = True,
    ) -> str:
        """
        Distill verbose text into concise statement.

        >>> config = LLMConfig(model="gpt-4")
        >>> agent = DistillationAgent(llm_config=config)
        >>> agent.llm_config.model
        'gpt-4'
        """
        if not self._llm:
            return f"[DISTILLED - No LLM] {verbose_text[:50]}..."

        word_constraint = f"Maximum {max_words} words. " if max_words else ""
        metrics_instruction = (
            "Preserve all numbers, metrics, and quantifiable results. "
            if preserve_metrics
            else ""
        )

        prompt = f"""Distill this verbose text into a concise, impactful statement.

Verbose text: {verbose_text}

Guidelines:
{word_constraint}{metrics_instruction}- Use strong action verbs
- Remove unnecessary words and filler
- Maintain professional tone
- Keep the core message and impact

Distilled version:"""

        try:
            response = self._llm.chat.completions.create(
                model=self.llm_config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens or 150,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[DISTILLATION ERROR: {e}] {verbose_text[:50]}..."


class MatchingAgent:
    """
    Performs semantic matching between candidate info and job requirements.

    Uses embedding-based similarity and cross-encoder reranking.
    """

    def __init__(self, *, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config or LLMConfig(model="gpt-3.5-turbo")
        self._llm = self._init_llm()

    def _init_llm(self):
        """Initialize LLM for matching analysis."""
        try:
            from openai import OpenAI

            return OpenAI(api_key=self.llm_config.api_key)
        except ImportError:
            return None

    def find_matches(
        self, candidate_text: str, job_requirements: str
    ) -> Iterable[dict]:
        """
        Find semantic matches between candidate experience and job needs.

        Yields dicts with 'candidate_snippet', 'job_requirement', 'score'.
        """
        if not self._llm:
            yield {
                "candidate_snippet": "N/A",
                "job_requirement": "N/A",
                "score": 0.0,
                "model": "none",
            }
            return

        prompt = f"""Analyze the candidate's experience and identify how it matches the job requirements.

Job Requirements:
{job_requirements}

Candidate Experience:
{candidate_text}

For each relevant match, provide:
1. A specific snippet from the candidate's experience
2. The job requirement it addresses
3. How strong the match is (0.0 to 1.0)

Format as JSON array:
[{{"candidate_snippet": "...", "job_requirement": "...", "score": 0.9}}]"""

        try:
            response = self._llm.chat.completions.create(
                model=self.llm_config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=self.llm_config.max_tokens or 500,
            )

            import json

            matches = json.loads(response.choices[0].message.content)
            for match in matches:
                match['model'] = self.llm_config.model
                yield match

        except Exception as e:
            yield {
                "candidate_snippet": f"Error: {e}",
                "job_requirement": "N/A",
                "score": 0.0,
                "model": self.llm_config.model,
            }


class SearchAgent:
    """
    Performs web searches to expand context about companies, technologies, etc.

    Integrates with search APIs to gather relevant information.
    """

    def __init__(self, *, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config or LLMConfig(model="gpt-3.5-turbo")
        self._llm = self._init_llm()

    def _init_llm(self):
        """Initialize LLM for summarizing search results."""
        try:
            from openai import OpenAI

            return OpenAI(api_key=self.llm_config.api_key)
        except ImportError:
            return None

    def search(self, query: str, *, result_count: int = 5) -> Iterable[dict]:
        """
        Search web for relevant information.

        Yields dicts with 'title', 'snippet', 'url'.
        """
        # Mock search results for now
        # TODO: Integrate with actual search API (Tavily, Serper, etc.)

        if not self._llm:
            yield {
                "title": f"Mock result for: {query}",
                "snippet": "Install search API for real results",
                "url": "https://example.com",
                "model": "none",
            }
            return

        # Use LLM to generate synthetic search results based on knowledge
        prompt = f"""Generate 3-5 key facts about: {query}

Format as JSON array:
[{{"title": "...", "snippet": "...", "url": "https://example.com"}}]

Focus on information relevant for a job candidate researching this company/topic."""

        try:
            response = self._llm.chat.completions.create(
                model=self.llm_config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            import json

            results = json.loads(response.choices[0].message.content)
            for result in results:
                result['model'] = self.llm_config.model
                yield result

        except Exception as e:
            yield {
                "title": f"Search for: {query}",
                "snippet": f"Error performing search: {e}",
                "url": "https://example.com",
                "model": self.llm_config.model,
            }


# ============================================================================
# Autonomous Agent (Uses Session as Tool)
# ============================================================================


class ResumeExpertAgent:
    """
    Autonomous agent that uses ResumeSession as a tool.

    Operates in auto mode, making decisions about expansion, distillation,
    search, and generation operations to produce complete resumes.

    >>> config = LLMConfig(model="gpt-4")
    >>> agent = ResumeExpertAgent(llm_config=config)
    >>> agent.llm_config.model
    'gpt-4'
    """

    def __init__(
        self,
        *,
        llm_config: Optional[LLMConfig] = None,
        model_registry: Optional[ModelRegistry] = None,
    ):
        # Prioritize registry over single config
        if model_registry:
            self.model_registry = model_registry
            self.llm_config = model_registry.supervisor
        elif llm_config:
            self.llm_config = llm_config
            self.model_registry = None
        else:
            # Default: high-quality model for autonomous planning
            self.llm_config = LLMConfig(model="gpt-4", temperature=0.3)
            self.model_registry = None

        self._execution_history: list[dict] = []
        self._planner_llm = self._init_planner()

    def _init_planner(self):
        """Initialize planner LLM."""
        # TODO: Initialize actual LangChain or DSPy LM for planning
        # from langchain_openai import ChatOpenAI
        # return ChatOpenAI(**self.llm_config.to_langchain_kwargs())
        return None

    def create_resume(
        self, session: ResumeSession, *, mode: str = "standard", max_iterations: int = 5
    ) -> str:
        """
        Autonomously create resume using session as tool.

        Operates in plan-and-execute pattern:
        1. Analyze job and candidate info
        2. Plan resume creation strategy
        3. Execute operations (expand, distill, match)
        4. Generate resume
        5. Critique and refine
        """
        # Generate plan
        plan = self.propose_plan(session, mode=mode)

        # Execute plan
        execution_result = self.execute_plan(session, plan, interactive=False)

        if not execution_result.get("success"):
            return f"Error executing plan: {execution_result.get('error', 'Unknown error')}"

        # Extract final resume from session state
        if 'resume' in session.state._data.get('drafts', {}):
            return session.state['drafts']['resume']

        # Fallback: get from last generation step
        for step_id in reversed(execution_result.get("completed_steps", [])):
            result = execution_result["results"].get(step_id)
            if result and result["action"] in ["generate_draft", "refine"]:
                return result["response"]

        return "Resume generation completed but no resume found in results."

    def _create_plan(self, session: ResumeSession, mode: str) -> list[dict]:
        """Create execution plan for resume generation."""
        # Deprecated. Use propose_plan instead.
        return [
            {"action": "analyze_job", "params": {}},
            {"action": "extract_key_requirements", "params": {}},
            {"action": "expand_achievements", "params": {}},
            {"action": "match_experience", "params": {}},
            {"action": "generate_draft", "params": {}},
        ]

    def propose_plan(self, session: ResumeSession, *, mode: str = "standard") -> Plan:
        """
        Generate execution plan for resume creation.

        Returns structured Plan object that can be edited before execution.
        """
        # TODO: Replace with actual LLM-based planning
        # For now, generate reasonable default plan based on mode

        if mode == "comprehensive":
            steps = [
                PlanStep(
                    id="step_1",
                    action="analyze_job",
                    description="Analyze job description to extract key requirements and priorities",
                    params={},
                ),
                PlanStep(
                    id="step_2",
                    action="search_company",
                    description="Research the company to understand culture and values",
                    params={"company_name": "extracted_from_job_info"},
                    dependencies=["step_1"],
                ),
                PlanStep(
                    id="step_3",
                    action="match_skills",
                    description="Identify strongest matches between candidate experience and job requirements",
                    params={},
                    dependencies=["step_1"],
                ),
                PlanStep(
                    id="step_4",
                    action="expand_achievements",
                    description="Expand top 3-5 achievements with metrics and impact",
                    params={"count": 5},
                    dependencies=["step_3"],
                ),
                PlanStep(
                    id="step_5",
                    action="generate_draft",
                    description="Generate complete resume draft in markdown",
                    params={"format": "markdown", "length": "1-page"},
                    dependencies=["step_4"],
                ),
                PlanStep(
                    id="step_6",
                    action="critique",
                    description="Review and critique the draft for improvements",
                    params={},
                    dependencies=["step_5"],
                ),
                PlanStep(
                    id="step_7",
                    action="refine",
                    description="Apply improvements from critique",
                    params={},
                    dependencies=["step_6"],
                ),
            ]
            rationale = "Comprehensive approach: research company, match skills carefully, expand key achievements, then generate and refine."
        else:  # standard mode
            steps = [
                PlanStep(
                    id="step_1",
                    action="analyze_job",
                    description="Extract key requirements from job description",
                    params={},
                ),
                PlanStep(
                    id="step_2",
                    action="expand_achievements",
                    description="Expand candidate's top 3 achievements",
                    params={"count": 3},
                    dependencies=["step_1"],
                ),
                PlanStep(
                    id="step_3",
                    action="generate_draft",
                    description="Generate resume draft",
                    params={"format": "markdown"},
                    dependencies=["step_2"],
                ),
            ]
            rationale = "Standard approach: analyze requirements, expand key achievements, generate resume."

        return Plan(steps=steps, rationale=rationale)

    def revise_plan(self, plan: Plan, instruction: str) -> Plan:
        """
        Revise plan based on natural language instruction.

        Uses LLM to interpret instruction and modify plan accordingly.
        """
        # Try to use planner LLM if available to parse the instruction
        import copy

        revised = copy.deepcopy(plan)

        if self._planner_llm:
            try:
                prompt = (
                    "You are a planner. Given the following plan (JSON) and a user instruction,"
                    " produce a revised plan as JSON with fields: steps (array of {id, action, description, params, dependencies})"
                )
                plan_json = {
                    "rationale": revised.rationale,
                    "steps": [
                        {
                            "id": s.id,
                            "action": s.action,
                            "description": s.description,
                            "params": s.params,
                            "dependencies": s.dependencies,
                        }
                        for s in revised.steps
                    ],
                }

                # Prefer chat-style interface
                try:
                    response = self._planner_llm.chat(
                        [
                            {"role": "system", "content": prompt},
                            {"role": "system", "content": json.dumps(plan_json)},
                            {"role": "user", "content": instruction},
                        ]
                    )
                except Exception:
                    response = self._planner_llm.complete(
                        f"{prompt}\nPLAN:{json.dumps(plan_json)}\nINSTRUCTION:{instruction}"
                    )

                # Parse JSON response into Plan
                try:
                    parsed = json.loads(response)
                    new_steps = []
                    for s in parsed.get("steps", []):
                        new_steps.append(
                            PlanStep(
                                id=s["id"],
                                action=s.get("action", ""),
                                description=s.get("description", ""),
                                params=s.get("params", {}),
                                dependencies=s.get("dependencies", []),
                            )
                        )
                    revised.steps = new_steps
                    revised.rationale = parsed.get("rationale", revised.rationale)
                    return revised
                except Exception:
                    revised.rationale += f"\n\nUser requested: {instruction} (planner LLM returned non-JSON)"
                    return revised

            except Exception as e:
                revised.rationale += (
                    f"\n\nPlan revision attempted but planner LLM error: {e}"
                )
                return revised

        # No planner LLM available: append note to rationale
        revised.rationale += f"\n\nUser requested: {instruction}"
        return revised

    def execute_plan(
        self,
        session: ResumeSession,
        plan: Plan,
        *,
        interactive: bool = False,
        approval_callback: Optional[Callable[[PlanStep], str]] = None,
    ) -> dict:
        """
        Execute a plan step by step.

        Args:
            session: Resume session to operate on
            plan: Plan to execute
            interactive: If True, pause after each step for approval

        Returns:
            Dict with execution results and final outputs
        """
        # Validate plan first
        errors = plan.validate()
        if errors:
            return {"success": False, "errors": errors, "completed_steps": []}

        completed_steps = set()
        results = {}

        # Switch to auto mode for execution
        original_mode = session.mode
        session.switch_mode(OperationMode.AUTO)

        try:
            while len(completed_steps) < len(plan.steps):
                # Get executable steps
                executable = plan.get_executable_steps(completed_steps)

                if not executable:
                    # Deadlock - no steps can execute
                    return {
                        "success": False,
                        "error": "Plan deadlock: no executable steps remaining",
                        "completed_steps": list(completed_steps),
                        "results": results,
                    }

                # Execute first executable step
                step = executable[0]

                if interactive:
                    if approval_callback:
                        response = approval_callback(step).lower()
                    else:
                        print(f"\nExecute: {step.description}?")
                        response = input("(y/n/skip): ").lower()

                    if response == 'n':
                        break
                    elif response == 'skip':
                        completed_steps.add(step.id)
                        continue

                # Execute the step
                instruction = self._step_to_instruction(step)
                response = session.chat(instruction)

                # Record result
                results[step.id] = {
                    "action": step.action,
                    "description": step.description,
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                }
                completed_steps.add(step.id)

                # Record in execution history
                self._execution_history.append(
                    {
                        "step_id": step.id,
                        "action": step.action,
                        "params": step.params,
                        "response": response,
                        "timestamp": datetime.now(),
                    }
                )

            return {
                "success": True,
                "completed_steps": list(completed_steps),
                "results": results,
            }

        finally:
            # Restore original mode
            session.switch_mode(original_mode)

    def _step_to_instruction(self, step: PlanStep) -> str:
        """Convert a plan step to natural language instruction."""
        # Map action types to instructions
        action_templates = {
            "analyze_job": "Analyze the job description and extract key requirements, focusing on technical skills and experience needed.",
            "search_company": f"Search for information about {step.params.get('company_name', 'the company')} and provide relevant context for a job candidate.",
            "match_skills": "Identify and list the strongest matches between the candidate's experience and the job requirements.",
            "expand_achievements": f"Expand the candidate's top {step.params.get('count', 3)} achievements into detailed bullet points with metrics and impact.",
            "generate_draft": f"Generate a complete {step.params.get('length', '')} resume in {step.params.get('format', 'markdown')} format.",
            "critique": "Critique the current resume draft and identify specific areas for improvement.",
            "refine": "Refine the resume based on the previous critique, implementing the suggested improvements.",
        }

        return action_templates.get(step.action, f"Perform action: {step.description}")

    def _execute_plan(self, session: ResumeSession, plan: list[dict]) -> None:
        """Execute plan steps using session tools."""
        for step in plan:
            action = step["action"]
            params = step["params"]

            # Execute action through session
            instruction = self._action_to_instruction(action, params)
            response = session.chat(instruction)

            # Record execution
            self._execution_history.append(
                {
                    "action": action,
                    "params": params,
                    "response": response,
                    "timestamp": datetime.now(),
                }
            )

    def _action_to_instruction(self, action: str, params: dict) -> str:
        """Convert action to natural language instruction."""
        # TODO: Implement action -> instruction mapping
        return f"Please perform: {action}"

    def _generate_resume(self, session: ResumeSession) -> str:
        """Generate resume from accumulated state."""
        response = session.chat(
            "Generate a complete resume in markdown format based on all "
            "the analysis and expansions we've done."
        )
        return response

    def _critique_and_refine(
        self, session: ResumeSession, resume: str, *, max_iterations: int = 3
    ) -> str:
        """Iteratively critique and refine resume."""
        current = resume

        for i in range(max_iterations):
            critique = session.chat(
                f"Critique this resume and identify specific improvements:\n\n{current}"
            )

            # Check if improvements needed
            if "no improvements needed" in critique.lower():
                break

            # Refine based on critique
            current = session.chat(
                f"Refine the resume based on this critique:\n\n{critique}"
            )

        return current


# ============================================================================
# Example Usage
# ============================================================================


def _example_manual_usage():
    """Example of manual mode usage with model configuration."""

    job_info = """
    Senior ML Engineer at TechCo
    - 5+ years Python, TensorFlow, PyTorch
    - Experience with large-scale ML systems
    - Team leadership experience
    """

    candidate_info = """
    Jane Doe
    - 6 years software engineering
    - Built ML recommendation system
    - Managed team of 3 engineers
    """

    # Option 1: Single model config (uses same model for everything)
    config = LLMConfig(model="gpt-4", temperature=0.7)
    session = ResumeSession(job_info, candidate_info, llm_config=config)

    # Option 2: Model registry for cost optimization
    # Use GPT-4 for supervisor, GPT-3.5-turbo for workers
    registry = ModelRegistry(
        supervisor=LLMConfig(model="gpt-4", temperature=0.3),
        workers=LLMConfig(model="gpt-3.5-turbo", temperature=0.7),
        # Optional: specify different models for specific operations
        expansion=LLMConfig(model="gpt-4", temperature=0.8),  # More creative
        distillation=LLMConfig(model="gpt-3.5-turbo", temperature=0.3),  # More precise
    )
    session_optimized = ResumeSession(job_info, candidate_info, model_registry=registry)

    # Option 3: Use presets
    session_fast = ResumeSession(
        job_info,
        candidate_info,
        model_registry=ModelRegistry.fast(),  # All GPT-3.5-turbo
    )

    session_quality = ResumeSession(
        job_info, candidate_info, model_registry=ModelRegistry.quality()  # All GPT-4
    )

    # Manual mode interaction
    response_1 = session.chat("Extract the key requirements from the job posting")
    print(f"Response 1: {response_1}")

    response_2 = session.chat(
        "Search for information about TechCo and summarize what might be "
        "relevant for the candidate"
    )
    print(f"Response 2: {response_2}")

    response_3 = session.chat(
        "Expand my recommendation system experience into detailed bullets"
    )
    print(f"Response 3: {response_3}")

    response_4 = session.chat("Generate a one-page resume in markdown")
    print(f"Response 4: {response_4}")

    # Inspect state
    print(f"\nTurn count: {len(session.history)}")
    print(f"State keys: {list(session.state._data.keys())}")
    print(f"Snapshots: {len(session.snapshots)}")
    print(f"Using model: {session.llm_config.model}")


def _example_auto_usage():
    """Example of autonomous mode usage with model configuration."""

    job_info = "Senior ML Engineer at TechCo..."
    candidate_info = "Jane Doe, 6 years experience..."

    # Option 1: Agent with single model
    agent = ResumeExpertAgent(llm_config=LLMConfig(model="gpt-4", temperature=0.3))

    # Option 2: Agent with model registry (recommended for production)
    registry = ModelRegistry(
        supervisor=LLMConfig(model="gpt-4", temperature=0.3),  # Planning
        workers=LLMConfig(model="gpt-3.5-turbo", temperature=0.7),  # Execution
    )
    agent_optimized = ResumeExpertAgent(model_registry=registry)

    # Create session (agent will use its own registry if provided)
    session = ResumeSession(
        job_info, candidate_info, model_registry=registry  # Session uses same registry
    )

    # Let agent autonomously create resume
    resume = agent_optimized.create_resume(session, mode="comprehensive")
    print(f"Generated resume:\n{resume}")
    print(f"Used planner model: {agent_optimized.llm_config.model}")


def _example_custom_provider():
    """Example with custom provider (e.g., local LLM, Anthropic)."""

    # Option 1: Single model for everything
    config = LLMConfig(
        model="deepseek-r1:8b",
        provider="ollama",
        base_url="http://localhost:11434",
        temperature=0.7,
    )

    session = ResumeSession(
        "Someone to modernize our processes to be more AI-driven.",
        "An AI director with experience in building AI-first products.",
        llm_config=config,
    )


def _example_custom_provider_registry():
    """Example with custom provider and model registry."""
    # Option 2: Model registry for optimization
    # Use deepseek-r1 for complex reasoning, mistral for simpler tasks
    registry = ModelRegistry(
        supervisor=LLMConfig(
            model="deepseek-r1:8b",  # Complex analysis and planning
            provider="ollama",
            base_url="http://localhost:11434",
            temperature=0.3,
        ),
        workers=LLMConfig(
            model="mistral:7b-instruct-q6_K",  # Fast for routine operations
            provider="ollama",
            base_url="http://localhost:11434",
            temperature=0.7,
        ),
        # Optional: specialized models
        expansion=LLMConfig(
            model="deepseek-r1:8b",  # Better for detailed expansions
            provider="ollama",
            base_url="http://localhost:11434",
            temperature=0.8,
        ),
        distillation=LLMConfig(
            model="mistral:7b-instruct-q6_K",  # Good enough for condensing
            provider="ollama",
            base_url="http://localhost:11434",
            temperature=0.3,
        ),
    )
    session = ResumeSession(
        "Someone to modernize our processes to be more AI-driven.",
        "An AI director with experience in building AI-first products.",
        model_registry=registry,
    )


def _example_persistence():
    """Example of session persistence and recovery."""

    job_info = "Senior ML Engineer at TechCo..."
    candidate_info = "Jane Doe, 6 years experience..."

    # Create session with auto-persistence (enabled by default)
    config = LLMConfig(
        model="deepseek-r1:8b", provider="ollama", base_url="http://localhost:11434"
    )

    session = ResumeSession(
        job_info,
        candidate_info,
        llm_config=config,
        auto_persist=True,  # Default is True
    )

    print(f"Created session: {session.session_id}")
    print(f"Data location: {session._store.data_dir}")

    # Each chat is automatically saved
    r1 = session.chat("Extract key job requirements")
    r2 = session.chat("Expand my experience bullets")

    # Later: List all persisted sessions
    print("\nPersisted sessions:")
    for info in ResumeSession.list_persisted():
        print(
            f"  - {info['session_id']}: {info['turn_count']} turns, "
            f"updated {info['updated_at']}"
        )

    # Load previous session
    loaded = ResumeSession.load(session.session_id, llm_config=config)

    if loaded:
        print(f"\nLoaded session with {len(loaded.history)} turns")
        # Continue from where you left off
        r3 = loaded.chat("Generate the resume now")

    # Custom data directory
    custom_session = ResumeSession(
        job_info,
        candidate_info,
        llm_config=config,
        data_dir=Path("./my_resume_sessions"),
    )

    # Disable auto-persisting and save manually
    manual_session = ResumeSession(
        job_info, candidate_info, llm_config=config, auto_persist=False
    )
    manual_session.chat("Do something")
    manual_session.save()  # Explicit save


def _example_semi_auto_usage():
    """Example of semi-autonomous mode with plan editing."""

    job_info = "Senior ML Engineer at TechCo..."
    candidate_info = "Jane Doe, 6 years experience..."

    config = LLMConfig(
        model="deepseek-r1:8b", provider="ollama", base_url="http://localhost:11434"
    )

    session = ResumeSession(job_info, candidate_info, llm_config=config)
    agent = ResumeExpertAgent(llm_config=config)

    # 1. Agent proposes plan
    plan = agent.propose_plan(session, mode="comprehensive")
    print(plan.to_markdown())

    # 2. User edits plan (example: remove company search)
    plan.steps = [s for s in plan.steps if s.action != "search_company"]

    # 3. Validate edited plan
    errors = plan.validate()
    if errors:
        print(f"Plan validation errors: {errors}")

    # 4. Execute with approval at each step
    result = agent.execute_plan(session, plan, interactive=True)

    # Or: Execute automatically
    # result = agent.execute_plan(session, plan)

    print(f"\nExecution completed: {result.get('success')}")
    print(f"Completed {len(result.get('completed_steps', []))} steps")


if __name__ == "__main__":
    _example_manual_usage()

    print("\n" + "=" * 80 + "\n")
    _example_semi_auto_usage()

    print("\n" + "=" * 80 + "\n")
    _example_auto_usage()

    print("\n" + "=" * 80 + "\n")
    _example_persistence()
