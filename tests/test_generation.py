from evaluation.generation import calculate_bleu


def test_identical_answers_have_perfect_bleu():
    text = "FastAPI is a Python web framework."

    score = calculate_bleu(text, text)

    assert score == 1.0
