"""
Phase 0 - Topic 04: Structured Output & Function/Tool Calling

Run:
    python code.py
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    return OpenAI(api_key=api_key)


def structured_output_demo(client, model: str) -> None:
    """Extract a strict JSON object from unstructured text."""
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "contact_info",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "company": {"type": "string"},
                },
                "required": ["name", "email", "company"],
                "additionalProperties": False,
            },
        },
    }
    text = (
        "Hi, I'm Sarah Chen from Northwind Robotics, reach me at sarah.chen@northwind.io"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Extract contact info from the user's message."},
            {"role": "user", "content": text},
        ],
        response_format=schema,
    )
    parsed = json.loads(response.choices[0].message.content)
    print("Extracted JSON:", json.dumps(parsed, indent=2))


def get_weather(city: str) -> str:
    """Fake weather lookup - stands in for a real API call."""
    fake_data = {"Dhaka": "28C, humid", "London": "14C, rainy", "Tokyo": "22C, clear"}
    return fake_data.get(city, "Unknown city")


def tool_calling_demo(client, model: str) -> None:
    """A full manual tool-call round trip: describe -> request -> execute -> feed back."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a named city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    messages = [{"role": "user", "content": "What's the weather in Dhaka?"}]

    # Step 1: model requests a tool call.
    response = client.chat.completions.create(model=model, messages=messages, tools=tools)
    message = response.choices[0].message
    tool_call = message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    print(f"Model requested: {tool_call.function.name}({args})")

    # Step 2: WE execute the function locally - the model never runs code itself.
    result = get_weather(**args)
    print(f"Local execution result: {result}")

    # Step 3: feed the result back as a `tool` message and get the final answer.
    messages.append(message)
    messages.append(
        {"role": "tool", "tool_call_id": tool_call.id, "content": result}
    )
    final = client.chat.completions.create(model=model, messages=messages)
    print(f"Final answer: {final.choices[0].message.content}")


def main() -> None:
    client = require_client()
    model = "gpt-4o-mini"

    print("=== 1) Structured output ===")
    structured_output_demo(client, model)

    print("\n=== 2) Tool calling round trip ===")
    tool_calling_demo(client, model)


if __name__ == "__main__":
    main()
