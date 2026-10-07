from nltk.translate.bleu_score import (
    SmoothingFunction,
    sentence_bleu,
)


def calculate_bleu(
    reference: str,
    generated: str,
) -> float:
    """Calculate sentence-level BLEU score."""
    reference_tokens = reference.lower().split()
    generated_tokens = generated.lower().split()

    return sentence_bleu(
        [reference_tokens],
        generated_tokens,
        weights=(0.25, 0.25, 0.25, 0.25),
        smoothing_function=SmoothingFunction().method1,
    )