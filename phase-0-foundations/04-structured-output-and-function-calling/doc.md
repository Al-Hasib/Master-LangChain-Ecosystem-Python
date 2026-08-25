# 04 — Structured Output & Function/Tool Calling

## Problem

Free-text answers can't be plugged into other code reliably, and models can't *do*
anything on their own — no web search, no database query. Structured output and tool
calling solve these two problems, and together they're the foundation everything in
Phase 1 ("Tools", "`create_agent`") is built on.

## Concept

- **Structured output** — constraining the model to return data matching a schema
  (typically JSON) instead of free prose, so your code can parse it without regex
  gymnastics. Modern APIs support this natively (JSON mode / schema-constrained
  decoding) rather than "please respond in JSON" prompting.
- **Function/tool calling** — you describe available functions (name, description,
  JSON-schema parameters) to the model. The model doesn't execute anything — it returns
  a *request* to call one, with arguments. **Your code** runs the function and sends the
  result back as a `tool` message. The model then continues, possibly calling another
  tool, until it produces a final answer.

```text
You: "describe tools" -> Model: "call get_weather(city='Dhaka')"
                       -> Your code: runs get_weather('Dhaka') -> "28C, humid"
                       -> Model (given the result): "It's 28°C and humid in Dhaka."
```

This request→execute→feed-back cycle, repeated, **is** the agent loop from Topic 01 —
Phase 1's `create_agent` automates exactly this.

## Minimal code

`code.py` shows both: (1) getting a JSON object back matching a schema for a simple
extraction task, and (2) a full manual tool-calling round-trip — describe a tool, get a
tool-call request, execute it locally, send the result back, get the final answer.

## Production notes

Always validate structured output against a schema (e.g. Pydantic) even when using
native JSON mode — models occasionally still produce malformed or incomplete output. For
tools, keep descriptions precise: vague tool descriptions are the #1 cause of an agent
picking the wrong tool or not calling one at all.

## Debugging

- Model returns JSON as a string wrapped in prose ("Sure! Here's the JSON: ...") →
  you're not using native structured-output mode, you're prompting for it — switch.
- Model calls a tool it shouldn't → tighten the tool's description / add "only use this
  when..." guidance.
- Model never calls any tool → tool description doesn't make the applicability obvious,
  or the question doesn't clearly require it.

## Mini challenge

Add a second tool (`convert_currency`) and ask a question that requires calling both
tools in sequence; trace the full round trip in printed output.
