"""
Phase 1 - Topic 04: Structured Output

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_keys()
    try:
        from langchain.chat_models import init_chat_model
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    class ContactInfo(BaseModel):
        """Contact information extracted from a message."""

        name: str = Field(description="The person's full name")
        email: str = Field(description="The person's email address")
        company: str = Field(description="The company the person works for")
        skills: list[str] = Field(
            description="Any technical skills mentioned, as separate short strings"
        )

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    structured_model = model.with_structured_output(ContactInfo)

    text = (
        "Hi, I'm Sarah Chen from Northwind Robotics (sarah.chen@northwind.io). "
        "I mostly work with Python, LangChain, and Kubernetes."
    )
    result = structured_model.invoke(text)

    print(f"Type: {type(result).__name__}")  # a real ContactInfo, not a string
    print(f"Name:    {result.name}")
    print(f"Email:   {result.email}")
    print(f"Company: {result.company}")
    print(f"Skills:  {result.skills}  (type: {type(result.skills).__name__})")


if __name__ == "__main__":
    main()
