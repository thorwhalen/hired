# hired

Streamline the job application process for job seekers

To install: `pip install hired`

## Overview

The `hired` package is a Python library designed to simplify the process of creating professional resumes tailored to specific job applications. It leverages AI-driven content generation, schema validation, and customizable rendering pipelines to produce high-quality resumes in various formats.

## Features

### 1. Content Generation
- **AI-Driven Content**: Automatically generate resume content by analyzing candidate profiles and job descriptions.
- **Flexible Sources**: Supports JSON, YAML, and Python dictionaries as input sources.

### 2. Validation
- **JSON Resume Schema**: Ensures compliance with the [JSON Resume schema](https://jsonresume.org/schema/).
- **Strict and Permissive Modes**: Validate content strictly or allow flexibility for missing fields.
- **Pruning**: Automatically removes `None` values to ensure schema compliance.

### 3. Rendering
- **HTML and PDF**: Render resumes as HTML or PDF.
- **Template-Based Themes**: Use Jinja2 templates for customizable themes (e.g., `default`, `minimal`).
- **Optional WeasyPrint Integration**: Generate professional PDFs with WeasyPrint if installed.
- **Fallback PDF Builder**: Minimal PDF generation without external dependencies.
- **Empty Section Omission**: Automatically skips rendering empty sections.


# hired - resume agent

The `resume_agent` is an AI-powered system designed to assist in creating tailored resumes. It operates in manual, semi-autonomous, and fully autonomous modes, providing flexibility and control over the resume generation process.

### 1. Setup: Providing Job and Candidate Information

First, define the job you're applying for and the candidate's background. This information will be the foundation for the AI's work.

```python
from hired.resume_agent import ResumeSession, ResumeExpertAgent, LLMConfig

# Define the job description
job_info = """
Senior Machine Learning Engineer at InnovateTech

We are seeking an experienced ML engineer to join our dynamic team. The ideal
candidate will have a strong background in building and deploying machine
learning models, with expertise in NLP and computer vision. Responsibilities
include designing and implementing ML pipelines, collaborating with
cross-functional teams, and driving innovation in our products.
"""

# Summarize the candidate's experience
candidate_info = """
- 7+ years of experience as a software and machine learning engineer.
- Proficient in Python, TensorFlow, and PyTorch.
- Led the development of a real-time recommendation engine, increasing user
  engagement by 20%.
- Designed and deployed a computer vision system for quality control in
  manufacturing, reducing defects by 15%.
- Published two papers on NLP in top-tier conferences.
"""

# Configure the LLM to be used by the agent
# (This is a conceptual example; you would integrate your preferred LLM provider)
llm_config = LLMConfig(model="gpt-4-turbo")
```

### 2. Manual Mode: Interactive Resume Building

In manual mode, you have direct control over the resume creation process. You can chat with the `ResumeSession` to expand on your achievements, distill verbose descriptions into impactful bullet points, or analyze how your experience matches the job. This is useful for users who want to guide the AI step-by-step and retain full control.

```python
# Create a session in manual mode
session = ResumeSession(
    job_info=job_info,
    candidate_info=candidate_info,
    llm_config=llm_config,
)

# Start a chat to expand on a specific point
response = session.chat(
    "Expand on the recommendation engine project. "
    "Mention the use of collaborative filtering and A/B testing."
)
print("AI-EXPANDED ACHIEVEMENT:")
print(response)

# You can continue the conversation to refine other sections
response = session.chat(
    "Now, distill the computer vision project description into a single, "
    "impactful resume bullet point."
)
print("\nAI-DISTILLED BULLET POINT:")
print(response)
```

### 3. Semi-Automatic Mode: Plan, Review, and Execute

For a more guided but still controlled approach, you can ask the `ResumeExpertAgent` to propose a plan. You can review this plan, make changes if needed, and then command the agent to execute it. This balances automation with human oversight.

```python
# Create an expert agent
agent = ResumeExpertAgent(llm_config=llm_config)

# Propose a plan for creating the resume
plan = agent.propose_plan(session)

print("PROPOSED PLAN:")
for step in plan.steps:
    print(f"- {step.id}: {step.description} (Depends on: {step.dependencies})")

# After reviewing (and optionally editing) the plan, execute it
# The agent will perform the steps, like analyzing the job,
# drafting sections, and matching skills.
results = agent.execute_plan(session, plan)

if results["success"]:
    print("\nPlan executed successfully!")
    # The final resume content is stored in the session state
    final_resume = session.state.get("final_resume_content")
    # print(final_resume)
```

### 4. Fully Automatic Mode: End-to-End Resume Generation

In the fully automatic mode, the `ResumeExpertAgent` handles the entire process from analysis to final output. It creates and executes its own plan to generate a resume tailored to the job description. This is the fastest way to get a first draft.

```python
# The agent handles everything autonomously
final_resume_content = agent.create_resume(session)

print("--- AUTONOMOUSLY GENERATED RESUME ---")
print(final_resume_content)
print("------------------------------------")
```


