import pytest
from hired.resume_agent import (
    Plan,
    PlanStep,
    ResumeExpertAgent,
    ResumeSession,
    LLMConfig,
    SessionState,
)
from datetime import datetime
import pytest
from hired.resume_agent import (
    Plan,
    PlanStep,
    ResumeExpertAgent,
    ResumeSession,
    LLMConfig,
    SessionState,
)
from datetime import datetime


class DummySession(ResumeSession):
    def __init__(self):
        # Minimal init without calling parent heavy init
        self.job_info = "job"
        self.candidate_info = "candidate"
        self.mode = None
        self.llm_config = LLMConfig(model="gpt-3.5-turbo")
        self._memory = None
        self._state = SessionState()
        self._snapshots = []
        self.created_at = datetime.now()
        self.session_id = "dummy"
        self.auto_persist = False
        self._store = None
        self.name = None

    def chat(self, message: str) -> str:
        # Echo back for testing
        return f"RESPOND:{message}"

    def switch_mode(self, mode):
        self.mode = mode


def test_plan_validation_detects_missing_dependency():
    steps = [
        PlanStep(id="s1", action="a", description="d", dependencies=["s2"]),
    ]
    plan = Plan(steps=steps, rationale="r")
    errors = plan.validate()
    assert any("non-existent" in e for e in errors)


def test_plan_validation_detects_cycle():
    steps = [
        PlanStep(id="s1", action="a", description="d", dependencies=["s2"]),
        PlanStep(id="s2", action="b", description="d", dependencies=["s1"]),
    ]
    plan = Plan(steps=steps, rationale="r")
    errors = plan.validate()
    assert any("cycle" in e.lower() for e in errors)


def test_get_executable_steps_and_execution():
    steps = [
        PlanStep(id="s1", action="analyze_job", description="desc1", dependencies=[]),
        PlanStep(
            id="s2", action="generate_draft", description="desc2", dependencies=["s1"]
        ),
    ]
    plan = Plan(steps=steps, rationale="r")
    sess = DummySession()
    agent = ResumeExpertAgent(llm_config=LLMConfig(model="gpt-3.5-turbo"))

    res = agent.execute_plan(sess, plan, interactive=False)
    assert res["success"] is True
    assert set(res["completed_steps"]) == {"s1", "s2"}
    assert "s1" in res["results"] and "s2" in res["results"]
    # Check responses recorded
    assert res["results"]["s1"]["response"].startswith("RESPOND:")
