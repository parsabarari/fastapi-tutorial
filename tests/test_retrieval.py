from evaluation.retrieval import calculate_retrieval_metrics


def test_retrieval_metrics():
    retrieved = ["doc1", "doc2", "doc3", "doc4"]
    relevant = ["doc1", "doc3", "doc5"]

    metrics = calculate_retrieval_metrics(
        retrieved,
        relevant,
    )

    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 2 / 3
