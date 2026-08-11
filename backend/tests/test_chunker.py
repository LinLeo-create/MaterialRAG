import unittest

from backend.chunker import chunk_pages, normalize_page_text
from backend.schemas import PageResult


def page(number: int, text: str) -> PageResult:
    return PageResult(page_number=number, text=text, character_count=len(text))


class ChunkerTestCase(unittest.TestCase):
    def test_normalizes_wrapped_lines_and_keeps_paragraphs(self):
        text = "The bandgap of ZnO is\n3.2 eV.\n\n製程溫度為 500 °C。"
        self.assertEqual(
            normalize_page_text(text),
            "The bandgap of ZnO is 3.2 eV.\n\n製程溫度為 500 °C。",
        )

    def test_chunks_never_cross_page_boundaries(self):
        chunks = chunk_pages(
            [page(1, "ZnO " * 80), page(2, "TiO2 " * 80)],
            chunk_size=120,
            overlap=20,
        )
        self.assertGreater(len(chunks), 2)
        self.assertEqual({chunk.page_number for chunk in chunks}, {1, 2})
        self.assertTrue(all("ZnO" in chunk.text for chunk in chunks if chunk.page_number == 1))
        self.assertTrue(all("TiO2" in chunk.text for chunk in chunks if chunk.page_number == 2))

    def test_assigns_stable_document_chunk_indexes(self):
        chunks = chunk_pages([page(3, "YBa2Cu3O7-delta " * 30)], chunk_size=140, overlap=20)
        self.assertEqual([chunk.chunk_index for chunk in chunks], list(range(len(chunks))))
        self.assertTrue(all(chunk.character_count <= 140 for chunk in chunks))

    def test_rejects_invalid_chunk_configuration(self):
        with self.assertRaises(ValueError):
            chunk_pages([], chunk_size=99)
        with self.assertRaises(ValueError):
            chunk_pages([], chunk_size=100, overlap=100)


if __name__ == "__main__":
    unittest.main()
