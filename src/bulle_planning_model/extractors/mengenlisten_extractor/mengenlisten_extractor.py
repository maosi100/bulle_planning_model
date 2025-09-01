import json
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from extractors.mengenlisten_extractor.mengenliste import Mengenliste
from extractors.mengenlisten_extractor.metadata import MengenlisteMetadata
from extractors.mengenlisten_extractor.mengenliste_entry import MengenlisteEntry
from extractors.mengenlisten_extractor.gemini_client import GeminiClient


class MengenlistenExtractor:
    def __init__(self):
        self.ai_client = GeminiClient()
        self.metadata: Optional[MengenlisteMetadata] = None
        self.unparsed_blocks: List[str] = []

    def read_file(self, file_path: Path) -> Optional[Mengenliste]:
        logger.info(f"Starting extraction from {file_path}")

        json_response = self.ai_client.generate_response(file_path)

        if not json_response:
            logger.error(f"Failed to get response from AI client for {file_path}")
            self.unparsed_blocks.append(str(file_path))
            self.metadata = MengenlisteMetadata(
                source_file=str(file_path), errors=["Failed to get AI response"]
            )
            return None

        try:
            mengenliste = self._parse_json_response(json_response)
            self.metadata = MengenlisteMetadata(source_file=str(file_path))
            logger.info(f"Successfully extracted data from {file_path}")
            return mengenliste

        except Exception as e:
            logger.error(f"Failed to parse AI response for {file_path}: {e}")
            self.unparsed_blocks.append(str(file_path))
            self.metadata = MengenlisteMetadata(
                source_file=str(file_path), errors=[f"Failed to parse AI response: {e}"]
            )
            return None

    def convert_to_json(self, mengenliste: Mengenliste, output_path: Path) -> None:
        json_data = {
            mengenliste.report_date.strftime("%Y-%m-%d"): {
                "production_day": mengenliste.production_day,
                "sales_day": mengenliste.sales_day,
                "articles": [
                    {
                        "article_name": article.article_name,
                        "stock": article.stock,
                        "leftover": article.leftover,
                        "sold_out": article.sold_out,
                    }
                    for article in mengenliste.articles
                ],
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved mengenliste data to {output_path}")

    def save_unparsed_blocks(self, output_path: Path) -> None:
        if not self.unparsed_blocks:
            logger.info("No unparsed blocks to save")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Unparsed PDF Files ({len(self.unparsed_blocks)} total)\n")
            f.write("=" * 60 + "\n\n")

            for i, file_path in enumerate(self.unparsed_blocks, 1):
                f.write(f"File {i}: {file_path}\n")
                f.write("-" * 40 + "\n\n")

        logger.info(
            f"Saved {len(self.unparsed_blocks)} unparsed files to {output_path}"
        )

    def _parse_json_response(self, json_string: str) -> Mengenliste:
        try:
            raw_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI response: {e}")
            logger.debug(f"Raw JSON: {json_string}")
            raise ValueError(f"Invalid JSON from AI: {e}")

        date_key = list(raw_data.keys())[0]
        data = raw_data[date_key]

        date_obj = datetime.strptime(date_key, "%Y-%m-%d").date()

        articles = []
        for article_data in data.get("articles", []):
            article = MengenlisteEntry(
                article_name=article_data["article_name"],
                stock=article_data.get("stock"),
                leftover=article_data.get("leftover"),
                sold_out=article_data.get("sold_out"),
            )
            articles.append(article)

        return Mengenliste(
            report_date=date_obj,
            production_day=data["production_day"],
            sales_day=data["sales_day"],
            articles=articles,
        )
