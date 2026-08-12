from collections.abc import Sequence
from hashlib import sha256
import os
from pathlib import Path
from typing import Protocol

import chromadb

from .schemas import DocumentResult, IndexedDocument, SearchResult


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class BgeM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self.model_name = model_name
        self._model = None

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        embeddings = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()


def document_id_for(content: bytes) -> str:
    return sha256(content).hexdigest()


class VectorIndex:
    def __init__(
        self,
        client=None,
        embedder: Embedder | None = None,
        collection_name: str = "materialrag_chunks",
    ) -> None:
        if client is None:
            index_path = Path(os.getenv("MATERIALRAG_INDEX_PATH", "data/chroma"))
            index_path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(index_path))
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = embedder or BgeM3Embedder(
            os.getenv("MATERIALRAG_EMBEDDING_MODEL", "BAAI/bge-m3")
        )

    def index_document(
        self,
        document_id: str,
        document: DocumentResult,
    ) -> IndexedDocument:
        existing = self.collection.get(where={"document_id": document_id}, include=[])
        status = "unchanged" if existing["ids"] else "indexed"
        if status == "unchanged":
            return IndexedDocument(
                document_id=document_id,
                filename=document.filename,
                title=document.title,
                page_count=document.page_count,
                character_count=document.character_count,
                has_extractable_text=document.has_extractable_text,
                chunk_count=len(existing["ids"]),
                chunks=document.chunks,
                status=status,
            )

        if document.chunks:
            texts = [chunk.text for chunk in document.chunks]
            embeddings = self.embedder.encode(texts)
            self.collection.upsert(
                ids=[f"{document_id}:{chunk.chunk_index}" for chunk in document.chunks],
                documents=texts,
                embeddings=embeddings,
                metadatas=[
                    {
                        "document_id": document_id,
                        "filename": document.filename,
                        "title": document.title,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                    }
                    for chunk in document.chunks
                ],
            )
        return IndexedDocument(
            document_id=document_id,
            filename=document.filename,
            title=document.title,
            page_count=document.page_count,
            character_count=document.character_count,
            has_extractable_text=document.has_extractable_text,
            chunk_count=document.chunk_count,
            chunks=document.chunks,
            status=status,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        count = self.collection.count()
        if count == 0:
            return []
        where = None
        if document_ids:
            where = (
                {"document_id": document_ids[0]}
                if len(document_ids) == 1
                else {"document_id": {"$in": document_ids}}
            )
        response = self.collection.query(
            query_embeddings=self.embedder.encode([query]),
            n_results=min(top_k, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        results = []
        for text, metadata, distance in zip(
            response["documents"][0],
            response["metadatas"][0],
            response["distances"][0],
            strict=True,
        ):
            results.append(
                SearchResult(
                    document_id=metadata["document_id"],
                    filename=metadata["filename"],
                    page_number=metadata["page_number"],
                    chunk_index=metadata["chunk_index"],
                    text=text,
                    score=max(0.0, min(1.0, 1.0 - float(distance))),
                )
            )
        return results

    def delete_document(self, document_id: str) -> int:
        existing = self.collection.get(where={"document_id": document_id}, include=[])
        deleted = len(existing["ids"])
        if deleted:
            self.collection.delete(where={"document_id": document_id})
        return deleted
