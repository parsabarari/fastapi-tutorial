from sentence_transformers import SentenceTransformer
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt


model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "I forgot my password.",
    "How can I reset my password?",
    "I cannot log into my account.",
    "I lost access to my account.",
    "The password reset link expired.",

    "The weather is sunny.",
    "It will rain tomorrow.",
    "Today's temperature is high.",

    "FastAPI is a Python framework.",
    "Django is a web framework.",
    "Python is a programming language.",
    ]

embeddings = model.encode(sentences)

projection = TSNE(
    n_components=2,
    random_state=42,
    perplexity=2,
).fit_transform(embeddings)

plt.scatter(projection[:, 0], projection[:, 1])

for i, text in enumerate(sentences):
    plt.annotate(text, projection[i])

plt.show()