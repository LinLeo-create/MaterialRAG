import unittest
from unittest.mock import patch

from backend.extraction import (
    EvidenceItem,
    ExtractionDraft,
    ExtractionService,
    ExtractedFieldDraft,
    GeminiExtractionProvider,
    OpenAIExtractionProvider,
    create_extraction_provider,
)
from backend.schemas import SearchResult


class FakeIndex:
    def search(self, query, top_k, document_ids):
        if query == "退火溫度":
            return [
                SearchResult(
                    document_id=document_ids[0],
                    filename="zno.pdf",
                    page_number=4,
                    chunk_index=7,
                    text="The ZnO films were annealed at 500 °C for 2 h.",
                    score=0.92,
                )
            ]
        return []


class FakeProvider:
    def extract(self, fields, evidence: list[EvidenceItem]):
        evidence_id = evidence[0].evidence_id
        return ExtractionDraft(
            fields=[
                ExtractedFieldDraft(
                    field="退火溫度",
                    value="500",
                    unit="°C",
                    confidence="high",
                    evidence_ids=[evidence_id],
                ),
                ExtractedFieldDraft(
                    field="能隙",
                    value=None,
                    unit=None,
                    confidence="not_found",
                    evidence_ids=[],
                ),
            ]
        )


class ExtractionServiceTestCase(unittest.TestCase):
    def test_extracts_value_with_verified_page_citation(self):
        result = ExtractionService(FakeIndex(), FakeProvider()).extract_document(
            "doc-a", ["退火溫度", "能隙"], 5
        )
        temperature = result.fields[0]
        self.assertEqual(temperature.value, "500")
        self.assertEqual(temperature.unit, "°C")
        self.assertEqual(temperature.citations[0].page_number, 4)
        self.assertEqual(result.fields[1].confidence, "not_found")

    def test_discards_value_when_llm_cites_unknown_evidence(self):
        class InvalidCitationProvider:
            def extract(self, fields, evidence):
                return ExtractionDraft(
                    fields=[
                        ExtractedFieldDraft(
                            field="退火溫度",
                            value="900",
                            unit="°C",
                            confidence="high",
                            evidence_ids=["invented"],
                        )
                    ]
                )

        result = ExtractionService(FakeIndex(), InvalidCitationProvider()).extract_document(
            "doc-a", ["退火溫度"], 5
        )
        self.assertIsNone(result.fields[0].value)
        self.assertEqual(result.fields[0].confidence, "not_found")
        self.assertEqual(result.fields[0].citations, [])


class GeminiProviderTestCase(unittest.TestCase):
    def test_parses_structured_gemini_response(self):
        class Models:
            def generate_content(self, **kwargs):
                self.arguments = kwargs
                return type(
                    "Response",
                    (),
                    {
                        "parsed": {
                            "fields": [
                                {
                                    "field": "能隙",
                                    "value": "3.2",
                                    "unit": "eV",
                                    "confidence": "high",
                                    "evidence_ids": ["E1"],
                                }
                            ]
                        },
                        "text": None,
                    },
                )()

        client = type("Client", (), {"models": Models()})()
        provider = GeminiExtractionProvider(client=client, model="gemini-test")
        draft = provider.extract(
            ["能隙"],
            [
                EvidenceItem(
                    evidence_id="E1",
                    field="能隙",
                    result=SearchResult(
                        document_id="doc-a",
                        filename="paper.pdf",
                        page_number=2,
                        chunk_index=1,
                        text="The bandgap is 3.2 eV.",
                        score=0.9,
                    ),
                )
            ],
        )
        self.assertEqual(draft.fields[0].value, "3.2")
        self.assertEqual(client.models.arguments["model"], "gemini-test")
        self.assertEqual(
            client.models.arguments["config"].response_mime_type,
            "application/json",
        )

    def test_requires_gemini_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = GeminiExtractionProvider()
            with self.assertRaisesRegex(Exception, "GEMINI_API_KEY"):
                provider.extract([], [])

    def test_factory_selects_configured_provider(self):
        self.assertIsInstance(create_extraction_provider("gemini"), GeminiExtractionProvider)
        self.assertIsInstance(create_extraction_provider("openai"), OpenAIExtractionProvider)
        with self.assertRaisesRegex(Exception, "不支援"):
            create_extraction_provider("unknown")


if __name__ == "__main__":
    unittest.main()
