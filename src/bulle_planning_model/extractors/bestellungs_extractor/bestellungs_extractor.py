import csv
import json
from typing import Dict, List, Optional
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from loguru import logger
import chardet

from extractors.bestellungs_extractor.order import Order
from extractors.bestellungs_extractor.line_item import LineItem
from extractors.bestellungs_extractor.metadata import ExtractMetadata


class BestellungsExtractor:
    def __init__(self):
        self.metadata: Optional[ExtractMetadata] = None

    def _convert_price_to_euros(self, cents: int) -> Decimal:
        """Convert price from cents to euros"""
        return Decimal(cents) / Decimal(100)

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        with open(file_path, "rb") as file:
            raw_data = file.read(10000)
            result = chardet.detect(raw_data)
            return result["encoding"] or "utf-8"

    def read_file(self, file_path: Path) -> List[Order]:
        """Read CSV file and return list of Order objects"""
        logger.info(f"Processing orders from {file_path}")

        encoding = self._detect_encoding(file_path)
        orders_dict: Dict[str, Dict] = defaultdict(
            lambda: {"id": None, "pickup_date": None, "line_items": []}
        )

        with open(file_path, "r", encoding=encoding) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                order_id = row["id"]
                pickup_date = datetime.strptime(row["abholdatum"], "%Y-%m-%d").date()
                article_name = row["artikelname"]
                quantity = Decimal(row["artikelanzahl"])
                price_euros = self._convert_price_to_euros(int(row["artikelpreis"]))

                orders_dict[order_id]["id"] = order_id
                orders_dict[order_id]["pickup_date"] = pickup_date
                orders_dict[order_id]["line_items"].append(
                    LineItem(
                        article_name=article_name, quantity=quantity, price=price_euros
                    )
                )

        orders = []
        for order_data in orders_dict.values():
            total_sum = sum(
                item.price * item.quantity for item in order_data["line_items"]
            )
            order = Order(
                id=order_data["id"],
                pickup_date=order_data["pickup_date"],
                sales=order_data["line_items"],
                sum=total_sum,
            )
            orders.append(order)

        self.metadata = ExtractMetadata(
            source_file=str(file_path), total_orders=len(orders)
        )

        logger.info(f"Processed {len(orders)} orders")
        return orders

    def convert_to_json(self, orders: List[Order], output_path: Path) -> None:
        """Convert orders to JSON format and save to file"""
        json_data = {}

        for order in orders:
            json_data[order.id] = {
                "pickup_date": order.pickup_date.strftime("%Y-%m-%d"),
                "sales": [
                    {
                        "article_name": item.article_name,
                        "quantity": float(item.quantity),
                        "price": float(item.price),
                    }
                    for item in order.sales
                ],
                "sum": float(order.sum),
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON output saved to {output_path}")

