"""
Phase 9 - Topic 06: LLM-as-a-Judge: RAG & Agent Evaluation

A structured-output judge (Phase 1 Topic 04 style) grades a RAG answer for
groundedness, and a second judge grades an agent run for task success.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

DOCS_TEXT = [
    "The company's return policy allows returns within 30 days of purchase.",
    "Support hours are 9am-6pm, Monday through Friday.",
    "Premium plan subscribers get free shipping on all orders.",
]
RAG_QUESTION = "What's the return window?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    if not os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        print(
            "[note] LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 not set - the judge calls "
            "below will still run for real against OpenAI, but won't be traced to "
            "LangSmith. Set both in ../../.env to see the judge's own runs in the UI."
        )

    class JudgeResult(BaseModel):
        """A judge's verdict on one answer."""

        score: bool = Field(description="True if the answer meets the grading criteria")
        reasoning: str = Field(description="One short sentence explaining the score")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    judge_model = model.with_structured_output(JudgeResult)

    # --- Judge 1: groundedness, on a minimal RAG pipeline ----------------------
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [Document(page_content=text) for text in DOCS_TEXT]
    vectorstore = Chroma.from_documents(documents, embedding=embeddings)

    retrieved = vectorstore.similarity_search(RAG_QUESTION, k=2)
    context = "\n".join(doc.page_content for doc in retrieved)
    rag_answer = model.invoke(
        f"Answer using ONLY this context:\n{context}\n\nQuestion: {RAG_QUESTION}"
    ).content

    groundedness_prompt = (
        "You are a strict fact-checker. Given CONTEXT and an ANSWER, decide whether "
        "every claim in the ANSWER is directly supported by the CONTEXT. Do not use "
        "outside knowledge.\n\n"
        f"CONTEXT:\n{context}\n\nANSWER:\n{rag_answer}"
    )
    groundedness_verdict: JudgeResult = judge_model.invoke(groundedness_prompt)

    print("=== Judge 1: Groundedness (RAG) ===")
    print(f"Question: {RAG_QUESTION}")
    print(f"Answer:   {rag_answer}")
    print(f"Verdict:  score={groundedness_verdict.score}  reasoning={groundedness_verdict.reasoning}\n")

    # --- Judge 2: task success, on a minimal agent ------------------------------
    @tool
    def get_order_status(order_id: str) -> str:
        """Look up the status of an order by its ID."""
        return "shipped, arriving in 2 days" if order_id == "A100" else "unknown order"

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[get_order_status],
        system_prompt="You are a helpful support assistant. Use tools to answer.",
    )
    task = "Tell the customer the status of order A100."
    agent_result = agent.invoke({"messages": [{"role": "user", "content": task}]})
    final_answer = agent_result["messages"][-1].content

    task_success_prompt = (
        "You are grading whether an assistant accomplished a TASK. Given the TASK and "
        "the assistant's FINAL ANSWER, decide if the task was actually accomplished.\n\n"
        f"TASK:\n{task}\n\nFINAL ANSWER:\n{final_answer}"
    )
    task_success_verdict: JudgeResult = judge_model.invoke(task_success_prompt)

    print("=== Judge 2: Task success (agent) ===")
    print(f"Task:         {task}")
    print(f"Final answer: {final_answer}")
    print(f"Verdict:      score={task_success_verdict.score}  reasoning={task_success_verdict.reasoning}\n")

    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print("Both the RAG/agent runs AND the two judge calls are LLM calls - if tracing")
    print("is on, all four show up as runs in your project:")
    print(f"  https://smith.langchain.com/  ->  project \"{project}\"")


if __name__ == "__main__":
    main()
