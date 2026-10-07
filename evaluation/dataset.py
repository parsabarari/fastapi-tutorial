EVALUATION_DATA = [
    {
        "question": "What is FastAPI?",
        "retrieved": ["doc1", "doc3", "doc5"],
        "relevant": ["doc1", "doc2", "doc3"],
        "reference": "FastAPI is a Python web framework.",
        "generated": "FastAPI is a Python framework for building APIs.",
    },
    {
        "question": "What is RAG?",
        "retrieved": ["doc2", "doc4", "doc6"],
        "relevant": ["doc2", "doc4", "doc5"],
        "reference": "RAG combines retrieval with generation.",
        "generated": "RAG combines document retrieval with language model generation.",
    },
    {
        "question": "What is LangChain?",
        "retrieved": ["doc1", "doc4", "doc7"],
        "relevant": ["doc4", "doc7"],
        "reference": "LangChain is a framework for building applications with language models.",
        "generated": "LangChain is a framework for building applications with language models.",
    },
]