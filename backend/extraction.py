from collections.abc import Sequence
import os
from typing import Protocol

from pydantic import BaseModel, Field

from .schemas import Citation, DocumentExtraction, ExtractedField, SearchResult


class ExtractionConfigurationError(RuntimeError):
    pass


class EvidenceItem(BaseModel):
    evidence_id: str
    field: str
    result: SearchResult


class ExtractedFieldDraft(BaseModel):
    field: str
    value: str | None
    unit: str | None
    confidence: str = Field(pattern="^(high|medium|low|not_found)$")
    evidence_ids: list[str]


class ExtractionDraft(BaseModel):
    fields: list[ExtractedFieldDraft]


class ExtractionProvider(Protocol):
    def extract(
        self,
        fields: Sequence[str],
        evidence: Sequence[EvidenceItem],
    ) -> ExtractionDraft: ...


class OpenAIExtractionProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-5.6-luna")
        self._client = None

    def extract(
        self,
        fields: Sequence[str],
        evidence: Sequence[EvidenceItem],
    ) -> ExtractionDraft:
        if not self.api_key:
            raise ExtractionConfigurationError(
                "尚未設定 OPENAI_API_KEY，無法執行 LLM 欄位擷取。"
            )
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)

        evidence_text = "\n\n".join(
            f"[{item.evidence_id}] field={item.field}; file={item.result.filename}; "
            f"page={item.result.page_number}\n{item.result.text}"
            for item in evidence
        )
        response = self._client.responses.parse(
            model=self.model,
            instructions=(
                "You extract material-science facts only from supplied evidence. "
                "Return every requested field exactly once. Never infer a missing value. "
                "If evidence is insufficient, set value and unit to null, confidence to "
                "not_found, and evidence_ids to an empty list. Only cite provided evidence IDs."
            ),
            input=f"Requested fields: {list(fields)}\n\nEvidence:\n{evidence_text}",
            text_format=ExtractionDraft,
            store=False,
        )
        if response.output_parsed is None:
            raise RuntimeError("LLM 未回傳可解析的結構化結果。")
        return response.output_parsed


class ExtractionService:
    def __init__(self, index, provider: ExtractionProvider) -> None:
        self.index = index
        self.provider = provider

    def extract_document(
        self,
        document_id: str,
        fields: list[str],
        top_k: int,
    ) -> DocumentExtraction:
        evidence = []
        filename = "未知文件"
        counter = 1
        for field in fields:
            results = self.index.search(field, top_k, [document_id])
            for result in results:
                filename = result.filename
                evidence.append(
                    EvidenceItem(
                        evidence_id=f"E{counter}",
                        field=field,
                        result=result,
                    )
                )
                counter += 1

        draft = self.provider.extract(fields, evidence)
        evidence_by_id = {item.evidence_id: item.result for item in evidence}
        drafts_by_field = {item.field: item for item in draft.fields if item.field in fields}
        extracted = []
        for field in fields:
            item = drafts_by_field.get(field)
            if item is None:
                extracted.append(
                    ExtractedField(
                        field=field,
                        value=None,
                        unit=None,
                        confidence="not_found",
                        citations=[],
                    )
                )
                continue
            citations = []
            seen = set()
            for evidence_id in item.evidence_ids:
                result = evidence_by_id.get(evidence_id)
                if result is None or evidence_id in seen:
                    continue
                seen.add(evidence_id)
                citations.append(
                    Citation(
                        filename=result.filename,
                        page_number=result.page_number,
                        chunk_index=result.chunk_index,
                        text=result.text,
                        score=result.score,
                    )
                )
            value = item.value if citations else None
            extracted.append(
                ExtractedField(
                    field=field,
                    value=value,
                    unit=item.unit if value is not None else None,
                    confidence=item.confidence if value is not None else "not_found",
                    citations=citations,
                )
            )
        return DocumentExtraction(
            document_id=document_id,
            filename=filename,
            fields=extracted,
        )
