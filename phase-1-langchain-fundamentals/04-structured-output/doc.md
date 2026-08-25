# 04 — Structured Output

## Problem

Phase 0 hand-built a JSON schema dict for structured output. That's verbose and gives
up Python-level validation. LangChain lets you describe the schema as a Pydantic model
and get a validated Python object back directly.

## Concept

`model.with_structured_output(Schema)` returns a wrapped model whose `.invoke()` returns
an **instance of your schema**, not text you have to parse:

```python
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    """Contact information for a person."""
    name: str = Field(description="The person's name")
    email: str = Field(description="The person's email address")

structured_model = model.with_structured_output(ContactInfo)
result = structured_model.invoke("Sarah Chen, sarah@example.com")
# result is a ContactInfo instance: result.name, result.email
```

Under the hood LangChain picks a strategy per provider: native structured-output APIs
where supported, or a tool-calling-based fallback otherwise — you don't have to know
which; the interface is the same either way.

The same Pydantic-schema pattern extends to agents (Topic 06): `create_agent(...,
response_format=Schema)` returns a validated object at `result["structured_response"]`
after the agent finishes acting.

## Minimal code

`code.py` defines a small Pydantic schema, extracts structured data from free text with
`with_structured_output`, and prints both the typed object and its field values directly
(no `json.loads` needed, unlike Phase 0's version of this).

## Production notes

Use `Field(description=...)` generously — the description is what the model reads to
decide what to put in each field, not just documentation for humans. Nested Pydantic
models work too, for structured output with sub-objects/lists.

## Debugging

- Field comes back `None`/empty when it shouldn't → tighten the field's `description`
  or add a `Literal`/`enum` constraint instead of free-form `str`.
- Validation error at runtime → the model's output didn't satisfy the Pydantic schema
  (rare with structured-output mode, more common with the tool-calling fallback on
  older/smaller models).

## Mini challenge

Add a field that's a `list[str]` (e.g. `skills: list[str]`) and confirm the model
returns an actual Python list, not a comma-separated string.
