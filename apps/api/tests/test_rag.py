from apps.api.app.rag.index import LocalRAGIndex


def test_rag_retrieval_and_recall():
    rag = LocalRAGIndex("runbooks")
    assert len(rag.documents) >= 15

    # Test top-1 relevance for specific query
    results = rag.search("Payments database slow query pg_sleep latency", top_k=3)
    assert len(results) > 0
    top_hit = results[0]["id"]
    assert "payments-slow-db" in top_hit
