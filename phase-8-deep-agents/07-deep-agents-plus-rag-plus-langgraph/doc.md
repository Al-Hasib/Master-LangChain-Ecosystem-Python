# 07 — Deep Agents + RAG / + LangGraph

## Problem

A deep agent's built-in filesystem is scratch space for *this run* — it's not a
knowledge base. Long-horizon tasks often need to ground answers in a real, persistent
document collection (RAG, Phase 3-4) too, and eventually need to run as one step inside a
larger, explicitly-controlled system (LangGraph, Phase 6). Neither is a special case —
both just mean giving the deep agent the right tool, or making the deep agent itself a
node.

## Concept

**Deep Agents + RAG:** a retriever is just another `@tool` in the `tools=` list — nothing
deep-agent-specific about it. Reusing the small in-code Chroma pattern from Phase 0 Topic
06 / Phase 2 Topic 06:

```python
from langchain_chroma import Chroma

vector_store = Chroma.from_documents(documents, embedding=embeddings)

@tool
def search_knowledge_base(query: str) -> str:
    """Search the internal knowledge base for relevant background."""
    results = vector_store.similarity_search(query, k=2)
    return "\n".join(doc.page_content for doc in results)

agent = create_deep_agent(model=model, tools=[search_knowledge_base])
```

The deep agent now decides *when* to retrieve (Phase 5's "agentic RAG" idea) exactly like
it decides when to call any other tool — combined with Topic 04's filesystem, it can also
save retrieved passages to a file rather than keep them live in every subsequent turn.

**Deep Agents + LangGraph:** because `create_deep_agent` returns a compiled LangGraph
graph (Topic 02), it can be wrapped as a single node inside a larger `StateGraph` (Phase
6) — e.g. a graph that classifies a request, routes "research" requests to a deep agent
node, and routes everything else down a simpler path. This file only sketches that
composition (illustrative, commented) since Phase 6 owns real `StateGraph` code:

```python
# Illustrative only - Phase 6 owns real LangGraph code:
# def deep_agent_node(state):
#     result = deep_research_agent.invoke({"messages": state["messages"]})
#     return {"messages": result["messages"]}
#
# graph.add_node("research", deep_agent_node)   # the deep agent IS one node
```

## Minimal code

`code.py` builds a tiny in-memory Chroma store (reusing the Phase 2 Topic 06 pattern),
wraps it as a retriever tool, gives it to a `create_deep_agent`, and asks a question that
should trigger retrieval — then prints which tool the agent chose to make the "just
another tool" point concrete.

## Production notes

Keep the retriever tool's docstring specific ("search the internal knowledge base for
policy/product info") so the model doesn't confuse it with a general web-search tool when
both are present — same lesson as Phase 1 Topic 05's tool-description guidance, still
true here.

## Debugging

If the agent never calls the retriever tool, check whether the question actually needs
information only the vector store has — models correctly skip retrieval when their own
knowledge (or another available tool) already answers the question, which is the *right*
agentic-RAG behavior (Phase 5), not a bug.

## Mini challenge

Add both a retriever tool and a web-search tool to the same deep agent, ask a question
that needs one but not the other, and confirm the agent picks correctly without being
told which to use.
