import math
import unittest
from uuid import uuid4

import chromadb

from backend.schemas import ChunkResult, DocumentResult, PageResult
from backend.vector_index import VectorIndex, document_id_for


class KeywordEmbedder:
    terms = ("zno", "tio2", "anneal", "bandgap")

    def encode(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vector = [float(lowered.count(term)) for term in self.terms]
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


def document() -> DocumentResult:
    chunks = [
        ChunkResult(
            chunk_index=0,
            page_number=2,
            text="ZnO films were annealed at 500 °C.",
            character_count=35,
        ),
        ChunkResult(
            chunk_index=1,
            page_number=4,
            text="The TiO2 bandgap was measured optically.",
            character_count=42,
        ),
    ]
    return DocumentResult(
        filename="paper.pdf",
        page_count=4,
        character_count=77,
        has_extractable_text=True,
        pages=[PageResult(page_number=2, text=chunks[0].text, character_count=35)],
        chunk_count=2,
        chunks=chunks,
    )


class VectorIndexTestCase(unittest.TestCase):
    def setUp(self):
        self.index = VectorIndex(
            client=chromadb.EphemeralClient(),
            embedder=KeywordEmbedder(),
            collection_name=f"test_{uuid4().hex}",
        )

    def test_indexes_searches_and_preserves_citation_metadata(self):
        indexed = self.index.index_document("doc-a", document())
        self.assertEqual(indexed.status, "indexed")
        self.assertEqual(indexed.chunk_count, 2)

        result = self.index.search("ZnO anneal", top_k=1)[0]
        self.assertEqual(result.document_id, "doc-a")
        self.assertEqual(result.filename, "paper.pdf")
        self.assertEqual(result.page_number, 2)
        self.assertEqual(result.chunk_index, 0)
        self.assertGreater(result.score, 0.9)

    def test_duplicate_document_is_not_indexed_twice(self):
        self.index.index_document("doc-a", document())
        duplicate = self.index.index_document("doc-a", document())
        self.assertEqual(duplicate.status, "unchanged")
        self.assertEqual(self.index.collection.count(), 2)

    def test_filters_and_deletes_by_document_id(self):
        self.index.index_document("doc-a", document())
        self.index.index_document("doc-b", document().model_copy(update={"filename": "other.pdf"}))
        results = self.index.search("bandgap", top_k=5, document_ids=["doc-b"])
        self.assertTrue(results)
        self.assertEqual({result.document_id for result in results}, {"doc-b"})
        self.assertEqual(self.index.delete_document("doc-a"), 2)
        self.assertEqual(self.index.delete_document("doc-a"), 0)
        self.assertEqual(self.index.collection.count(), 2)

    def test_content_hash_is_stable(self):
        self.assertEqual(document_id_for(b"pdf"), document_id_for(b"pdf"))
        self.assertNotEqual(document_id_for(b"pdf"), document_id_for(b"other"))


if __name__ == "__main__":
    unittest.main()
