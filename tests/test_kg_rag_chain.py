import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from src.chain import kg_rag_chain


@pytest.mark.asyncio
async def test_kg_rag_chain_returns_answer_and_exact_source_documents(monkeypatch) -> None:
    retrieved_docs = [
        Document(
            page_content="Retrieved context",
            metadata={"chunk_id": "chunk-1", "source_file": "notes.pdf"},
        )
    ]
    retrieval_calls: list[str] = []

    def retrieve(question: str) -> list[Document]:
        retrieval_calls.append(question)
        return retrieved_docs

    monkeypatch.setattr(
        kg_rag_chain,
        "get_kg_retriever",
        lambda **_kwargs: RunnableLambda(retrieve),
    )
    monkeypatch.setattr(
        kg_rag_chain,
        "build_tutor_prompt",
        lambda: RunnableLambda(lambda inputs: inputs["context"]),
    )
    monkeypatch.setattr(
        kg_rag_chain,
        "get_llm",
        lambda _temperature: RunnableLambda(lambda prompt: f"answer using {prompt}"),
    )

    chain = kg_rag_chain.build_kg_rag_chain(
        chroma_collection="course_scope",
        graph_scope="course_scope",
    )

    result = await chain.ainvoke({"question": "what is this?"})

    assert retrieval_calls == ["what is this?"]
    assert result["source_documents"] == retrieved_docs
    assert result["answer"] == "answer using [Source 1: notes.pdf]\nRetrieved context"
