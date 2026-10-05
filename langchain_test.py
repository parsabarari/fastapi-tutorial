
from rag.chain import rag_chain


question = "What is FastAPI?"


answer = rag_chain.invoke(question)

print(answer)