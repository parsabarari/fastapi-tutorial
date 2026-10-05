from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import get_settings

from .prompts import rag_prompt
from .retriever import PineconeRetriever


settings = get_settings()

def format_documents(documents: list[Document]) -> str:
    return "\n\n".join(
        document.page_content
        for document in documents
    )


retriever = PineconeRetriever(
    top_k=3,
    score_threshold=0.5,
)

llm = ChatOpenAI(
    model=settings.openai_model,
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key,
)

parser = StrOutputParser()


rag_chain = (
    {
        "context": retriever | format_documents,
        "question": RunnablePassthrough(),
    }
    | rag_prompt
    | llm
    | parser
)