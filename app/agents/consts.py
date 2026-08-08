"""Purpose: constants specific to agent implementations. Anything used
outside `app/agents/` belongs in the top-level `app/constants.py` instead —
see CLAUDE.md's No Magic Values table.
"""

# Caps the length of a single agent's LLM response. Not user-configurable —
# this bounds cost/latency per call, unlike MAX_CONCURRENT_LLM_CALLS (in
# app/config.py) which bounds how many calls happen at once.
WRITING_AGENT_MAX_TOKENS = 1024
