import unittest

from backend.extraction import (
    EvidenceItem,
    ExtractionDraft,
    ExtractionService,
    ExtractedFieldDraft,
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


if __name__ == "__main__":
    unittest.main()
