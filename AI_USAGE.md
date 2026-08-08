# AI Tool Usage

## Tools I Used

- ChatGPR - Mainly for double check decisions, compare libraries to ts.
- ClaudeCode - Usually sonnet5 for code & Haiku4.5 for quetsions and planning.
- Google - to read more about the libraries and how to write an agent.

## What Helped Most

- breaking down the assignment. 1st prompt with the assignment details, my prefrences for the assignment general build - see the plan and twik with my and chatgpt comments. and planning 5 phases to go through(each one in a commit - that way easier to review and change)

-

## What I Had to Fix

- 3rd phase test suite hung indefinitely: The execution engine shared one AsyncSession across concurrently-gathered steps, deadlocking. Fixed by serializing DB writes behind an `asyncio.Lock`.

## What AI Struggled With

- I mainly still have a problem with making claude stick to the code restrictions and prefrences i define at claude.md - it will still miss some thigs - i try to fix it between projects i do and change manually and try to make it update the claude.md based on my changes.
- 
