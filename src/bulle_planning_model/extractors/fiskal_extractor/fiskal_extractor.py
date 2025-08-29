from typing import Generator, Optional, List
from pathlib import Path
import json
import re
from datetime import datetime
from decimal import Decimal
from loguru import logger
import chardet

from extractors.fiskal_extractor.transaction import Transaction
from extractors.fiskal_extractor.metadata import ExtractMetadata
from extractors.fiskal_extractor.line_item import LineItem


class FiskalExtractor:
    def __init__(self):
        self.metadata: Optional[ExtractMetadata] = None
        self.unparsed_blocks: List[List[str]] = []

    def read_file(self, file_path: Path) -> List[Transaction]:
        transactions = list(self._parse_transactions(file_path))

        self.metadata = ExtractMetadata(
            source_file=str(file_path), total_transactions=len(transactions)
        )

        return transactions

    def convert_to_json(
        self, transactions: List[Transaction], output_path: Path
    ) -> None:
        json_data = []

        for transaction in transactions:
            transaction_dict = {
                "UUID": transaction.uuid,
                "date": transaction.date.strftime("%Y-%m-%d"),
                "time": transaction.date.strftime("%H:%M:%S"),
                "bill_number": str(transaction.bill_number),
                "sales": [
                    {
                        "article": {
                            "article_name": item.article_name,
                            "article_number": str(item.article_number),
                            "quantity": str(item.quantity),
                            "category": item.category,
                            "category_number": str(item.category_number),
                            "price": str(item.price),
                        }
                    }
                    for item in transaction.items
                ],
                "sum": str(transaction.total_gross),
            }
            json_data.append(transaction_dict)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(json_data)} transactions to {output_path}")
    
    def save_unparsed_blocks(self, output_path: Path) -> None:
        if not self.unparsed_blocks:
            logger.info("No unparsed blocks to save")
            return
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Unparsed Transaction Blocks ({len(self.unparsed_blocks)} total)\n")
            f.write("=" * 60 + "\n\n")
            
            for i, block in enumerate(self.unparsed_blocks, 1):
                f.write(f"Block {i}:\n")
                f.write("-" * 20 + "\n")
                for line in block:
                    f.write(f"{line}\n")
                f.write("\n" + "=" * 60 + "\n\n")
        
        logger.info(f"Saved {len(self.unparsed_blocks)} unparsed blocks to {output_path}")

    def _parse_transactions(
        self, file_path: Path
    ) -> Generator[Transaction, None, None]:
        logger.info(f"Starting extraction from {file_path}")

        current_block_lines = []
        inside_transaction = False
        transaction_count = 0

        # Detect file encoding
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding'] or 'utf-8'
            logger.debug(f"Detected encoding: {encoding} (confidence: {encoding_result['confidence']})")

        try:
            with open(file_path, "r", encoding=encoding) as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()

                    if line.startswith("Rechnung (#"):
                        inside_transaction = True
                        current_block_lines = [line]
                        logger.debug(f"Found transaction start at line {line_num}")
                        continue

                    if inside_transaction and line.startswith("Signatur: "):
                        current_block_lines.append(line)
                        try:
                            transaction = self._parse_transaction_block(
                                current_block_lines
                            )
                            transaction_count += 1
                            logger.debug(
                                f"Successfully parsed transaction {transaction.uuid}"
                            )
                            yield transaction
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse transaction at line {line_num}: {e}"
                            )
                            self.unparsed_blocks.append(current_block_lines.copy())

                        current_block_lines = []
                        inside_transaction = False
                        continue

                    if inside_transaction:
                        current_block_lines.append(line)

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

        logger.info(f"Extraction complete. Found {transaction_count} transactions")
        if self.unparsed_blocks:
            logger.warning(f"Found {len(self.unparsed_blocks)} unparsed transaction blocks")

    def _parse_transaction_block(self, lines: List[str]) -> Transaction:
        uuid = self._extract_uuid(lines)
        date = self._extract_date(lines)
        bill_number = self._extract_bill_number(lines)
        items = self._extract_items(lines)
        total_gross = self._extract_total_gross(lines)

        return Transaction(
            uuid=uuid,
            date=date,
            bill_number=bill_number,
            items=items,
            total_gross=total_gross,
        )

    def _extract_uuid(self, lines: List[str]) -> str:
        for line in lines:
            if line.startswith("UUID: "):
                return line.split("UUID: ")[1]
        raise ValueError("UUID not found in transaction block")

    def _extract_date(self, lines: List[str]) -> datetime:
        for line in lines:
            if "Rechnung (#" in line:
                date_match = re.search(
                    r"(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})$", line
                )
                if date_match:
                    date_str = date_match.group(1)
                    return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        raise ValueError("Date not found in transaction block")

    def _extract_bill_number(self, lines: List[str]) -> int:
        for line in lines:
            if line.startswith("Rechnung (#"):
                bill_match = re.search(r"Rechnung \(#(\d+)\)", line)
                if bill_match:
                    return int(bill_match.group(1))
        raise ValueError("Bill number not found in transaction block")

    def _extract_items(self, lines: List[str]) -> List[LineItem]:
        items = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for item lines like "0.5x Roggenmischbrot (#71)                                                2,45"
            item_match = re.match(
                r"^(\d+(?:\.\d+)?)x\s+(.+?)\s+\(#(\d+)\)\s+(\d+,\d+)$", line
            )
            if item_match:
                quantity = Decimal(item_match.group(1).replace(",", "."))
                article_name = item_match.group(2)
                article_number = int(item_match.group(3))
                price = Decimal(item_match.group(4).replace(",", "."))

                # Look for category in next line
                category = "Unknown"
                category_number = 0
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    category_match = re.match(
                        r"^\s*Warengruppe:\s+(.+?)\s+\(#(\d+)\)$", next_line
                    )
                    if category_match:
                        category = category_match.group(1)
                        category_number = int(category_match.group(2))

                items.append(
                    LineItem(
                        article_number=article_number,
                        article_name=article_name,
                        quantity=quantity,
                        category=category,
                        category_number=category_number,
                        price=price,
                    )
                )

            i += 1

        return items

    def _extract_total_gross(self, lines: List[str]) -> Decimal:
        for line in lines:
            if "Summe Brutto" in line:
                # Only match positive amounts - excludes cancellations, refunds, and negative transactions
                total_match = re.search(r"Summe Brutto\s+(\d+,\d+)", line)
                if total_match:
                    return Decimal(total_match.group(1).replace(",", "."))
        raise ValueError("Total gross not found in transaction block")
