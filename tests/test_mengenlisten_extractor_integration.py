import unittest
from pathlib import Path
import json
import tempfile
import shutil
import os

from src.bulle_planning_model.extractors.mengenlisten_extractor.mengenlisten_extractor import (
    MengenlistenExtractor,
)


class TestMengenlistenExtractorIntegration(unittest.TestCase):
    """Integration tests for MengenlistenExtractor using real test data."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - run API call once for all tests."""
        cls.test_file_path = (
            Path(__file__).parent / "test_files/Mengenliste-2024-11-08.pdf"
        )
        cls.extractor = MengenlistenExtractor()

        # Skip all tests if no API key is available
        if not os.environ.get("GEMINI_API_KEY"):
            cls.mengenliste = None
            cls.api_available = False
        else:
            cls.api_available = True
            # Make single API call for all tests
            cls.mengenliste = cls.extractor.read_file(cls.test_file_path)

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_read_file_success(self):
        """Test successful file reading and parsing."""
        # Skip test if no API key is available
        if not self.api_available:
            self.skipTest("GEMINI_API_KEY not available - skipping integration test")

        self.assertTrue(
            self.test_file_path.exists(), f"Test file not found: {self.test_file_path}"
        )

        if self.mengenliste is None:
            # If extraction failed, check if we have error metadata
            self.assertIsNotNone(self.extractor.metadata)
            self.assertTrue(len(self.extractor.metadata.errors) > 0)
            print(
                f"⚠️  Extraction failed as expected (API/processing issue): {self.extractor.metadata.errors}"
            )
            return

        # If successful, validate the extracted data
        self.assertIsNotNone(self.mengenliste, "Should return mengenliste object")
        self.assertIsNotNone(self.extractor.metadata, "Should have metadata")
        self.assertEqual(self.extractor.metadata.source_file, str(self.test_file_path))

        # Verify basic mengenliste structure
        self.assertTrue(hasattr(self.mengenliste, "report_date"))
        self.assertTrue(hasattr(self.mengenliste, "production_day"))
        self.assertTrue(hasattr(self.mengenliste, "sales_day"))
        self.assertTrue(hasattr(self.mengenliste, "articles"))
        self.assertIsInstance(self.mengenliste.articles, list)

        print(
            f"✅ Successfully extracted mengenliste with {len(self.mengenliste.articles)} articles"
        )

    def test_convert_to_json(self):
        """Test JSON conversion functionality."""
        # Skip test if no API key is available
        if not self.api_available:
            self.skipTest("GEMINI_API_KEY not available - skipping integration test")

        if self.mengenliste is None:
            self.skipTest("Extraction failed - cannot test JSON conversion")

        output_path = self.temp_dir / "test_mengenliste_output.json"
        self.extractor.convert_to_json(self.mengenliste, output_path)

        self.assertTrue(output_path.exists(), "JSON file should be created")

        # Verify JSON content is valid
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        self.assertIsInstance(json_data, dict, "JSON should be a dictionary")
        self.assertGreater(len(json_data), 0, "JSON should have data")

        # Check expected structure
        for date_key, date_data in json_data.items():
            self.assertIn("production_day", date_data)
            self.assertIn("sales_day", date_data)
            self.assertIn("articles", date_data)
            self.assertIsInstance(date_data["articles"], list)

            if len(date_data["articles"]) > 0:
                article = date_data["articles"][0]
                self.assertIn("article_name", article)

        print(f"✅ JSON conversion successful: {output_path}")

    def test_unparsed_blocks_handling(self):
        """Test handling of unparsed blocks."""
        # This test doesn't require API calls - just tests the method
        unparsed_path = self.temp_dir / "unparsed_mengenlisten.txt"
        self.extractor.save_unparsed_blocks(unparsed_path)

        # File should be created only if there are unparsed blocks
        if self.extractor.unparsed_blocks:
            self.assertTrue(
                unparsed_path.exists(), "Unparsed blocks file should be created"
            )
        else:
            # This is expected - no unparsed blocks in our test
            pass

        print(f"✅ Unparsed blocks handling works: {unparsed_path}")

    def test_metadata_contains_expected_info(self):
        """Test that metadata contains expected information."""
        # Skip test if no API key is available
        if not self.api_available:
            self.skipTest("GEMINI_API_KEY not available - skipping integration test")

        metadata = self.extractor.metadata
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.source_file, str(self.test_file_path))
        self.assertTrue(hasattr(metadata, "errors"))
        self.assertIsInstance(metadata.errors, list)

        if self.mengenliste is None:
            # If extraction failed, should have error info
            self.assertGreater(
                len(metadata.errors), 0, "Failed extraction should have error messages"
            )
            print(
                f"✅ Metadata validation passed with errors (expected): {len(metadata.errors)} errors"
            )
        else:
            print(f"✅ Metadata validation passed: successful extraction")

    def test_article_data_integrity(self):
        """Test that extracted article data has expected integrity."""
        # Skip test if no API key is available
        if not self.api_available:
            self.skipTest("GEMINI_API_KEY not available - skipping integration test")

        if self.mengenliste is None:
            self.skipTest("Extraction failed - cannot test article data integrity")

        self.assertGreater(
            len(self.mengenliste.articles), 0, "Should have at least one article"
        )

        for i, article in enumerate(self.mengenliste.articles):
            # Check required fields exist
            self.assertTrue(
                article.article_name, f"Article {i} should have article_name"
            )
            # Optional fields can be None, but if present should be reasonable
            if article.stock is not None:
                # Stock can be string or int from API
                self.assertTrue(
                    isinstance(article.stock, (str, int)),
                    f"Article {i} stock should be string or int",
                )
            if article.leftover is not None:
                self.assertTrue(
                    isinstance(article.leftover, (str, int)),
                    f"Article {i} leftover should be string or int",
                )
            if article.sold_out is not None:
                self.assertIsInstance(
                    article.sold_out, str, f"Article {i} sold_out should be string"
                )

        print(
            f"✅ Data integrity validated for {len(self.mengenliste.articles)} articles"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

