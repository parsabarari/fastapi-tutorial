from langchain_core.prompts import ChatPromptTemplate


rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a customer support assistant.

Use the following context to answer the question.

If the answer cannot be found in the context,
say that you don't have enough information.

Context:
{context}
""",
        ),
        (
            "human",
            "{question}",
        ),
    ]
)