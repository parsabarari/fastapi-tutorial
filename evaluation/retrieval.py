def calculate_retrieval_metrics(
    retrieved: list[str],
    relevant: list[str],
) -> dict[str, float]:
    """Calculate precision and recall for retrieved documents."""
    retrieved_set = set(retrieved)
    relevant_set = set(relevant)

    true_positives = len(retrieved_set & relevant_set)
    false_positives = len(retrieved_set - relevant_set)
    false_negatives = len(relevant_set - retrieved_set)

    precision = (
        true_positives / (true_positives + false_positives)
        if retrieved_set
        else 0.0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if relevant_set
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
    }
