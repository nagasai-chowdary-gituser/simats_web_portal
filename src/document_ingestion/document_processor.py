
from langchain_community.document_loaders import (
    PyPDFLoader, 
    PyPDFDirectoryLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from typing import List
from langchain_core.documents import Document


class DocumentProcessor:

    def __init__(self, chunk_size=400, chunk_overlap=60):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def load_documents(self, sources: List[str]) -> List[Document]:
        docs = []
        for src in sources:
            path = Path(src)

            if path.is_dir():
                docs.extend(PyPDFDirectoryLoader(str(path)).load())

            elif path.suffix.lower() == ".pdf":
                docs.extend(PyPDFLoader(str(path)).load())

            elif path.suffix.lower() == ".txt":
                docs.extend(TextLoader(str(path)).load())

            else:
                raise ValueError(f"Unsupported format: {src}")

        return docs

    def process(self, sources: List[str]):
        docs = self.load_documents(sources)
        return self.splitter.split_documents(docs)
