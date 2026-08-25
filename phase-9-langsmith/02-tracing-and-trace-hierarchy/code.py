"""
Phase 9 - Topic 02: Tracing & Trace Hierarchy

Also the Phase 9 project: a minimal RAG pipeline (built entirely in-code, no
dependency on other phases' files), instrumented end-to-end with @traceable so a
real parent/child trace tree gets created in LangSmith.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

DOCS_TEXT = [
    "LangSmith traces are trees: a root run with nested child runs for each step.",
    "The @traceable decorator turns a plain Python function into a traced child run.",
    "LangChain constructs like chat models and retrievers trace themselves automatically.",
    "Reading a trace tree means finding which child run has the highest latency.",
]
QUESTION = "How do I turn a plain Python function into a traced run?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def require_langsmith_key() -> None:
    if not os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        sys.exit(
            "This topic is about reading a real trace tree, so it needs LangSmith on.\n"
            "1) cp ../../.env.example ../../.env\n"
            "2) fill in LANGCHAIN_API_KEY (free account at https://smith.langchain.com/)\n"
            "3) set LANGCHAIN_TRACING_V2=true\n4) re-run"
        )


def main() -> None:
    require_openai_key()
    require_langsmith_key()
    try:
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langsmith import traceable
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [Document(page_content=text) for text in DOCS_TEXT]
    vectorstore = Chroma.from_documents(documents, embedding=embeddings)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # run_type tells the LangSmith UI how to render/aggregate this node
    # ("retriever" gets retrieval-specific columns, "llm" gets token counters, etc).
    @traceable(run_type="retriever")
    def retrieve(question: str) -> list[str]:
        """Child run #1 - becomes a node nested under whatever called it."""
        results = vectorstore.similarity_search(question, k=2)
        return [doc.page_content for doc in results]

    @traceable(run_type="chain")
    def rag_answer(question: str) -> str:
        """Root run for this call - everything invoked inside becomes a child."""
        context = retrieve(question)  # nested child run: retrieve
        prompt = (
            "Answer the question using ONLY the context below.\n\n"
            f"Context:\n{chr(10).join(context)}\n\nQuestion: {question}"
        )
        response = model.invoke(prompt)  # nested child run: ChatOpenAI (auto-traced)
        return response.content

    answer = rag_answer(QUESTION)

    print(f"Question: {QUESTION}\n")
    print(f"Answer: {answer}\n")
    print("--- Trace tree that was just created ---")
    print("rag_answer (root)")
    print("  |- retrieve (child, run_type=retriever)")
    print("  |    |- Chroma similarity_search (auto-traced)")
    print("  |- ChatOpenAI (child, run_type=llm, auto-traced)")
    print()
    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print("Go inspect the real tree (expand each node to see its input/output):")
    print(f"  https://smith.langchain.com/  ->  project \"{project}\"  ->  latest run")


if __name__ == "__main__":
    main()
