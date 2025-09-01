import unittest
from pathlib import Path
import json
import tempfile
import shutil

from src.bulle_planning_model.extractors.fiskal_extractor.fiskal_extractor import (
    FiskalExtractor,
)


class TestFiskalExtractorIntegration(unittest.TestCase):
    """Integration tests for FiskalExtractor using real test data."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_file_path = Path(__file__).parent / "test_files/Fiskaljournal.txt"
        self.temp_dir = Path(tempfile.mkdtemp())
        self.extractor = FiskalExtractor()

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_read_file_success(self):
        """Test successful file reading and parsing."""
        self.assertTrue(
            self.test_file_path.exists(), f"Test file not found: {self.test_file_path}"
        )

        transactions = self.extractor.read_file(self.test_file_path)

        self.assertIsNotNone(transactions, "Should return transactions list")
        self.assertGreater(
            len(transactions), 0, "Should extract at least one transaction"
        )
        self.assertIsNotNone(self.extractor.metadata, "Should have metadata")
        self.assertEqual(self.extractor.metadata.source_file, str(self.test_file_path))

        # Verify basic transaction structure
        first_transaction = transactions[0]
        self.assertTrue(hasattr(first_transaction, "uuid"))
        self.assertTrue(hasattr(first_transaction, "date"))
        self.assertTrue(hasattr(first_transaction, "bill_number"))
        self.assertTrue(hasattr(first_transaction, "items"))
        self.assertTrue(hasattr(first_transaction, "total_gross"))

        print(f"✅ Successfully extracted {len(transactions)} transactions")

    def test_convert_to_json(self):
        """Test JSON conversion functionality."""
        transactions = self.extractor.read_file(self.test_file_path)
        self.assertIsNotNone(transactions)

        output_path = self.temp_dir / "test_output.json"
        self.extractor.convert_to_json(transactions, output_path)

        self.assertTrue(output_path.exists(), "JSON file should be created")

        # Verify JSON content is valid
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        self.assertIsInstance(json_data, list, "JSON should be a list of transactions")
        self.assertGreater(len(json_data), 0, "JSON should have data")

        # Check expected structure
        transaction = json_data[0]
        self.assertIn("UUID", transaction)
        self.assertIn("bill_number", transaction)
        self.assertIn("sales", transaction)
        self.assertIn("sum", transaction)

        print(f"✅ JSON conversion successful: {output_path}")

    def test_unparsed_blocks_handling(self):
        """Test handling of unparsed blocks."""
        transactions = self.extractor.read_file(self.test_file_path)
        self.assertIsNotNone(transactions)

        unparsed_path = self.temp_dir / "unparsed_blocks.txt"
        self.extractor.save_unparsed_blocks(unparsed_path)

        # File should be created only if there are unparsed blocks
        # Since our test file should parse successfully, no file is expected
        if self.extractor.unparsed_blocks:
            self.assertTrue(
                unparsed_path.exists(), "Unparsed blocks file should be created"
            )
        else:
            # This is expected - no unparsed blocks in our test file
            pass

        print(f"✅ Unparsed blocks handling works: {unparsed_path}")

    def test_metadata_contains_expected_info(self):
        """Test that metadata contains expected information."""
        transactions = self.extractor.read_file(self.test_file_path)
        self.assertIsNotNone(transactions)

        metadata = self.extractor.metadata
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.source_file, str(self.test_file_path))
        self.assertGreaterEqual(metadata.total_transactions, 0)
        self.assertTrue(hasattr(metadata, "errors"))
        self.assertIsInstance(metadata.errors, list)

        print(
            f"✅ Metadata validation passed: {metadata.total_transactions} transactions"
        )

    def test_transaction_data_integrity(self):
        """Test that extracted transaction data has expected integrity."""
        transactions = self.extractor.read_file(self.test_file_path)
        self.assertIsNotNone(transactions)
        self.assertGreater(len(transactions), 0)

        for i, transaction in enumerate(transactions):
            # Check required fields exist and have reasonable values
            self.assertTrue(transaction.uuid, f"Transaction {i} should have UUID")
            self.assertTrue(transaction.date, f"Transaction {i} should have date")
            self.assertIsNotNone(
                transaction.bill_number, f"Transaction {i} should have bill_number"
            )
            self.assertIsInstance(
                transaction.items, list, f"Transaction {i} items should be list"
            )

            # Check line items if any exist
            for j, item in enumerate(transaction.items):
                self.assertTrue(
                    item.article_name,
                    f"Transaction {i}, item {j} should have article_name",
                )
                self.assertIsNotNone(
                    item.quantity, f"Transaction {i}, item {j} should have quantity"
                )
                self.assertIsNotNone(
                    item.price, f"Transaction {i}, item {j} should have price"
                )

        print(f"✅ Data integrity validated for {len(transactions)} transactions")


if __name__ == "__main__":
    unittest.main(verbosity=2)

