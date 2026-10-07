from evaluation.dataset import EVALUATION_DATA
from evaluation.generation import calculate_bleu
from evaluation.retrieval import calculate_retrieval_metrics


def run_evaluation(
    evaluation_data: list[dict],
) -> dict[str, float]:
    """Run retrieval and generation evaluation."""
    precision_scores = []
    recall_scores = []
    bleu_scores = []

    for example in evaluation_data:
        retrieval_metrics = calculate_retrieval_metrics(
            retrieved=example["retrieved"],
            relevant=example["relevant"],
        )

        bleu_score = calculate_bleu(
            reference=example["reference"],
            generated=example["generated"],
        )

        precision_scores.append(retrieval_metrics["precision"])
        recall_scores.append(retrieval_metrics["recall"])
        bleu_scores.append(bleu_score)

    return {
        "precision": sum(precision_scores) / len(precision_scores),
        "recall": sum(recall_scores) / len(recall_scores),
        "bleu": sum(bleu_scores) / len(bleu_scores),
    }


if __name__ == "__main__":
    results = run_evaluation(EVALUATION_DATA)

    print("Evaluation Results")
    print("------------------")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall:    {results['recall']:.4f}")
    print(f"BLEU:      {results['bleu']:.4f}")