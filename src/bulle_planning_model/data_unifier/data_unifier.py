from pathlib import Path
from typing import Dict, List, Tuple
from decimal import Decimal
from datetime import datetime
import json

from data_unifier.consolidated_product_data import ConsolidatedProductData
from data_unifier.master_article_data import MasterArticleData
from data_unifier.article_lookup_table import ArticleLookupTable
from extractors.fiskal_extractor.transaction import Transaction
from extractors.fiskal_extractor.line_item import LineItem
from extractors.mengenlisten_extractor.mengenliste import Mengenliste
from extractors.bestellungs_extractor.order import Order
from extractors.bestellungs_extractor.line_item import LineItem as BestellungLineItem


class DataUnifier:
    def __init__(self):
        self.lookup_table: ArticleLookupTable = self._load_lookup_table()

    def _load_lookup_table(self) -> ArticleLookupTable:
        return ArticleLookupTable.from_file()

    def unify_monthly_data(
        self, fiskal_extract_path: Path, mengenlisten_dir_path: Path, bestellungen_extract_path: Path = None
    ) -> Dict[str, ConsolidatedProductData]:
        with open(fiskal_extract_path, "r", encoding="utf-8") as f:
            transactions_data = json.load(f)

        transactions = self._parse_fiskal_transactions(transactions_data)

        fiskal_by_date = self._group_fiskal_by_date(transactions)

        mengenlisten_by_date = self._load_mengenlisten_directory(mengenlisten_dir_path)
        
        bestellungen_by_date = {}
        if bestellungen_extract_path and bestellungen_extract_path.exists():
            bestellungen_data = self._parse_bestellungen_data(bestellungen_extract_path)
            bestellungen_by_date = self._group_bestellungen_by_date(bestellungen_data)

        all_dates = set(fiskal_by_date.keys()) | set(mengenlisten_by_date.keys()) | set(bestellungen_by_date.keys())

        consolidated_data = {}
        for date_str in all_dates:
            date_transactions = fiskal_by_date.get(date_str, [])
            mengenliste = mengenlisten_by_date.get(date_str)
            date_bestellungen = bestellungen_by_date.get(date_str, [])

            master_articles, unmapped_fiskal = self._process_fiskal_transactions(
                date_transactions
            )

            unmapped_mengenlisten = []
            if mengenliste:
                unmapped_mengenlisten = self._merge_mengenlisten_data(
                    mengenliste, master_articles
                )

            unmapped_bestellungen = self._process_bestellungen_transactions(
                date_bestellungen, master_articles
            )

            if unmapped_fiskal or unmapped_mengenlisten or unmapped_bestellungen:
                self._write_unmapped_items(
                    unmapped_fiskal, unmapped_mengenlisten, unmapped_bestellungen, date_str
                )

            total_revenue = sum(
                article.total_sales for article in master_articles.values()
            )

            consolidated_data[date_str] = ConsolidatedProductData(
                date=date_str,
                total_revenue=total_revenue,
                master_articles=master_articles,
            )

        return consolidated_data

    def _parse_fiskal_transactions(
        self, transactions_data: List[dict]
    ) -> List[Transaction]:
        transactions = []
        for txn_data in transactions_data:
            # Convert date and time strings to datetime
            date_str = txn_data["date"]
            time_str = txn_data["time"]
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

            # Parse line items from sales
            items = []
            for sale in txn_data["sales"]:
                article = sale["article"]
                line_item = LineItem(
                    article_number=int(article["article_number"]),
                    article_name=article["article_name"],
                    quantity=Decimal(article["quantity"]),
                    category=article["category"],
                    category_number=int(article["category_number"]),
                    price=Decimal(article["price"]),
                )
                items.append(line_item)

            # Create transaction
            transaction = Transaction(
                uuid=txn_data["UUID"],
                date=dt,
                bill_number=int(txn_data["bill_number"]),
                items=items,
                total_gross=Decimal(txn_data["sum"]),
            )
            transactions.append(transaction)

        return transactions

    def _group_fiskal_by_date(
        self, transactions: List[Transaction]
    ) -> Dict[str, List[Transaction]]:
        fiskal_by_date = {}
        for transaction in transactions:
            date_str = transaction.date.strftime("%Y-%m-%d")
            if date_str not in fiskal_by_date:
                fiskal_by_date[date_str] = []
            fiskal_by_date[date_str].append(transaction)
        return fiskal_by_date

    def _load_mengenlisten_directory(
        self, mengenlisten_dir_path: Path
    ) -> Dict[str, Mengenliste]:
        mengenlisten_by_date = {}

        if not mengenlisten_dir_path.exists():
            return mengenlisten_by_date

        for json_file in mengenlisten_dir_path.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    mengenliste_data = json.load(f)

                for date_str, mengenliste_dict in mengenliste_data.items():
                    # Add missing report_date field from the date_str key
                    mengenliste_dict["report_date"] = date_str
                    mengenliste = Mengenliste(**mengenliste_dict)
                    mengenlisten_by_date[date_str] = mengenliste
            except Exception as e:
                print(f"Warning: Could not load mengenliste file {json_file}: {e}")

        return mengenlisten_by_date

    def _parse_bestellungen_data(self, bestellungen_path: Path) -> List[Order]:
        """Parse bestellungen JSON extract and return list of Order objects"""
        with open(bestellungen_path, "r", encoding="utf-8") as f:
            bestellungen_data = json.load(f)
        
        orders = []
        for order_id, order_data in bestellungen_data.items():
            # Convert pickup_date string to date
            pickup_date_str = order_data["pickup_date"]
            pickup_date = datetime.strptime(pickup_date_str, "%Y-%m-%d").date()
            
            # Parse line items
            line_items = []
            for item_data in order_data["sales"]:
                line_item = BestellungLineItem(
                    article_name=item_data["article_name"],
                    quantity=Decimal(str(item_data["quantity"])),
                    price=Decimal(str(item_data["price"]))
                )
                line_items.append(line_item)
            
            # Create Order
            order = Order(
                id=order_id,
                pickup_date=pickup_date,
                sales=line_items,
                sum=Decimal(str(order_data["sum"]))
            )
            orders.append(order)
            
        return orders

    def _group_bestellungen_by_date(self, orders: List[Order]) -> Dict[str, List[Order]]:
        """Group orders by pickup date"""
        bestellungen_by_date = {}
        for order in orders:
            date_str = order.pickup_date.strftime("%Y-%m-%d")
            if date_str not in bestellungen_by_date:
                bestellungen_by_date[date_str] = []
            bestellungen_by_date[date_str].append(order)
        return bestellungen_by_date

    def _process_bestellungen_transactions(
        self, orders: List[Order], master_articles: Dict[str, MasterArticleData]
    ) -> List[str]:
        """Process bestellungen orders and update master articles, return unmapped items"""
        unmapped_items = []
        
        for order in orders:
            for item in order.sales:
                article_name = item.article_name
                
                if article_name in self.lookup_table.variant_to_master:
                    master_name = self.lookup_table.variant_to_master[article_name]
                    
                    # Create master article entry if it doesn't exist
                    if master_name not in master_articles:
                        master_articles[master_name] = MasterArticleData(
                            master_name=master_name,
                            total_sales=Decimal("0"),
                            total_quantity=Decimal("0"),
                        )
                    
                    # Add bestellungen data to sales quantities
                    master_articles[master_name].total_quantity += item.quantity
                    master_articles[master_name].total_sales += item.price * item.quantity
                    
                else:
                    if article_name not in unmapped_items:
                        unmapped_items.append(article_name)
        
        return unmapped_items

    def _process_fiskal_transactions(
        self, transactions: List[Transaction]
    ) -> Tuple[Dict[str, MasterArticleData], List[str]]:
        master_articles = {}
        unmapped_items = []

        for transaction in transactions:
            for item in transaction.items:
                article_name = item.article_name

                if article_name in self.lookup_table.variant_to_master:
                    master_name = self.lookup_table.variant_to_master[article_name]

                    if master_name not in master_articles:
                        master_articles[master_name] = MasterArticleData(
                            master_name=master_name,
                            total_sales=Decimal("0"),
                            total_quantity=Decimal("0"),
                        )

                    master_articles[master_name].total_sales += item.price
                    master_articles[master_name].total_quantity += item.quantity

                else:
                    if article_name not in unmapped_items:
                        unmapped_items.append(article_name)

        return master_articles, unmapped_items

    def _merge_mengenlisten_data(
        self, mengenliste: Mengenliste, master_articles: Dict[str, MasterArticleData]
    ) -> List[str]:
        unmapped_items = []

        for entry in mengenliste.articles:
            article_name = entry.article_name

            if article_name in self.lookup_table.variant_to_master:
                master_name = self.lookup_table.variant_to_master[article_name]

                # Create master article entry if it doesn't exist (mengenlisten-only article)
                if master_name not in master_articles:
                    master_articles[master_name] = MasterArticleData(
                        master_name=master_name,
                        total_sales=Decimal("0"),
                        total_quantity=Decimal("0"),
                    )

                # Update with mengenlisten data
                master_articles[master_name].leftover = entry.leftover
                master_articles[master_name].sold_out_time = entry.sold_out

            else:
                if article_name not in unmapped_items:
                    unmapped_items.append(article_name)

        return unmapped_items

    def _write_unmapped_items(
        self, unmapped_fiskal: List[str], unmapped_mengenlisten: List[str], unmapped_bestellungen: List[str], date: str
    ):
        qc_dir = Path("data/qc")
        qc_dir.mkdir(parents=True, exist_ok=True)

        qc_data = {
            "date": date,
            "unmapped_fiskal_items": unmapped_fiskal,
            "unmapped_mengenlisten_items": unmapped_mengenlisten,
            "unmapped_bestellungen_items": unmapped_bestellungen,
        }

        qc_file_path = qc_dir / f"unmapped_items_{date}.json"
        with open(qc_file_path, "w", encoding="utf-8") as f:
            json.dump(qc_data, f, indent=2, ensure_ascii=False)

    def write_monthly_consolidated_data(
        self, consolidated_data: Dict[str, ConsolidatedProductData], output_path: Path
    ):
        """Write consolidated monthly data to JSON file."""
        serialized_data = {}
        for date_str, data in consolidated_data.items():
            serialized_data[date_str] = data.model_dump()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False, default=str)
