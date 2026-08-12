from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from backend.extraction import ExtractionDraft, ExtractedFieldDraft
from backend.main import app, get_extraction_provider, get_vector_index
from backend.schemas import SearchResult


def blank_pdf() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


class ApiTestCase(unittest.TestCase):
    client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_extraction_status_does_not_expose_api_key(self):
        with patch.dict(
            "os.environ",
            {
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "secret-value",
                "GEMINI_EXTRACTION_MODEL": "gemini-test",
            },
            clear=False,
        ):
            response = self.client.get("/api/extraction/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"provider": "gemini", "model": "gemini-test", "configured": True},
        )
        self.assertNotIn("secret-value", response.text)

    def test_parses_pdf_and_preserves_page_number(self):
        response = self.client.post(
            "/api/documents/parse",
            files=[("files", ("paper.pdf", blank_pdf(), "application/pdf"))],
        )
        self.assertEqual(response.status_code, 200)
        document = response.json()["documents"][0]
        self.assertEqual(document["filename"], "paper.pdf")
        self.assertEqual(document["title"], "paper")
        self.assertEqual(document["page_count"], 1)
        self.assertFalse(document["has_extractable_text"])
        self.assertEqual(document["chunk_count"], 0)
        self.assertEqual(document["chunks"], [])
        self.assertEqual(document["pages"][0]["page_number"], 1)

    def test_rejects_non_pdf_content(self):
        response = self.client.post(
            "/api/documents/parse",
            files=[("files", ("fake.pdf", b"not a pdf", "application/pdf"))],
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("不是有效的 PDF", response.json()["detail"])

    def test_search_endpoint_returns_traceable_results(self):
        class FakeIndex:
            def search(self, query, top_k, document_ids):
                self.arguments = (query, top_k, document_ids)
                return [
                    SearchResult(
                        document_id="doc-a",
                        filename="paper.pdf",
                        page_number=3,
                        chunk_index=4,
                        text="ZnO was annealed at 500 °C.",
                        score=0.91,
                    )
                ]

        fake = FakeIndex()
        app.dependency_overrides[get_vector_index] = lambda: fake
        try:
            response = self.client.post(
                "/api/retrieval/search",
                json={"query": "ZnO 退火溫度", "top_k": 3, "document_ids": ["doc-a"]},
            )
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.arguments, ("ZnO 退火溫度", 3, ["doc-a"]))
        self.assertEqual(response.json()["results"][0]["page_number"], 3)

    def test_search_rejects_empty_query(self):
        response = self.client.post("/api/retrieval/search", json={"query": ""})
        self.assertEqual(response.status_code, 422)

    def test_extraction_endpoint_returns_verified_structure(self):
        class FakeIndex:
            def search(self, query, top_k, document_ids):
                return [
                    SearchResult(
                        document_id="doc-a",
                        filename="paper.pdf",
                        page_number=2,
                        chunk_index=1,
                        text="The bandgap is 3.2 eV.",
                        score=0.9,
                    )
                ]

        class FakeProvider:
            def extract(self, fields, evidence):
                return ExtractionDraft(
                    fields=[
                        ExtractedFieldDraft(
                            field="能隙",
                            value="3.2",
                            unit="eV",
                            confidence="high",
                            evidence_ids=[evidence[0].evidence_id],
                        )
                    ]
                )

        app.dependency_overrides[get_vector_index] = FakeIndex
        app.dependency_overrides[get_extraction_provider] = FakeProvider
        try:
            response = self.client.post(
                "/api/extraction/run",
                json={"document_ids": ["doc-a"], "fields": ["能隙"], "top_k": 3},
            )
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200)
        field = response.json()["documents"][0]["fields"][0]
        self.assertEqual(field["value"], "3.2")
        self.assertEqual(field["citations"][0]["page_number"], 2)


if __name__ == "__main__":
    unittest.main()
