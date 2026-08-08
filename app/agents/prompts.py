"""Purpose: system prompts for each agent — never an inline string built ad
hoc inside agent logic (see CLAUDE.md's No Magic Values table).
"""

WRITING_AGENT_SYSTEM_PROMPT = (
    "You are a writing assistant. Given a goal, produce clear, well-structured "
    "content that directly accomplishes it. Respond with only the finished content."
)
