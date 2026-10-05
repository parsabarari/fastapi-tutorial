from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from dependencies import get_pinecone_index, model


class PineconeRetriever(BaseRetriever):
    top_k: int = 3
    score_threshold: float = 0.5

    def _get_relevant_documents(
        self,
        query: str,
    ) -> list[Document]:
        query_vector = model.encode(query).tolist()

        index = get_pinecone_index()

        results = index.query(
            vector=query_vector,
            top_k=self.top_k,
            include_metadata=True,
        )

        matches = results.to_dict()["matches"]

        documents: list[Document] = []

        for match in matches:
            metadata = match.get("metadata", {})
            score = match.get("score", 0.0)

            if "text" not in metadata:
                continue

            if score < self.score_threshold:
                continue

            documents.append(
                Document(
                    page_content=metadata["text"],
                    metadata={
                        "id": match["id"],
                        "source": metadata.get("source"),
                        "score": score,
                    },
                )
            )

        return documents