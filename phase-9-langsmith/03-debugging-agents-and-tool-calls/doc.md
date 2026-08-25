# 03 — Debugging Agents & Tool Calls

## Problem

Phase 1 Topic 08 covered debugging agents from *inside your code* (inspect
`result["messages"]`, add retries/fallbacks). That works when you're the one running the
script. It doesn't work once the agent is deployed and a user reports "it gave me a weird
answer three hours ago" — you weren't watching, there's no `print()` output to read. You
need a persisted, inspectable record of exactly what the agent did. That's a trace.

## Concept

Every tool call an agent makes is its own child run in the trace (Topic 02), which means
a trace answers the two questions that matter most when an agent misbehaves:

1. **Did it call the right tool?** — visible directly: the trace shows the tool name and
   the exact arguments the model chose to pass.
2. **Did the tool return something reasonable, and did the model use it correctly?** —
   also visible: each tool call's child run shows its return value, and the next LLM
   call's input shows that return value being fed back in.

```text
agent run (root)
├─ ChatOpenAI            <- model decides which tool(s) to call, with what args
├─ tool: flaky_lookup     <- child run: see the EXACT input args + returned output
│    (latency: 2.1s)      <- a slow child run is instantly visible here
├─ ChatOpenAI            <- model reacts to that tool's output
└─ ...
```

This turns "the agent is wrong" into a mechanical checklist against the trace:
- Wrong tool chosen → look at the system prompt / tool descriptions the model saw (the
  first `ChatOpenAI` child run's input shows exactly what it read before deciding).
- Right tool, bad output used → the tool's child run shows what it actually returned;
  if that's wrong, the bug is in the tool, not the model.
- Right tool, good output, still a bad final answer → the *last* `ChatOpenAI` child run's
  input shows whether the good tool output even made it into the prompt.
- Everything's slow → sort child runs by latency; a single slow tool is a much smaller
  fix than "the agent is slow."

## Minimal code

`code.py` builds a `create_agent` with two tools: `unit_price` (correct, fast) and
`flaky_shipping_estimate` (deliberately slow — a `time.sleep` — **and** deliberately
wrong for one input, to simulate a real bug). It asks a question that forces both tools
to be called, runs it fully traced, and prints a hint pointing at exactly which trace
node to open to spot each problem.

## Production notes

Tag traces with `metadata={"tool_version": ...}` so that when you fix a flaky tool, you
can filter LangSmith to "runs after the fix" and confirm the latency/wrong-output problem
is actually gone — comparing before/after by eye across hundreds of runs isn't feasible,
filtering by metadata is.

## Debugging

- Trace shows a tool called with obviously wrong arguments → the tool's docstring/type
  hints under-specify what it expects (Phase 1 Topic 05's point about tool descriptions
  being what the model reads, not documentation for humans).
- Trace shows correct tool + correct output, but the final answer still ignores it →
  the system prompt likely doesn't instruct the model to prioritize tool output over its
  own assumptions.
- A tool's child run never appears at all → the model never decided to call it — that's
  a prompt/tool-description problem, not a tool-implementation problem, and the trace
  tells you which side of that line you're on immediately.

## Mini challenge

Add a third tool that raises an exception for one specific input, run the agent against
that input, and find the errored child run in the trace — confirm LangSmith marks it
distinctly (as an error) rather than just showing an empty output.
