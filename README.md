# Project structure

1. v1 rollout:
    - Single LLM call (Data desc, model desc, project desc, guidelines) $\rightarrow$ LLM response.
    - Notebook making : notebook with manually formatted context (LLM input), with Responses rendered during runtime with LLM response (Single markdown text cell).

2. v2 rollout
    - ReACT agent
    - Notebook setup fully rendered during runtime using LLM response. (make LLM give self-sufficient response)

## project structure

```text

|_  Core
    |_  frontend
        |_  Notebook maker
    |_  backend
        |_  LLM (LLM intializers)
        |_  xai (Explainability methods)
        |_  `TBD` Agent (tool calls, agent initializers) uses other existing modules.

|_  Assets
    |_  Guidelines
    |_  Prompt templates (user and system)
|_  Data


```