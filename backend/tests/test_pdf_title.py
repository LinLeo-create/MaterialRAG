import unittest

from backend.pdf_parser import infer_title


class PdfTitleTestCase(unittest.TestCase):
    def test_prefers_valid_metadata_title(self):
        self.assertEqual(
            infer_title(
                "download.pdf",
                "  Optical Properties of ZnO Thin Films  ",
                "Journal header\nA different visible heading",
            ),
            "Optical Properties of ZnO Thin Films",
        )

    def test_ignores_filename_like_metadata_and_uses_first_page(self):
        self.assertEqual(
            infer_title(
                "paper-123.pdf",
                "paper-123",
                "Synthesis and Characterization of TiO2\nNanostructured Thin Films\nJohn Doe",
            ),
            "Synthesis and Characterization of TiO2 Nanostructured Thin Films",
        )

    def test_falls_back_to_filename_when_no_text_exists(self):
        self.assertEqual(infer_title("my-paper.pdf", None, ""), "my-paper")


if __name__ == "__main__":
    unittest.main()
