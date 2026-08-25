"""
Phase 0 - Topic 01: What is an LLM Application?
LLM (completion) vs Chat Model vs Agent, using the raw OpenAI SDK (no LangChain yet).

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n"
            "1) cp .env.example .env\n"
            "2) put your key in .env\n"
            "3) re-run this script"
        )
    return api_key


def completion_style_call(client, model: str) -> str:
    """A completion-style prompt: no roles, just 'continue this text'."""
    prompt = "The three layers of an LLM application are"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
    )
    return response.choices[0].message.content


def chat_style_call(client, model: str) -> str:
    """A proper multi-turn chat: explicit system/user/assistant roles."""
    messages = [
        {"role": "system", "content": "You are a concise AI engineering instructor."},
        {"role": "user", "content": "In one sentence, what is a chat model?"},
        {
            "role": "assistant",
            "content": "A chat model is an LLM served to accept structured "
            "conversation turns instead of a single block of text.",
        },
        {"role": "user", "content": "Now do the same for 'AI agent'."},
    ]
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=60)
    return response.choices[0].message.content


def one_agent_loop_iteration(client, model: str) -> str:
    """
    Not a real agent (no framework, no actual tool execution) - this just shows
    the SHAPE of the decision an agent loop makes each iteration: answer directly,
    or ask for a tool call. Phase 1 wires this into a real loop with real tools.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    messages = [{"role": "user", "content": "What's the weather in Dhaka right now?"}]
    response = client.chat.completions.create(
        model=model, messages=messages, tools=tools, max_tokens=100
    )
    choice = response.choices[0]
    if choice.message.tool_calls:
        call = choice.message.tool_calls[0]
        return f"Model chose to call a tool: {call.function.name}({call.function.arguments})"
    return f"Model answered directly: {choice.message.content}"


def main() -> None:
    api_key = require_api_key()
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    client = OpenAI(api_key=api_key)
    model = "gpt-4o-mini"

    print("--- 1) Completion-style call (no roles) ---")
    print(completion_style_call(client, model))

    print("\n--- 2) Chat-style call (system/user/assistant turns) ---")
    print(chat_style_call(client, model))

    print("\n--- 3) One 'agent loop' decision (answer vs. call a tool) ---")
    print(one_agent_loop_iteration(client, model))


if __name__ == "__main__":
    main()
