import unittest
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions, smoldocling_vlm_mlx_conversion_options
from docling.pipeline.vlm_pipeline import VlmPipeline

class TestDocLing(unittest.TestCase):

    def setUp(self):
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=VlmPipelineOptions(vlm_options=smoldocling_vlm_mlx_conversion_options),
                ),
                InputFormat.IMAGE: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=VlmPipelineOptions(vlm_options=smoldocling_vlm_mlx_conversion_options),
                ),
            }
        )
        self.test_pdf_path = Path("tests/data/pdf/2305.03393v1-pg9.pdf")

    def test_conversion_pdf(self):
        result = self.converter.convert(str(self.test_pdf_path))
        self.assertIsNotNone(result)
        self.assertTrue(result.document.num_pages() > 0)

    def test_conversion_output_formats(self):
        result = self.converter.convert(str(self.test_pdf_path))
        html_output = result.document.save_as_html(filename=Path("output.html"))
        json_output = result.document.save_as_json(Path("output.json"))
        markdown_output = result.document.save_as_markdown(Path("output.md"))

        self.assertTrue(Path("output.html").exists())
        self.assertTrue(Path("output.json").exists())
        self.assertTrue(Path("output.md").exists())

    def tearDown(self):
        for output_file in ["output.html", "output.json", "output.md"]:
            if Path(output_file).exists():
                Path(output_file).unlink()

if __name__ == '__main__':
    unittest.main()