# src/vectorstore/vectorstore.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone import ServerlessSpec
from src.config.config import Config


class VectorStore:

    def __init__(self):
        self.embedding = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self._ensure_index()
        self.index = self.pc.Index(Config.PINECONE_INDEX)
        self.retriever = None

    def _ensure_index(self):
        indexes = [i.name for i in self.pc.list_indexes()]
        if Config.PINECONE_INDEX not in indexes:
            self.pc.create_index(
                name=Config.PINECONE_INDEX,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

    def create_vectorstore(self, docs):
        PineconeVectorStore.from_documents(
            documents=docs,
            embedding=self.embedding,
            index_name=Config.PINECONE_INDEX
        )

        self.retriever = PineconeVectorStore.from_existing_index(
            index_name=Config.PINECONE_INDEX,
            embedding=self.embedding
        ).as_retriever(search_kwargs={"k": 6})

    def get_retriever(self):
        return self.retriever
