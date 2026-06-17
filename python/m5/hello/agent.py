# python/m5/hello/agent.py
"""A minimal deep agent, exposed as a graph for `langgraph dev`.

This is the whole agent: a model, nothing else. The point of this lab is the
*deployment*, not the agent — so we keep the agent as small as it gets and let
`langgraph dev` serve it over HTTP.
"""

import sys
from pathlib import Path

# Make the shared workshop model module importable (python/models.py), so the
# agent uses whatever provider you configured in setup instead of a hardcoded
# model. parents[2] = python/ (this file is python/m5/hello/agent.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from deepagents import create_deep_agent  # noqa: E402

from models import model  # noqa: E402

# `langgraph.json` points at this module-level variable: "./agent.py:graph".
graph = create_deep_agent(model=model)
